from collections import namedtuple

FormatElements = namedtuple('FormatElements', ['leading_tag', 'trailing_tag'])
format_styling = {
    'strong': FormatElements('**', "**"),
    'b': FormatElements('**', "**"),
    'em': FormatElements('*', "*"),
    'del': FormatElements('~~', "~~"),
    'u': FormatElements('<u>', "</u>"),
    'mark': FormatElements('<mark>', "</mark>"),
    'code': FormatElements('`', "`"),
}