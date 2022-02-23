from dataclasses import dataclass
from typing import List


@dataclass
class EmbeddedFileTypes:
    documents: List[str]
    images: List[str]
    audio: List[str]
    video: List[str]
