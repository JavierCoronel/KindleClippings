from typing import Set
import os
import re
import io
import logging
from tqdm import tqdm

logging.basicConfig(format='%(asctime)s %(name)s %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)

def parse_clippings(source_file: str, output_directory: str, encoding: str = "utf-8", include_clip_meta: bool = False) -> Set[str]:
    """
    Parse Kindle clippings and organize them by book on separate .txt files.

    Parameters
    ----------
    source_file : str
        Path to the source clippings file.
    output_directory : str
        Directory where organized highlights will be saved.
    encoding : str, optional
        Encoding of the source file, by default 'utf-8'.
    include_clip_meta : bool, optional
        Whether to include metadata from the clippings, by default False.

    Returns
    -------
    Set[str]
        A set of output file paths created.
    """
    logger.info(f'Processing highlights file: {source_file}')
    if not os.path.isfile(source_file):
        raise IOError(f"ERROR: cannot find {source_file}")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_files = set()
    title = ""

    with io.open(source_file, "r", encoding=encoding, errors="ignore") as f:

        highlight_chunks = f.read().split("==========")
        logger.info(f'{len(highlight_chunks)} highligths identified')
        for highlight in tqdm(highlight_chunks):
            lines = highlight.split("\n")[1:]
            if len(lines) < 3 or lines[3] == "":
                continue

            title = lines[0]
            if title[0] == "\ufeff":
                title = title[1:]

            outfile_name = remove_chars(title, output_directory) + ".txt"
            path = os.path.join(output_directory, outfile_name)

            if outfile_name not in (list(output_files) + os.listdir(output_directory)):
                logger.info(f'New highligths recognized from the book: {title}')
                mode = "w"
                output_files.add(path)
                current_text = ""
            else:
                mode = "a"
                with io.open(path, "r", encoding=encoding, errors="ignore") as textfile:
                    current_text = textfile.read()

            clipping_text = lines[3]
            clip_meta = lines[1]

            with io.open(path, mode, encoding=encoding, errors="ignore") as outfile:
                if clipping_text not in current_text:
                    outfile.write(clipping_text + "\n")
                    if include_clip_meta:
                        outfile.write(clip_meta + "\n")
                    outfile.write("\n...\n\n")

    return output_files


def remove_chars(s: str, output_directory: str = "") -> str:
    """Removes special characters from a string to make it a valid filename."""
    s = re.sub(" *: *", " - ", s)
    s = s.replace("?", "").replace("&", "and")
    s = re.sub(r"\((.+?)\)", r"- \1", s)
    s = re.sub(r"[^a-zA-Z\d\s\w;,_-]+", "", s)
    s = re.sub(r"^\W+|\W+$", "", s)

    max_length = 245 - len(output_directory)
    return s[:max_length]
