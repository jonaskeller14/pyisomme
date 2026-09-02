from __future__ import annotations

import copy
import fnmatch
import glob
import logging
import os
import re
import shutil
import tempfile
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from pyisomme.channel import Channel, create_sample
from pyisomme.code import Code
from pyisomme.errors import InvalidCodeError, ParsingChannelStatus
from pyisomme.info import Info, InfoInput, InfoValue
from pyisomme.parsing import (
    parse_chn,
    parse_mii,
    parse_mme,
    parse_pho,
    parse_sd1,
    parse_txt,
    parse_xxx,
)
from pyisomme.providers import PROVIDERS
from pyisomme.sources import ArchiveSource, FolderSource, TarSource, ZipSource
from pyisomme.utils import debug_logging

logger = logging.getLogger(__name__)


def _find_member(
    names: Iterable[str], path: PurePosixPath, description: str
) -> str | None:
    """Find one case-insensitive container member, warning about duplicates."""
    expected = path.as_posix().casefold()
    matches = [name for name in names if name.casefold() == expected]
    if len(matches) > 1:
        logger.warning(
            "Multiple %s found: %s. Only the first is used.", description, matches
        )
    return matches[0] if matches else None


class Isomme:
    test_number: str | None
    test_info: Info
    channels: list[Channel]
    channel_info: Info | None
    text_txt: str | None
    channel_txt: str | None
    diagram_txt: str | None
    movie_txt: str | None
    photo_txt: str | None
    report_txt: str | None
    static_txt: str | None
    movie_mii: Info | None
    photo_pho: Info | None
    static_sd1: Info | None

    def __init__(
        self,
        test_number: str | None = None,
        test_info: InfoInput | None = None,
        channels: list[Channel] | None = None,
        channel_info: InfoInput | None = None,
        text_txt: str | None = None,
        channel_txt: str | None = None,
        diagram_txt: str | None = None,
        movie_txt: str | None = None,
        photo_txt: str | None = None,
        report_txt: str | None = None,
        static_txt: str | None = None,
        movie_mii: InfoInput | None = None,
        photo_pho: InfoInput | None = None,
        static_sd1: InfoInput | None = None,
    ):
        """
        Create empty Isomme object.
        """
        self.test_number = test_number
        self.test_info = Info() if test_info is None else Info(test_info)
        self.channels = [] if channels is None else channels
        self.channel_info = None if channel_info is None else Info(channel_info)
        self.text_txt = text_txt
        self.channel_txt = channel_txt
        self.diagram_txt = diagram_txt
        self.movie_txt = movie_txt
        self.photo_txt = photo_txt
        self.report_txt = report_txt
        self.static_txt = static_txt
        self.movie_mii = None if movie_mii is None else Info(movie_mii)
        self.photo_pho = None if photo_pho is None else Info(photo_pho)
        self.static_sd1 = None if static_sd1 is None else Info(static_sd1)

    def get_test_info(self, *labels) -> InfoValue:
        """
        Get test info by giving one or multiple label(s) to identify information.
        Regex or fnmatch patterns possible.
        :param labels: key to find information in dict
        :return: first match or None
        """
        for label in labels:
            for name, value in self.test_info:
                if fnmatch.fnmatch(name, label):
                    return value
                try:
                    if re.match(label, name):
                        return value
                except re.error:
                    continue
        return None

    def get_channel_info(self, *labels) -> Any | None:
        """
        Get channel info by giving one or multiple label(s) to identify information.
        Regex or fnmmatch pattern possible.
        :param labels: key to find information in dict
        :return: first match or None
        """
        if self.channel_info is None:
            return None
        for label in labels:
            for key in self.channel_info.keys():
                if fnmatch.fnmatch(key, label):
                    return self.channel_info[key]
                try:
                    if re.match(label, key):
                        return self.channel_info[key]
                except re.error:
                    continue
        return None

    def read(self, path: str | Path, *channel_code_patterns) -> Isomme:
        """
        path must reference...
        - a .zip/.tar/.tar.gz which contains .mme-file
        - a folder which contains .mme-file
        - a .mme file
        - a .chn file
        - a .001/.002/.. file
        :param path:
        :return:
        """
        path = Path(path).absolute()
        suffixes = [suffix.lower() for suffix in path.suffixes]
        if not path.exists():
            raise FileNotFoundError(path)
        if path.is_dir():
            self.read_from_folder(path, *channel_code_patterns)
        elif path.suffix.lower() == ".mme":
            self.read_from_mme(path, *channel_code_patterns)
        elif suffixes[-2:] == [".tar", ".gz"]:
            self.read_from_tarfile(path, *channel_code_patterns, mode="r:gz")
        elif path.suffix.lower() == ".zip":
            self.read_from_zip(path, *channel_code_patterns)
        elif path.suffix.lower() == ".tar":
            self.read_from_tarfile(path, *channel_code_patterns, mode="r")
        elif path.suffix.lower() == ".chn":
            self.read_from_chn(path, *channel_code_patterns)
        elif re.fullmatch(r"\.\d+", path.suffix):
            self.read_from_xxx(path, *channel_code_patterns)
        else:
            raise NotImplementedError(f"Could not read path: {path}")
        logger.info(f"Reading '{path}' done. Number of channel: {len(self.channels)}")
        return self

    def _read_mme(
        self, source: ArchiveSource, mme_name: str | None
    ) -> tuple[str, Info, str]:
        if mme_name is None:
            mme_names = fnmatch.filter(source.names, "*.[mM][mM][eE]")
            if len(mme_names) == 0:
                raise FileNotFoundError("No .mme file found.")
            elif len(mme_names) > 1:
                raise Exception("Multiple .mme files found.")
            mme_name = mme_names[0]
        test_number = Path(mme_name).stem
        test_info = parse_mme(source.read_text(mme_name))
        return test_number, test_info, mme_name

    def _read_txt(self, source: ArchiveSource, path: PurePosixPath) -> str | None:
        member_name = _find_member(source.names, path, str(path))
        return None if member_name is None else parse_txt(source.read_text(member_name))

    def _read_mii(self, source: ArchiveSource, path: PurePosixPath) -> Info | None:
        member_name = _find_member(source.names, path, str(path))
        return None if member_name is None else parse_mii(source.read_text(member_name))

    def _read_pho(self, source: ArchiveSource, path: PurePosixPath) -> Info | None:
        member_name = _find_member(source.names, path, str(path))
        return None if member_name is None else parse_pho(source.read_text(member_name))

    def _read_sd1(self, source: ArchiveSource, path: PurePosixPath) -> Info | None:
        member_name = _find_member(source.names, path, str(path))
        return None if member_name is None else parse_sd1(source.read_text(member_name))

    def _read_chn(self, source: ArchiveSource, path: PurePosixPath) -> Info | None:
        chn_name = _find_member(source.names, path, "CHN file")
        return None if chn_name is None else parse_chn(source.read_text(chn_name))

    def _read_from_source(
        self, source: ArchiveSource, *channel_code_patterns, mme_name: str | None = None
    ) -> Isomme:
        """
        Read an ISO-MME container from any :class:`ArchiveSource` (folder/zip/tar).

        This is the single implementation behind ``read_from_mme``/``read_from_zip``/
        ``read_from_tarfile``; the thin wrappers only build the right source. Member names
        are matched with :func:`fnmatch.filter`, which normalizes case and path separators
        so ``str(Path(...).joinpath(...))`` patterns work identically across backends.
        :param source: backend the container is stored in
        :param channel_code_patterns: (optional) only read channels matching these patterns
        :param mme_name: known .mme member name (filesystem case); if ``None`` it is located
        """
        # MME
        self.test_number, self.test_info, mme_name = self._read_mme(source, mme_name)

        # TXT files
        test_root = PurePosixPath(mme_name).parent
        self.text_txt = self._read_txt(source, test_root / f"{self.test_number}.TXT")
        self.channel_txt = self._read_txt(source, test_root / "Channel/CHANNEL.TXT")
        self.diagram_txt = self._read_txt(source, test_root / "Diagram/DIAGRAM.TXT")
        self.movie_txt = self._read_txt(source, test_root / "Movie/MOVIE.TXT")
        self.photo_txt = self._read_txt(source, test_root / "Photo/PHOTO.TXT")
        self.report_txt = self._read_txt(source, test_root / "Report/REPORT.TXT")
        self.static_txt = self._read_txt(source, test_root / "Static/STATIC.TXT")

        # MII
        self.movie_mii = self._read_mii(
            source, test_root / f"Movie/{self.test_number}.MII"
        )

        # PHO
        self.photo_pho = self._read_pho(
            source, test_root / f"Photo/{self.test_number}.PHO"
        )

        # SD1
        self.static_sd1 = self._read_sd1(
            source, test_root / f"Static/{self.test_number}.SD1"
        )

        # CHN
        self.channel_info = self._read_chn(
            source, test_root / f"Channel/{self.test_number}.CHN"
        )

        # 001
        if self.channel_info is None:
            self.channels = []
        else:
            self.channels = self._read_channels(
                source, test_root / "Channel", channel_code_patterns
            )
        return self

    def _read_channels(
        self,
        source: ArchiveSource,
        channel_directory: PurePosixPath,
        channel_code_patterns: tuple[str, ...],
    ) -> list[Channel]:
        """Read the channels referenced by the current CHN metadata."""
        assert self.channel_info is not None
        xxx_names: list[str] = []
        channel_keys = fnmatch.filter(self.channel_info.keys(), "Name of channel *")
        for key in channel_keys:
            channel_reference = self.channel_info[key]
            if not isinstance(channel_reference, str):
                raise ValueError(
                    f"Invalid channel reference in CHN data for {key!r}: "
                    f"expected a string, got {channel_reference!r}"
                )
            code = channel_reference.split()[0].split("/")[0]
            if len(channel_code_patterns) != 0:
                skip = True
                for channel_code_pattern in channel_code_patterns:
                    if fnmatch.fnmatch(code, channel_code_pattern):
                        skip = False
                        break
                if skip:
                    continue

            channel_number_match = re.search(r"Name of channel (\d*)", key)
            if channel_number_match is None:
                raise ValueError(f"Invalid channel number in CHN data: {key}")
            channel_number = channel_number_match.groups()[0]
            xxx_name = _find_member(
                source.names,
                channel_directory / f"{self.test_number}.{channel_number}",
                f"channel file {self.test_number}.{channel_number}",
            )
            if xxx_name is None:
                logger.critical(
                    f"Channel file '{self.test_number}.{channel_number}' not found."
                )
                continue
            xxx_names.append(xxx_name)

        parsed_channels: list[tuple[Channel, ParsingChannelStatus]] = []
        with logging_redirect_tqdm():
            with tqdm(
                total=len(xxx_names), desc=f"Read Channel of {self.test_number}"
            ) as pbar:
                for xxx_name in xxx_names:
                    logger.debug(xxx_name)
                    channel, parse_status = parse_xxx(source.read_text(xxx_name))
                    parsed_channels.append((channel, parse_status))
                    if parse_status == ParsingChannelStatus.OK:
                        pbar.update(1)

                channels = [channel for channel, _ in parsed_channels]
                for pending_channel, parse_status in parsed_channels:
                    if parse_status == ParsingChannelStatus.OK:
                        continue
                    reference_channel_code_value = pending_channel.info.get(
                        "Reference channel name"
                    )
                    reference_channel_code = (
                        reference_channel_code_value
                        if isinstance(reference_channel_code_value, str)
                        else None
                    )
                    if reference_channel_code is None:
                        logger.error(
                            f"[{pending_channel.code}] 'Reference channel name' is missing or invalid -> using sample index"
                        )
                        continue
                    reference_channel = next(
                        (
                            channel
                            for channel in channels
                            if str(channel.code) == reference_channel_code
                        ),
                        None,
                    )
                    if reference_channel is None:
                        logger.error(
                            f"[{pending_channel.code}] 'Reference channel name' mentioned Channel {reference_channel_code} is missing -> using sample index"
                        )
                        continue
                    reference_data = reference_channel.get_data()
                    if len(reference_data) != len(pending_channel.data):
                        logger.error(
                            f"[{pending_channel.code}] Reference channel {reference_channel_code} has "
                            f"{len(reference_data)} samples, expected {len(pending_channel.data)} "
                            "-> using sample index"
                        )
                        continue
                    pending_channel.data.index = reference_data
                    pending_channel.data = pending_channel.data[
                        ~pending_channel.data.index.duplicated(keep="first")
                    ].sort_index()
                    pbar.update(1)
        return channels

    def read_from_mme(self, mme_path: Path, *channel_code_patterns) -> Isomme:
        mme_path = Path(mme_path)
        return self._read_from_source(
            FolderSource(mme_path.parent),
            *channel_code_patterns,
            mme_name=mme_path.name,
        )

    def read_from_folder(self, folder_path: Path, *channel_code_patterns) -> Isomme:
        mme_paths = list(folder_path.rglob("*.[mM][mM][eE]"))
        if len(mme_paths) == 0:
            raise FileNotFoundError("Folder not containing any .mme/.MME file.")
        elif len(mme_paths) > 1:
            raise Exception(
                "Multiple .mme files found inside of the folder. Please specify the .mme-file path."
            )
        return self.read_from_mme(mme_paths[0], *channel_code_patterns)

    def read_from_chn(self, chn_path: Path, *channel_code_patterns) -> Isomme:
        mme_paths = list(chn_path.parent.parent.glob("*.[mM][mM][eE]"))
        if len(mme_paths) == 0:
            raise FileNotFoundError("Parent Folder not containing any .mme file.")
        return self.read_from_mme(mme_paths[0], *channel_code_patterns)

    def read_from_xxx(self, xxx_path: Path, *channel_code_patterns) -> Isomme:
        mme_paths = list(xxx_path.parent.parent.glob("*.[mM][mM][eE]"))
        if len(mme_paths) == 0:
            raise FileNotFoundError("Parent Folder not containing any .mme file.")
        return self.read_from_mme(mme_paths[0], *channel_code_patterns)

    def read_from_zip(self, zip_path: Path, *channel_code_patterns) -> Isomme:
        with ZipSource(zip_path) as source:
            return self._read_from_source(source, *channel_code_patterns)

    def read_from_tarfile(
        self,
        tar_path: Path,
        *channel_code_patterns,
        mode: Literal["r", "r:*", "r:", "r:gz", "r:bz2", "r:xz"] = "r",
    ) -> Isomme:
        with TarSource(tar_path, mode) as source:
            return self._read_from_source(source, *channel_code_patterns)

    def _write_mme(
        self,
        path: Path,
        *channel_code_patterns,
        max_workers: int | None = None,
    ) -> list[Path]:
        channels = (
            self.get_channels(*channel_code_patterns)
            if len(channel_code_patterns) != 0
            else self.channels
        )

        if path.stem != self.test_number:
            logger.warning(
                "Test number does not match file stem. Not compliant with convention."
            )

        os.makedirs(path.parent, exist_ok=True)

        # MME
        self._write_mme_file(path)

        channel_info = self._channel_info_for_write(channels)

        written_paths = [
            # TXT files
            self._write_txt(path.parent / f"{path.stem}.txt", self.text_txt),
            self._write_txt(path.parent / "Channel/CHANNEL.TXT", self.channel_txt),
            self._write_txt(path.parent / "Diagram/DIAGRAM.TXT", self.diagram_txt),
            self._write_txt(path.parent / "Movie/MOVIE.TXT", self.movie_txt),
            self._write_txt(path.parent / "Photo/PHOTO.TXT", self.photo_txt),
            self._write_txt(path.parent / "Report/REPORT.TXT", self.report_txt),
            self._write_txt(path.parent / "Static/STATIC.TXT", self.static_txt),
            # MII
            self._write_mii(path.parent / f"Movie/{path.stem}.mii"),
            # PHO
            self._write_pho(path.parent / f"Photo/{path.stem}.pho"),
            # SD1
            self._write_sd1(path.parent / f"Static/{path.stem}.sd1"),
            # CHN
            self._write_chn(path.parent / f"Channel/{path.stem}.chn", channel_info),
        ]

        # 001
        self._write_channels(path.parent / "Channel", path.stem, channels, max_workers)

        relative_paths = [
            written_path.relative_to(path.parent)
            for written_path in written_paths
            if written_path is not None
        ]
        return relative_paths

    def _write_mme_file(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as mme_file:
            self.test_info.write(mme_file)

    @staticmethod
    def _write_txt(path: Path, text: str | None) -> Path | None:
        if text is None:
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
        # Comment files are opaque strings, so preserve their line endings instead of
        # applying the platform text-mode newline conversion.
        with open(path, "w", encoding="utf-8", newline="") as text_file:
            text_file.write(text)
        return path

    @staticmethod
    def _write_info_file(path: Path, info: Info | None) -> Path | None:
        if info is None:
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as info_file:
            info.write(info_file)
        return path

    def _write_mii(self, path: Path) -> Path | None:
        return self._write_info_file(path, self.movie_mii)

    def _write_pho(self, path: Path) -> Path | None:
        return self._write_info_file(path, self.photo_pho)

    def _write_sd1(self, path: Path) -> Path | None:
        return self._write_info_file(path, self.static_sd1)

    def _channel_info_for_write(self, channels: list[Channel]) -> Info | None:
        if self.channel_info is None and not channels:
            return None

        channel_info = (
            Info() if self.channel_info is None else copy.deepcopy(self.channel_info)
        )
        for info in channel_info[:]:
            name, _ = info
            if "Name of channel" in name:
                channel_info.remove(info)
        channel_info.update({"Number of channels": len(channels)})
        for channel_idx, channel in enumerate(channels, 1):
            channel_info[f"Name of channel {channel_idx:03}"] = channel.code + (
                f" / {channel.get_info('Name of the channel')}"
                if channel.get_info("Name of the channel") is not None
                else ""
            )
        return channel_info

    def _write_chn(self, path: Path, channel_info: Info | None) -> Path | None:
        if channel_info is None:
            return None
        path.parent.mkdir(exist_ok=True)
        with open(path, "w", encoding="utf-8") as chn_file:
            channel_info.write(chn_file)
        return path

    def _write_channels(
        self,
        channel_directory: Path,
        test_number: str,
        channels: list[Channel],
        max_workers: int | None,
    ) -> None:
        """Write the numbered channel data files."""
        channel_writes: list[tuple[Channel, Path]] = []
        for channel_idx, channel in enumerate(channels, 1):
            channel_writes.append(
                (
                    channel,
                    channel_directory / f"{test_number}.{channel_idx:03}",
                )
            )

        if not channel_writes:
            return

        # Each channel has its own output file, so these writes can safely overlap.
        with logging_redirect_tqdm():
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(channel.write, channel_path)
                    for channel, channel_path in channel_writes
                ]
                for future in tqdm(
                    as_completed(futures),
                    desc=f"Write Channel of {self.test_number}",
                    total=len(futures),
                ):
                    future.result()

    def _write_folder(
        self,
        path: Path,
        *channel_code_patterns,
        max_workers: int | None = None,
    ) -> None:
        self._write_mme(
            path.joinpath(f"{self.test_number}.mme"),
            *channel_code_patterns,
            max_workers=max_workers,
        )

    @staticmethod
    def _backup_path(parent: Path) -> Path:
        """Reserve an unused sibling path for a rollback copy."""
        backup_path = Path(tempfile.mkdtemp(prefix=".pyisomme-backup-", dir=parent))
        backup_path.rmdir()
        return backup_path

    @staticmethod
    def _remove_path(path: Path) -> None:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

    def _replace_outputs_transactionally(
        self, replacements: list[tuple[Path, Path]]
    ) -> None:
        """Replace output paths together, restoring previous outputs on failure."""
        backups: dict[Path, Path] = {}
        placed: list[tuple[Path, Path]] = []
        try:
            for destination, _ in replacements:
                if destination.exists():
                    backup_path = self._backup_path(destination.parent)
                    os.replace(destination, backup_path)
                    backups[destination] = backup_path

            for destination, source in replacements:
                os.replace(source, destination)
                placed.append((destination, source))
        except Exception:
            for destination, source in reversed(placed):
                os.replace(destination, source)
            for destination, backup_path in backups.items():
                os.replace(backup_path, destination)
            raise
        else:
            for backup_path in backups.values():
                self._remove_path(backup_path)

    def _write_mme_transactionally(
        self,
        path: Path,
        *channel_code_patterns,
        max_workers: int | None = None,
    ) -> None:
        """Write an MME container and its present companion files transactionally."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=path.parent) as temporary_directory:
            temporary_path = Path(temporary_directory)
            temporary_mme_path = temporary_path / path.name
            written_paths = self._write_mme(
                temporary_mme_path,
                *channel_code_patterns,
                max_workers=max_workers,
            )
            replacements = [(path, temporary_mme_path)]
            temporary_channel_directory = temporary_path / "Channel"
            if temporary_channel_directory.exists():
                replacements.append(
                    (path.parent / "Channel", temporary_channel_directory)
                )
            # Channel is exchanged as a whole above.  Replacing other files
            # individually avoids deleting media beside their MII/PHO metadata.
            for relative_path in written_paths:
                if relative_path.parts[0].casefold() != "channel":
                    destination = path.parent / relative_path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    replacements.append((destination, temporary_path / relative_path))
            self._replace_outputs_transactionally(replacements)

    def _write_folder_transactionally(
        self,
        path: Path,
        *channel_code_patterns,
        max_workers: int | None = None,
    ) -> None:
        """Write a folder container without replacing its prior contents on failure."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=path.parent) as temporary_directory:
            temporary_path = Path(temporary_directory) / "isomme"
            self._write_folder(
                temporary_path,
                *channel_code_patterns,
                max_workers=max_workers,
            )
            self._replace_outputs_transactionally([(path, temporary_path)])

    def _write_archive(
        self,
        path: Path,
        archive_format: Literal["zip", "tar", "gztar"],
        *channel_code_patterns,
        max_workers: int | None = None,
    ) -> None:
        """Write an archive without touching sibling directories or partial output."""
        path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(dir=path.parent) as temporary_directory:
            temporary_path = Path(temporary_directory)
            folder_path = temporary_path / "isomme"
            self._write_folder(
                folder_path,
                *channel_code_patterns,
                max_workers=max_workers,
            )
            archive_path = Path(
                shutil.make_archive(
                    str(temporary_path / "archive"),
                    archive_format,
                    root_dir=folder_path,
                    logger=logger if archive_format == "zip" else None,
                )
            )
            os.replace(archive_path, path)

    def write(
        self,
        path: str | Path,
        *channel_code_patterns,
        max_workers: int | None = None,
    ) -> Isomme:
        """
        Write ISO-MME data to a file, folder, or archive.
        :param path: output path where to save the ISO-MME data (.mme, folder, .zip, .tar, or .tar.gz)
        :param channel_code_patterns: (optional) only export specific channels identified by code-pattern
        :param max_workers: maximum number of channel-writer threads; ``None`` uses
            :class:`ThreadPoolExecutor`'s default and ``1`` disables concurrency
        :return:
        """
        path = Path(path)
        if path.suffix.lower() == ".mme":
            self._write_mme_transactionally(
                path, *channel_code_patterns, max_workers=max_workers
            )
        elif path.suffix == "":
            self._write_folder_transactionally(
                path, *channel_code_patterns, max_workers=max_workers
            )
        elif path.suffix.lower() == ".zip":
            self._write_archive(
                path, "zip", *channel_code_patterns, max_workers=max_workers
            )
        elif path.suffix.lower() == ".tar":
            self._write_archive(
                path, "tar", *channel_code_patterns, max_workers=max_workers
            )
        elif (
            len(path.suffixes) >= 2
            and path.suffixes[-1].lower() == ".gz"
            and path.suffixes[-2].lower() == ".tar"
        ):
            self._write_archive(
                path, "gztar", *channel_code_patterns, max_workers=max_workers
            )
        else:
            raise NotImplementedError(
                f"{path.suffix} is not supported. Only .mme/folder/.zip/.tar/.tar.gz are supported."
            )
        return self

    def extend(self, *others) -> Isomme:
        """
        Extend channel list with channels of other Isomme-object, with a single Channel-object or a list/tuple of
        Channel-objects.
        Test- and Channel-Info of other Isomme-object will be ignored.
        :param others: Isomme-Object or Channel-object or list/tuple of Channel-objects
        :return: self
        """
        for other in others:
            if isinstance(other, Isomme):
                self.channels += other.channels
            elif isinstance(other, Channel):
                self.channels.append(other)
            elif isinstance(other, (list, tuple)):
                for other_item in other:
                    self.extend(other_item)
            else:
                raise NotImplementedError(
                    f"Could not extend Isomme with type {type(other)}"
                )
        return self

    def delete_duplicates(self, filter_class_duplicates: bool = False) -> Isomme:
        """
        Delete channel duplicates (same channel code). The last added one will be deleted first.
        :param filter_class_duplicates: Delete redundant channels and only keep channels with the least amount of filtering applied
        :return: self
        """
        for code in {channel.code for channel in self.channels}:
            channels = self.get_channels(
                code,
                calculate=False,
                filter=False,
                differentiate=False,
                integrate=False,
            )
            for channel in channels[1:]:
                self.channels.remove(channel)
                logger.debug(f"Removed duplicate Channel: {channel.code}")

        if filter_class_duplicates:
            for code in {channel.code for channel in self.channels}:
                channels = self.get_channels(
                    code[:-1].replace("?", "[?]") + "?",
                    calculate=False,
                    filter=False,
                    differentiate=False,
                    integrate=False,
                )
                sort_seq = "0XAEPBF2CG3DHQLVS"
                sort_map = {
                    filter_class: sort_seq.index(filter_class)
                    for filter_class in sort_seq
                }
                for channel in sorted(
                    channels,
                    key=lambda c: sort_map.get(c.code.filter_class, float("inf")),
                )[1:]:
                    self.channels.remove(channel)
                    logger.debug(f"Removed duplicate filter Channel: {channel.code}")
        return self

    def __repr__(self) -> str:
        return f"Isomme({self.test_number or 'Unnamed'})"

    def __str__(self) -> str:
        return self.test_number or "Unnamed ISOMME"

    def __len__(self) -> int:
        return len(self.channels)

    def __getitem__(self, index: int | slice | str) -> Channel | list[Channel]:
        """Index into the container.

        - ``iso[0]`` -> the Channel at that position
        - ``iso[0:3]`` -> a list of Channels
        - ``iso["11HEAD??????ACXP"]`` -> shorthand for ``get_channels(pattern)`` (a list)

        Note the key type decides the return type: an ``int`` yields a single Channel while
        a ``str`` pattern yields a *list*. When you want exactly one match, prefer
        ``get_channel(pattern)``; for a list, ``get_channels(pattern)`` or this shorthand.
        """
        if isinstance(index, str):
            return self.get_channels(index)
        if isinstance(index, (int, slice)):
            return self.channels[index]
        raise TypeError(
            f"Isomme indices must be int, slice or str, not {type(index).__name__}"
        )

    def __contains__(self, item) -> bool:
        return item in self.channels

    def __iter__(self):
        yield from self.channels

    @debug_logging(logger)
    def get_channel(
        self,
        *code_patterns: str,
        filter: bool = True,
        calculate: bool = True,
        differentiate: bool = True,
        integrate: bool = True,
    ) -> Channel | None:
        """
        Get channel by channel code pattern.
        First match will be returned, although multiple matches could exist.
        If channel does not exist, it will be created through filtering and calculations if possible.
        :param code_patterns:
        :param filter: create channel by filtering if channel does not exist yet
        :param calculate: create channel by calculation if channel does not exist yet
        :param differentiate: Allow differentiation if channel not found otherwise
        :param integrate: Allow integration if channel not found otherwise
        :return: Channel object or None
        """
        for code_pattern in code_patterns:
            # 1. Channel does exist already
            for channel in self.channels:
                if fnmatch.fnmatch(channel.code, code_pattern):
                    return channel

            try:
                code = Code(code_pattern)
            except InvalidCodeError:
                continue

            # 2. Filter Channel
            if filter and code.is_filterable():
                source_pattern = code.set(filter_class="?")
                for channel in self.channels:
                    if fnmatch.fnmatch(channel.code, source_pattern):
                        filtered_channel = channel.cfc(code.filter_class)
                        if fnmatch.fnmatch(filtered_channel.code, code_pattern):
                            return filtered_channel

            # 3. Calculate Channel
            if calculate:
                for provider in PROVIDERS:
                    if provider.matches(code):
                        built_channel = provider.build(self, code)
                        if built_channel is not None:
                            return built_channel

            # 4. Differentiate
            if differentiate:
                try:
                    code_integrated = code.integrate()
                except NotImplementedError as error:
                    logger.debug(error)
                else:
                    channel_int = self.get_channel(
                        code_integrated,
                        filter=filter,
                        calculate=calculate,
                        integrate=False,
                    )
                    if channel_int is not None:
                        try:
                            differentiated_channel = channel_int.differentiate()
                            if fnmatch.fnmatch(
                                differentiated_channel.code, code_pattern
                            ):
                                return differentiated_channel
                        except (AttributeError, NotImplementedError) as error:
                            logger.debug(error)

            # 5. Integrate
            if integrate:
                try:
                    code_differentiated = code.differentiate()
                except NotImplementedError as error:
                    logger.debug(error)
                else:
                    channel_dif = self.get_channel(
                        code_differentiated,
                        filter=filter,
                        calculate=calculate,
                        differentiate=False,
                    )
                    if channel_dif is not None:
                        try:
                            integrated_channel = channel_dif.integrate()
                            if fnmatch.fnmatch(integrated_channel.code, code_pattern):
                                return integrated_channel
                        except (AttributeError, NotImplementedError) as error:
                            logger.debug(error)

            logger.info(f"No channel found for pattern: '{code_pattern}'")
        return None

    @debug_logging(logger)
    def get_channels(
        self,
        *code_patterns: str,
        filter: bool = True,
        calculate: bool = True,
        differentiate: bool = False,
        integrate: bool = False,
    ) -> list[Channel]:
        """
        Get all channels by channel code pattern. All wildcards are supported.
        A list of all matching channels will be returned.
        :param code_patterns:
        :param filter:
        :param calculate:
        :param differentiate:
        :param integrate:
        :return: list of Channels
        """
        channel_list: list[Channel] = []
        for code_pattern in code_patterns:
            # 1. Channel does exist already
            for channel in self.channels:
                if (
                    fnmatch.fnmatch(channel.code, code_pattern)
                    and channel not in channel_list
                ):
                    channel_list.append(channel)

            try:
                code = Code(code_pattern)
            except InvalidCodeError:
                continue

            # 2. Filter Channel
            if filter and code.is_filterable():
                source_pattern = code.set(filter_class="?")
                for channel in self.channels:
                    if channel in channel_list:
                        continue
                    if fnmatch.fnmatch(channel.code, source_pattern):
                        filtered_channel = channel.cfc(code.filter_class)
                        if fnmatch.fnmatch(
                            filtered_channel.code, code_pattern
                        ) and filtered_channel.code not in [
                            result.code for result in channel_list
                        ]:
                            channel_list.append(filtered_channel)

            # 3. Calculate Channel
            if calculate:
                calculated_channel = self.get_channel(
                    code,
                    filter=filter,
                    calculate=calculate,
                    differentiate=differentiate,
                    integrate=integrate,
                )
                if (
                    calculated_channel is not None
                    and calculated_channel not in channel_list
                    and calculated_channel.code
                    not in [result.code for result in channel_list]
                ):
                    channel_list.append(calculated_channel)

            # 4. Differentiate
            if differentiate:
                try:
                    for channel in self.get_channels(
                        code.integrate(),
                        filter=filter,
                        calculate=calculate,
                        integrate=False,
                    ):
                        differentiated_channel = channel.differentiate()
                        if fnmatch.fnmatch(
                            differentiated_channel.code, code_pattern
                        ) and differentiated_channel.code not in [
                            result.code for result in channel_list
                        ]:
                            channel_list.append(differentiated_channel)
                except (AttributeError, NotImplementedError) as error:
                    logger.debug(error)

            # 5. Integrate
            if integrate:
                try:
                    for channel in self.get_channels(
                        code.differentiate(),
                        filter=filter,
                        calculate=calculate,
                        differentiate=False,
                    ):
                        integrated_channel = channel.integrate()
                        if fnmatch.fnmatch(
                            integrated_channel.code, code_pattern
                        ) and integrated_channel.code not in [
                            result.code for result in channel_list
                        ]:
                            channel_list.append(integrated_channel)
                except (AttributeError, NotImplementedError) as error:
                    logger.debug(error)
        return channel_list

    def add_sample_channel(self, *args, **kwargs) -> Isomme:
        self.channels.append(create_sample(*args, **kwargs))
        return self

    def print_channel_list(self) -> None:
        """
        Print all channel codes to console.
        :return: None
        """
        print(f"{self.test_number} - Channel List:")
        for idx, channel in enumerate(self.channels):
            print(f"\t{(idx + 1):03}\t{channel.code}")

    def set_code(self, *args, **kwargs) -> Isomme:
        for channel in self.channels:
            channel.set_code(*args, **kwargs)
        return self

    def cfc(self, *args, **kwargs) -> Isomme:
        kwargs.pop("return_copy", None)
        for channel in self.channels:
            channel.cfc(*args, **kwargs, return_copy=False)  # type: ignore[misc]
        return self

    def scale_y(self, *args, **kwargs) -> Isomme:
        for channel in self.channels:
            channel.scale_y(*args, **kwargs)
        return self

    def scale_x(self, *args, **kwargs) -> Isomme:
        for channel in self.channels:
            channel.scale_x(*args, **kwargs)
        return self

    def offset_y(self, *args, **kwargs) -> Isomme:
        for channel in self.channels:
            channel.offset_y(*args, **kwargs)
        return self

    def auto_offset_y(self, *args, **kwargs) -> Isomme:
        for channel in self.channels:
            channel.auto_offset_y(*args, **kwargs)
        return self

    def offset_x(self, *args, **kwargs) -> Isomme:
        for channel in self.channels:
            channel.offset_x(*args, **kwargs)
        return self

    def crop(self, *args, **kwargs) -> Isomme:
        for channel in self.channels:
            channel.crop(*args, **kwargs)
        return self


def read(
    *paths,
    channel_code_patterns: list[str] | None = None,
    recursive: bool = True,
    merge: bool = True,
    max_workers: int | None = None,
) -> list[Isomme]:
    """Read independent ISO-MME containers concurrently.

    ``max_workers=None`` uses :class:`ThreadPoolExecutor`'s default. Pass ``1``
    for sequential execution. Results retain the order in which the input paths
    were discovered, even when worker threads finish in a different order.
    """
    all_paths: list[str] = []
    for path in paths:
        all_paths += glob.glob(os.fspath(path), recursive=recursive)
    unique_paths = list(dict.fromkeys(all_paths))

    channel_code_patterns = (
        [] if channel_code_patterns is None else channel_code_patterns
    )

    ordered_results: list[Isomme | None] = [None] * len(unique_paths)
    with logging_redirect_tqdm():
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_indices = {
                executor.submit(Isomme().read, path, *channel_code_patterns): path_index
                for path_index, path in enumerate(unique_paths)
            }
            for future in tqdm(
                as_completed(future_indices),
                desc="Reading",
                total=len(future_indices),
            ):
                try:
                    ordered_results[future_indices[future]] = future.result()
                except Exception as error:
                    logger.critical(error)

    iso_list = [isomme for isomme in ordered_results if isomme is not None]

    if merge:
        iso_list = merge_duplicate_isommes(iso_list)
        for isomme in iso_list:
            isomme.delete_duplicates(filter_class_duplicates=True)
    return iso_list


def merge_duplicate_isommes(isommes: Iterable[Isomme]) -> list[Isomme]:
    isommes_dict: dict[str | None, Isomme] = {}
    for isomme in isommes:
        if isomme.test_number in isommes_dict:
            isommes_dict[isomme.test_number].extend(isomme)
        else:
            isommes_dict[isomme.test_number] = isomme
    return list(isommes_dict.values())
