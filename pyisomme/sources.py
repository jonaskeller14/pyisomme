from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import tarfile
from typing import Literal
import zipfile


def read_text_with_fallback(data: bytes) -> str:
    """
    Decode raw ISO-MME text bytes, trying UTF-8 first and falling back to ISO-8859-1.

    ISO-MME files in the wild use both encodings; ISO-8859-1 decodes any byte sequence,
    so it is the safe fallback. Centralized here so a decoding fix lands everywhere at once.
    """
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("iso-8859-1")


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

    def close(self) -> None:
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
