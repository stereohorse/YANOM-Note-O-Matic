from abc import ABC, abstractmethod
import logging
import re

from bs4 import BeautifulSoup

import config


def what_module_is_this():
    return __name__


def enable_checklist_tags(html_content):
    """Enable input tags"""
    soup = BeautifulSoup(html_content, 'html.parser')
    input_tags = soup.find_all('input', type="checkbox")
    for tag in input_tags:
        del tag['disabled']

    return str(soup)


class ChecklistItem:
    def __init__(self):
        self.checked = False
        self._indent = 0
        self._sibling_extra_indent = 0
        self._placeholder_text = ''
        self._markdown_item_text = ''
        self._create_placeholder_text()

    def _create_placeholder_text(self):
        self._placeholder_text = f'checklist-placeholder-id-{str(id(self))}'

    def generate_markdown_item_text(self):
        tabs = '\t' * self._indent
        checked = ' '
        if self.checked:
            checked = 'x'

        self._markdown_item_text = f"{tabs}- [{checked}]"

    @property
    def placeholder_text(self):
        return self._placeholder_text

    @property
    def indent(self):
        return self._indent

    @indent.setter
    def indent(self, value):
        self._indent = int(value)

    @property
    def markdown_item_text(self):
        return self._markdown_item_text

    @property
    def sibling_extra_indent(self):
        return self._sibling_extra_indent

    @sibling_extra_indent.setter
    def sibling_extra_indent(self, value: int):
        self._sibling_extra_indent = value


class ChecklistProcessor(ABC):
    def __init__(self, html_content):
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                        f'{what_module_is_this()}.'
                                        f'{self.__class__.__name__}'
                                        )
        self.logger.setLevel(config.yanom_globals.logger_level)
        self._raw_html = html_content
        self._processed_html = ''
        self._list_of_checklist_items = []
        self._soup = BeautifulSoup(self._raw_html, 'html.parser')
        self._checklist_pre_processing()

    @property
    def processed_html(self):
        return self._processed_html

    @property
    def list_of_checklist_items(self):
        return self._list_of_checklist_items

    def _calculate_indents(self):
        self.logger.debug("Generate cleaned checklists")
        set_of_indents = {item.indent for item in self._list_of_checklist_items}

        list_of_indents = sorted(set_of_indents)

        indent_level_lookup = {list_of_indents[level]: level for level in range(0, len(list_of_indents))}

        for item in self._list_of_checklist_items:
            item.indent = indent_level_lookup[item.indent] + item.sibling_extra_indent

    def generate_markdown_checklist_item_text(self):
        for item in self._list_of_checklist_items:
            item.generate_markdown_item_text()

    @abstractmethod
    def _checklist_pre_processing(self):  # pragma: no cover
        pass

    @abstractmethod
    def find_all_checklist_items(self):  # pragma: no cover
        pass

    @staticmethod
    @abstractmethod
    def find_checked_status(tag):  # pragma: no cover
        pass

    @abstractmethod  # pragma: no cover
    def update_tags(self, tag, this_checklist_item):
        pass

    @staticmethod
    def find_indent(tag):
        if 'style' in tag.parent.attrs:
            style = tag.parent.attrs['style']
            match = re.findall(r'(?:padding|margin)-left[^\d]*(\d+)', style)
            if match:
                return int(match[0])
        return 0


class HTMLInputMDOutputChecklistProcessor(ChecklistProcessor):
    def find_all_checklist_items(self):
        self.logger.debug("Searching for checklist items")
        return self._soup.select('input[type="checkbox"]')

    @staticmethod
    def find_checked_status(tag):
        return 'checked' in tag.attrs

    def _checklist_pre_processing(self):
        """
        Pre-process content for checklist items, gather information on the item and update the content.

        Identify input tags in the content. Obtain the checked status and calculate the indent required for displaying
        correctly in a hieratical checklist.  Place a placeholder id into the content to be replaced in post processing
        by the required formatted markdown.  The original input tag is removed as no longer required.

        """
        self.logger.debug("Pre process checklists")
        checklists = self.find_all_checklist_items()

        self._pre_process_html_tags(checklists)
        self._calculate_indents()

        self.generate_markdown_checklist_item_text()

        self._processed_html = str(self._soup)

    def _pre_process_html_tags(self, checklists):
        extra_indents = {}  # key is checklist tag index, value is amount of indent to add in markdown
        for i in range(len(checklists)):
            this_checklist_item = ChecklistItem()
            this_checklist_item.checked = self.find_checked_status(checklists[i])

            # if there were multiple sibling input tags we already have them no need to look at them again
            if i not in extra_indents.keys():
                new_indents = self.find_extra_indent_for_sibling_checklist_items(checklists[i], i)
                extra_indents = {**extra_indents, **new_indents}

            this_checklist_item.sibling_extra_indent = extra_indents.get(i, 0)

            this_checklist_item.indent = self.find_indent(checklists[i])

            self.update_tags(checklists[i], this_checklist_item)

            # Remove the input tag as no longer needed.
            # The information it held is now in this_checklist_item and the placeholder-id is in next navigable string
            # and will be uses in post processing to put the information from this_checklist_item into the content again
            checklists[i].decompose()

            self._list_of_checklist_items.append(this_checklist_item)

    @staticmethod
    def find_extra_indent_for_sibling_checklist_items(tag, index) -> dict:
        """
        Identify input tags that are siblings of the tag provided and return dict with sibling index and indent.

        If the html content has more than one checklist item on a line identify the siblings of the first input tag
        on that line.
        These sibling input tags need an indent to make them a child checklist item.
        so,
        [x] An item [x] another item
        becomes,
        - [x] An item
            - [x] another item

        Return a dict with the key = index of the sibling and indent value = 1 e.g. {2:1, 3:1}.

        Parameters
        ----------
        tag : BeautifulSoup Tag Element
            An input tag that may have siblings that are also input tags.
        index : int
            Index of the tag in a list of tags.  Next sibling, if any, will be at index + 1 etc.

        Returns
        -------
        dict of {int: int}
            Dictionary where key is the index of the tag that needs an additional indent
            and the value is the indent amount.
        """
        new_indents = {}
        num_siblings = 0
        for _sibling in tag.find_next_siblings('input'):
            num_siblings += 1
            new_indents[index + num_siblings] = 1

        return new_indents

    def update_tags(self, tag, this_checklist_item):
        """
        Add a place holder id to the navigable string for the tag provided.

        If the tag has a next sibling and the tag does not have a previous sibling add the placeholder id to that
        start of it's the next siblings NavigableString.
        If the tag has a next sibling and has a previous sibling then it is a second checklist on the same line.
        Wrap it in a 'p' tag and add the placeholder id to that start of it's next siblings NavigableString.
        If the tag does not have sibling replace it in a 'p' tag with the placeholder id in the NavigableString.

        Parameters
        ----------
        tag : Beautifulsoup.Tag
            An input tag element.
        this_checklist_item :  ChecklistItem
            ChecklistItem object holding details of the tag

        """
        # check if there is another item and if there is a navigable string
        if tag.next_sibling and tag.next_sibling.string:
            if tag.previousSibling is None:
                tag.next_sibling.string.replace_with(
                    f'{this_checklist_item.placeholder_text} {tag.next_sibling.string}')
            else:
                # if there is a previous sibling we have a second checklist item on the same line
                # so we wrap in p tag to get it on it's own line
                new_tag = self._soup.new_tag("p")
                tag.next_sibling.string.replace_with(
                    f'{this_checklist_item.placeholder_text} {tag.next_sibling.string}')
                tag.next_sibling.string.wrap(new_tag)
        else:  # checklist item has no navigable string so add one to it
            new_tag = self._soup.new_tag('p')
            new_tag.string = f'{this_checklist_item.placeholder_text}'
            tag.wrap(new_tag)

    def checklist_post_processing(self, content):
        self.logger.debug(f"Add checklists to page")
        for item in self._list_of_checklist_items:
            # NOTE this may cause issues with html formats not yet imagined to be tested against.  works so far....
            search_for = rf'-*\ *{item.placeholder_text}'
            replace_with = f'{item.markdown_item_text}'
            content, count_of_subs = re.subn(search_for, replace_with, content)
        return content


class NSXInputMDOutputChecklistProcessor(HTMLInputMDOutputChecklistProcessor):
    def find_all_synology_checklist_items(self):
        self.logger.debug("Searching for checklist items")
        synology_tags = self._soup.find_all(class_="syno-notestation-editor-checkbox")
        return synology_tags

    @staticmethod
    def find_checked_status_synology(tag):
        return 'syno-notestation-editor-checkbox-checked' in tag.attrs['class']

    def _checklist_pre_processing(self):
        """
        Pre-process content for checklist items, gather information on the item and update the content.

        Identify input tags in the content. Obtain the checked status and calculate the indent required for displaying
        correctly in a hieratical checklist.  Place a placeholder id into the content to be replaced in post processing
        by the required formatted markdown.  The original input tag is removed as no longer required.

        """
        self.logger.debug("Pre process checklists")
        synology_checklists = self.find_all_synology_checklist_items()
        self._pre_process_synology_tags(synology_checklists)

        html_checklists = self.find_all_checklist_items()
        self._pre_process_html_tags(html_checklists)

        self._calculate_indents()
        self.generate_markdown_checklist_item_text()

        self._processed_html = str(self._soup)

    def _pre_process_synology_tags(self, checklists):
        for tag in checklists:
            this_checklist_item = ChecklistItem()
            this_checklist_item.checked = self.find_checked_status_synology(tag)
            self.update_synology_tags(tag, this_checklist_item)
            self._list_of_checklist_items.append(this_checklist_item)

    def update_synology_tags(self, tag, this_checklist_item):
        self.logger.debug("Cleaning nsx checklist items")
        del tag['class']
        del tag['src']
        del tag['type']
        if this_checklist_item.checked:
            tag['checked'] = ''
        tag['type'] = 'checkbox'


class NSXInputHTMLOutputChecklistProcessor(ChecklistProcessor):
    def find_all_checklist_items(self):
        self.logger.debug("Searching for checklist items")
        return self._soup.find_all(class_="syno-notestation-editor-checkbox")

    @staticmethod
    def find_checked_status(tag):
        return 'syno-notestation-editor-checkbox-checked' in tag.attrs['class']

    def update_tags(self, tag, this_checklist_item):
        self.logger.debug("Cleaning nsx checklist items")
        del tag['class']
        del tag['src']
        del tag['type']
        if this_checklist_item.checked:
            tag['checked'] = ''
        tag['type'] = 'checkbox'

    def _checklist_pre_processing(self):
        """
        Correct formatting of synology checklist items.

        Identify synology formatted input tags in the content. obtain the checked status and updating the tags by
        removing unused attributes, setting the checked status and a valid input tag type.
        Finally update the html content with the modified tags.

        """
        self.logger.debug("Pre process checklists")
        checklists = self.find_all_checklist_items()
        self._pre_process_synology_tags(checklists)
        self._processed_html = str(self._soup)

    def _pre_process_synology_tags(self, checklists):
        self.logger.info("Pre-processing synology formatted checklists")
        for tag in checklists:
            this_checklist_item = ChecklistItem()
            this_checklist_item.checked = self.find_checked_status(tag)
            self.update_tags(tag, this_checklist_item)
            self._list_of_checklist_items.append(this_checklist_item)
