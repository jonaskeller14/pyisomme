from __future__ import annotations

from pyisomme.parsing import parse_mme, parse_chn, parse_xxx
from pyisomme.channel import create_sample, Channel
from pyisomme.code import Code
from pyisomme.errors import InvalidCodeError
from pyisomme.sources import ArchiveSource, FolderSource, ZipSource, TarSource
from pyisomme.providers import PROVIDERS
from pyisomme.utils import debug_logging
from pyisomme.info import Info

from collections.abc import Iterable
from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
from typing import Literal
import os
import glob
import re
import copy
from pathlib import Path
import fnmatch
import logging
import shutil


logger = logging.getLogger(__name__)


class Isomme:
    test_number: str | None
    test_info: Info
    channels: list[Channel]
    channel_info: Info

    def __init__(
        self,
        test_number: str | None = None,
        test_info: list | None = None,
        channels: list[Channel] | None = None,
        channel_info: list | None = None,
    ):
        """
        Create empty Isomme object.
        """
        self.test_number = test_number
        self.test_info = Info([]) if test_info is None else Info(test_info)
        self.channels = [] if channels is None else channels
        self.channel_info = Info([]) if channel_info is None else Info(channel_info)

    def get_test_info(self, *labels) -> str | None:
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

    def get_channel_info(self, *labels) -> str | None:
        """
        Get channel info by giving one or multiple label(s) to identify information.
        Regex or fnmmatch pattern possible.
        :param labels: key to find information in dict
        :return: first match or None
        """
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

        if not path.exists():
            raise FileNotFoundError(path)
        elif path.suffix.lower() == ".mme":
            self.read_from_mme(path, *channel_code_patterns)
        elif path.suffix == "":
            self.read_from_folder(path, *channel_code_patterns)
        elif path.suffix.lower() == ".zip":
            self.read_from_zip(path, *channel_code_patterns)
        elif path.suffix.lower() == ".chn":
            self.read_from_chn(path, *channel_code_patterns)
        elif re.fullmatch(r"\.\d+", path.suffix):
            self.read_from_xxx(path, *channel_code_patterns)
        elif path.suffix.lower() == ".tar":
            self.read_from_tarfile(path, *channel_code_patterns, mode="r")
        elif (
            len(path.suffixes) >= 2
            and path.suffixes[-1].lower() == ".gz"
            and path.suffixes[-2].lower() == ".tar"
        ):
            self.read_from_tarfile(path, *channel_code_patterns, mode="r:gz")
        else:
            raise NotImplementedError(f"Could not read path: {path}")
        logger.info(f"Reading '{path}' done. Number of channel: {len(self.channels)}")
        return self

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
        names = source.names()

        # MME
        if mme_name is None:
            mme_names = fnmatch.filter(names, "*.[mM][mM][eE]")
            if len(mme_names) == 0:
                raise FileNotFoundError("No .mme file found.")
            elif len(mme_names) > 1:
                raise Exception("Multiple .mme files found.")
            mme_name = mme_names[0]
        self.test_number = Path(mme_name).stem
        self.test_info = parse_mme(source.read_text(mme_name))

        # CHN
        chn_pattern = str(
            Path(mme_name).parent.joinpath(
                "[cC][hH][aA][nN][nN][eE][lL]*", f"{self.test_number}.[cC][hH][nN]"
            )
        )
        chn_names = fnmatch.filter(names, chn_pattern)
        if len(chn_names) == 0:
            raise FileNotFoundError("No .chn file found.")
        elif len(chn_names) > 1:
            logger.warning(
                f"Multiple .chn file found. {chn_names}. Only first will be considered."
            )

        chn_name = chn_names[0]
        self.channel_info = parse_chn(source.read_text(chn_name))

        # 001
        self.channels = []  # in case channel exist trough constructor, use extend()
        with logging_redirect_tqdm():
            for key in tqdm(
                fnmatch.filter(self.channel_info.keys(), "Name of channel *"),
                desc=f"Read Channel of {self.test_number}",
            ):
                code = self.channel_info[key].split()[0].split("/")[0]
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
                xxx_pattern = str(
                    Path(chn_name).parent.joinpath(
                        f"{self.test_number}.{channel_number}"
                    )
                )
                xxx_names = fnmatch.filter(names, xxx_pattern)
                if len(xxx_names) == 0:
                    logger.critical(
                        f"Channel file '{self.test_number}.{channel_number}' not found."
                    )
                    continue

                xxx_name = xxx_names[0]
                logger.debug(xxx_name)
                self.channels.append(parse_xxx(source.read_text(xxx_name), isomme=self))
        return self

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

    def write_mme(self, path: str | Path, *channel_code_patterns) -> Isomme:
        channels = (
            self.get_channels(*channel_code_patterns)
            if len(channel_code_patterns) != 0
            else self.channels
        )
        path = Path(path)

        if path.stem != self.test_number:
            logger.warning(
                "Test number does not match file stem. Not compliant with convention."
            )

        os.makedirs(path.parent, exist_ok=True)

        # MME
        with open(path, "w") as mme_file:
            self.test_info.write(mme_file)

        # Channel-Folder
        os.makedirs(path.parent.joinpath("Channel"), exist_ok=True)

        # Update Channel Info
        channel_info = copy.deepcopy(self.channel_info)
        for info in channel_info[:]:
            name, value = info
            if "Name of channel" in name:
                channel_info.remove(info)
        channel_info.update({"Number of channels": len(channels)})

        # 001 - iterate over channels
        with logging_redirect_tqdm():
            for channel_idx, channel in tqdm(
                enumerate(channels, 1),
                desc=f"Write Channel of {self.test_number}",
                total=len(channels),
            ):
                channel_info[f"Name of channel {channel_idx:03}"] = channel.code + (
                    f" / {channel.get_info('Name of the channel')}"
                    if channel.get_info("Name of the channel") is not None
                    else ""
                )
                channel.write(
                    path.parent.joinpath("Channel", f"{path.stem}.{channel_idx:03}")
                )

        # CHN
        with open(path.parent.joinpath("Channel", f"{path.stem}.chn"), "w") as chn_file:
            channel_info.write(chn_file)
        return self

    def write_folder(self, path: str | Path, *channel_code_patterns) -> Isomme:
        path = Path(path)
        self.write_mme(path.joinpath(f"{self.test_number}.mme"), *channel_code_patterns)
        return self

    def write_zip(self, path: str | Path, *channel_code_patterns) -> Isomme:
        path = Path(path)
        folder_path = path.parent.joinpath(path.stem)
        self.write_folder(folder_path, *channel_code_patterns)
        shutil.make_archive(str(folder_path), "zip", str(folder_path), logger=logger)
        shutil.rmtree(folder_path)
        return self

    def write_tar(self, path: str | Path, *channel_code_patterns) -> Isomme:
        path = Path(path)
        folder_path = path.parent.joinpath(path.stem)
        self.write(folder_path, *channel_code_patterns)
        shutil.make_archive(str(folder_path), "tar", folder_path)
        shutil.rmtree(folder_path)
        return self

    def write_tar_gz(self, path: str | Path, *channel_code_patterns) -> Isomme:
        path = Path(path)
        folder_path = str(path).removesuffix(".tar.gz")
        self.write(folder_path, *channel_code_patterns)
        shutil.make_archive(folder_path, "gztar", folder_path)
        shutil.rmtree(folder_path)
        return self

    def write(self, path: str | Path, *channel_code_patterns) -> Isomme:
        """
        Write ISO-MME data to files.
        :param path: output path where to save the ISO-MME data (.mme, folder or .zip)
        :param channel_code_patterns: (optional) only export specific channels identified by code-pattern
        :return:
        """
        path = Path(path)
        if path.suffix.lower() == ".mme":
            return self.write_mme(path, *channel_code_patterns)
        elif path.suffix == "":
            return self.write_folder(path, *channel_code_patterns)
        elif path.suffix.lower() == ".zip":
            return self.write_zip(path, *channel_code_patterns)
        elif path.suffix.lower() == ".tar":
            return self.write_tar(path, *channel_code_patterns)
        elif (
            len(path.suffixes) >= 2
            and path.suffixes[-1].lower() == ".gz"
            and path.suffixes[-2].lower() == ".tar"
        ):
            return self.write_tar_gz(path, *channel_code_patterns)
        else:
            raise NotImplementedError(
                f"{path.suffix} is not supported. Only .mme/folder/.zip/.tar/.tar.gz are supported."
            )

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

    def __eq__(self, other) -> bool:
        return self.test_number == other.test_number

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

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

    def __hash__(self) -> int:
        return hash(self.test_number or "Unnamed ISOMME")

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
            # 2. Filter Channel
            if filter and fnmatch.fnmatch(code_pattern, "*[ABCD]"):
                for channel in self.channels:
                    if fnmatch.fnmatch(channel.code, code_pattern[:-1] + "?"):
                        return channel.cfc(code_pattern[-1])
            try:
                code_pattern = Code(code_pattern)
            except InvalidCodeError:
                continue
            # 3. Calculate Channel
            if calculate:
                for provider in PROVIDERS:
                    if provider.matches(code_pattern):
                        built_channel = provider.build(self, code_pattern)
                        if built_channel is not None:
                            return built_channel

            # 4. Differentiate
            if differentiate:
                try:
                    code_integrated = code_pattern.integrate()
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
                            return channel_int.differentiate()
                        except (AttributeError, NotImplementedError) as error:
                            logger.debug(error)

            # 5. Integrate
            if integrate:
                try:
                    code_differentiated = code_pattern.differentiate()
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
                            return channel_dif.integrate()
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
        Get all channels by channel code patter. All Wildcards are supported.
        A list of all matching channels will be returned.
        Filtering and Calculations are not supported yet. See 'get_channel()' instead.
        :param code_patterns:
        :param filter:
        :param calculate:
        :param differentiate:
        :param integrate:
        :return: list of Channels
        """
        channel_list = []
        for code_pattern in code_patterns:
            # 1. Channel does exist already
            for channel in self.channels:
                if fnmatch.fnmatch(channel.code, code_pattern):
                    channel_list.append(channel)
            # 2. Filter Channel
            if filter:
                for channel in self.channels:
                    if channel in channel_list:
                        continue
                    if fnmatch.fnmatch(channel.code, code_pattern[:-1] + "?"):
                        channel_list.append(channel.cfc(code_pattern[-1]))

            try:
                code_pattern = Code(code_pattern)
            except InvalidCodeError:
                continue
            # 3. Calculate Channel
            if calculate:
                calculated_channel = self.get_channel(code_pattern)
                if (
                    calculated_channel is not None
                    and calculated_channel not in channel_list
                ):
                    channel_list.append(calculated_channel)

            # 4. Differentiate
            if differentiate:
                try:
                    for channel in self.get_channels(
                        code_pattern.integrate(),
                        filter=filter,
                        calculate=calculate,
                        integrate=False,
                    ):
                        channel_list.append(channel.differentiate())
                except (AttributeError, NotImplementedError) as error:
                    logger.debug(error)

            # 5. Integrate
            if integrate:
                try:
                    for channel in self.get_channels(
                        code_pattern.differentiate(),
                        filter=filter,
                        calculate=calculate,
                        differentiate=False,
                    ):
                        channel_list.append(channel.integrate())
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
    channel_code_patterns: list | None = None,
    recursive: bool = True,
    merge: bool = True,
) -> list[Isomme]:
    all_paths: list[str] = []
    for path in paths:
        all_paths += glob.glob(path, recursive=recursive)
    unique_paths = set(all_paths)

    channel_code_patterns = (
        [] if channel_code_patterns is None else channel_code_patterns
    )

    iso_list = []
    with logging_redirect_tqdm():
        for path in tqdm(unique_paths, desc="Reading"):
            try:
                iso_list.append(Isomme().read(path, *channel_code_patterns))
            except Exception as e:
                logger.critical(e)

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
