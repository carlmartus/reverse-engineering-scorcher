import io
import sys
import logging
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Iterable, Optional
from struct import unpack

_TAGDEN = "TAGDEN.BIN"
_ABSOLUTE_DEV_COMPUTER_PREFIX: PureWindowsPath = PureWindowsPath("l:\\scorpc\\game\\")

logger = logging.getLogger()


@dataclass
class TagdenFile:
    internal_path: PureWindowsPath
    type: int
    offset: int
    size: int
    unknown1: int
    output_path: Optional[Path] = None


def _read_file(path: Path) -> bytes:
    with open(path, "rb") as fd:
        return fd.read()


def _identify_tagden_files(buf: io.BytesIO) -> Iterable[TagdenFile]:
    while True:
        frame_start = buf.tell()
        buf.read(2)
        type, offset, size, unknown1, frame_size = unpack(">HIIHH", buf.read(14))
        if type != 16:
            break
        path_raw: bytes = buf.read(frame_size - (buf.tell() - frame_start))
        internal_tagden_path = PureWindowsPath(
            path_raw[: path_raw.find(b"\x00")].decode()
        )
        logger.debug("Found file '%s'", internal_tagden_path)
        yield TagdenFile(internal_tagden_path, type, offset, size, unknown1)


def _remove_absolute_tagden_path(internal_tagden_path: PureWindowsPath) -> Path:
    """
    Files are stored with absolute file names from a developer computer.
    Convert these to something that can be stored in the output directory.
    """
    return Path(*internal_tagden_path.parts[len(_ABSOLUTE_DEV_COMPUTER_PREFIX.parts) :])


def _extract_tagden_file(
    tagden_buf: io.BytesIO, tagden_file: TagdenFile, dest_dir: Path
) -> None:
    win_path = _remove_absolute_tagden_path(tagden_file.internal_path)
    put_path = dest_dir / win_path
    put_dir = Path(*put_path.parts[:-1])
    if not put_dir.exists():
        put_dir.mkdir(parents=True)
        logger.debug("Creating directory '%s' for extraction", put_dir)
    tagden_buf.seek(tagden_file.offset)
    with open(put_path, "wb") as fd:
        fd.write(tagden_buf.read(tagden_file.size))
    logger.debug("Extracted file '%s'", put_path)


def extract_all(tagden_path: Path, dest_dir: Path) -> None:
    logger.info("Extracting assets from file '%s'", tagden_path)
    if not tagden_path.exists():
        raise FileNotFoundError(tagden_path)
    if not dest_dir.exists():
        logger.info("Creating output directory '%s'", dest_dir)
        dest_dir.mkdir()

    tagden_buf: bytes = _read_file(tagden_path)
    tagden_files: list[TagdenFile] = list(
        _identify_tagden_files(io.BytesIO(tagden_buf))
    )
    logger.info("Found %d files in '%s', extracting...", len(tagden_files), tagden_path)

    read_buf = io.BytesIO(tagden_buf)
    for tagden_file in tagden_files:
        _extract_tagden_file(read_buf, tagden_file, dest_dir)
    logger.info("All files extraced")


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
