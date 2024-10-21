import logging
import fire
from src.clippings_parser import parse_clippings
from src.file_conversion import convert_files_to_formatted_highlights

logging.basicConfig(format='%(asctime)s %(name)s %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)

def main(source: str, destination: str, encoding: str = "utf8", output_format: str = "pdf", include_clip_meta: bool = True):
    """
    Main function to parse Kindle clippings and create formatted files.

    Parameters
    ----------
    source : str
        Path to the source file or directory.
    destination : str
        Path to the destination directory.
    encoding : str, optional
        Encoding of the source file, by default 'utf8'.
    output_format : str, optional
        Output format, by default 'pdf'.
    include_clip_meta : bool, optional
        Whether to include clipping metadata, by default True.
    """
    logger.info(f"Using parameters: source: {source}, destination: {destination}, output_format: {output_format}, include_clip_meta: {include_clip_meta}")
    parsed_files = parse_clippings(source, destination, encoding, include_clip_meta)
    formatted_files = convert_files_to_formatted_highlights(parsed_files, output_format)
    logger.info(f"{len(formatted_files)} converted successfully")

if __name__ == "__main__":
    fire.Fire(main)
