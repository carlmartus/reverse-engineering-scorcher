import sys
import logging
from pathlib import Path

_TAGDEN = "TAGDEN.BIN"

logger = logging.getLogger()


def extract_all(tagden_path: Path, dest_dir: Path) -> None:
    logger.info("Extracting assets from file '%s'", tagden_path)
    if not tagden_path.exists():
        raise FileNotFoundError(tagden_path)
    if not dest_dir.exists():
        logger.info("Creating output directory '%s'", dest_dir)
        dest_dir.mkdir()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
    if len(sys.argv) != 2:
        logger.error(
            "Please specify path to '%s' as argument",
            _TAGDEN,
        )
        sys.exit(1)
    else:
        src = Path(sys.argv[1])
        dst = Path("./output")
        try:
            extract_all(src, dst)
        except FileNotFoundError as err:
            logger.error("Failed to find file '%s'", err.filename)
            sys.exit(1)
