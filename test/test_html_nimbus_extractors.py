import datetime
from pathlib import Path

from bs4 import BeautifulSoup
import pytest

from embeded_file_types import EmbeddedFileTypes
import helper_functions
import html_data_extractors
import html_nimbus_extractors
from nimbus_note_content_data import EmbedNimbus, NimbusProcessingOptions
from nimbus_note_content_data import FileEmbedNimbusHTML, NimbusToggle
from nimbus_note_content_data import MentionFolder, MentionNote, MentionUser, MentionWorkspace
from nimbus_note_content_data import NimbusDateItem
from nimbus_note_content_data import TableCheckItem, TableCollaborator
from note_content_data import BlockQuote, Break, BulletList, BulletListItem
from note_content_data import Caption
from note_content_data import Figure
from note_content_data import ImageEmbed
from note_content_data import TextFormatItem, Title
from note_content_data import Checklist, ChecklistItem
from note_content_data import CodeItem
from note_content_data import HeadingItem, Paragraph
from note_content_data import Hyperlink
from note_content_data import NumberedList, NumberedListItem
from note_content_data import Outline, OutlineItem
from note_content_data import Table, TableItem, TableHeader, TableRow
from note_content_data import TextItem


@pytest.fixture
def processing_options() -> NimbusProcessingOptions:
    embed_these_document_types = ['md', 'pdf']
    embed_these_image_types = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']
    embed_these_audio_types = ['mp3', 'webm', 'wav', 'm4a', 'ogg', '3gp', 'flac']
    embed_these_video_types = ['mp4', 'webm', 'ogv']
    embed_files = EmbeddedFileTypes(embed_these_document_types, embed_these_image_types,
                                    embed_these_audio_types, embed_these_video_types)

    filename_options = helper_functions.FileNameOptions(max_length=255,
                                                        allow_unicode=True,
                                                        allow_uppercase=True,
                                                        allow_non_alphanumeric=True,
                                                        allow_spaces=False,
                                                        space_replacement='-')
    export_format = 'obsidian'
    unrecognised_tag_format = 'html'
    keep_nimbus_row_and_column_headers = False

    return NimbusProcessingOptions(embed_files,
                                   export_format,
                                   unrecognised_tag_format,
                                   filename_options,
                                   keep_nimbus_row_and_column_headers,
                                   )


class TestProcessChildItems:
    def test_process_child_items(self, processing_options):
        html = '<head><title>My Title</title></head>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('head')
        result = html_nimbus_extractors.process_child_items(tag, processing_options)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Title)

    def test_process_child_items_mulitple_child_levels(self, processing_options):
        html = '<head><title>My Title</title><p>paragraph</p><p>paragraph2<p>paragraph3</p></p></head>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('head')
        result = html_nimbus_extractors.process_child_items(tag, processing_options)

        assert isinstance(result, list)
        assert len(result) == 4
        assert isinstance(result[0], Title)
        assert isinstance(result[1], TextItem)

    def test_process_child_items_with_navigable_strings(self, processing_options):
        html = '<head>\n<title>My Title</title>\n</head>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('head')
        result = html_nimbus_extractors.process_child_items(tag, processing_options)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Title)


class TestExtractFromNimbusTag:

    def test_extract_from_tag_unrecognised_tag(self, processing_options):
        html = '<head><title>My Title</title></head>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('head')
        result = html_nimbus_extractors.extract_from_nimbus_tag(tag, processing_options)

        assert result is None

    @pytest.mark.parametrize(
        'html, tag_type, exp_type', [
            (
                    """<ul class="editor-list number-template-decimal-all" id="b788977277_51"><li class="list-item-checkbox editable-text list-item indent-0" data-checked="false" id="b788977277_57" style="text-align: left;">check 1</li><li class="list-item-checkbox editable-text list-item indent-1" data-checked="false" id="b788977277_78" style="text-align: left;">check <strong>level</strong> 2</li><li class="list-item-checkbox editable-text list-item indent-1" data-checked="true" id="b788977277_105" style="text-align: left;">check <strong><em>level</em></strong> 2 item 2</li><li class="list-item-checkbox editable-text list-item indent-0" data-checked="false" id="b788977277_136" style="text-align: left;">check <em>level</em> 1 item 2, below is an empty check item</li><li class="list-item-checkbox editable-text list-item indent-0" data-checked="false" id="b1786634969_7" style="text-align: left;"><br/></li></ul>""",
                    'ul',
                    Checklist),
            (
                    """<mention class="mention" data-mention-id="gbb91m" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-type="note" data-mention-workspace_id="23c421363hn6ndes">﻿<span class="mention-link" contenteditable="false" data-mention-id="gbb91m" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-type="note" data-mention-workspace_id="23c421363hn6ndes"><a href="https://nimbusweb.me/ws/23c421363hn6ndes/zEZUSiVmAQPITGLD" target="_blank">Test 1</a></span>﻿</mention>""",
                    'mention',
                    MentionNote),
            (
                    """<div class="embed-wrapper image-wrapper indent-0" data-block-background="transparent" data-content-align="center"><div class="image" contenteditable="false" id="b788977277_455"><div class="resize-container disabled-resize" style="width: 489.015625px; --width: 489.015625px; height: 283px;"><div class="image-container" contenteditable="false"><a href="./assets/0UJGinY2jASIj13F.png" target="_blank"><img class="img-hide" src="./assets/0UJGinY2jASIj13F.png"/></a></div></div></div><div class="editable-text attachment-caption" id="b788977277_460" style="text-align: center; width: 489.015625px;">An image caption</div></div>""",
                    'div',
                    Figure),
            (
                    """<div class="embed-wrapper file-wrapper"><div class="file" id="b788977277_491"><div class="file-container view-mode-full" contenteditable="false"><div class="file-too-small"><div class="compact-view-content"><div class="file-left"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h24v24H0z"></path> <path class="graphic" d="M12 4H7a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-9h-5a1 1 0 0 1-1-1V4zm8 5.008V19a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3h5.992L20 9.008zM14 8V5.414L16.586 8H14zm-6 9a1 1 0 0 1 1-1h6a1 1 0 0 1 0 2H9a1 1 0 0 1-1-1zm1-5a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2H9z" fill="#5C6061"></path> </g></svg></div><div class="file-info file-name-trim-end"><div><span class="file-name" data-editor-toolip="Download test page.pdf" data-editor-tooltip-options='{"positionFixed":true}' data-file-export="b788977277_491.end"><a href="./assets/OFVVRj4UIjtz4S5T.pdf" target="_blank"><span><span class="file-name-main">test page.</span><span class="file-name-ext">pdf</span></span></a></span><span class="file-size">(320.36 kB)</span></div></div></div></div></div></div><div class="editable-text attachment-caption" id="b788977277_496" style="text-align: center; width: 100%;">an attachment caption</div></div>""",
                    'div',
                    FileEmbedNimbusHTML),
            ("""<div class="embed-wrapper table-wrapper export"><div class="table-blot" contenteditable="false" id="b788977277_649"><div class="table-embed"><div class="table-scroll"><div class="table-scroll-items"><table class="table-component"><thead><tr><th class="table-head-start"><div class="table-header-circle"></div></th><th></th><th class="table-head-item" data-index="0" width="180"><div class="item-ui"><div class="item-title" style="max-width: 136px;">A</div></div></th><th class="table-head-item" data-index="1" width="180"><div class="item-ui"><div class="item-title" style="max-width: 136px;">B</div></div></th><th class="table-head-item" data-index="2" width="180"><div class="item-ui"><div class="item-title" style="max-width: 136px;">C</div></div></th></tr></thead><tbody><tr height="36"><td class="table-head-item" data-index="0" height="36"><div class="item-ui"><div class="item-title">1</div></div></td><td></td><td><div class="table-text-common">r1c1
</div></td><td><div class="table-text-common">r1c2
</div></td><td><div class="table-text-common">r1c3
</div></td></tr><tr height="36"><td class="table-head-item" data-index="1" height="36"><div class="item-ui"><div class="item-title">2</div></div></td><td></td><td><div class="table-text-common">r2c1
</div></td><td><div class="table-text-common">r2c2
</div></td><td><div class="table-text-common">r2c2
</div></td></tr><tr height="36"><td class="table-head-item" data-index="2" height="36"><div class="item-ui"><div class="item-title">3</div></div></td><td></td><td><div class="table-text-common">12%
</div></td><td><div class="table-text-common">1234
</div></td><td></td></tr><tr height="36"><td class="table-head-item" data-index="3" height="36"><div class="item-ui"><div class="item-title">4</div></div></td><td></td><td><div class="table-text-common">23</div></td><td><div class="table-text-common">$109</div></td><td class="cell-attachment"><div class="table-attachment-wrap"><div><div class="table-attachment"><div class="attachment-item"></div></div></div></div></td></tr><tr height="36"><td class="table-head-item" data-index="4" height="36"><div class="item-ui"><div class="item-title">5</div></div></td><td></td><td><span class="checkbox-component"></span></td><td><span class="checkbox-component checked"></span></td><td class="full-height"><div class="select-component"><div class="select-list"><span class="select-label adaptive-text bg-palette-brown"><span class="select-label-text">singel select</span></span></div></div></td></tr><tr height="36"><td class="table-head-item" data-index="5" height="36"><div class="item-ui"><div class="item-title">6</div></div></td><td></td><td class="full-height"><div class="select-component"><div class="select-list"><span class="select-label adaptive-text bg-palette-green-sea"><span class="select-label-text">select 1</span></span><span class="select-label adaptive-text bg-palette-yellow"><span class="select-label-text">select 2</span></span></div></div></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="rfusba" data-mention-name="kevindurston21@gmail.com" data-mention-object_id="2510963" data-mention-type="user">kevindurston21@gmail.com</span></span></td><td class="full-height"><div class="collaborate-component"><div class="collaborate-list"><span class="collaborate-item" data-mention-id="rd0qzj" data-mention-name="kevindurston21@gmail.com" data-mention-type="user" data-user-id="2510963"><span class="collaborate-item-img"><span class="user-avatar" style="background: rgb(250, 201, 47);">K</span></span><span class="collaborate-item-name"><span class="collaborate-item-text">kevindurston21@gmail.com</span></span></span></div></div></td></tr><tr height="36"><td class="table-head-item" data-index="6" height="36"><div class="item-ui"><div class="item-title">7</div></div></td><td></td><td class="cell-date table-text-common"><span class="input-date"><span class="input-date-string"><span class="input-date-text">11/01/2022 22:03</span></span></span></td><td><div class="table-text-common"><a href="https://www.google.com" rel="nofollow noopener" target="_blank">a link in a cell</a></div></td><td><div class="rating-component"><span class="rating-item rating-active"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#fda639" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-active"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#fda639" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-active"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#fda639" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-inactive"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#e8e8e8" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-inactive"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#e8e8e8" fill-rule="evenodd"></path></svg></span></div></td></tr><tr height="36"><td class="table-head-item" data-index="7" height="36"><div class="item-ui"><div class="item-title">8</div></div></td><td></td><td class="cell-progress"><div class="table-progress progress-low"><div class="input-slider readonly table-progress-slider"><span class="slider-range"><span class="slider-progress" style="width: 0%;"><span class="slider-holder"></span></span></span></div><span class="progress-value table-text-common">0%</span></div></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="hu4brg" data-mention-name="Default workspace" data-mention-object_id="23c421363hn6ndes" data-mention-type="workspace">Default workspace</span></span></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="a9k6af" data-mention-name="another topic subfolder renamed" data-mention-object_id="TvjfOrJ0NtSLV3KH" data-mention-type="folder">another topic subfolder renamed</span></span></td></tr><tr height="36"><td class="table-head-item" data-index="8" height="36"><div class="item-ui"><div class="item-title">9</div></div></td><td></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="lzcl03" data-mention-name="Emoji - 😀  - note title" data-mention-object_id="fnk139kSrRzJOEVd" data-mention-type="note">Emoji - 😀  - note title</span></span></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="m4tjz1" data-mention-name="The attached file above is exported but not linked in html" data-mention-object_id="Asl0q2f5F4TGCWSx" data-mention-type="note">The attached file above is exported but not linked in html</span></span></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="j5bjyn" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-type="note">Test 1</span></span></td></tr></tbody><tfoot><tr><td class="add-row"></td><td></td><td><div class="summary-wrap"><div class="summary-item"><span class="summary-name overflow-ellipsis">Percent empty</span>:<div class="summary-value" data-editor-toolip="22.22%" data-editor-tooltip-options='{"positionFixed":true,"modifiers":{"offset":{"offset":"0,0"}}}' valuelength="6">22.22%</div><span class="summary-menu-icon"><svg height="16" viewbox="0 0 16 16" width="16" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h16v16H0z"></path> <path class="graphic" d="M4 7h8l-4 4z" fill="#AEB7B8"></path> </g></svg></span></div></div></td><td><div class="summary-wrap"><div class="summary-item"><span class="summary-name">All</span>:<div class="summary-value" data-editor-toolip="9" data-editor-tooltip-options='{"positionFixed":true,"modifiers":{"offset":{"offset":"0,0"}}}' valuelength="1">9</div><span class="summary-menu-icon"><svg height="16" viewbox="0 0 16 16" width="16" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h16v16H0z"></path> <path class="graphic" d="M4 7h8l-4 4z" fill="#AEB7B8"></path> </g></svg></span></div></div></td><td><div class="summary-wrap"><div class="summary-item"><span class="summary-name">All</span>:<div class="summary-value" data-editor-toolip="9" data-editor-tooltip-options='{"positionFixed":true,"modifiers":{"offset":{"offset":"0,0"}}}' valuelength="1">9</div><span class="summary-menu-icon"><svg height="16" viewbox="0 0 16 16" width="16" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h16v16H0z"></path> <path class="graphic" d="M4 7h8l-4 4z" fill="#AEB7B8"></path> </g></svg></span></div></div></td></tr></tfoot></table></div></div></div><div class="table-blot-edit-area"></div></div><div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b788977277_666" style="text-align: center; width: 50px;"><br/></div></div>""",
             'div',
             Table),
            (
                    """<div class="horizontal-line" contenteditable="false" id="b406348235_72"><hr data-linetype="undefined"/></div>""",
                    'div',
                    TextItem),  # horizontal rule <hr>
            (
                    """<div class="embed-wrapper remote-frame-wrapper"><div class="exported-remote-frame as-iframe"><iframe allowfullscreen="allowfullscreen" sandbox="allow-scripts allow-same-origin allow-popups allow-forms" src="https://www.youtube.com/embed/bWbYWOMVkyY" style="width:1000px;height:562.5px;border:0;"></iframe></div><div class="editable-text attachment-caption" id="b1023299123_1339" style="text-align: center; width: 100%;">caption after an embed</div></div>""",
                    'div',
                    list),  # iframe embed
            (
                    """<div class="editable-text attachment-caption" id="b1023299123_1339" style="text-align: center; width: 100%;">caption after an embed</div>""",
                    'div',
                    Caption),
            (
                    """<div class="nimbus-bookmark" id="b1023299123_1415"><div class="nimbus-bookmark-container" contenteditable="false"><a href="https://www.youtube.com/watch?v=bWbYWOMVkyY" style="display: contents;"><div class="nimbus-bookmark-content is-card" style="max-width: 650px;"><div class="nimbus-bookmark__info"><div class="nimbus-bookmark__info__name">SpaceX Starship Booster Removed, Starship Static Fire, JWST Update, Angara A5 &amp; OneWeb Launch - YouTube</div><a class="nimbus-bookmark__info__src" href="https://www.youtube.com/watch?v=bWbYWOMVkyY"><div class="nimbus-bookmark__icon"><img src="https://www.youtube.com/s/desktop/df3209e6/img/favicon_32x32.png"/></div><div class="nimbus-bookmark__info__src-text">https://www.youtube.com/watch?v=bWbYWOMVkyY</div></a><div class="nimbus-bookmark__info__desc">Save 10% off your first website or domain at https://www.squarespace.com/marcushouse - Coupon Code: MARCUSHOUSEHappy New Year to you all! This year I’m betti...</div></div><div class="nimbus-bookmark__preview"><img src="./assets/xNGMnJrJJ1X3Gyb3.png"/></div></div></a></div></div>""",
                    'div',
                    Paragraph),
            (
                    """<div class="embed-wrapper remote-frame-wrapper"><div class="exported-remote-frame as-link"><a href="&lt;blockquote class=" twitter-tweet"=""></a><p dir="ltr" lang="en"><a href="&lt;blockquote class=" twitter-tweet"="">Sunsets don't get much better than this one over </a><a href="https://twitter.com/GrandTetonNPS?ref_src=twsrc%5Etfw">@GrandTetonNPS</a>. <a href="https://twitter.com/hashtag/nature?src=hash&amp;ref_src=twsrc%5Etfw">#nature</a> <a href="https://twitter.com/hashtag/sunset?src=hash&amp;ref_src=twsrc%5Etfw">#sunset</a> <a href="http://t.co/YuKy2rcjyU">pic.twitter.com/YuKy2rcjyU</a></p>— US Department of the Interior (@Interior) <a href="https://twitter.com/Interior/status/463440424141459456?ref_src=twsrc%5Etfw">May 5, 2014</a> <script async="" charset="utf-8" src="https://platform.twitter.com/widgets.js"></script>"&gt;<blockquote class="twitter-tweet"><p dir="ltr" lang="en">Sunsets don't get much better than this one over <a href="https://twitter.com/GrandTetonNPS?ref_src=twsrc%5Etfw">@GrandTetonNPS</a>. <a href="https://twitter.com/hashtag/nature?src=hash&amp;ref_src=twsrc%5Etfw">#nature</a> <a href="https://twitter.com/hashtag/sunset?src=hash&amp;ref_src=twsrc%5Etfw">#sunset</a> <a href="http://t.co/YuKy2rcjyU">pic.twitter.com/YuKy2rcjyU</a></p>— US Department of the Interior (@Interior) <a href="https://twitter.com/Interior/status/463440424141459456?ref_src=twsrc%5Etfw">May 5, 2014</a></blockquote> <script async="" charset="utf-8" src="https://platform.twitter.com/widgets.js"></script></div><div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b992245780_696" style="text-align: center; width: 50px;"><br/></div></div>""",
                    'div',
                    EmbedNimbus),  # twitter
            (
                    """<div class="embed-wrapper syntax-wrapper"><syntax class="syntax-main editor-syntax" data-nimbus-language="plaintext" id="b406348235_180" spellcheck="false"><div class="syntax-cm-container"><div><div class="syntax-control-wrapper" contenteditable="false"><div class="syntax-control-wrap no-margin" contenteditable="false"><span class="syntax-control-label">Plain Text</span></div></div><pre style="white-space: pre-wrap; ">code section plain text</pre></div></div></syntax><div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b406348235_190" style="text-align: center; width: 50px;"><br/></div></div>""",
                    'div',
                    CodeItem),
            (
                    """<date class="date-inline date-content" data-date-alerts="" data-date-dateid="f9eb39" data-date-format-showtime="true" data-date-format-timeformat="24" data-date-format-timezonegmt="false" data-date-format-type="default" data-date-reminders="" data-date-timestamp="1641424807590"><span contenteditable="false"><span class="input-date"><span class="input-date-string"><span class="input-date-text">05/01/2022 23:20</span></span></span></span>﻿</date>""",
                    'date',
                    NimbusDateItem),
            (
                    """<div class="editable-text paragraph hintblock indent-0" data-block-background="cloudy" data-text="Type something" style="text-align:left;">This is a hint</div>""",
                    'div',
                    BlockQuote),
            (
                    """<div class="nimbus-toggle"><div class="toggle-arrow"><div class="toggle-arrow-icon"><svg fill="none" height="5" viewbox="0 0 8 5" width="8" xmlns="http://www.w3.org/2000/svg"><path class="graphic" d="M1.44948 0L6.55052 0C7.12009 0 7.42736 0.668079 7.05669 1.10053L4.50617 4.07613C4.24011 4.38654 3.75989 4.38654 3.49383 4.07613L0.943309 1.10053C0.572639 0.668079 0.879912 0 1.44948 0Z" fill="#AEB7B8"></path></svg></div></div><div class="nimbus-toggle-header editable-text">toggle block no entries</div><div class="nimbus-toggle-content with-placeholder"><div class="editable-text paragraph indent-0" style="text-align:left;"><br/></div></div></div>""",
                    'div',
                    NimbusToggle),
            (
                    """<div class="outline" id="b406348235_764"><div class="outline-container" contenteditable="false"><div class="outline-content-wrapper"><div class="outline-header"><div class="outline-left"><div class="outline-expand-icon"> </div></div><div class="outline-name">Outline</div></div><div class="outline-body"><ul class="outline-list outline-numbered"><li class="outline-list-item level-0"><a href="#b1023299123_950">A test note of page content</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1009">Testing lists</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1042">Testing inserted files</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1086">Testing a table</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1130">There are only 3 levels of heading in nimbus</a></li><li class="outline-list-item level-0"><a href="#b788977277_831">heading 1</a></li><li class="outline-list-item level-1"><a href="#b788977277_860">heading 2</a></li><li class="outline-list-item level-2"><a href="#b788977277_889">heading 3</a></li><li class="outline-list-item level-0"><a href="#b1023299123_1757">heading with italic text</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1218">Testing the horizontal line</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1266">Link and embeds</a></li><li class="outline-list-item level-1"><a href="#b992245780_93">Code Blocks</a></li><li class="outline-list-item level-1"><a href="#b992245780_132">Nimbus mentions</a></li><li class="outline-list-item level-1"><a href="#b992245780_175">Quoted text</a></li><li class="outline-list-item level-1"><a href="#b992245780_196">Hints</a></li><li class="outline-list-item level-1"><a href="#b992245780_220">Toggle block</a></li><li class="outline-list-item level-1"><a href="#b2183561539_350">Outline (effectively a linked TOC)</a></li><li class="outline-list-item level-1"><a href="#b992245780_450">Nimbus button</a></li><li class="outline-list-item level-1"><a href="#b992245780_478">Text formatting</a></li><li class="outline-list-item level-1"><a href="#b942953620_901">Testing inserted mp3</a></li><li class="outline-list-item level-1"><a href="#b942953620_1059">Test block sections - may or may not export!</a></li><li class="outline-list-item level-1"><a href="#b216345050_62">Adventures in Exporting from Nimbus Notes...</a></li><li class="outline-list-item level-0"><a href="#b942953620_969">This is the end of the file</a></li></ul></div></div></div></div>""",
                    'div',
                    Outline),
            (
                    """<div class="button-single" contenteditable="false" id="b32879378_144"><div class="button-single-container" data-align="left"><nimbus-button class="single-button" data-background="bondi-blue" data-shape="rounded" data-size="small" data-target="_blank" data-type="3d" data-url="https://www.google.com" id="button_001a229e" onclick="window.open('https://www.google.com', '_blank', 'noopener')"><span class="button-content"><b>a button</b></span></nimbus-button></div></div>""",
                    'div',
                    Paragraph),
            ("""<span class="background-color" data-highlight="yellow">This is highlighted. </span>""",
             'span',
             TextFormatItem),
            (
                    """<nimbus-button class="inline-button" data-background="bondi-blue" data-shape="rounded" data-size="small" data-target="_blank" data-title="Click to see " data-type="3d" data-url="https://nimbusweb.me/s/share/4196282/063i1t5kiqlf3gcgm5ny#b4142816705_2" id="button_9e91f9d0" onclick="window.open('https://nimbusweb.me/s/share/4196282/063i1t5kiqlf3gcgm5ny#b4142816705_2', '_blank', 'noopener')">﻿<span class="button-content" contenteditable="false"><b>Click to see </b></span>﻿</nimbus-button>""",
                    'nimbus-button',
                    Hyperlink),
            ("""<nimbus-html class="nimbus-html" id="b3218098446_1"><div class="nimbus-html-container" contenteditable="false"><div class="collapsible-content nimbus-html-wrapper"><div class="collapsible-content-header nimbus-html-header"><div class="collapsible-content-header-left"><div class="collapsible-content-expand-icon expanded"> </div></div><div class="collapsible-content-name"><span class="collapsible-content-name-text" data-editor-toolip="Graduation - Assassin's Creed Unity Wiki Guide - IGN">Graduation - Assassin's Creed Unity Wiki Guide - IGN</span></div></div><div class="collapsible-content-body nimbus-html-body"><div><div><div style="min-height: 83px; font-size: 16px; display: block; min-width: 100%; position: relative;"> <div style="tab-size: 4; line-height: 1.15; box-sizing: border-box; font-size: 16px; color: rgb(37, 38, 39); color-scheme: dark;"><div style="box-sizing: border-box; text-rendering: optimizelegibility; font-family: ars-maquette-web, sans-serif; overflow: auto;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; transition: color 0.2s ease 0s, background 0.2s ease 0s; color: rgb(225, 229, 236);"><span style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; overflow-x: auto; line-height: 32px;"><p style="box-sizing: border-box;"><i style="box-sizing: border-box;">Take note that while it's best to stay stealthy, the challenge will NOT count against you if the guards spot you. As <a href="https://www.ign.com/wikis/assassins-creed-5/Long" style="box-sizing: border-box; color: rgb(135, 167, 224); text-underline-position: under; text-decoration: underline;" title="Long">long</a> as you kill all guards while taking cover (even if they're looking for you), the challenge will be completed.</i></p></div></div></div></div></div></div></span></div></div></div></div></div></div><div><div style="min-height: 360px; font-size: 16px; display: block; min-width: 100%; position: relative;"> <div style="tab-size: 4; line-height: 1.15; box-sizing: border-box; font-size: 16px; color: rgb(37, 38, 39); color-scheme: dark;"><div style="box-sizing: border-box; text-rendering: optimizelegibility; font-family: ars-maquette-web, sans-serif; overflow: auto;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; transition: color 0.2s ease 0s, background 0.2s ease 0s; color: rgb(225, 229, 236);"><span style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; overflow-x: auto;"><span style="box-sizing: border-box; justify-content: center;"><img height="360" src="./assets/JDboVx0Lr0STnnrv.jpeg" style="box-sizing: border-box; cursor: pointer;" width="640"/></span></div></div></div></div></div></div></span></div></div></div></div></div></div><div><div style="min-height: 32px; font-size: 16px; display: block; min-width: 100%; position: relative;"> <div style="tab-size: 4; line-height: 1.15; box-sizing: border-box; font-size: 16px; color: rgb(37, 38, 39); color-scheme: dark;"><div style="box-sizing: border-box; text-rendering: optimizelegibility; font-family: ars-maquette-web, sans-serif; overflow: auto;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; transition: color 0.2s ease 0s, background 0.2s ease 0s; color: rgb(225, 229, 236);"><span style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; overflow-x: auto; line-height: 32px;"><p style="box-sizing: border-box;">When all three guards are down, approach the bell and SABOTAGE it to trigger the next sequence.
</p></div></div></div></div></div></div></span></div></div></div></div></div></div><div><div style="min-height: 360px; font-size: 16px; display: block; min-width: 100%; position: relative;"> <div style="tab-size: 4; line-height: 1.15; box-sizing: border-box; font-size: 16px; color: rgb(37, 38, 39); color-scheme: dark;"><div style="box-sizing: border-box; text-rendering: optimizelegibility; font-family: ars-maquette-web, sans-serif; overflow: auto;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; transition: color 0.2s ease 0s, background 0.2s ease 0s; color: rgb(225, 229, 236);"><span style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; overflow-x: auto;"><span style="box-sizing: border-box; justify-content: center;"><img height="360" src="./assets/mB1zbF8UfzNtqS30.jpeg" style="box-sizing: border-box; cursor: pointer;" width="640"/></span></div></div></div></div></div></div></span></div></div></div></div></div></div><div><div style="min-height: 64px; font-size: 16px; display: block; min-width: 100%; position: relative;"> <div style="tab-size: 4; line-height: 1.15; box-sizing: border-box; font-size: 16px; color: rgb(37, 38, 39); color-scheme: dark;"><div style="box-sizing: border-box; text-rendering: optimizelegibility; font-family: ars-maquette-web, sans-serif; overflow: auto;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; transition: color 0.2s ease 0s, background 0.2s ease 0s; color: rgb(225, 229, 236);"><span style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; overflow-x: auto; line-height: 32px;"><p style="box-sizing: border-box;">After the cutscene, approach the baddie and kill from behind. From there, drop a <a href="https://www.ign.com/wikis/assassins-creed-5/Smoke_Bomb" style="box-sizing: border-box; color: rgb(135, 167, 224); text-underline-position: under; text-decoration: underline;" title="Smoke Bomb">Smoke Bomb</a> on the guards and follow Bellec through the rooftops.
</p></div></div></div></div></div></div></span></div></div></div></div></div></div><div><div style="min-height: 360px; font-size: 16px; display: block; min-width: 100%; position: relative;"> <div style="tab-size: 4; line-height: 1.15; box-sizing: border-box; font-size: 16px; color: rgb(37, 38, 39); color-scheme: dark;"><div style="box-sizing: border-box; text-rendering: optimizelegibility; font-family: ars-maquette-web, sans-serif; overflow: auto;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; transition: color 0.2s ease 0s, background 0.2s ease 0s; color: rgb(225, 229, 236);"><span style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; overflow-x: auto;"><span style="box-sizing: border-box; justify-content: center;"><img height="360" src="./assets/m2RowpIUN2mfZ8LI.jpeg" style="box-sizing: border-box; cursor: pointer;" width="640"/></span></div></div></div></div></div></div></span></div></div></div></div></div></div><div><div style="min-height: 64px; font-size: 16px; display: block; min-width: 100%; position: relative;"> <div style="tab-size: 4; line-height: 1.15; box-sizing: border-box; font-size: 16px; color: rgb(37, 38, 39); color-scheme: dark;"><div style="box-sizing: border-box; text-rendering: optimizelegibility; font-family: ars-maquette-web, sans-serif; overflow: auto;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; transition: color 0.2s ease 0s, background 0.2s ease 0s; color: rgb(225, 229, 236);"><span style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box;"><div style="box-sizing: border-box; overflow-x: auto; line-height: 32px;"><p style="box-sizing: border-box;">Once you've reached the Cafe, enter the doorway and follow Bellec into the chamber to complete the mission.
</p></div></div></div></div></div></div></span></div></div></div></div></div></div></div></div></div></div></nimbus-html>""",
             'nimbus-html',
             list),
        ],
    )
    def test_extract_from_nimbus_tag(self, html, tag_type, exp_type, processing_options):
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find()
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_tag(tag, processing_options)
        assert isinstance(result, exp_type)


class TestExtractFromNimbusDiv:
    pass


class TestExtractFromNimbusHighlightSpan:
    def test_extract_from_nimbus_highlight_span(self, processing_options, mocker):
        """Test passing correct tag"""
        html = '<span class="background-color" data-highlight="yellow">This is highlighted. </span>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('span')
        assert tag.name == 'span'

        mocker.patch('html_data_extractors.extract_from_tag')
        _ = html_nimbus_extractors.extract_from_nimbus_highlight_span(tag, processing_options)

        html_data_extractors.extract_from_tag.assert_called_once()
        args = html_data_extractors.extract_from_tag.call_args.args
        assert args[0].name == 'mark'
        # this confirms tag is changed to mark tag
        # in the full code it is then processed when it is returned to html_data_extractors

    def test_extract_from_head_tag_incorrect_tag_no_data_higlight_property(self, processing_options):
        """Test passing incorrect tag"""
        html = '<span class="background-color">This is highlighted. </span>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('span')
        assert tag.name == 'span'

        result = html_nimbus_extractors.extract_from_nimbus_highlight_span(tag, processing_options)
        assert result is None

    def test_extract_from_head_tag_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = '<a class="background-color">This is highlighted. </a>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('a')
        assert tag.name == 'a'

        result = html_nimbus_extractors.extract_from_nimbus_highlight_span(tag, processing_options)
        assert result is None


class TestExtractFromNimbusOutline:
    def test_extract_from_nimbus_outline(self, processing_options):
        """Test passing correct tag"""
        html = '<div class="outline" id="b406348235_764"><div contenteditable="false" class="outline-container"><div class="outline-content-wrapper "><div class="outline-header "><div class="outline-left"><div class="outline-expand-icon "> </div></div><div class="outline-name">Outline</div></div><div class="outline-body"><ul class="outline-list outline-numbered"><li class="outline-list-item level-0"><a href="#b1023299123_950">A test note of page content</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1009">Testing lists</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1042">Testing inserted files</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1086">Testing a table</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1130">There are only 3 levels of heading in nimbus</a></li><li class="outline-list-item level-0"><a href="#b788977277_831">heading 1</a></li><li class="outline-list-item level-1"><a href="#b788977277_860">heading 2</a></li><li class="outline-list-item level-2"><a href="#b788977277_889">heading 3</a></li><li class="outline-list-item level-0"><a href="#b1023299123_1757">heading with italic text</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1218">Testing the horizontal line</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1266">Link and embeds</a></li><li class="outline-list-item level-1"><a href="#b992245780_93">Code Blocks</a></li><li class="outline-list-item level-1"><a href="#b992245780_132">Nimbus mentions</a></li><li class="outline-list-item level-1"><a href="#b992245780_175">Quoted text</a></li><li class="outline-list-item level-1"><a href="#b992245780_196">Hints</a></li><li class="outline-list-item level-1"><a href="#b992245780_220">Toggle block</a></li><li class="outline-list-item level-1"><a href="#b2183561539_350">Outline (effectively a linked TOC)</a></li><li class="outline-list-item level-1"><a href="#b992245780_450">Nimbus button</a></li><li class="outline-list-item level-1"><a href="#b992245780_478">Text formatting</a></li><li class="outline-list-item level-1"><a href="#b942953620_901">Testing inserted mp3</a></li><li class="outline-list-item level-1"><a href="#b942953620_1059">Test block sections - may or may not export!</a></li><li class="outline-list-item level-1"><a href="#b216345050_62">Adventures in Exporting from Nimbus Notes...</a></li><li class="outline-list-item level-0"><a href="#b942953620_969">This is the end of the file</a></li></ul></div></div></div></div>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_nimbus_outline(tag, processing_options)
        assert isinstance(result, Outline)
        assert len(result.contents) == 1  # title
        assert result.contents[0].contents == 'Outline'
        assert len(result.outline_items.contents) == 23  # line items in TOC

    def test_extract_from_from_nimbus_outline_incorrect_tag_no_outline_class(self, processing_options):
        """Test passing incorrect tag"""
        html = "<div>My Div</div>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_nimbus_outline(tag, processing_options)
        assert result is None

    def test_extract_from_from_nimbus_outline_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = '<title class="outline">My Div</title>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        result = html_nimbus_extractors.extract_from_nimbus_outline(tag, processing_options)
        assert result is None


class TestExtractFromNimbusHintBlock:
    def test_extract_from_hint_block(self, processing_options):
        """Test passing correct tag"""
        html = """<div class="editable-text paragraph hintblock indent-0" data-block-background="cloudy" data-text="Type something" style="text-align:left;">This is a hint</div>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_hint_block(tag, processing_options)
        assert isinstance(result, BlockQuote)
        assert result.contents[0].contents == 'This is a hint'

    def test_extract_from_hint_block_incorrect_tag(self, processing_options):
        """Test passing correct tag"""
        html = """<title>My Title</title>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        result = html_nimbus_extractors.extract_from_hint_block(tag, processing_options)
        assert result is None

    def test_extract_from_hint_block_missing_class(self, processing_options):
        """Test passing correct tag"""
        html = """<div class="editable-text paragraph indent-0" data-block-background="cloudy" data-text="Type something" style="text-align:left;">This is a hint</div>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_hint_block(tag, processing_options)
        assert result is None


class TestExtractFromNimbusOutlineItems:

    def test_extract_from_nimbus_outline_items(self, processing_options):
        """Test passing correct tags"""
        html = '<ul class="outline-list outline-numbered"><li class="outline-list-item level-0"><a href="#b1023299123_950">A test note of page content</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1009">Testing lists</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1042">Testing inserted files</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1086">Testing a table</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1130">There are only 3 levels of heading in nimbus</a></li><li class="outline-list-item level-0"><a href="#b788977277_831">heading 1</a></li><li class="outline-list-item level-1"><a href="#b788977277_860">heading 2</a></li><li class="outline-list-item level-2"><a href="#b788977277_889">heading 3</a></li><li class="outline-list-item level-0"><a href="#b1023299123_1757">heading with italic text</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1218">Testing the horizontal line</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1266">Link and embeds</a></li><li class="outline-list-item level-1"><a href="#b992245780_93">Code Blocks</a></li><li class="outline-list-item level-1"><a href="#b992245780_132">Nimbus mentions</a></li><li class="outline-list-item level-1"><a href="#b992245780_175">Quoted text</a></li><li class="outline-list-item level-1"><a href="#b992245780_196">Hints</a></li><li class="outline-list-item level-1"><a href="#b992245780_220">Toggle block</a></li><li class="outline-list-item level-1"><a href="#b2183561539_350">Outline (effectively a linked TOC)</a></li><li class="outline-list-item level-1"><a href="#b992245780_450">Nimbus button</a></li><li class="outline-list-item level-1"><a href="#b992245780_478">Text formatting</a></li><li class="outline-list-item level-1"><a href="#b942953620_901">Testing inserted mp3</a></li><li class="outline-list-item level-1"><a href="#b942953620_1059">Test block sections - may or may not export!</a></li><li class="outline-list-item level-1"><a href="#b216345050_62">Adventures in Exporting from Nimbus Notes...</a></li><li class="outline-list-item level-0"><a href="#b942953620_969">This is the end of the file</a></li></ul>'
        soup = helper_functions.make_soup_from_html(html)
        tags = soup.find_all('li')
        assert tags[0].name == 'li'

        result = html_nimbus_extractors.extract_from_nimbus_outline_items(tags, processing_options)
        assert isinstance(result, NumberedList)
        assert len(result.contents) == 23
        assert isinstance(result.contents[0], OutlineItem)
        assert result.contents[0].contents.contents == 'A test note of page content'

    def test_extract_from_heading_incorrect_tag(self, processing_options):
        """Test passing one incorrect tag with wrong class and one good tag"""
        html = '<ul class="outline-list outline-numbered"><li class="level-0"><a href="#b1023299123_950">A test note of page content</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1009">Testing lists</a></li></ul>'
        soup = helper_functions.make_soup_from_html(html)
        tags = soup.find_all('li')
        assert tags[0].name == 'li'

        result = html_nimbus_extractors.extract_from_nimbus_outline_items(tags, processing_options)
        assert isinstance(result, NumberedList)
        assert len(result.contents) == 1
        assert isinstance(result.contents[0], OutlineItem)
        assert result.contents[0].contents.contents == 'Testing lists'

    def test_extract_from_heading_incorrect_tags(self, processing_options):
        """Test passing two incorrect tag with wrong"""
        html = '<ul class="outline-list outline-numbered"><li class="level-0"><a href="#b1023299123_950">A test note of page content</a></li><li class="level-1"><a href="#b1023299123_1009">Testing lists</a></li></ul>'
        soup = helper_functions.make_soup_from_html(html)
        tags = soup.find_all('li')
        assert tags[0].name == 'li'

        result = html_nimbus_extractors.extract_from_nimbus_outline_items(tags, processing_options)
        assert result is None

    def test_extract_from_heading_incorrect_tag_type(self, processing_options):
        """Test passing two incorrect tag with wrong"""
        html = '<p class="level-0"><a href="#b1023299123_950">A test note of page content</a></p><p class="level-1"><a href="#b1023299123_1009">Testing lists</a></p>'
        soup = helper_functions.make_soup_from_html(html)
        tags = soup.find_all('p')
        assert tags[0].name == 'p'

        result = html_nimbus_extractors.extract_from_nimbus_outline_items(tags, processing_options)
        assert result is None


class TestExtractFromNimbusUnorderedLists:
    @pytest.mark.parametrize(
        'html, tag_type, exp_type', [
            (
                    """<ul class="editor-list number-template-decimal-all" id="b788977277_51"><li class="list-item-checkbox editable-text list-item indent-0" data-checked="false" id="b788977277_57" style="text-align: left;">check 1</li><li class="list-item-checkbox editable-text list-item indent-1" data-checked="false" id="b788977277_78" style="text-align: left;">check <strong>level</strong> 2</li><li class="list-item-checkbox editable-text list-item indent-1" data-checked="true" id="b788977277_105" style="text-align: left;">check <strong><em>level</em></strong> 2 item 2</li><li class="list-item-checkbox editable-text list-item indent-0" data-checked="false" id="b788977277_136" style="text-align: left;">check <em>level</em> 1 item 2, below is an empty check item</li><li class="list-item-checkbox editable-text list-item indent-0" data-checked="false" id="b1786634969_7" style="text-align: left;"><br/></li></ul>""",
                    'ul',
                    Checklist)
            ,
            (
                    """<ul class="editor-list number-template-decimal-all" id="b788977277_207"><li class="list-item-number editable-text list-item indent-0 one-cnt-sym" id="b788977277_213" style="text-align: left;">number one</li><li class="list-item-number editable-text list-item indent-0 one-cnt-sym" id="b788977277_237" style="text-align: left;">number two</li><li class="list-item-number editable-text list-item indent-1 one-cnt-sym" id="b788977277_258" style="text-align: left;">number <strong>bold</strong> 2-1</li><li class="list-item-number editable-text list-item indent-1 one-cnt-sym" id="b788977277_280" style="text-align: left;">number <em>Italic</em> 2-2</li><li class="list-item-number editable-text list-item indent-0 one-cnt-sym" id="b788977277_301" style="text-align: left;">number <strong><em>bold italic</em></strong> 3 below is an empty numbered item</li><li class="list-item-number editable-text list-item indent-0 one-cnt-sym" id="b1786634969_81" style="text-align: left;"><br/></li></ul>""",
                    'ul',
                    NumberedList
            ),
            (
                    """<ul class="editor-list number-template-decimal-all" id="b788977277_351"><li class="list-item-bullet editable-text list-item indent-0" id="b788977277_357" list-style="circle" style="text-align: left;">bullet 1</li><li class="list-item-bullet editable-text list-item indent-1" id="b788977277_378" list-style="rectangle" style="text-align: left;">sub <strong>bullet</strong> two, below is an empty bullet</li><li class="list-item-bullet editable-text list-item indent-1" id="b1786634969_118" list-style="rectangle" style="text-align: left;"><br/></li><li class="list-item-bullet editable-text list-item indent-0" id="b788977277_405" list-style="circle" style="text-align: left;">bullet 2</li></ul>""",
                    'ul',
                    BulletList
            ),
            (
                    """<ul class="outline-list outline-numbered"><li class="outline-list-item level-0"><a href="#b1023299123_950">A test note of page content</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1009">Testing lists</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1042">Testing inserted files</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1086">Testing a table</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1130">There are only 3 levels of heading in nimbus</a></li><li class="outline-list-item level-0"><a href="#b788977277_831">heading 1</a></li><li class="outline-list-item level-1"><a href="#b788977277_860">heading 2</a></li><li class="outline-list-item level-2"><a href="#b788977277_889">heading 3</a></li><li class="outline-list-item level-0"><a href="#b1023299123_1757">heading with italic text</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1218">Testing the horizontal line</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1266">Link and embeds</a></li><li class="outline-list-item level-1"><a href="#b992245780_93">Code Blocks</a></li><li class="outline-list-item level-1"><a href="#b992245780_132">Nimbus mentions</a></li><li class="outline-list-item level-1"><a href="#b992245780_175">Quoted text</a></li><li class="outline-list-item level-1"><a href="#b992245780_196">Hints</a></li><li class="outline-list-item level-1"><a href="#b992245780_220">Toggle block</a></li><li class="outline-list-item level-1"><a href="#b2183561539_350">Outline (effectively a linked TOC)</a></li><li class="outline-list-item level-1"><a href="#b992245780_450">Nimbus button</a></li><li class="outline-list-item level-1"><a href="#b992245780_478">Text formatting</a></li><li class="outline-list-item level-1"><a href="#b942953620_901">Testing inserted mp3</a></li><li class="outline-list-item level-1"><a href="#b942953620_1059">Test block sections - may or may not export!</a></li><li class="outline-list-item level-1"><a href="#b216345050_62">Adventures in Exporting from Nimbus Notes...</a></li><li class="outline-list-item level-0"><a href="#b942953620_969">This is the end of the file</a></li></ul>""",
                    'ul',
                    NumberedList
            ),
        ],
    )
    def test_extract_from_nimbus_unordered_lists(self, html, tag_type, exp_type, processing_options):
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find()
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_unordered_lists(tag, processing_options)
        assert isinstance(result, exp_type)

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<ul class="editor-list number-template-decimal-all" id="b788977277_51"></ul>""",
                    'ul',
            ),
            (
                    """<ul class="outline-list outline-numbered" id="b788977277_51"><li class="dummy">Item</li></ul>""",
                    'ul',
            ),
            (
                    "<title>My title</title>",
                    'title',
            ),
        ],
        ids=['no li items', 'li item with wrong class', 'wrong tag type']
    )
    def test_extract_from_nimbus_unordered_lists_invalid_tags(self, html, tag_type, processing_options):
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find()
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_unordered_lists(tag, processing_options)
        assert result is None


#


class TestExtractFromNimbusEmbed:
    def test_extract_from_nimbus_embed_iframe(self, processing_options):
        """Test passing correct tag with iframe embed"""
        html = '<DIV class="embed-wrapper remote-frame-wrapper" ><div class="exported-remote-frame as-iframe"><iframe src="https://www.youtube.com/embed/bWbYWOMVkyY" style="width:1000px;height:562.5px;border:0;" sandbox="allow-scripts allow-same-origin allow-popups allow-forms" allowfullscreen="allowfullscreen"></iframe></div><div class="editable-text attachment-caption" id="b1023299123_1339" style="text-align: center; width: 100%;">caption after an embed</div></DIV>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_nimbus_embed(tag, processing_options)
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], Paragraph)
        assert isinstance(result[0].contents, list)
        assert isinstance(result[0].contents[0], TextItem)
        assert result[0].contents[0].contents.startswith('<iframe')
        assert result[0].contents[0].contents.endswith('</iframe>')
        assert isinstance(result[1].contents, list)
        assert len(result[1].contents) == 1
        assert isinstance(result[1].contents[0], TextItem)
        assert result[1].contents[0].contents == 'caption after an embed'

    @pytest.mark.parametrize(
        'html, exp_caption', [
            (
                    """<DIV class="embed-wrapper remote-frame-wrapper" ><div class="exported-remote-frame as-link"><a href="<blockquote class=" twitter-tweet"=""></a><p lang="en" dir="ltr"><a href="<blockquote class=" twitter-tweet"="">Sunsets don't get much better than this one over </a><a href="https://twitter.com/GrandTetonNPS?ref_src=twsrc%5Etfw">@GrandTetonNPS</a>. <a href="https://twitter.com/hashtag/nature?src=hash&amp;ref_src=twsrc%5Etfw">#nature</a> <a href="https://twitter.com/hashtag/sunset?src=hash&amp;ref_src=twsrc%5Etfw">#sunset</a> <a href="http://t.co/YuKy2rcjyU">pic.twitter.com/YuKy2rcjyU</a></p>— US Department of the Interior (@Interior) <a href="https://twitter.com/Interior/status/463440424141459456?ref_src=twsrc%5Etfw">May 5, 2014</a> <script async="" src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>"&gt;<blockquote class="twitter-tweet"><p lang="en" dir="ltr">Sunsets don't get much better than this one over <a href="https://twitter.com/GrandTetonNPS?ref_src=twsrc%5Etfw">@GrandTetonNPS</a>. <a href="https://twitter.com/hashtag/nature?src=hash&amp;ref_src=twsrc%5Etfw">#nature</a> <a href="https://twitter.com/hashtag/sunset?src=hash&amp;ref_src=twsrc%5Etfw">#sunset</a> <a href="http://t.co/YuKy2rcjyU">pic.twitter.com/YuKy2rcjyU</a></p>— US Department of the Interior (@Interior) <a href="https://twitter.com/Interior/status/463440424141459456?ref_src=twsrc%5Etfw">May 5, 2014</a></blockquote> <script async="" src="https://platform.twitter.com/widgets.js" charset="utf-8"></script></div><div <div class="editable-text attachment-caption" id="b992245780_696" style="text-align: center; width: 50px;">This is the caption</div></DIV>""",
                    'This is the caption'),
            (
                    """<DIV class="embed-wrapper remote-frame-wrapper" ><div class="exported-remote-frame as-link"><a href="<blockquote class=" twitter-tweet"=""></a><p lang="en" dir="ltr"><a href="<blockquote class=" twitter-tweet"="">Sunsets don't get much better than this one over </a><a href="https://twitter.com/GrandTetonNPS?ref_src=twsrc%5Etfw">@GrandTetonNPS</a>. <a href="https://twitter.com/hashtag/nature?src=hash&amp;ref_src=twsrc%5Etfw">#nature</a> <a href="https://twitter.com/hashtag/sunset?src=hash&amp;ref_src=twsrc%5Etfw">#sunset</a> <a href="http://t.co/YuKy2rcjyU">pic.twitter.com/YuKy2rcjyU</a></p>— US Department of the Interior (@Interior) <a href="https://twitter.com/Interior/status/463440424141459456?ref_src=twsrc%5Etfw">May 5, 2014</a> <script async="" src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>"&gt;<blockquote class="twitter-tweet"><p lang="en" dir="ltr">Sunsets don't get much better than this one over <a href="https://twitter.com/GrandTetonNPS?ref_src=twsrc%5Etfw">@GrandTetonNPS</a>. <a href="https://twitter.com/hashtag/nature?src=hash&amp;ref_src=twsrc%5Etfw">#nature</a> <a href="https://twitter.com/hashtag/sunset?src=hash&amp;ref_src=twsrc%5Etfw">#sunset</a> <a href="http://t.co/YuKy2rcjyU">pic.twitter.com/YuKy2rcjyU</a></p>— US Department of the Interior (@Interior) <a href="https://twitter.com/Interior/status/463440424141459456?ref_src=twsrc%5Etfw">May 5, 2014</a></blockquote> <script async="" src="https://platform.twitter.com/widgets.js" charset="utf-8"></script></div><div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b992245780_696" style="text-align: center; width: 50px;"><br></div></DIV>""",
                    ''),
            (
                    """<DIV class="embed-wrapper remote-frame-wrapper" ><div class="exported-remote-frame as-link"><a href="<blockquote class=" twitter-tweet"=""></a><p lang="en" dir="ltr"><a href="<blockquote class=" twitter-tweet"="">Sunsets don't get much better than this one over </a><a href="https://twitter.com/GrandTetonNPS?ref_src=twsrc%5Etfw">@GrandTetonNPS</a>. <a href="https://twitter.com/hashtag/nature?src=hash&amp;ref_src=twsrc%5Etfw">#nature</a> <a href="https://twitter.com/hashtag/sunset?src=hash&amp;ref_src=twsrc%5Etfw">#sunset</a> <a href="http://t.co/YuKy2rcjyU">pic.twitter.com/YuKy2rcjyU</a></p>— US Department of the Interior (@Interior) <a href="https://twitter.com/Interior/status/463440424141459456?ref_src=twsrc%5Etfw">May 5, 2014</a> <script async="" src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>"&gt;<blockquote class="twitter-tweet"><p lang="en" dir="ltr">Sunsets don't get much better than this one over <a href="https://twitter.com/GrandTetonNPS?ref_src=twsrc%5Etfw">@GrandTetonNPS</a>. <a href="https://twitter.com/hashtag/nature?src=hash&amp;ref_src=twsrc%5Etfw">#nature</a> <a href="https://twitter.com/hashtag/sunset?src=hash&amp;ref_src=twsrc%5Etfw">#sunset</a> <a href="http://t.co/YuKy2rcjyU">pic.twitter.com/YuKy2rcjyU</a></p>— US Department of the Interior (@Interior) <a href="https://twitter.com/Interior/status/463440424141459456?ref_src=twsrc%5Etfw">May 5, 2014</a></blockquote> <script async="" src="https://platform.twitter.com/widgets.js" charset="utf-8"></script></div></DIV>""",
                    ''),
        ],
        ids=['normal tag', 'normal tag empty caption', 'tag with no caption div']
    )
    def test_extract_from_nimbus_embed_blockquote_twitter(self, html, exp_caption, processing_options):
        """Test passing correct tag with twitter blockquote embed"""
        # html = """<DIV class="embed-wrapper remote-frame-wrapper" ><div class="exported-remote-frame as-link"><a href="<blockquote class=" twitter-tweet"=""></a><p lang="en" dir="ltr"><a href="<blockquote class=" twitter-tweet"="">Sunsets don't get much better than this one over </a><a href="https://twitter.com/GrandTetonNPS?ref_src=twsrc%5Etfw">@GrandTetonNPS</a>. <a href="https://twitter.com/hashtag/nature?src=hash&amp;ref_src=twsrc%5Etfw">#nature</a> <a href="https://twitter.com/hashtag/sunset?src=hash&amp;ref_src=twsrc%5Etfw">#sunset</a> <a href="http://t.co/YuKy2rcjyU">pic.twitter.com/YuKy2rcjyU</a></p>— US Department of the Interior (@Interior) <a href="https://twitter.com/Interior/status/463440424141459456?ref_src=twsrc%5Etfw">May 5, 2014</a> <script async="" src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>"&gt;<blockquote class="twitter-tweet"><p lang="en" dir="ltr">Sunsets don't get much better than this one over <a href="https://twitter.com/GrandTetonNPS?ref_src=twsrc%5Etfw">@GrandTetonNPS</a>. <a href="https://twitter.com/hashtag/nature?src=hash&amp;ref_src=twsrc%5Etfw">#nature</a> <a href="https://twitter.com/hashtag/sunset?src=hash&amp;ref_src=twsrc%5Etfw">#sunset</a> <a href="http://t.co/YuKy2rcjyU">pic.twitter.com/YuKy2rcjyU</a></p>— US Department of the Interior (@Interior) <a href="https://twitter.com/Interior/status/463440424141459456?ref_src=twsrc%5Etfw">May 5, 2014</a></blockquote> <script async="" src="https://platform.twitter.com/widgets.js" charset="utf-8"></script></div><div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b992245780_696" style="text-align: center; width: 50px;"><br></div></DIV>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_nimbus_embed(tag, processing_options)
        assert isinstance(result, EmbedNimbus)
        assert isinstance(result.contents, BlockQuote)
        assert len(result.contents.contents) == 10
        assert isinstance(result.embed_caption, Caption)
        assert isinstance(result.embed_caption.contents[0], TextItem)
        assert result.embed_caption.contents[0].contents == exp_caption

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    '<DIV class="embed-wrapper" ><div class="exported-remote-frame as-iframe"><iframe src="https://www.youtube.com/embed/bWbYWOMVkyY" style="width:1000px;height:562.5px;border:0;" sandbox="allow-scripts allow-same-origin allow-popups allow-forms" allowfullscreen="allowfullscreen"></iframe></div><div class="editable-text attachment-caption" id="b1023299123_1339" style="text-align: center; width: 100%;">caption after an embed</div></DIV>',
                    'div'),
            (
                    '<DIV><div class="exported-remote-frame as-iframe"><iframe src="https://www.youtube.com/embed/bWbYWOMVkyY" style="width:1000px;height:562.5px;border:0;" sandbox="allow-scripts allow-same-origin allow-popups allow-forms" allowfullscreen="allowfullscreen"></iframe></div><div class="editable-text attachment-caption" id="b1023299123_1339" style="text-align: center; width: 100%;">caption after an embed</div></DIV>',
                    'div'),
            ('<title>My Title</title>', 'title')
        ],
        ids=['no remote-frame-wrapper class element', 'no class at all', 'incorrect tag type']
    )
    def test_extract_from_nimbus_embed_no_correct_class(self, html, tag_type, processing_options):
        """Test passing invalid tags and classes tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_embed(tag, processing_options)
        assert result is None


class TestExtractFromNimbusButton:
    def test_extract_from_nimbus_button(self, processing_options):
        """Test passing correct tag"""
        html = """<div class="button-single" contenteditable="false" id="b32879378_144"><div class="button-single-container" data-align="left"><nimbus-button id="button_001a229e" class="single-button" data-background="bondi-blue" data-shape="rounded" data-size="small" data-target="_blank" data-url="https://www.google.com" data-type="3d" onclick="window.open('https://www.google.com', '_blank', 'noopener')"><span class="button-content"><b>a button</b></span></nimbus-button></div></div><div"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_nimbus_button(tag, processing_options)

        assert isinstance(result, Paragraph)
        assert isinstance(result.contents[0], Hyperlink)
        assert result.contents[0].contents == 'a button'
        assert result.contents[0].href == "https://www.google.com"

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<div class="none" contenteditable="false" id="b32879378_144"><div class="button-single-container" data-align="left"><nimbus-button id="button_001a229e" class="single-button" data-background="bondi-blue" data-shape="rounded" data-size="small" data-target="_blank" data-url="https://www.google.com" data-type="3d" onclick="window.open('https://www.google.com', '_blank', 'noopener')"><span class="button-content"><b>a button</b></span></nimbus-button></div></div>""",
                    'div'),
            (
                    """<div  contenteditable="false" id="b32879378_144"><div class="button-single-container" data-align="left"><nimbus-button id="button_001a229e" class="single-button" data-background="bondi-blue" data-shape="rounded" data-size="small" data-target="_blank" data-url="https://www.google.com" data-type="3d" onclick="window.open('https://www.google.com', '_blank', 'noopener')"><span class="button-content"><b>a button</b></span></nimbus-button></div></div>""",
                    'div'),
            ('<title>My Title</title>', 'title')
        ],
        ids=['no button-single class element', 'no class at all', 'incorrect tag type']
    )
    def test_extract_from_nimbus_button_no_correct_class(self, html, tag_type, processing_options):
        """Test passing invalid tags and classes tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_button(tag, processing_options)
        assert result is None


class TestExtractFromNimbusInlineButton:
    def test_extract_from_nimbus_inline_button(self, processing_options):
        """Test passing correct tag"""
        html = """<nimbus-button class="inline-button" data-title="Click to see " data-url="https://www.google.com" data-target="_blank" data-shape="rounded" data-background="bondi-blue" data-size="small" data-type="3d" id="button_9e91f9d0" onclick="window.open('https://nimbusweb.me/s/share/4196282/063i1t5kiqlf3gcgm5ny#b4142816705_2', '_blank', 'noopener')"><span contenteditable="false" class="button-content"><b>Click to see </b></span></nimbus-button>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('nimbus-button')
        assert tag.name == 'nimbus-button'

        result = html_nimbus_extractors.extract_from_nimbus_inline_button(tag, processing_options)

        assert isinstance(result, Hyperlink)
        assert result.contents == 'Click to see '
        assert result.href == "https://www.google.com"

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<nimbus-button class="something" data-title="Click to see " data-url="https://www.google.com" data-target="_blank" data-shape="rounded" data-background="bondi-blue" data-size="small" data-type="3d" id="button_9e91f9d0" onclick="window.open('https://nimbusweb.me/s/share/4196282/063i1t5kiqlf3gcgm5ny#b4142816705_2', '_blank', 'noopener')"><span contenteditable="false" class="button-content"><b>Click to see </b></span></nimbus-button>""",
                    'nimbus-button'),
            (
                    """<div  contenteditable="false" id="b32879378_144"><div class="button-single-container" data-align="left"><nimbus-button id="button_001a229e" class="single-button" data-background="bondi-blue" data-shape="rounded" data-size="small" data-target="_blank" data-url="https://www.google.com" data-type="3d" onclick="window.open('https://www.google.com', '_blank', 'noopener')"><span class="button-content"><b>a button</b></span></nimbus-button></div></div><div""",
                    'nimbus-button'),
            ('<title>My Title</title>', 'title')
        ],
        ids=['no inline-button class element', 'no class at all', 'incorrect tag type']
    )
    def test_extract_from_nimbus_inline_button_invalid_tags(self, html, tag_type, processing_options):
        """Test passing invalid tags and classes tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_inline_button(tag, processing_options)
        assert result is None


class TestExtractFromNimbusBookmark:
    def test_extract_from_nimbus_bookmark(self, processing_options):
        """Test passing correct tag"""
        html = """<div class="nimbus-bookmark" id="b1023299123_1415"><div contenteditable="false" class="nimbus-bookmark-container"><a href="https://www.youtube.com/watch?v=bWbYWOMVkyY" style="display: contents;"><div class="nimbus-bookmark-content is-card" style="max-width: 650px;"><div class="nimbus-bookmark__info"><div class="nimbus-bookmark__info__name">SpaceX Starship Booster Removed, Starship Static Fire, JWST Update, Angara A5 &amp; OneWeb Launch - YouTube</div><a class="nimbus-bookmark__info__src" href="https://www.youtube.com/watch?v=bWbYWOMVkyY"><div class="nimbus-bookmark__icon"><img src="https://www.youtube.com/s/desktop/df3209e6/img/favicon_32x32.png"></div><div class="nimbus-bookmark__info__src-text">https://www.youtube.com/watch?v=bWbYWOMVkyY</div></a><div class="nimbus-bookmark__info__desc">Save 10% off your first website or domain at https://www.squarespace.com/marcushouse - Coupon Code: MARCUSHOUSEHappy New Year to you all! This year I’m betti...</div></div><div class="nimbus-bookmark__preview"><img src="./assets/xNGMnJrJJ1X3Gyb3.png"></div></div></a></div></div>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_nimbus_bookmark(tag, processing_options)
        assert isinstance(result, Paragraph)
        assert len(result.contents) == 3
        assert isinstance(result.contents[0], Hyperlink)
        assert isinstance(result.contents[1], TextItem)
        assert isinstance(result.contents[2], ImageEmbed)

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<div class="" id="b1023299123_1415"><div contenteditable="false" class="nimbus-bookmark-container"><a href="https://www.youtube.com/watch?v=bWbYWOMVkyY" style="display: contents;"><div class="nimbus-bookmark-content is-card" style="max-width: 650px;"><div class="nimbus-bookmark__info"><div class="nimbus-bookmark__info__name">SpaceX Starship Booster Removed, Starship Static Fire, JWST Update, Angara A5 &amp; OneWeb Launch - YouTube</div><a class="nimbus-bookmark__info__src" href="https://www.youtube.com/watch?v=bWbYWOMVkyY"><div class="nimbus-bookmark__icon"><img src="https://www.youtube.com/s/desktop/df3209e6/img/favicon_32x32.png"></div><div class="nimbus-bookmark__info__src-text">https://www.youtube.com/watch?v=bWbYWOMVkyY</div></a><div class="nimbus-bookmark__info__desc">Save 10% off your first website or domain at https://www.squarespace.com/marcushouse - Coupon Code: MARCUSHOUSEHappy New Year to you all! This year I’m betti...</div></div><div class="nimbus-bookmark__preview"><img src="./assets/xNGMnJrJJ1X3Gyb3.png"></div></div></a></div></div>""",
                    'div'),
            (
                    """<div id="b1023299123_1415"><div contenteditable="false" class="nimbus-bookmark-container"><a href="https://www.youtube.com/watch?v=bWbYWOMVkyY" style="display: contents;"><div class="nimbus-bookmark-content is-card" style="max-width: 650px;"><div class="nimbus-bookmark__info"><div class="nimbus-bookmark__info__name">SpaceX Starship Booster Removed, Starship Static Fire, JWST Update, Angara A5 &amp; OneWeb Launch - YouTube</div><a class="nimbus-bookmark__info__src" href="https://www.youtube.com/watch?v=bWbYWOMVkyY"><div class="nimbus-bookmark__icon"><img src="https://www.youtube.com/s/desktop/df3209e6/img/favicon_32x32.png"></div><div class="nimbus-bookmark__info__src-text">https://www.youtube.com/watch?v=bWbYWOMVkyY</div></a><div class="nimbus-bookmark__info__desc">Save 10% off your first website or domain at https://www.squarespace.com/marcushouse - Coupon Code: MARCUSHOUSEHappy New Year to you all! This year I’m betti...</div></div><div class="nimbus-bookmark__preview"><img src="./assets/xNGMnJrJJ1X3Gyb3.png"></div></div></a></div></div>""",
                    'div'),
            ('<title>My Title</title>',
             'title'),
        ],
        ids=['no nimbus-bookmark class element', 'no class at all', 'incorrect tag type']
    )
    def test_extract_from_nimbus_bookmark_invalid_tags(self, html, tag_type, processing_options):
        """Test passing invalid tags and classes tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_bookmark(tag, processing_options)
        assert result is None

    @pytest.mark.parametrize(
        'html, tag_type, expected_types', [
            (
                    """<div class="nimbus-bookmark" id="b1023299123_1415"><div contenteditable="false" class="nimbus-bookmark-container"><a href="https://www.youtube.com/watch?v=bWbYWOMVkyY" style="display: contents;"><div class="nimbus-bookmark-content is-card" style="max-width: 650px;"><div class="nimbus-bookmark__info"><div class="nimbus-bookmark__info__name">SpaceX Starship Booster Removed, Starship Static Fire, JWST Update, Angara A5 &amp; OneWeb Launch - YouTube</div><a class="nimbus-bookmark__info__src" href="https://www.youtube.com/watch?v=bWbYWOMVkyY"><div class="nimbus-bookmark__icon"><img src="https://www.youtube.com/s/desktop/df3209e6/img/favicon_32x32.png"></div><div class="nimbus-bookmark__info__src-text">https://www.youtube.com/watch?v=bWbYWOMVkyY</div></a></div><div class="nimbus-bookmark__preview"><img src="./assets/xNGMnJrJJ1X3Gyb3.png"></div></div></a></div></div>""",
                    'div',
                    {Hyperlink, ImageEmbed}),
            (
                    """<div class="nimbus-bookmark" id="b1023299123_1415"><div contenteditable="false" class="nimbus-bookmark-container"><a href="https://www.youtube.com/watch?v=bWbYWOMVkyY" style="display: contents;"><div class="nimbus-bookmark-content is-card" style="max-width: 650px;"><div class="nimbus-bookmark__info"><div class="nimbus-bookmark__info__name">SpaceX Starship Booster Removed, Starship Static Fire, JWST Update, Angara A5 &amp; OneWeb Launch - YouTube</div><a class="nimbus-bookmark__info__src" href="https://www.youtube.com/watch?v=bWbYWOMVkyY"><div class="nimbus-bookmark__icon"><img src="https://www.youtube.com/s/desktop/df3209e6/img/favicon_32x32.png"></div><div class="nimbus-bookmark__info__src-text">https://www.youtube.com/watch?v=bWbYWOMVkyY</div></a><div class="nimbus-bookmark__info__desc">Save 10% off your first website or domain at https://www.squarespace.com/marcushouse - Coupon Code: MARCUSHOUSEHappy New Year to you all! This year I’m betti...</div></div></div></a></div></div>""",
                    'div', {Hyperlink, TextItem}),
        ],
        ids=['no description', 'no image']
    )
    def test_extract_from_nimbus_bookmark_invalid_tags2(self, html, tag_type, expected_types, processing_options):
        """Test passing invalid tags with parts of html missing"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_bookmark(tag, processing_options)
        result_types = {type(item) for item in result.contents}
        assert len(result_types) == len(expected_types)
        assert len(expected_types - result_types) == 0


class TestExtractFromNimbusToggle:
    @pytest.mark.parametrize(
        'html, exp_length_of_items_in_toggle', [
            (
                    """<div class="nimbus-toggle"><div class="toggle-arrow"><div class="toggle-arrow-icon"><svg width="8" height="5" viewBox="0 0 8 5" fill="none" xmlns="http://www.w3.org/2000/svg"><path class="graphic" d="M1.44948 0L6.55052 0C7.12009 0 7.42736 0.668079 7.05669 1.10053L4.50617 4.07613C4.24011 4.38654 3.75989 4.38654 3.49383 4.07613L0.943309 1.10053C0.572639 0.668079 0.879912 0 1.44948 0Z" fill="#AEB7B8"></path></svg></div></div><div class="nimbus-toggle-header editable-text">toggle with further entries</div><div class="nimbus-toggle-content"><div class="editable-text paragraph indent-0" style="text-align:left;">something else with <strong>bold</strong> text</div><div class="editable-text paragraph indent-0" style="text-align:left;">something else</div><div class="editable-text paragraph indent-0" style="text-align:left;">a last line</div></div></div>""",
                    4),
            (
                    """<div class="nimbus-toggle"><div class="toggle-arrow"><div class="toggle-arrow-icon"><svg fill="none" height="5" viewbox="0 0 8 5" width="8" xmlns="http://www.w3.org/2000/svg"><path class="graphic" d="M1.44948 0L6.55052 0C7.12009 0 7.42736 0.668079 7.05669 1.10053L4.50617 4.07613C4.24011 4.38654 3.75989 4.38654 3.49383 4.07613L0.943309 1.10053C0.572639 0.668079 0.879912 0 1.44948 0Z" fill="#AEB7B8"></path></svg></div></div><div class="nimbus-toggle-header editable-text">toggle block no entries</div><div class="nimbus-toggle-content with-placeholder"><div class="editable-text paragraph indent-0" style="text-align:left;"><br/></div></div></div>""",
                    2),
        ],
        ids=['toggle with entries', 'toggle no entries']
    )
    def test_extract_from_nimbus_toggle(self, html, exp_length_of_items_in_toggle, processing_options):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_nimbus_toggle(tag, processing_options)
        assert isinstance(result, NimbusToggle)
        assert len(result.contents) == exp_length_of_items_in_toggle
        assert isinstance(result.contents[0], HeadingItem)
        assert isinstance(result.contents[1], Paragraph)

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<div class=""><div class="toggle-arrow"><div class="toggle-arrow-icon"><svg width="8" height="5" viewBox="0 0 8 5" fill="none" xmlns="http://www.w3.org/2000/svg"><path class="graphic" d="M1.44948 0L6.55052 0C7.12009 0 7.42736 0.668079 7.05669 1.10053L4.50617 4.07613C4.24011 4.38654 3.75989 4.38654 3.49383 4.07613L0.943309 1.10053C0.572639 0.668079 0.879912 0 1.44948 0Z" fill="#AEB7B8"></path></svg></div></div><div class="nimbus-toggle-header editable-text">toggle with further entries</div><div class="nimbus-toggle-content"><div class="editable-text paragraph indent-0" style="text-align:left;">something else with <strong>bold</strong> text</div><div class="editable-text paragraph indent-0" style="text-align:left;">something else</div><div class="editable-text paragraph indent-0" style="text-align:left;">a last line</div></div></div>""",
                    'div'),
            (
                    """<div><div class="toggle-arrow"><div class="toggle-arrow-icon"><svg width="8" height="5" viewBox="0 0 8 5" fill="none" xmlns="http://www.w3.org/2000/svg"><path class="graphic" d="M1.44948 0L6.55052 0C7.12009 0 7.42736 0.668079 7.05669 1.10053L4.50617 4.07613C4.24011 4.38654 3.75989 4.38654 3.49383 4.07613L0.943309 1.10053C0.572639 0.668079 0.879912 0 1.44948 0Z" fill="#AEB7B8"></path></svg></div></div><div class="nimbus-toggle-header editable-text">toggle with further entries</div><div class="nimbus-toggle-content"><div class="editable-text paragraph indent-0" style="text-align:left;">something else with <strong>bold</strong> text</div><div class="editable-text paragraph indent-0" style="text-align:left;">something else</div><div class="editable-text paragraph indent-0" style="text-align:left;">a last line</div></div></div>""",
                    'div'),
            ('<title>My Title</title>', 'title')
        ],
        ids=['no nimbus-bookmark class element', 'no class at all', 'incorrect tag type']
    )
    def test_extract_from_nimbus_toggle_invalid_tags(self, html, tag_type, processing_options):
        """Test passing invalid tags and classes tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_toggle(tag, processing_options)
        assert result is None

    def test_extract_from_nimbus_toggle_no_items_just_heading(self, processing_options):
        """Test passing invalid tags and classes tag"""
        html = """<div class="nimbus-toggle"><div class="toggle-arrow"><div class="toggle-arrow-icon"><svg width="8" height="5" viewBox="0 0 8 5" fill="none" xmlns="http://www.w3.org/2000/svg"><path class="graphic" d="M1.44948 0L6.55052 0C7.12009 0 7.42736 0.668079 7.05669 1.10053L4.50617 4.07613C4.24011 4.38654 3.75989 4.38654 3.49383 4.07613L0.943309 1.10053C0.572639 0.668079 0.879912 0 1.44948 0Z" fill="#AEB7B8"></path></svg></div></div><div class="nimbus-toggle-header editable-text">toggle block no entries</div><div class="nimbus-toggle-content with-placeholder"><div class="editable-text paragraph indent-0" style="text-align:left;"><br/></div></div></div>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_nimbus_toggle(tag, processing_options)
        assert isinstance(result, NimbusToggle)
        assert len(result.contents) == 2
        assert isinstance(result.contents[0], HeadingItem)
        assert isinstance(result.contents[1], Paragraph)
        assert isinstance(result.contents[1].contents[0], Break)


class TestExtractFromNimbusMentionItems:

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<mention class="mention" data-mention-id="qyvgue" data-mention-name="Default workspace" data-mention-object_id="23c421363hn6ndes" data-mention-type="workspace"><span class="mention-link" contenteditable="false" data-mention-id="qyvgue" data-mention-name="Default workspace" data-mention-object_id="23c421363hn6ndes" data-mention-type="workspace"><a href="https://nimbusweb.me/ws/23c421363hn6ndes" target="_blank">Default workspace</a></span></mention>""",
                    'mention'),
            (
                    """<span class="mention-link" contenteditable="false" data-mention-id="hu4brg" data-mention-name="Default workspace" data-mention-object_id="23c421363hn6ndes" data-mention-type="workspace">Default workspace</span>""",
                    'span'),
        ],
        ids=['mention tag ', 'span tag']
    )
    def test_extract_from_nimbus_mention_items_mention_workspace(self, html, tag_type, processing_options):
        """Test passing correct MentionWorkspace tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_mention_items(tag, processing_options)
        assert isinstance(result, MentionWorkspace)
        assert result.contents == "Default workspace"
        assert result.workspace_id == '23c421363hn6ndes'

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<mention class="mention" data-mention-id="2jsddn" data-mention-name="user@gmail.com" data-mention-object_id="2510963" data-mention-type="user"><span class="mention-link" contenteditable="false" data-mention-id="2jsddn" data-mention-name="user@gmail.com" data-mention-object_id="2510963" data-mention-type="user">user@gmail.com</span></mention>""",
                    'mention'),
            (
                    """<span class="mention-link" contenteditable="false" data-mention-id="rfusba" data-mention-name="user@gmail.com" data-mention-object_id="2510963" data-mention-type="user">user@gmail.com</span>""",
                    'span'),
        ],
        ids=['mention tag ', 'span tag']
    )
    def test_extract_from_nimbus_mention_items_mention_user(self, html, tag_type, processing_options):
        """Test passing correct MentionUser tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_mention_items(tag, processing_options)
        assert isinstance(result, MentionUser)
        assert result.contents == "user@gmail.com"

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<mention class="mention" data-mention-id="wai09d" data-mention-name="another topic subfolder" data-mention-object_id="TvjfOrJ0NtSLV3KH" data-mention-type="folder" data-mention-workspace_id="23c421363hn6ndes"><span class="mention-link" contenteditable="false" data-mention-id="wai09d" data-mention-name="another topic subfolder" data-mention-object_id="TvjfOrJ0NtSLV3KH" data-mention-type="folder" data-mention-workspace_id="23c421363hn6ndes"><a href="https://nimbusweb.me/ws/23c421363hn6ndes/folder/TvjfOrJ0NtSLV3KH" target="_blank">another topic subfolder</a></span></mention>""",
                    'mention'),
            (
                    """<span class="mention-link" contenteditable="false" data-mention-id="a9k6af" data-mention-name="another topic subfolder" data-mention-object_id="TvjfOrJ0NtSLV3KH" data-mention-type="folder">another topic subfolder</span>""",
                    'span'),
        ],
        ids=['mention tag ', 'span tag']
    )
    def test_extract_from_nimbus_mention_items_mention_folder(self, html, tag_type, processing_options):
        """Test passing correct MentionFolder tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_mention_items(tag, processing_options)
        assert isinstance(result, MentionFolder)
        assert result.contents == "another topic subfolder"
        if tag_type == 'mention':
            assert result.workspace_id == '23c421363hn6ndes'
        else:
            assert result.workspace_id == ''
        assert result.folder_id == 'TvjfOrJ0NtSLV3KH'

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<mention class="mention" data-mention-id="gbb91m" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-type="note" data-mention-workspace_id="23c421363hn6ndes"><span class="mention-link" contenteditable="false" data-mention-id="gbb91m" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-type="note" data-mention-workspace_id="23c421363hn6ndes"><a href="https://nimbusweb.me/ws/23c421363hn6ndes/zEZUSiVmAQPITGLD" target="_blank">Test 1</a></span></mention>""",
                    'mention'),
            (
                    """<span class="mention-link" contenteditable="false" data-mention-id="j5bjyn" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-type="note">Test 1</span>""",
                    'span'),
        ],
        ids=['mention tag ', 'span tag']
    )
    def test_extract_from_nimbus_mention_items_mention_note(self, html, tag_type, processing_options):
        """Test passing correct MentionNote tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_mention_items(tag, processing_options)
        assert isinstance(result, MentionNote)
        assert result.contents == "Test 1"

        if tag_type == 'mention':
            assert result.workspace_id == '23c421363hn6ndes'
        else:
            assert result.workspace_id == ''

        assert result.note_id == 'zEZUSiVmAQPITGLD'

    def test_extract_from_nimbus_mention_items_no_mention_type_value(self, processing_options):
        """Test invalid correct MentionNote tag"""
        html = """<mention class="mention" data-mention-id="gbb91m" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-workspace_id="23c421363hn6ndes"><span class="mention-link" contenteditable="false" data-mention-id="gbb91m" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-type="note" data-mention-workspace_id="23c421363hn6ndes"><a href="https://nimbusweb.me/ws/23c421363hn6ndes/zEZUSiVmAQPITGLD" target="_blank">Test 1</a></span></mention>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('mention')
        assert tag.name == 'mention'

        result = html_nimbus_extractors.extract_from_mention_items(tag, processing_options)
        assert result is None


class TestExtractFromNimbusMentionTag:
    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<mention class="mention" data-mention-id="gbb91m" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-workspace_id="23c421363hn6ndes"><span class="mention-link" contenteditable="false" data-mention-id="gbb91m" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-workspace_id="23c421363hn6ndes"><a href="https://nimbusweb.me/ws/23c421363hn6ndes/zEZUSiVmAQPITGLD" target="_blank">Test 1</a></span></mention>""",
                    'mention'),
            ("""<title>My title</title>""",
             'title'),
        ],
        ids=['mention tag  no mention type value', 'invalid tag']
    )
    def test_extract_from_nimbus_mention_tag_no_mention_type_class(self, html, tag_type, processing_options):
        """Test passing invalid MentionNote tag with no value for data-mention-type"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_mention_tag(tag, processing_options)
        assert result is None

    def test_extract_from_nimbus_mention_tag_mention_note(self, processing_options):
        """Test passing correct MentionNote tag"""
        html = """<mention class="mention" data-mention-id="gbb91m" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-type="note" data-mention-workspace_id="23c421363hn6ndes"><span class="mention-link" contenteditable="false" data-mention-id="gbb91m" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-type="note" data-mention-workspace_id="23c421363hn6ndes"><a href="https://nimbusweb.me/ws/23c421363hn6ndes/zEZUSiVmAQPITGLD" target="_blank">Test 1</a></span></mention>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('mention')
        assert tag.name == 'mention'

        result = html_nimbus_extractors.extract_from_mention_items(tag, processing_options)
        assert isinstance(result, MentionNote)
        assert result.contents == "Test 1"
        assert result.workspace_id == '23c421363hn6ndes'
        assert result.note_id == 'zEZUSiVmAQPITGLD'


class TestExtractFromNimbusMentionSpan:
    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<span class="mention-link" contenteditable="false" data-mention-id="j5bjyn" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD">Test 1</span>""",
                    'span'),
            ("""<title>My title</title>""",
             'title'),
        ],
        ids=['span tag  no mention type value', 'invalid tag']
    )
    def test_extract_from_nimbus_mention_span_no_mention_type_value(self, html, tag_type, processing_options):
        """Test passing invalid MentionNote tags"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_mention_span(tag, processing_options)
        assert result is None

    def test_extract_from_nimbus_mention_span_mention_note(self, processing_options):
        """Test passing correct MentionNote tag"""
        html = """<span class="mention-link" contenteditable="false" data-mention-id="j5bjyn" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-type="note">Test 1</span>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('span')
        assert tag.name == 'span'

        result = html_nimbus_extractors.extract_from_nimbus_mention_span(tag, processing_options)
        assert isinstance(result, MentionNote)
        assert result.contents == "Test 1"
        assert result.note_id == 'zEZUSiVmAQPITGLD'


class TestExtractFromNimbusDate:
    def test_extract_from_nimbus_date(self, processing_options):
        """Test passing correct tag"""
        html = """<date class="date-inline date-content" data-date-dateid="f9eb39" data-date-timestamp="1641424807590" data-date-reminders="" data-date-alerts="" data-date-format-type="default" data-date-format-showtime="true" data-date-format-timezonegmt="false" data-date-format-timeformat="24"><span contenteditable="false"><span class="input-date "><span class="input-date-string"><span class="input-date-text">05/01/2022 23:20</span></span></span></span></date>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('date')
        assert tag.name == 'date'

        result = html_nimbus_extractors.extract_from_nimbus_date(tag, processing_options)
        assert isinstance(result, NimbusDateItem)
        assert result.unix_time_seconds
        assert result.contents == datetime.datetime.fromtimestamp(result.unix_time_seconds).strftime(
            '%Y-%m-%d %H:%M:%S')

    def test_extract_from_nimbus_date_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<div>My Div</div>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_nimbus_date(tag, processing_options)
        assert result is None


class TestExtractFromNimbusCodePre:

    @pytest.mark.parametrize(
        'html, tag_type, expected_language', [
            (
                    """<div class="embed-wrapper syntax-wrapper"><syntax class="syntax-main editor-syntax" data-nimbus-language="python" id="b406348235_255" spellcheck="false"><div class="syntax-cm-container"><div><div class="syntax-control-wrapper" contenteditable="false"><div class="syntax-control-wrap no-margin" contenteditable="false"><span class="syntax-control-label">Python</span></div></div><pre style="white-space: pre-wrap; "><span class="hljs-keyword">import</span> something\n<span class="hljs-built_in">print</span>(<span class="hljs-string">"hello"</span>)</pre></div></div></syntax><div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b406348235_265" style="text-align: center; width: 50px;"><br/></div></div>""",
                    'div',
                    'python'),
            (
                    """<div class="embed-wrapper syntax-wrapper"><syntax class="syntax-main editor-syntax" id="b406348235_255" spellcheck="false"><div class="syntax-cm-container"><div><div class="syntax-control-wrapper" contenteditable="false"><div class="syntax-control-wrap no-margin" contenteditable="false"><span class="syntax-control-label">Python</span></div></div><pre style="white-space: pre-wrap; "><span class="hljs-keyword">import</span> something\n<span class="hljs-built_in">print</span>(<span class="hljs-string">"hello"</span>)</pre></div></div></syntax><div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b406348235_265" style="text-align: center; width: 50px;"><br/></div></div>""",
                    'div',
                    ''),
        ],
        ids=['good div tag', 'no data-nimbus-language key']
    )
    def test_extract_from_nimbus_code_pre(self, html, tag_type, expected_language, processing_options):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_code_pre(tag, processing_options)
        assert isinstance(result, CodeItem)
        assert result.contents == 'import something\nprint("hello")'
        assert result.language == expected_language

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<div class="embed-wrapper"><syntax class="syntax-main editor-syntax" data-nimbus-language="python" id="b406348235_255" spellcheck="false"><div class="syntax-cm-container"><div><div class="syntax-control-wrapper" contenteditable="false"><div class="syntax-control-wrap no-margin" contenteditable="false"><span class="syntax-control-label">Python</span></div></div><pre style="white-space: pre-wrap; "><span class="hljs-keyword">import</span> something\n<span class="hljs-built_in">print</span>(<span class="hljs-string">"hello"</span>)</pre></div></div></syntax><div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b406348235_265" style="text-align: center; width: 50px;"><br/></div></div>""",
                    'div'),
            (
                    """<div class="embed-wrapper syntax-wrapper"><syntax class="syntax-main editor-syntax" data-nimbus-language="python" id="b406348235_255" spellcheck="false"><div class="syntax-cm-container"><div><div class="syntax-control-wrapper" contenteditable="false"><div class="syntax-control-wrap no-margin" contenteditable="false"><span class="syntax-control-label">Python</span></div></div></div></div></syntax><div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b406348235_265" style="text-align: center; width: 50px;"><br/></div></div>""",
                    'div'),
            (
                    """<div class="embed-wrapper syntax-wrapper"><div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b406348235_265" style="text-align: center; width: 50px;"><br/></div></div>""",
                    'div'),
            ("""<title>My title</title>""",
             'title'),
        ],
        ids=['div tag no syntax-wrapper class', 'div tag but no pre content', 'no syntax tag', 'invalid tag']
    )
    def test_extract_from_nimbus_code_pre_incorrect_tag(self, html, tag_type, processing_options):
        """Test passing incorrect tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        expected = None
        result = html_nimbus_extractors.extract_from_nimbus_code_pre(tag, processing_options)
        assert result == expected


class TestExtractFromNimbusFileEmbed:
    @pytest.mark.parametrize(
        'html, tag_type, expected_target_filename, caption, expected_contents_class', [
            (
                    """<div class="embed-wrapper file-wrapper"><div class="file" id="b788977277_491"><div class="file-container view-mode-full" contenteditable="false"><div class="file-too-small"><div class="compact-view-content"><div class="file-left"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h24v24H0z"></path> <path class="graphic" d="M12 4H7a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-9h-5a1 1 0 0 1-1-1V4zm8 5.008V19a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3h5.992L20 9.008zM14 8V5.414L16.586 8H14zm-6 9a1 1 0 0 1 1-1h6a1 1 0 0 1 0 2H9a1 1 0 0 1-1-1zm1-5a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2H9z" fill="#5C6061"></path> </g></svg></div><div class="file-info file-name-trim-end"><div><span class="file-name" data-editor-toolip="Download test page.pdf" data-editor-tooltip-options='{"positionFixed":true}' data-file-export="b788977277_491.end"><a href="./assets/OFVVRj4UIjtz4S5T.pdf" target="_blank"><span><span class="file-name-main">test page.</span><span class="file-name-ext">pdf</span></span></a></span><span class="file-size">(320.36 kB)</span></div></div></div></div></div></div><div class="editable-text attachment-caption" id="b788977277_496" style="text-align: center; width: 100%;">an attachment caption</div></div>""",
                    'div',
                    'test-page.pdf',
                    'an attachment caption',
                    Caption),
            (
                    """<div class="embed-wrapper file-wrapper"><div class="file" id="b788977277_491"><div class="file-container view-mode-full" contenteditable="false"><div class="file-too-small"><div class="compact-view-content"><div class="file-left"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h24v24H0z"></path> <path class="graphic" d="M12 4H7a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-9h-5a1 1 0 0 1-1-1V4zm8 5.008V19a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3h5.992L20 9.008zM14 8V5.414L16.586 8H14zm-6 9a1 1 0 0 1 1-1h6a1 1 0 0 1 0 2H9a1 1 0 0 1-1-1zm1-5a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2H9z" fill="#5C6061"></path> </g></svg></div><div class="file-info file-name-trim-end"><div><span class="file-name" data-editor-toolip="Download test page.pdf" data-editor-tooltip-options='{"positionFixed":true}' data-file-export="b788977277_491.end"><a href="./assets/OFVVRj4UIjtz4S5T.pdf" target="_blank"><span></span></a></span><span class="file-size">(320.36 kB)</span></div></div></div></div></div></div><div class="editable-text attachment-caption" id="b788977277_496" style="text-align: center; width: 100%;">an attachment caption</div></div>""",
                    'div',
                    'OFVVRj4UIjtz4S5T.pdf',
                    'an attachment caption',
                    Caption),
            (
                    """<div class="embed-wrapper file-wrapper"><div class="file" id="b788977277_491"><div class="file-container view-mode-full" contenteditable="false"><div class="file-too-small"><div class="compact-view-content"><div class="file-left"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h24v24H0z"></path> <path class="graphic" d="M12 4H7a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-9h-5a1 1 0 0 1-1-1V4zm8 5.008V19a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3h5.992L20 9.008zM14 8V5.414L16.586 8H14zm-6 9a1 1 0 0 1 1-1h6a1 1 0 0 1 0 2H9a1 1 0 0 1-1-1zm1-5a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2H9z" fill="#5C6061"></path> </g></svg></div><div class="file-info file-name-trim-end"><div><span class="file-name" data-editor-toolip="Download test page.pdf" data-editor-tooltip-options='{"positionFixed":true}' data-file-export="b788977277_491.end"><a href="./assets/OFVVRj4UIjtz4S5T.pdf" target="_blank"><span><span class="file-name-main">test page.</span><span class="file-name-ext">pdf</span></span></a></span><span class="file-size">(320.36 kB)</span></div></div></div></div></div></div></div>""",
                    'div',
                    'test-page.pdf',
                    '',
                    Caption),
        ],
        ids=['good tag', 'missing file and extension span', 'no caption']
    )
    def test_extract_from_nimbus_file_embed(self, html, tag_type, expected_target_filename,
                                            caption, expected_contents_class, processing_options):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_file_embed(tag, processing_options)
        assert isinstance(result, FileEmbedNimbusHTML)
        assert isinstance(result.contents, expected_contents_class)
        assert result.contents.contents[0].contents == caption
        assert result.href == "./assets/OFVVRj4UIjtz4S5T.pdf"
        assert result.target_filename == expected_target_filename

    @pytest.mark.parametrize(
        'html, tag_type, expected_target_filename, caption, expected_contents_class', [
            (
                    """<div class="embed-wrapper file-wrapper"><div class="file" id="b788977277_491"><div class="file-container view-mode-full" contenteditable="false"><div class="file-too-small"><div class="compact-view-content"><div class="file-left"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h24v24H0z"></path> <path class="graphic" d="M12 4H7a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-9h-5a1 1 0 0 1-1-1V4zm8 5.008V19a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3h5.992L20 9.008zM14 8V5.414L16.586 8H14zm-6 9a1 1 0 0 1 1-1h6a1 1 0 0 1 0 2H9a1 1 0 0 1-1-1zm1-5a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2H9z" fill="#5C6061"></path> </g></svg></div><div class="file-info file-name-trim-end"><div><span class="file-name" data-editor-toolip="Download test page.pdf" data-editor-tooltip-options='{"positionFixed":true}' data-file-export="b788977277_491.end"><a href="./assets/OFVVRj4UIjtz4S5T.pdf" target="_blank"><span><span class="file-name-main">test page.</span></span></a></span><span class="file-size">(320.36 kB)</span></div></div></div></div></div></div><div class="editable-text attachment-caption" id="b788977277_496" style="text-align: center; width: 100%;">an attachment caption</div></div>""",
                    'div',
                    'test-page.pdf',
                    'an attachment caption',
                    Caption),
        ]
    )
    def test_extract_from_nimbus_file_embed_filename_missing_extension(self, html, tag_type, expected_target_filename,
                                                                       caption, expected_contents_class,
                                                                       processing_options):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_file_embed(tag, processing_options)
        assert isinstance(result, FileEmbedNimbusHTML)
        assert isinstance(result.contents, expected_contents_class)
        assert result.contents.contents[0].contents == caption
        assert result.href == "./assets/OFVVRj4UIjtz4S5T.pdf"
        assert result.target_filename == expected_target_filename

    @pytest.mark.parametrize(
        'html, tag_type, expected_target_filename, caption, expected_contents_class', [
            (
                    """<div class="embed-wrapper file-wrapper"><div class="file" id="b788977277_491"><div class="file-container view-mode-full" contenteditable="false"><div class="file-too-small"><div class="compact-view-content"><div class="file-left"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h24v24H0z"></path> <path class="graphic" d="M12 4H7a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-9h-5a1 1 0 0 1-1-1V4zm8 5.008V19a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3h5.992L20 9.008zM14 8V5.414L16.586 8H14zm-6 9a1 1 0 0 1 1-1h6a1 1 0 0 1 0 2H9a1 1 0 0 1-1-1zm1-5a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2H9z" fill="#5C6061"></path> </g></svg></div><div class="file-info file-name-trim-end"><div><span class="file-name" data-editor-toolip="Download test page.pdf" data-editor-tooltip-options='{"positionFixed":true}' data-file-export="b788977277_491.end"><a href="./assets/OFVVRj4UIjtz4S5T.pdf" target="_blank"><span><span class="file-name-ext">pdf</span></span></a></span><span class="file-size">(320.36 kB)</span></div></div></div></div></div></div><div class="editable-text attachment-caption" id="b788977277_496" style="text-align: center; width: 100%;">an attachment caption</div></div>""",
                    'div',
                    '.pdf',
                    'an attachment caption',
                    Caption),
        ]
    )
    def test_extract_from_nimbus_file_embed_filename_missing_filename(self, html, tag_type, expected_target_filename,
                                                                      caption, expected_contents_class,
                                                                      processing_options):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_file_embed(tag, processing_options)
        assert isinstance(result, FileEmbedNimbusHTML)
        assert isinstance(result.contents, expected_contents_class)
        assert result.contents.contents[0].contents == caption
        assert result.href == "./assets/OFVVRj4UIjtz4S5T.pdf"
        assert Path(result.target_filename).suffix == expected_target_filename
        assert Path(result.target_filename).stem == 'OFVVRj4UIjtz4S5T'

    @pytest.mark.parametrize(
        'html, tag_type', [
            (
                    """<div class="embed-wrapper file-wrapper"><div class="file" id="b788977277_491"><div class="file-container view-mode-full" contenteditable="false"><div class="file-too-small"><div class="compact-view-content"><div class="file-left"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h24v24H0z"></path> <path class="graphic" d="M12 4H7a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-9h-5a1 1 0 0 1-1-1V4zm8 5.008V19a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3h5.992L20 9.008zM14 8V5.414L16.586 8H14zm-6 9a1 1 0 0 1 1-1h6a1 1 0 0 1 0 2H9a1 1 0 0 1-1-1zm1-5a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2H9z" fill="#5C6061"></path> </g></svg></div><div class="file-info file-name-trim-end"><div><span class="file-name" data-editor-toolip="Download test page.pdf" data-editor-tooltip-options='{"positionFixed":true}' data-file-export="b788977277_491.end"></span><span class="file-size">(320.36 kB)</span></div></div></div></div></div></div><div class="editable-text attachment-caption" id="b788977277_496" style="text-align: center; width: 100%;">an attachment caption</div></div>""",
                    'div'),
            ("""<title>My title</title>""",
             'title'),
        ],
        ids=['div tag no a tag', 'invalid tag']
    )
    def test_extract_from_nimbus_file_embed_incorrect_tag(self, html, tag_type, processing_options):
        """Test passing incorrect tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        expected = None
        result = html_nimbus_extractors.extract_from_nimbus_file_embed(tag, processing_options)
        assert result == expected


class TestExtractFromNimbusImageAttachment:
    @pytest.mark.parametrize(
        'html, exp_caption, exp_width, exp_height', [
            (
                    """<div class="embed-wrapper image-wrapper indent-0" data-block-background="transparent" data-content-align="center"><div class="image" contenteditable="false" id="b788977277_455"><div class="resize-container disabled-resize" style="width: 489.015625px; --width: 489.015625px; height: 283px;"><div class="image-container" contenteditable="false"><a href="./assets/0UJGinY2jASIj13F.png" target="_blank"><img class="img-hide" src="./assets/0UJGinY2jASIj13F.png"/></a></div></div></div><div class="editable-text attachment-caption" id="b788977277_460" style="text-align: center; width: 489.015625px;">An image caption</div></div>""",
                    'An image caption',
                    '489',
                    '283',
            ),
            (
                    """<div class="embed-wrapper image-wrapper indent-0" data-block-background="transparent" data-content-align="center"><div class="image" contenteditable="false" id="b788977277_455"><div class="resize-container disabled-resize" style="width: 489.015625px; --width: 489.015625px; height: 283px;"><div class="image-container" contenteditable="false"><a href="./assets/0UJGinY2jASIj13F.png" target="_blank"><img class="img-hide" width="200" src="./assets/0UJGinY2jASIj13F.png"/></a></div></div></div><div class="editable-text attachment-caption" id="b788977277_460" style="text-align: center; width: 489.015625px;">An image caption</div></div>""",
                    'An image caption',
                    '489',
                    '283',
            ),
            (
                    """<div class="embed-wrapper image-wrapper indent-0" data-block-background="transparent" data-content-align="center"><div class="image" contenteditable="false" id="b788977277_455"><div class="resize-container disabled-resize" style="width: 489.015625px; --width: 489.015625px; height: 283px;"><div class="image-container" contenteditable="false"><a href="./assets/0UJGinY2jASIj13F.png" target="_blank"><img class="img-hide" height="300" src="./assets/0UJGinY2jASIj13F.png"/></a></div></div></div><div class="editable-text attachment-caption" id="b788977277_460" style="text-align: center; width: 489.015625px;">An image caption</div></div>""",
                    'An image caption',
                    '489',
                    '283',
            ),
            (
                    """<div class="embed-wrapper image-wrapper indent-0" data-block-background="transparent" data-content-align="center"><div class="image" contenteditable="false" id="b788977277_455"><div class="resize-container disabled-resize" style="width: 489.015625px; --width: 489.015625px; height: 283px;"><div class="image-container" contenteditable="false"><a href="./assets/0UJGinY2jASIj13F.png" target="_blank"><img class="img-hide" width="200" height="300" src="./assets/0UJGinY2jASIj13F.png"/></a></div></div></div><div class="editable-text attachment-caption" id="b788977277_460" style="text-align: center; width: 489.015625px;">An image caption</div></div>""",
                    'An image caption',
                    '489',
                    '283',
            ),
            (
                    """<div class="embed-wrapper image-wrapper indent-0" data-block-background="transparent" data-content-align="center"><div class="image" contenteditable="false" id="b788977277_455"><div class="resize-container disabled-resize"><div class="image-container" contenteditable="false"><a href="./assets/0UJGinY2jASIj13F.png" target="_blank"><img class="img-hide" width="200" height="300" src="./assets/0UJGinY2jASIj13F.png"/></a></div></div></div><div class="editable-text attachment-caption" id="b788977277_460" style="text-align: center; width: 489.015625px;">An image caption</div></div>""",
                    'An image caption',
                    '200',
                    '300',
            ),
        ],
        ids=['good tag', 'tag with a width also in img tag', 'tag with a height also in img tag',
             'tag with a width and height also in img tag', 'no style width and heights but are in img tag']
    )
    def test_extract_from_nimbus_image_attachment(self, html, exp_caption, exp_width, exp_height, processing_options):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_nimbus_image_attachment(tag, processing_options)
        assert isinstance(result, Figure)
        assert result.contents[1].contents[0].contents == exp_caption
        assert result.contents[0].href == "./assets/0UJGinY2jASIj13F.png"
        assert result.contents[0].width == exp_width
        assert result.contents[0].height == exp_height

    @pytest.mark.parametrize(
        'html, tag_type', [
            ("""<div>My Div</div>""",
             'div'),
            ("""<title>My title</title>""",
             'title'),
        ],
        ids=['div tag no img tag', 'invalid tag']
    )
    def test_extract_from_nimbus_image_attachment_incorrect_tag(self, html, tag_type, processing_options):
        """Test passing incorrect tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.extract_from_nimbus_image_attachment(tag, processing_options)
        assert result is None


class TestExtractFromNimbusAttachmentCaption:

    @pytest.mark.parametrize(
        'html, exp_caption', [
            (
                    """<div class="editable-text attachment-caption" id="b788977277_496" style="text-align: center; width: 100%;">an attachment caption</div>""",
                    'an attachment caption'),
            (
                    """<div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b2174778974_7" style="text-align: center; width: 50px;"><br></div>""",
                    ''),
        ],
        ids=['with caption', 'empty caption']
    )
    def test_extract_from_nimbus_attachment_caption(self, html, exp_caption, processing_options):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_nimbus_extractors.extract_from_nimbus_attachment_caption(tag, processing_options)
        assert isinstance(result, Caption)
        assert result.contents[0].contents == exp_caption

    def test_extract_from_nimbus_attachment_caption_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<title>My Title</title>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        result = html_nimbus_extractors.extract_from_nimbus_attachment_caption(tag, processing_options)
        assert result is None


class TestGetWidthAndHeightFromNimbusTag:

    @pytest.mark.parametrize(
        'html, exp_width, exp_height, tag_type', [
            (
                    """<div class="embed-wrapper image-wrapper indent-0" data-block-background="transparent" data-content-align="center"><div class="image" contenteditable="false" id="b788977277_455"><div class="resize-container disabled-resize" style="width: 489.015625px; --width: 489.015625px; height: 283px;"><div class="image-container" contenteditable="false"><a href="./assets/0UJGinY2jASIj13F.png" target="_blank"><img class="img-hide" src="./assets/0UJGinY2jASIj13F.png"/></a></div></div></div><div class="editable-text attachment-caption" id="b788977277_460" style="text-align: center; width: 489.015625px;">An image caption</div></div>""",
                    '489',
                    '283',
                    'div',
            ),
            (
                    """<div class="embed-wrapper image-wrapper indent-0" data-block-background="transparent" data-content-align="center"><div class="image" contenteditable="false" id="b788977277_455"><div class="resize-container disabled-resize"><div class="image-container" contenteditable="false"><a href="./assets/0UJGinY2jASIj13F.png" target="_blank"><img class="img-hide" src="./assets/0UJGinY2jASIj13F.png"/></a></div></div></div><div class="editable-text attachment-caption" id="b788977277_460" style="text-align: center; width: 489.015625px;">An image caption</div></div>""",
                    '',
                    '',
                    'div',
            ),
            ("""<title>My title</title>""",
             '',
             '',
             'title'
             ),
        ],
        ids=['good tag', 'no style width and heights', 'invalid tag']
    )
    def test_get_with_and_height_from_nimbus_tag(self, html, exp_width, exp_height, tag_type):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result_width, result_height = html_nimbus_extractors.get_with_and_height_from_nimbus_tag(tag)
        assert result_width == exp_width
        assert result_height == exp_height

    @pytest.mark.parametrize(
        'html, exp_caption, tag_type', [
            (
                    """<div class="editable-text attachment-caption" id="b788977277_496" style="text-align: center; width: 100%;">an attachment caption</div>""",
                    'an attachment caption',
                    'div'),
            (
                    """<div><div class="editable-text attachment-caption" id="b788977277_496" style="text-align: center; width: 100%;">an attachment caption</div></div>""",
                    'an attachment caption',
                    'div'),
            (
                    """<div class="editable-text attachment-caption" id="b788977277_496" style="text-align: center; width: 100%;"></div>""",
                    '',
                    'div'),
            ("""<title>My title</title>""",
             '',
             'title'),
        ],
        ids=['with caption', 'with caption wrapped in a div', 'empty caption', 'invalid tag']
    )
    def test_get_caption_text(self, html, exp_caption, tag_type, processing_options):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_type)
        assert tag.name == tag_type

        result = html_nimbus_extractors.get_caption_text(tag, processing_options)
        assert isinstance(result, Caption)
        assert result.contents[0].contents == exp_caption


class TestExtractFromNimbusTable:

    @pytest.mark.parametrize(
        'keep_abc, exp_length', [
            (True, 10),
            (False, 9),
        ],
    )
    def test_extract_from__nimbus_table(self, keep_abc, exp_length, processing_options):
        html = """<div class="embed-wrapper table-wrapper export"><div class="table-blot" contenteditable="false" id="b788977277_649"><div class="table-embed"><div class="table-scroll"><div class="table-scroll-items"><table class="table-component"><thead><tr><th class="table-head-start"><div class="table-header-circle"></div></th><th></th><th class="table-head-item" data-index="0" width="180"><div class="item-ui"><div class="item-title" style="max-width: 136px;">A</div></div></th><th class="table-head-item" data-index="1" width="180"><div class="item-ui"><div class="item-title" style="max-width: 136px;">B</div></div></th><th class="table-head-item" data-index="2" width="180"><div class="item-ui"><div class="item-title" style="max-width: 136px;">C</div></div></th></tr></thead><tbody><tr height="36"><td class="table-head-item" data-index="0" height="36"><div class="item-ui"><div class="item-title">1</div></div></td><td></td><td><div class="table-text-common">r1c1
</div></td><td><div class="table-text-common">r1c2
</div></td><td><div class="table-text-common">r1c3
</div></td></tr><tr height="36"><td class="table-head-item" data-index="1" height="36"><div class="item-ui"><div class="item-title">2</div></div></td><td></td><td><div class="table-text-common">r2c1
</div></td><td><div class="table-text-common">r2c2
</div></td><td><div class="table-text-common">r2c2
</div></td></tr><tr height="36"><td class="table-head-item" data-index="2" height="36"><div class="item-ui"><div class="item-title">3</div></div></td><td></td><td><div class="table-text-common">12%
</div></td><td><div class="table-text-common">1234
</div></td><td></td></tr><tr height="36"><td class="table-head-item" data-index="3" height="36"><div class="item-ui"><div class="item-title">4</div></div></td><td></td><td><div class="table-text-common">23</div></td><td><div class="table-text-common">$109</div></td><td class="cell-attachment"><div class="table-attachment-wrap"><div><div class="table-attachment"><div class="attachment-item"></div></div></div></div></td></tr><tr height="36"><td class="table-head-item" data-index="4" height="36"><div class="item-ui"><div class="item-title">5</div></div></td><td></td><td><span class="checkbox-component"></span></td><td><span class="checkbox-component checked"></span></td><td class="full-height"><div class="select-component"><div class="select-list"><span class="select-label adaptive-text bg-palette-brown"><span class="select-label-text">singel select</span></span></div></div></td></tr><tr height="36"><td class="table-head-item" data-index="5" height="36"><div class="item-ui"><div class="item-title">6</div></div></td><td></td><td class="full-height"><div class="select-component"><div class="select-list"><span class="select-label adaptive-text bg-palette-green-sea"><span class="select-label-text">select 1</span></span><span class="select-label adaptive-text bg-palette-yellow"><span class="select-label-text">select 2</span></span></div></div></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="rfusba" data-mention-name="kevindurston21@gmail.com" data-mention-object_id="2510963" data-mention-type="user">kevindurston21@gmail.com</span></span></td><td class="full-height"><div class="collaborate-component"><div class="collaborate-list"><span class="collaborate-item" data-mention-id="rd0qzj" data-mention-name="kevindurston21@gmail.com" data-mention-type="user" data-user-id="2510963"><span class="collaborate-item-img"><span class="user-avatar" style="background: rgb(250, 201, 47);">K</span></span><span class="collaborate-item-name"><span class="collaborate-item-text">kevindurston21@gmail.com</span></span></span></div></div></td></tr><tr height="36"><td class="table-head-item" data-index="6" height="36"><div class="item-ui"><div class="item-title">7</div></div></td><td></td><td class="cell-date table-text-common"><span class="input-date"><span class="input-date-string"><span class="input-date-text">11/01/2022 22:03</span></span></span></td><td><div class="table-text-common"><a href="https://www.google.com" rel="nofollow noopener" target="_blank">a link in a cell</a></div></td><td><div class="rating-component"><span class="rating-item rating-active"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#fda639" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-active"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#fda639" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-active"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#fda639" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-inactive"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#e8e8e8" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-inactive"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#e8e8e8" fill-rule="evenodd"></path></svg></span></div></td></tr><tr height="36"><td class="table-head-item" data-index="7" height="36"><div class="item-ui"><div class="item-title">8</div></div></td><td></td><td class="cell-progress"><div class="table-progress progress-low"><div class="input-slider readonly table-progress-slider"><span class="slider-range"><span class="slider-progress" style="width: 0%;"><span class="slider-holder"></span></span></span></div><span class="progress-value table-text-common">0%</span></div></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="hu4brg" data-mention-name="Default workspace" data-mention-object_id="23c421363hn6ndes" data-mention-type="workspace">Default workspace</span></span></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="a9k6af" data-mention-name="another topic subfolder renamed" data-mention-object_id="TvjfOrJ0NtSLV3KH" data-mention-type="folder">another topic subfolder renamed</span></span></td></tr><tr height="36"><td class="table-head-item" data-index="8" height="36"><div class="item-ui"><div class="item-title">9</div></div></td><td></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="lzcl03" data-mention-name="Emoji - 😀  - note title" data-mention-object_id="fnk139kSrRzJOEVd" data-mention-type="note">Emoji - 😀  - note title</span></span></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="m4tjz1" data-mention-name="The attached file above is exported but not linked in html" data-mention-object_id="Asl0q2f5F4TGCWSx" data-mention-type="note">The attached file above is exported but not linked in html</span></span></td><td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="j5bjyn" data-mention-name="Test 1" data-mention-object_id="zEZUSiVmAQPITGLD" data-mention-type="note">Test 1</span></span></td></tr></tbody><tfoot><tr><td class="add-row"></td><td></td><td><div class="summary-wrap"><div class="summary-item"><span class="summary-name overflow-ellipsis">Percent empty</span>:<div class="summary-value" data-editor-toolip="22.22%" data-editor-tooltip-options='{"positionFixed":true,"modifiers":{"offset":{"offset":"0,0"}}}' valuelength="6">22.22%</div><span class="summary-menu-icon"><svg height="16" viewbox="0 0 16 16" width="16" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h16v16H0z"></path> <path class="graphic" d="M4 7h8l-4 4z" fill="#AEB7B8"></path> </g></svg></span></div></div></td><td><div class="summary-wrap"><div class="summary-item"><span class="summary-name">All</span>:<div class="summary-value" data-editor-toolip="9" data-editor-tooltip-options='{"positionFixed":true,"modifiers":{"offset":{"offset":"0,0"}}}' valuelength="1">9</div><span class="summary-menu-icon"><svg height="16" viewbox="0 0 16 16" width="16" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h16v16H0z"></path> <path class="graphic" d="M4 7h8l-4 4z" fill="#AEB7B8"></path> </g></svg></span></div></div></td><td><div class="summary-wrap"><div class="summary-item"><span class="summary-name">All</span>:<div class="summary-value" data-editor-toolip="9" data-editor-tooltip-options='{"positionFixed":true,"modifiers":{"offset":{"offset":"0,0"}}}' valuelength="1">9</div><span class="summary-menu-icon"><svg height="16" viewbox="0 0 16 16" width="16" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"> <path d="M0 0h16v16H0z"></path> <path class="graphic" d="M4 7h8l-4 4z" fill="#AEB7B8"></path> </g></svg></span></div></div></td></tr></tfoot></table></div></div></div><div class="table-blot-edit-area"></div></div><div class="editable-text attachment-caption empty-caption empty-caption-hidden" id="b788977277_666" style="text-align: center; width: 50px;"><br/></div></div>"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        processing_options.keep_abc_123_columns = keep_abc
        result = html_nimbus_extractors.extract_from__nimbus_table(tag, processing_options)
        assert isinstance(result, Table)
        assert len(result.contents) == exp_length
        assert isinstance(result.contents[0], TableHeader)
        assert isinstance(result.contents[1], TableRow)

    def test_extract_from_123abc_table_header_row(self, processing_options):
        table_th_cell_items = ['<th class="table-head-start"><div class="table-header-circle"></div></th>', '<th></th>',
                               '<th class="table-head-item" data-index="0" width="180"><div class="item-ui"><div class="item-title" style="max-width: 136px;">A</div></div></th>',
                               '<th class="table-head-item" data-index="1" width="180"><div class="item-ui"><div class="item-title" style="max-width: 136px;">B</div></div></th>',
                               '<th class="table-head-item" data-index="2" width="180"><div class="item-ui"><div class="item-title" style="max-width: 136px;">C</div></div></th>']
        table_header_tags = []
        for item in table_th_cell_items:
            soup = helper_functions.make_soup_from_html(item)
            tag = soup.find('th')
            table_header_tags.append(tag)

        result = html_nimbus_extractors.extract_from_123abc_table_header_row(table_header_tags, processing_options)
        assert isinstance(result, list)
        assert len(result) == 4
        assert isinstance(result[0], TableItem)
        assert result[0].contents[0].contents == ''
        assert result[1].contents[0].contents == 'A'

    @pytest.mark.parametrize(
        'keep_abc, exp_length, item_1, item_2', [
            (True, 4, '1', 'r1c1'),
            (False, 3, 'r1c1', 'r1c2'),
        ],
    )
    def test_extract_from_table_row(self, keep_abc, exp_length, item_1, item_2, processing_options):
        table_th_cell_items = [
            '<td class="table-head-item" data-index="0" height="36"><div class="item-ui"><div class="item-title">1</div></div></td>',
            '<td></td>', '<td><div class="table-text-common">r1c1\n</div></td>',
            '<td><div class="table-text-common">r1c2\n</div></td>',
            '<td><div class="table-text-common">r1c3\n</div></td>']
        table_header_tags = []
        for item in table_th_cell_items:
            soup = helper_functions.make_soup_from_html(item)
            tag = soup.find('td')
            table_header_tags.append(tag)

        processing_options.keep_abc_123_columns = keep_abc
        result = html_nimbus_extractors.extract_from_table_row(table_header_tags, processing_options)
        assert isinstance(result, list)
        assert len(result) == exp_length
        assert isinstance(result[0], TableItem)
        assert result[0].contents[0].contents == item_1
        assert result[1].contents[0].contents == item_2

    class TestExtractFromNimbusTableTextItem:
        @pytest.mark.parametrize(
            'html, exp_contents', [
                ("""<td><div class="table-text-common">r1c1</div></td>""", 'r1c1'),
                ("""<td><div class="item-title">title</div></td>""", 'title'),
            ],
        )
        def test_extract_from_nimbus_table_text_item(self, html, exp_contents, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find('td')
            assert tag.name == 'td'

            result = html_nimbus_extractors.extract_from_nimbus_table_text_item(tag, processing_options)
            assert isinstance(result, list)
            assert isinstance(result[0], TextItem)
            assert result[0].contents == exp_contents

        @pytest.mark.parametrize(
            'html', [
                ("""<td><div class="table-text-common"></div></td>"""),
                ("""<td><div class="item-title"></div></td>"""),
            ],
        )
        def test_extract_from_nimbus_table_text_item_empty_item(self, html, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find('td')
            assert tag.name == 'td'

            result = html_nimbus_extractors.extract_from_nimbus_table_text_item(tag, processing_options)
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextItem)
            assert result[0].contents == ''

        @pytest.mark.parametrize(
            'html, tag_type', [
                (
                        """<td class="cell-progress"><div class="table-progress progress-low"><div class="input-slider readonly table-progress-slider"><span class="slider-range"><span class="slider-progress" style="width: 0%;"><span class="slider-holder"></span></span></span></div><span class="progress-value table-text-common">0%</span></div></td>""",
                        'td'),
                ("""<title>My Title</title>>""",
                 'title'),
            ],
        )
        def test_extract_from_nimbus_table_text_item_incorrect_tag(self, html, tag_type, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find(tag_type)
            assert tag.name == tag_type

            result = html_nimbus_extractors.extract_from_nimbus_table_text_item(tag, processing_options)
            assert result is None

    class TestExtractFromNimbusTableProgressItem:
        def test_extract_from_nimbus_table_progress_item(self, processing_options):
            html = """<td class="cell-progress"><div class="table-progress progress-low"><div class="input-slider readonly table-progress-slider"><span class="slider-range"><span class="slider-progress" style="width: 0%;"><span class="slider-holder"></span></span></span></div><span class="progress-value table-text-common">0%</span></div></td>"""
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find('td')
            assert tag.name == 'td'

            result = html_nimbus_extractors.extract_from_nimbus_table_progress_item(tag, processing_options)
            assert isinstance(result, TableItem)
            assert isinstance(result.contents[0], TextItem)
            assert result.contents[0].contents == 'Progress 0%'

        @pytest.mark.parametrize(
            'html, tag_type', [
                ("""<td><div class="table-text-common">r1c1</div></td>""",
                 'td'),
                ("""<title>My Title</title>>""",
                 'title'),
            ],
        )
        def test_extract_from_nimbus_table_progress_item_incorrect_tag(self, html, tag_type, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find(tag_type)
            assert tag.name == tag_type

            result = html_nimbus_extractors.extract_from_nimbus_table_progress_item(tag, processing_options)
            assert result is None

    class TestExtractFromNimbusTableRatingItem:
        def test_extract_from_nimbus_table_rating_item(self, processing_options):
            html = """<td><div class="rating-component"><span class="rating-item rating-active"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#fda639" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-active"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#fda639" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-active"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#fda639" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-inactive"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#e8e8e8" fill-rule="evenodd"></path></svg></span><span class="rating-item rating-inactive"><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M10.548 3.807c.467-1.343 2.367-1.343 2.834 0l1.65 4.748 5.026.103c1.422.029 2.009 1.836.875 2.695l-4.005 3.037 1.455 4.81c.412 1.362-1.125 2.479-2.292 1.666l-4.126-2.87-4.126 2.87c-1.167.813-2.704-.304-2.293-1.665l1.456-4.811-4.006-3.037c-1.133-.86-.546-2.666.876-2.695l5.026-.103 1.65-4.748z" fill="#e8e8e8" fill-rule="evenodd"></path></svg></span></div></td>"""
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find('td')
            assert tag.name == 'td'

            result = html_nimbus_extractors.extract_from_nimbus_table_rating_item(tag, processing_options)
            assert isinstance(result, TableItem)
            assert isinstance(result.contents[0], TextItem)
            assert result.contents[0].contents == 'Rating 3/5 stars'

        @pytest.mark.parametrize(
            'html, tag_type', [
                ("""<td><div class="table-text-common">r1c1</div></td>""",
                 'td'),
                ("""<title>My Title</title>>""",
                 'title'),
            ],
        )
        def test_extract_from_nimbus_table_rating_item_incorrect_tag(self, html, tag_type, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find(tag_type)
            assert tag.name == tag_type

            result = html_nimbus_extractors.extract_from_nimbus_table_rating_item(tag, processing_options)
            assert result is None

    class TestExtractFromNimbusTableHyperlinkItem:
        def test_extract_from_nimbus_table_hyperlink_item(self, processing_options):
            html = """<td><div class="table-text-common"><a href="https://www.google.com" rel="nofollow noopener" target="_blank">a link in a cell</a></div></td>"""
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find('td')
            assert tag.name == 'td'

            result = html_nimbus_extractors.extract_from_nimbus_table_hyperlink_item(tag, processing_options)
            assert isinstance(result, TableItem)
            assert isinstance(result.contents[0], Hyperlink)
            assert result.contents[0].href == "https://www.google.com"
            assert result.contents[0].contents == "a link in a cell"

        @pytest.mark.parametrize(
            'html, tag_type', [
                ("""<td><div class="table-text-common">r1c1</div></td>""",
                 'td'),
                ("""<title>My Title</title>>""",
                 'title'),
            ],
        )
        def test_extract_from_nimbus_table_hyperlink_item_incorrect_tag(self, html, tag_type, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find(tag_type)
            assert tag.name == tag_type

            result = html_nimbus_extractors.extract_from_nimbus_table_hyperlink_item(tag, processing_options)
            assert result is None

    class TestExtractFromNimbusTableDateItem:
        def test_extract_from_nimbus_table_date_item(self, processing_options):
            html = """<td class="cell-date table-text-common"><span class="input-date"><span class="input-date-string"><span class="input-date-text">11/01/2022 22:03</span></span></span></td>"""
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find('td')
            assert tag.name == 'td'

            result = html_nimbus_extractors.extract_from_nimbus_table_date_item(tag, processing_options)
            assert isinstance(result, TableItem)
            assert isinstance(result.contents[0], TextItem)
            assert result.contents[0].contents == "11/01/2022 22:03"

        @pytest.mark.parametrize(
            'html, tag_type', [
                ("""<td><div class="table-text-common">r1c1</div></td>""",
                 'td'),
                ("""<title>My Title</title>>""",
                 'title'),
            ],
        )
        def test_extract_from_nimbus_table_date_item_incorrect_tag(self, html, tag_type, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find(tag_type)
            assert tag.name == tag_type

            result = html_nimbus_extractors.extract_from_nimbus_table_date_item(tag, processing_options)
            assert result is None

    class TestExtractFromNimbusTableCollaboratorItem:
        def test_extract_from_nimbus_table_collaboration_item(self, processing_options):
            html = """<td class="full-height"><div class="collaborate-component"><div class="collaborate-list"><span class="collaborate-item" data-mention-id="rd0qzj" data-mention-name="user@gmail.com" data-mention-type="user" data-user-id="2510963"><span class="collaborate-item-img"><span class="user-avatar" style="background: rgb(250, 201, 47);">K</span></span><span class="collaborate-item-name"><span class="collaborate-item-text">user@gmail.com</span></span></span></div></div></td>"""
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find('td')
            assert tag.name == 'td'

            result = html_nimbus_extractors.extract_from_nimbus_table_collaboration_item(tag, processing_options)
            assert isinstance(result, TableItem)
            assert isinstance(result.contents[0], TableCollaborator)
            assert result.contents[0].contents == "user@gmail.com"

        @pytest.mark.parametrize(
            'html, tag_type', [
                ("""<td><div class="table-text-common">r1c1</div></td>""",
                 'td'),
                ("""<title>My Title</title>>""",
                 'title'),
            ],
        )
        def test_extract_from_nimbus_table_collaboration_item_incorrect_tag(self, html, tag_type, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find(tag_type)
            assert tag.name == tag_type

            result = html_nimbus_extractors.extract_from_nimbus_table_collaboration_item(tag, processing_options)
            assert result is None

    class TestExtractFromNimbusTableMentionItem:

        @pytest.mark.parametrize(
            'html, mention_type, exp_contents', [
                (
                        """<td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="rfusba" data-mention-name="user@gmail.com" data-mention-object_id="2510963" data-mention-type="user">user@gmail.com</span></span></td>""",
                        MentionUser,
                        "user@gmail.com"),
                (
                        """<td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="hu4brg" data-mention-name="Default workspace" data-mention-object_id="23c421363hn6ndes" data-mention-type="workspace">Default workspace</span></span></td>""",
                        MentionWorkspace,
                        "Default workspace"),
                (
                        """<td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="a9k6af" data-mention-name="another topic subfolder renamed" data-mention-object_id="TvjfOrJ0NtSLV3KH" data-mention-type="folder">another topic subfolder renamed</span></span></td>""",
                        MentionFolder,
                        "another topic subfolder renamed"),
                (
                        """<td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="lzcl03" data-mention-name="Emoji - 😀  - note title" data-mention-object_id="fnk139kSrRzJOEVd" data-mention-type="note">Emoji - 😀  - note title</span></span></td>""",
                        MentionNote,
                        "Emoji - 😀  - note title"),
            ],
        )
        def test_extract_from_nimbus_table_mention_item(self, html, mention_type, exp_contents, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find('td')
            assert tag.name == 'td'

            result = html_nimbus_extractors.extract_from_nimbus_table_mention_item(tag, processing_options)
            assert isinstance(result, TableItem)
            assert isinstance(result.contents[0], mention_type)
            assert result.contents[0].contents == exp_contents

        @pytest.mark.parametrize(
            'html, tag_type', [
                ("""<td><div class="table-text-common">r1c1</div></td>""",
                 'td'),
                ("""<title>My Title</title>>""",
                 'title'),
                (
                        """<td class="cell-mention table-text-common"><span class="cell-mention-wrap"><span class="mention-link" contenteditable="false" data-mention-id="a9k6af" data-mention-name="another topic subfolder renamed" data-mention-object_id="TvjfOrJ0NtSLV3KH">another topic subfolder renamed</span></span></td>""",
                        'td',),
            ],
            ids=['div tag not apn tag', 'invlaid tag', 'td has missing data-mention-type']
        )
        def test_extract_from_nimbus_table_mention_item_incorrect_tag(self, html, tag_type, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find(tag_type)
            assert tag.name == tag_type

            result = html_nimbus_extractors.extract_from_nimbus_table_mention_item(tag, processing_options)
            assert result is None

    class TestExtractFromNimbusTableSelectItem:
        @pytest.mark.parametrize(
            'html, exp_contents', [
                (
                        """<td class="full-height"><div class="select-component"><div class="select-list"><span class="select-label adaptive-text bg-palette-brown"><span class="select-label-text">single select</span></span></div></div></td>""",
                        "single select"),
                (
                        """<td class="full-height"><div class="select-component"><div class="select-list"><span class="select-label adaptive-text bg-palette-green-sea"><span class="select-label-text">select 1</span></span><span class="select-label adaptive-text bg-palette-yellow"><span class="select-label-text">select 2</span></span></div></div></td>""",
                        "select 1 select 2"),
            ],
        )
        def test_extract_from_nimbus_table_select_item(self, html, exp_contents, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find('td')
            assert tag.name == 'td'

            result = html_nimbus_extractors.extract_from_nimbus_table_select_item(tag, processing_options)
            assert isinstance(result, TableItem)
            assert isinstance(result.contents[0], TextItem)
            assert result.contents[0].contents == exp_contents

        @pytest.mark.parametrize(
            'html, tag_type', [
                ("""<td><div class="table-text-common">r1c1</div></td>""",
                 'td'),
                ("""<title>My Title</title>>""",
                 'title'),
            ],
        )
        def test_extract_from_nimbus_table_select_item_incorrect_tag(self, html, tag_type, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find(tag_type)
            assert tag.name == tag_type

            result = html_nimbus_extractors.extract_from_nimbus_table_select_item(tag, processing_options)
            assert result is None

    class TestExtractFromNimbusTableCheckItem:
        @pytest.mark.parametrize(
            'html, exp_contents', [
                ("""<td><span class="checkbox-component"></span></td>""",
                 False),
                ("""<td><span class="checkbox-component checked"></span></td>""",
                 True),
            ],
        )
        def test_extract_from_nimbus_table_check_item(self, html, exp_contents, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find('td')
            assert tag.name == 'td'

            result = html_nimbus_extractors.extract_from_nimbus_table_check_item(tag, processing_options)
            assert isinstance(result, TableCheckItem)
            assert result.contents == exp_contents

        @pytest.mark.parametrize(
            'html, tag_type', [
                ("""<td><div class="table-text-common">r1c1</div></td>""",
                 'td'),
                ("""<title>My Title</title>>""",
                 'title'),
                ("""<td><span class=""></span></td>""",
                 'td'),
            ],
        )
        def test_extract_from_nimbus_table_check_item_incorrect_tag(self, html, tag_type, processing_options):
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find(tag_type)
            assert tag.name == tag_type

            result = html_nimbus_extractors.extract_from_nimbus_table_check_item(tag, processing_options)
            assert result is None


class TestExtractFromNimbusBulletList:
    def test_extract_from_nimbus_bullet_list(self, processing_options):
        bullet_items = [
            '<li class="list-item-bullet editable-text list-item indent-0" id="b788977277_357" list-style="circle" style="text-align: left;">bullet 1</li>',
            '<li class="list-item-bullet editable-text list-item indent-1" id="b788977277_378" list-style="rectangle" style="text-align: left;">sub <strong>bullet</strong> two, below is an empty bullet</li>',
            '<li class="list-item-bullet editable-text list-item indent-1" id="b1786634969_118" list-style="rectangle" style="text-align: left;"><br/></li>',
            '<li class="list-item-bullet editable-text list-item indent-0" id="b788977277_405" list-style="circle" style="text-align: left;">bullet 2</li>']
        bullet_item_tags = []
        for item in bullet_items:
            soup = helper_functions.make_soup_from_html(item)
            tag = soup.find('li')
            bullet_item_tags.append(tag)

        result = html_nimbus_extractors.extract_from_nimbus_bullet_list(bullet_item_tags, processing_options)
        assert isinstance(result, BulletList)
        assert len(result.contents) == 4
        assert isinstance(result.contents[0], BulletListItem)


class TestExtractFromNimbusNumberedList:
    def test_extract_from_nimbus_numbered_list(self, processing_options):
        number_items = [
            '<li class="list-item-number editable-text list-item indent-0 one-cnt-sym" id="b788977277_213" style="text-align: left;">number one</li>',
            '<li class="list-item-number editable-text list-item indent-0 one-cnt-sym" id="b788977277_237" style="text-align: left;">number two</li>',
            '<li class="list-item-number editable-text list-item indent-1 one-cnt-sym" id="b788977277_258" style="text-align: left;">number <strong>bold</strong> 2-1</li>',
            '<li class="list-item-number editable-text list-item indent-1 one-cnt-sym" id="b788977277_280" style="text-align: left;">number <em>Italic</em> 2-2</li>',
            '<li class="list-item-number editable-text list-item indent-0 one-cnt-sym" id="b788977277_301" style="text-align: left;">number <strong><em>bold italic</em></strong> 3 below is an empty numbered item</li>',
            '<li class="list-item-number editable-text list-item indent-0 one-cnt-sym" id="b1786634969_81" style="text-align: left;"><br/></li>']
        number_item_tags = []
        for item in number_items:
            soup = helper_functions.make_soup_from_html(item)
            tag = soup.find('li')
            number_item_tags.append(tag)

        result = html_nimbus_extractors.extract_from_nimbus_numbered_list(number_item_tags, processing_options)
        assert isinstance(result, NumberedList)
        assert len(result.contents) == 6
        assert isinstance(result.contents[0], NumberedListItem)


class TestExtractFromNimbusChecklist:
    def test_extract_from_nimbus_checklist(self, processing_options):
        check_items = [
            '<li class="list-item-checkbox editable-text list-item indent-0" data-checked="false" id="b788977277_57" style="text-align: left;">check 1</li>',
            '<li class="list-item-checkbox editable-text list-item indent-1" data-checked="false" id="b788977277_78" style="text-align: left;">check <strong>level</strong> 2</li>',
            '<li class="list-item-checkbox editable-text list-item indent-1" data-checked="true" id="b788977277_105" style="text-align: left;">check <strong><em>level</em></strong> 2 item 2</li>',
            '<li class="list-item-checkbox editable-text list-item indent-0" data-checked="false" id="b788977277_136" style="text-align: left;">check <em>level</em> 1 item 2, below is an empty check item</li>',
            '<li class="list-item-checkbox editable-text list-item indent-0" data-checked="false" id="b1786634969_7" style="text-align: left;"><br/></li>']
        check_item_tags = []
        for item in check_items:
            soup = helper_functions.make_soup_from_html(item)
            tag = soup.find('li')
            check_item_tags.append(tag)

        result = html_nimbus_extractors.extract_from_nimbus_checklist(check_item_tags, processing_options)
        assert isinstance(result, Checklist)
        assert len(result.contents) == 5
        assert isinstance(result.contents[0], ChecklistItem)
