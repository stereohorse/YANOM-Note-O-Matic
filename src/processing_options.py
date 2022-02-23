from dataclasses import dataclass

from helper_functions import FileNameOptions
from embeded_file_types import EmbeddedFileTypes


@dataclass
class ProcessingOptions:
    embed_files: EmbeddedFileTypes
    export_format: str
    unrecognised_tag_format: str
    filename_options: FileNameOptions
