from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import tarfile
from typing import Literal
import zipfile


#: Single-byte codecs tried, in order, once UTF-8 has been ruled out.
#:
#: cp1252 comes first because the Windows tooling that writes most ISO-MME containers uses
#: it, and because it only *adds* printable characters to ISO-8859-1: the two agree on
#: 0xA0-0xFF and differ only on 0x80-0x9F, which ISO-8859-1 leaves as unused C1 control
#: codes. Decoding those as controls is never the intended reading, and one of them is
#: actively destructive — 0x85 becomes U+0085 NEL, which ``str.splitlines()`` treats as a
#: line terminator, so a single ``…`` in a header value would split that line in two and
#: silently truncate it (in a channel file, that ends the header and corrupts the data
#: section). ISO-8859-1 stays as the final fallback for the five bytes cp1252 leaves
#: undefined (0x81, 0x8D, 0x8F, 0x90, 0x9D); it decodes any byte sequence, so decoding
#: can never fail.
SINGLE_BYTE_CODECS = ("cp1252", "iso-8859-1")


def read_text_with_fallback(data: bytes) -> str:
    """
    Decode raw ISO-MME text bytes, guessing the encoding the writer used.

    ISO-MME files in the wild carry no encoding declaration, so the encoding has to be
    recovered from the bytes. The order below is from most to least self-evident: a byte
    order mark states the encoding outright, UTF-8 is self-validating (non-UTF-8 text
    almost never decodes as valid UTF-8), and only then do the single-byte guesses in
    :data:`SINGLE_BYTE_CODECS` apply. Centralized here so a decoding fix lands everywhere
    at once.
    """
    # 1. An explicit BOM. utf-8-sig also strips a UTF-8 BOM, which would otherwise survive
    #    as a U+FEFF glued to the first header key ("﻿Channel code"), making that key
    #    unfindable. UTF-16 must be detected here because its ASCII text is a run of
    #    NUL-interleaved bytes that decodes as *valid* UTF-8 — it would otherwise pass
    #    silently and yield garbage rather than raising.
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass

    for codec in SINGLE_BYTE_CODECS:
        try:
            return data.decode(codec)
        except UnicodeDecodeError:
            continue
    # Unreachable while iso-8859-1 is the last entry, but keep the contract explicit.
    return data.decode("iso-8859-1", errors="replace")


class ArchiveSource(ABC):
    """
    Read-only, flat namespace of member files backing an ISO-MME container.

    Abstracts the three storage backends (filesystem folder, zip, tar) behind a common
    ``names()`` / ``read_bytes()`` pair so the reader logic exists once. Member names are
    matched with :func:`fnmatch.filter`, which normalizes case and path separators, so the
    forward-slash names of archives and the OS-native names of folders behave the same.
    """

    @abstractmethod
    def names(self) -> list[str]:
        """Return every member file name (archive-relative, using ``/`` separators)."""

    @abstractmethod
    def read_bytes(self, name: str) -> bytes:
        """Return the raw bytes of one member."""

    def read_text(self, name: str) -> str:
        """Return one member decoded to text via :func:`read_text_with_fallback`."""
        return read_text_with_fallback(self.read_bytes(name))

    def close(self) -> None:  # noqa: B027 - deliberate no-op default, not every source holds a handle
        """Release any underlying handle. No-op by default."""

    def __enter__(self) -> ArchiveSource:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class FolderSource(ArchiveSource):
    """An ISO-MME container laid out as plain files under a directory root."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def names(self) -> list[str]:
        return [p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file()]

    def read_bytes(self, name: str) -> bytes:
        return (self.root / name).read_bytes()


class ZipSource(ArchiveSource):
    """An ISO-MME container stored inside a ``.zip`` archive."""

    def __init__(self, zip_path: str | Path):
        self.archive = zipfile.ZipFile(zip_path, "r")

    def names(self) -> list[str]:
        return self.archive.namelist()

    def read_bytes(self, name: str) -> bytes:
        with self.archive.open(name, "r") as member:
            return member.read()

    def close(self) -> None:
        self.archive.close()


class TarSource(ArchiveSource):
    """An ISO-MME container stored inside a ``.tar`` / ``.tar.gz`` archive."""

    def __init__(self, tar_path: str | Path, mode: Literal['r', 'r:*', 'r:', 'r:gz', 'r:bz2', 'r:xz'] = 'r'):
        self.tar = tarfile.open(tar_path, mode)

    def names(self) -> list[str]:
        return self.tar.getnames()

    def read_bytes(self, name: str) -> bytes:
        member = self.tar.extractfile(name)
        if member is None:
            raise FileNotFoundError(name)
        try:
            return member.read()
        finally:
            member.close()

    def close(self) -> None:
        self.tar.close()
