from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:  # avoid circular import error for Typing  pragma: no cover
    from processing_options import ProcessingOptions  # pragma: no cover


def embed_image(processing_options: ProcessingOptions,
                alt_text: str, width: str, height: str, target_path: Path, caption: str = ''):

    md_embed_symbol = ''
    md_alt_text = alt_text.strip() if alt_text else ''
    md_width = ''
    md_x_height = ''
    md_height = ''
    md_target_path = str(target_path) if target_path else ''
    md_alt_pipe = ''
    md_caption = f"{caption}\n" if caption else ''

    if width:
        md_alt_pipe = '|'
        md_width = width

    if height and width:  # NOTE for obsidian for height you must have a width, no width then no height
        md_x_height = 'x'
        md_height = f"{height}"

    if target_path and target_path.suffix.lstrip('.') in processing_options.embed_files.images:
        md_embed_symbol = '!'

    return f"{md_embed_symbol}" \
           f"[{md_alt_text}{md_alt_pipe}{md_width}{md_x_height}{md_height}]" \
           f"({md_target_path})\n{md_caption}"

#
# def embed_file(processing_options: ProcessingOptions, alt_text: str, target_path: Path, caption: str = ''):
#     md_embed_symbol = ''
#     md_alt_text = ''
#     md_target_path = str(target_path)
#     md_caption = ''
#
#     if alt_text:
#         md_alt_text = alt_text.strip()
#
#     if caption:
#         md_caption = f"{caption}\n"
#
#     available_embeds = [*processing_options.embed_files.documents,
#                         *processing_options.embed_files.audio,
#                         *processing_options.embed_files.video]
#
#     if target_path.suffix.lstrip('.') in available_embeds:
#         md_embed_symbol = '!'
#
#     return f"{md_embed_symbol}[{md_alt_text}]({md_target_path})\n{md_caption}"
