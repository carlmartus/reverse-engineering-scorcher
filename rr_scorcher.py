import io
import sys
import logging
import numpy as np
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from PIL import Image
from typing import Iterable, Optional
from struct import unpack

_TAGDEN = "TAGDEN.BIN"
_ABSOLUTE_DEV_COMPUTER_PREFIX: PureWindowsPath = PureWindowsPath("l:\\scorpc\\game\\")
_EXT_R0V = ".r0v"

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
    tagden_file.output_path = put_path


@dataclass(frozen=True)
class R0vData:
    magic: str
    w: int
    h: int
    line_rl: list[Optional[int]]
    pixs_raw: bytes


def _r0v_extract_bits(num: int) -> list[int]:
    rs = [range(10, 15), range(5, 10), range(0, 5)]

    def ext(r):
        col = (num >> r.start) & ((1 << (r.stop - r.start)) - 1)
        return col * 8

    return [ext(r) for r in rs]


def _r0v_extract_pix(raw: bytes) -> list[int]:
    (num,) = unpack(">H", raw)
    assert isinstance(num, int)
    return _r0v_extract_bits(num)


def _r0v_filter_rl(rl: int):
    return None if rl == 0xFFFFFFFF else rl


def r0v_parse(path: Path) -> R0vData:
    fd = open(path, "rb")

    # File must start with identifier
    magic = fd.read(8).decode()
    assert magic == "PARGB15 "

    # Image dimensions
    w, h = unpack(">II", fd.read(8))

    # Vertical run lengths offsets
    line_rl = list(map(_r0v_filter_rl, [unpack(">I", fd.read(4))[0] for _ in range(h)]))

    # Pixels
    pixs_raw = fd.read()
    fd.close()
    return R0vData(magic, w, h, line_rl, pixs_raw)


def r0v_convert(rp: R0vData) -> np.ndarray:
    arr = np.zeros((rp.h, rp.w, 3), dtype=np.uint8)
    for y, y_rl in enumerate(rp.line_rl):
        if y_rl is None:
            continue
        byte_offset = y_rl * 2
        x_base, count = unpack(">2H", rp.pixs_raw[byte_offset : byte_offset + 4])
        byte_offset += 4
        terminate = False
        while not terminate:
            for x in range(x_base, x_base + count):
                arr[y][x][:] = _r0v_extract_pix(
                    rp.pixs_raw[byte_offset : byte_offset + 2]
                )
                byte_offset += 2
            (x_deriv,) = unpack(">H", rp.pixs_raw[byte_offset : byte_offset + 2])
            byte_offset += 2
            if x_deriv == 0:
                terminate = True
            else:
                x_base += x_deriv + count
                (count,) = unpack(">H", rp.pixs_raw[byte_offset : byte_offset + 2])
                byte_offset += 2
    return arr


def _r0v_to_image(tagden_file: TagdenFile) -> Image.Image:
    """Convert an "R0V" image into a PIL Image."""

    assert tagden_file.output_path is not None
    parse = r0v_parse(tagden_file.output_path)
    arr = r0v_convert(parse)
    return Image.fromarray(arr)


def _save_image(img: Image.Image, source: TagdenFile) -> None:
    """Save PIL image as PNG next to source image."""

    assert source.output_path is not None
    img.save(source.output_path.with_suffix(".png"))


def _filter_tagden_files_by_extension(
    tagden_files: Iterable[TagdenFile], ext: str
) -> Iterable[TagdenFile]:
    """Filter list of tagden files by extension."""

    def check(tagden_file: TagdenFile):
        return tagden_file.internal_path.suffix.lower() == ext

    return filter(check, tagden_files)


def _save_r0v_images(r0v_files: list[TagdenFile]) -> None:
    for r0v_file in r0v_files:
        logger.debug("Converting r0v image '%s'", r0v_file.output_path)
        image = _r0v_to_image(r0v_file)
        _save_image(image, r0v_file)


def extract_all(tagden_path: Path, dest_dir: Path) -> None:
    """Extract all files from a tagden file."""

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

    r0v_files = list(_filter_tagden_files_by_extension(tagden_files, _EXT_R0V))
    logger.info("Found %d r0v files, converting images to .png...", len(r0v_files))
    _save_r0v_images(r0v_files)

    logger.info("Extraction completed")


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
