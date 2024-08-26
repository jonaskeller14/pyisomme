from __future__ import annotations

from pyisomme.parsing import parse_mme, parse_chn, parse_xxx
from pyisomme.channel import create_sample
from pyisomme.code import Code
from pyisomme.calculate import *
from pyisomme.utils import debug_logging
from pyisomme.info import Info

from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
import os
import glob
import re
import copy
from pathlib import Path
import fnmatch
import zipfile
import logging
import shutil
import pandas as pd
import tarfile


logger = logging.getLogger(__name__)


class Isomme:
    test_number: str
    test_info: Info
    channels: list
    channel_info: Info

    def __init__(self, test_number: str = None,
                 test_info: list = None,
                 channels: list = None,
                 channel_info: list = None):
        """
        Create empty Isomme object.
        """
        self.test_number = test_number
        self.test_info = Info([]) if test_info is None else Info(test_info)
        self.channels = [] if channels is None else channels
        self.channel_info = Info([]) if channel_info is None else Info(channel_info)

    def get_test_info(self, *labels):
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

    def get_channel_info(self, *labels):
        """
        Get channel info by giving one or multiple label(s) to identify information.
        Regex or fnmmatch pattern possible.
        :param labels: key to find information in dict
        :return: first match or None
        """
        for label in labels:
            for key in self.channel_info:
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
        elif len(path.suffixes) >= 2 and path.suffixes[-1].lower() == ".gz" and path.suffixes[-2].lower() == ".tar":
            self.read_from_tarfile(path, *channel_code_patterns, mode="r:gz")
        else:
            raise NotImplementedError(f"Could not read path: {path}")
        logger.info(f"Reading '{path}' done. Number of channel: {len(self.channels)}")
        return self

    def read_from_mme(self, mme_path: Path, *channel_code_patterns) -> Isomme:
        # MME
        self.test_number = mme_path.stem
        try:
            with open(mme_path, "r", encoding="utf-8") as mme_file:
                self.test_info = parse_mme(mme_file.read())
        except UnicodeDecodeError:
            with open(mme_path, "r", encoding="iso-8859-1") as mme_file:
                self.test_info = parse_mme(mme_file.read())

        # CHN
        chn_paths = list(mme_path.parent.glob(f"[cC][hH][aA][nN][nN][eE][lL]*/{self.test_number}.[cC][hH][nN]"))
        if len(chn_paths) == 0:
            raise FileNotFoundError("No .chn file found.")
        elif len(chn_paths) > 1:
            logger.warning(f"Multiple .chn file found. {chn_paths}. Only first will be considered.")

        chn_path = chn_paths[0]
        try:
            with open(chn_path, "r", encoding="utf-8") as chn_file:
                self.channel_info = parse_chn(chn_file.read())
        except UnicodeDecodeError:
            with open(chn_path, "r", encoding="iso-8859-1") as chn_file:
                self.channel_info = parse_chn(chn_file.read())

        # 001
        self.channels = []  # in case channel exist trough constructor, use extend()
        with logging_redirect_tqdm():
            for key in tqdm(fnmatch.filter(self.channel_info.keys(), "Name of channel *"), desc=f"Read Channel of {self.test_number}"):
                code = self.channel_info[key].split()[0].split("/")[0]
                if len(channel_code_patterns) != 0:
                    skip = True
                    for channel_code_pattern in channel_code_patterns:
                        if fnmatch.fnmatch(code, channel_code_pattern):
                            skip = False
                            break
                    if skip:
                        continue

                xxx = re.search(r"Name of channel (\d*)", key)
                if xxx is None:
                    raise Exception
                xxx = xxx.groups()[0]
                xxx_paths = list(Path(chn_path).parent.glob(f"{self.test_number}.{xxx}"))
                if len(xxx_paths) == 0:
                    logger.critical(f"Channel file '{self.test_number}.{xxx}' not found.")
                    continue

                xxx_path = xxx_paths[0]
                logger.debug(xxx_path)
                try:
                    with open(xxx_path, "r", encoding="utf-8") as xxx_file:
                        self.channels.append(parse_xxx(xxx_file.read(), isomme=self))
                except UnicodeDecodeError:
                    with open(xxx_path, "r", encoding="iso-8859-1") as xxx_file:
                        self.channels.append(parse_xxx(xxx_file.read(), isomme=self))
        return self

    def read_from_folder(self, folder_path: Path, *channel_code_patterns) -> Isomme:
        mme_paths = list(folder_path.rglob("*.[mM][mM][eE]"))
        if len(mme_paths) == 0:
            raise FileNotFoundError("Folder not containing any .mme/.MME file.")
        elif len(mme_paths) > 1:
            raise Exception("Multiple .mme files found inside of the folder. Please specify the .mme-file path.")
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
        archive = zipfile.ZipFile(zip_path, "r")

        # MME
        mme_paths = fnmatch.filter(archive.namelist(), "*.[mM][mM][eE]")
        if len(mme_paths) == 0:
            raise FileNotFoundError("No .mme file found.")
        elif len(mme_paths) > 1:
            raise Exception("Multiple .mme files found.")

        mme_path = mme_paths[0]
        self.test_number = Path(mme_path).stem

        with archive.open(mme_path, "r") as mme_file:
            mme_content = mme_file.read()
            try:
                self.test_info = parse_mme(mme_content.decode("utf-8"))
            except UnicodeDecodeError:
                self.test_info = parse_mme(mme_content.decode("iso-8859-1"))

        # CHN
        chn_paths = fnmatch.filter(archive.namelist(), str(Path(mme_path).parent.joinpath("[cC][hH][aA][nN][nN][eE][lL]*", f"{self.test_number}.[cC][hH][nN]")))
        if len(chn_paths) == 0:
            raise FileNotFoundError("No .chn file found.")
        elif len(chn_paths) > 1:
            logger.warning(f"Multiple .chn file found. {chn_paths}. Only first will be considered.")

        chn_path = chn_paths[0]
        with archive.open(chn_path, "r") as chn_file:
            chn_content = chn_file.read()
            try:
                self.channel_info = parse_chn(chn_content.decode("utf-8"))
            except UnicodeDecodeError:
                self.channel_info = parse_chn(chn_content.decode("iso-8859-1"))

        # 001
        self.channels = []  # in case channel exist trough constructor
        with logging_redirect_tqdm():
            for key in tqdm(fnmatch.filter(self.channel_info.keys(), "Name of channel *"), desc=f"Read Channel of {self.test_number}"):
                code = self.channel_info[key].split()[0].split("/")[0]
                if len(channel_code_patterns) != 0:
                    skip = True
                    for channel_code_pattern in channel_code_patterns:
                        if fnmatch.fnmatch(code, channel_code_pattern):
                            skip = False
                            break
                    if skip:
                        continue

                xxx = re.search(r"Name of channel (\d*)", key)
                if xxx is None:
                    raise Exception
                xxx = xxx.groups()[0]
                xxx_paths = fnmatch.filter(archive.namelist(), str(Path(chn_path).parent.joinpath(f"*.{xxx}")))
                if len(xxx_paths) == 0:
                    logger.critical(f"Channel file '*.{xxx}' not found.")
                    continue

                xxx_path = xxx_paths[0]
                logger.debug(xxx_path)
                with archive.open(xxx_path, "r") as xxx_file:
                    xxx_content = xxx_file.read()
                    try:
                        self.channels.append(parse_xxx(xxx_content.decode("utf-8"), isomme=self))
                    except UnicodeDecodeError:
                        self.channels.append(parse_xxx(xxx_content.decode("iso-8859-1"), isomme=self))
        return self

    def read_from_tarfile(self, tar_path: Path, *channel_code_patterns, mode: str = "r") -> Isomme:
        with tarfile.open(tar_path, mode) as tar_file:
            # MME
            mme_paths = fnmatch.filter(tar_file.getnames(), "*.[mM][mM][eE]")
            if len(mme_paths) == 0:
                raise FileNotFoundError("No .mme file found.")
            elif len(mme_paths) > 1:
                raise Exception("Multiple .mme files found.")

            mme_path = mme_paths[0]
            self.test_number = Path(mme_path).stem

            with tar_file.extractfile(mme_path) as mme_file:
                mme_content = mme_file.read()
                try:
                    self.test_info = parse_mme(mme_content.decode("utf-8"))
                except UnicodeDecodeError:
                    self.test_info = parse_mme(mme_content.decode("iso-8859-1"))

            # CHN
            chn_paths = fnmatch.filter(tar_file.getnames(), f"*{self.test_number}.[cC][hH][nN]")
            if len(chn_paths) == 0:
                raise FileNotFoundError("No .chn file found.")
            elif len(chn_paths) > 1:
                raise Exception("Multiple .chn files found.")

            chn_path = chn_paths[0]
            with tar_file.extractfile(chn_path) as chn_file:
                chn_content = chn_file.read()
                try:
                    self.channel_info = parse_chn(chn_content.decode("utf-8"))
                except UnicodeDecodeError:
                    self.channel_info = parse_chn(chn_content.decode("iso-8859-1"))

            # 001
            self.channels = []  # in case channel exist trough constructor
            with logging_redirect_tqdm():
                for key in tqdm(fnmatch.filter(self.channel_info.keys(), "Name of channel *"), desc=f"Read Channel of {self.test_number}"):
                    code = self.channel_info[key].split()[0].split("/")[0]
                    if len(channel_code_patterns) != 0:
                        skip = True
                        for channel_code_pattern in channel_code_patterns:
                            if fnmatch.fnmatch(code, channel_code_pattern):
                                skip = False
                                break
                        if skip:
                            continue

                    xxx = re.search(r"Name of channel (\d*)", key)
                    if xxx is None:
                        raise Exception
                    xxx = xxx.groups()[0]
                    xxx_paths = fnmatch.filter(tar_file.getnames(), str(Path(chn_path).parent.joinpath(f"*.{xxx}")))
                    if len(xxx_paths) == 0:
                        logger.critical(f"Channel file '*.{xxx}' not found.")
                        continue

                    xxx_path = xxx_paths[0]
                    logger.debug(xxx_path)
                    with tar_file.extractfile(xxx_path) as xxx_file:
                        xxx_content = xxx_file.read()
                        try:
                            self.channels.append(parse_xxx(xxx_content.decode("utf-8"), isomme=self))
                        except UnicodeDecodeError:
                            self.channels.append(parse_xxx(xxx_content.decode("iso-8859-1"), isomme=self))
            return self

    def write_mme(self, path: str | Path, *channel_code_patterns) -> Isomme:
        channels = self.get_channels(*channel_code_patterns) if len(channel_code_patterns) != 0 else self.channels
        path = Path(path)

        if path.stem != self.test_number:
            logger.warning("Test number does not match file stem. Not compliant with convention.")

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
            for channel_idx, channel in tqdm(enumerate(channels, 1), desc=f"Write Channel of {self.test_number}",
                                             total=len(channels)):
                channel_info[f"Name of channel {channel_idx:03}"] = channel.code + (
                    f' / {channel.get_info("Name of the channel")}' if channel.get_info(
                        "Name of the channel") is not None else "")
                channel.write(path.parent.joinpath("Channel", f"{path.stem}.{channel_idx:03}"))

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
        shutil.make_archive(str(folder_path), 'zip', str(folder_path))
        shutil.rmtree(folder_path)
        return self

    def write_tar(self, path: str | Path, *channel_code_patterns) -> Isomme:
        path = Path(path)
        folder_path = path.parent.joinpath(path.stem)
        self.write(folder_path, *channel_code_patterns)
        shutil.make_archive(str(folder_path), 'tar', folder_path)
        shutil.rmtree(folder_path)
        return self

    def write_tar_gz(self, path: str | Path, *channel_code_patterns) -> Isomme:
        path = Path(path)
        folder_path = str(path).removesuffix(".tar.gz")
        self.write(folder_path, *channel_code_patterns)
        shutil.make_archive(folder_path, 'gztar', folder_path)
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
        elif len(path.suffixes) >= 2 and path.suffixes[-1].lower() == ".gz" and path.suffixes[-2].lower() == ".tar":
            return self.write_tar_gz(path, *channel_code_patterns)
        else:
            raise NotImplementedError(f"{path.suffix} is not supported. Only .mme/folder/.zip/.tar/.tar.gz are supported.")

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
                raise NotImplementedError(f"Could not extend Isomme with type {type(other)}")
        return self

    def delete_duplicates(self, filter_class_duplicates: bool = False):
        """
        Delete channel duplicates (same channel code). The last added one will be deleted first.
        :param filter_class_duplicates: Delete redundant channels and only keep channels with the least amount of filtering applied
        :return: self
        """
        for code in {channel.code for channel in self.channels}:
            channels = self.get_channels(code, calculate=False, filter=False, differentiate=False, integrate=False)
            for channel in channels[1:]:
                self.channels.remove(channel)
                logger.debug(f"Removed duplicate Channel: {channel.code}")

        if filter_class_duplicates:
            for code in {channel.code for channel in self.channels}:
                channels = self.get_channels(code[:-1].replace("?", "[?]") + "?", calculate=False, filter=False, differentiate=False, integrate=False)
                sort_seq = "0XAEPBF2CG3DHQLVS"
                sort_map = {filter_class: sort_seq.index(filter_class) for filter_class in sort_seq}
                for channel in sorted(channels, key=lambda c: sort_map.get(c.code.filter_class, float('inf')))[1:]:
                    self.channels.remove(channel)
                    logger.debug(f"Removed duplicate filter Channel: {channel.code}")
        return self

    def __eq__(self, other):
        return self.test_number == other.test_number

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"Isomme({self.test_number})"

    def __str__(self):
        return self.test_number

    def __len__(self):
        return len(self.channels)

    def __getitem__(self, index):
        if isinstance(index, str):
            return self.get_channels(index)
        elif isinstance(index, int) or isinstance(index, slice):
            return self.channels[index]

    def __contains__(self, item):
        return item in self.channels

    def __iter__(self):
        for channel in self.channels:
            yield channel

    def __hash__(self):
        return hash(self.test_number)

    @debug_logging(logger)
    def get_channel(self, *code_patterns: str, filter: bool = True, calculate: bool = True, differentiate=True, integrate=True) -> Channel | None:
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
            except AssertionError:
                continue
            # 3. Calculate Channel
            if calculate:
                # Resultant Channel
                if code_pattern.direction == "R" and code_pattern.filter_class != "X":
                    channel_xyz = [self.get_channel(code_pattern.set(direction=direction)) for direction in "XYZ"]
                    if None not in channel_xyz:
                        return calculate_resultant(*channel_xyz)
                    channel_123 = [self.get_channel(code_pattern.set(direction=direction)) for direction in "123"]
                    if None not in channel_123:
                        return calculate_resultant(*channel_123)

                # BrIC
                if code_pattern.main_location == "BRIC" and code_pattern.filter_class == "X":
                    channel_head_av_xyz = [self.get_channel(code_pattern.set(main_location="HEAD", physical_dimension="AV", direction=direction, filter_class="D")) for direction in "XYZ"]
                    if None not in channel_head_av_xyz:
                        return calculate_bric(*channel_head_av_xyz)

                # HIC
                if code_pattern.main_location == "HICR" and code_pattern.filter_class == "X":
                    head_channel = self.get_channel(code_pattern.set(main_location="HEAD",
                                                                     fine_location_1="??",
                                                                     fine_location_2="00",
                                                                     physical_dimension="AC",
                                                                     filter_class="A"))
                    if head_channel is not None:
                        return calculate_hic(head_channel, max_delta_t=int(code_pattern.fine_location_2))

                # xms
                if fnmatch.fnmatch(code_pattern.fine_location_2, "[0-9][CS]") and code_pattern.filter_class == "X":
                    channel = self.get_channel(code_pattern.set(fine_location_2="00",
                                                                filter_class="A" if not code_pattern.main_location == "THSP" else "C"))
                    if channel is not None:
                        return calculate_xms(channel, min_delta_t=int(code_pattern.fine_location_2[0]), method=code_pattern.fine_location_2[1])

                # Damage
                if code_pattern.fine_location_1 == "DA" and code_pattern.fine_location_2 == "MA" and code_pattern.physical_dimension == "AA":
                    if code_pattern.filter_class == "X":
                        channel_xyz = [self.get_channel(code_pattern.set(fine_location_1="00", fine_location_2="00", direction=direction, filter_class="A"),
                                                        code_pattern.set(fine_location_1="CG", fine_location_2="00", direction=direction, filter_class="A")) for direction in "XYZ"]
                        if None not in channel_xyz:
                            if code_pattern.direction == "X":
                                return calculate_damage(*channel_xyz)[4]
                            if code_pattern.direction == "Y":
                                return calculate_damage(*channel_xyz)[5]
                            if code_pattern.direction == "Z":
                                return calculate_damage(*channel_xyz)[6]
                            if code_pattern.direction == "R":
                                return calculate_damage(*channel_xyz)[7]
                    else:
                        channel_xyz = [self.get_channel(code_pattern.set(fine_location_1="00", fine_location_2="00", direction=direction),
                                                        code_pattern.set(fine_location_1="CG", fine_location_2="00", direction=direction)) for direction in "XYZ"]
                        if None not in channel_xyz:
                            if code_pattern.direction == "X":
                                return calculate_damage(*channel_xyz)[0]
                            if code_pattern.direction == "Y":
                                return calculate_damage(*channel_xyz)[1]
                            if code_pattern.direction == "Z":
                                return calculate_damage(*channel_xyz)[2]
                            if code_pattern.direction == "R":
                                return calculate_damage(*channel_xyz)[3]

                # Neck Total Moment
                if code_pattern.main_location == "TMON":
                    if code_pattern.fine_location_1 == "UP":
                        if code_pattern.direction == "X":
                            if code_pattern.filter_class == "X":
                                channel_mx = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="MO", direction="X", filter_class="B"))
                                channel_fy = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="FO", direction="Y", filter_class="B"))
                                if None not in (channel_mx, channel_fy):
                                    return calculate_neck_MOCx(channel_mx, channel_fy)[1]
                            else:
                                channel_mx = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="MO", direction="X"))
                                channel_fy = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="FO", direction="Y"))
                                if None not in (channel_mx, channel_fy):
                                    return calculate_neck_MOCx(channel_mx, channel_fy)[0]
                        elif code_pattern.direction == "Y":
                            if code_pattern.filter_class == "X":
                                channel_my = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="MO", direction="Y", filter_class="B"))
                                channel_fx = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="FO", direction="X", filter_class="B"))
                                if None not in (channel_my, channel_fx):
                                    return calculate_neck_MOCy(channel_my, channel_fx)[1]
                            else:
                                channel_my = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="MO", direction="Y"))
                                channel_fx = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="FO", direction="X"))
                                if None not in (channel_my, channel_fx):
                                    return calculate_neck_MOCy(channel_my, channel_fx)[0]
                    elif code_pattern.fine_location_1 == "LO":
                        if code_pattern.direction == "X":
                            if code_pattern.filter_class == "X":
                                channel_mx = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="MO", direction="X", filter_class="B"))
                                channel_fy = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="FO", direction="Y", filter_class="B"))
                                if None not in (channel_mx, channel_fy):
                                    return calculate_neck_Mx_base(channel_mx, channel_fy)[1]
                            else:
                                channel_mx = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="MO", direction="X"))
                                channel_fy = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="FO", direction="Y"))
                                if None not in (channel_mx, channel_fy):
                                    return calculate_neck_Mx_base(channel_mx, channel_fy)[0]
                        elif code_pattern.direction == "Y":
                            if code_pattern.filter_class == "X":
                                channel_my = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="MO", direction="Y", filter_class="B"))
                                channel_fx = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="FO", direction="X", filter_class="B"))
                                if None not in (channel_my, channel_fx):
                                    return calculate_neck_My_base(channel_my, channel_fx)[1]
                            else:
                                channel_my = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="MO", direction="Y"))
                                channel_fx = self.get_channel(code_pattern.set(main_location="NECK", physical_dimension="FO", direction="X"))
                                if None not in (channel_my, channel_fx):
                                    return calculate_neck_My_base(channel_my, channel_fx)[0]

                # Neck NIJ  # FIXME: Total Moment (TMON statt NECK ??)
                if code_pattern.main_location == "NIJC":
                    if code_pattern.filter_class == "X":
                        c_fz = self.get_channel(code_pattern.set(main_location="NECK", fine_location_1="UP", fine_location_2="00", physical_dimension="FO", direction="Z", filter_class="B"))
                        c_mocy = self.get_channel(code_pattern.set(main_location="NECK", fine_location_1="UP", fine_location_2="00", physical_dimension="MO", direction="Y", filter_class="B"))
                        if None not in (c_fz, c_mocy):
                            if code_pattern.fine_location_2 == "00":
                                return calculate_neck_nij(c_fz, c_mocy, oop=code_pattern.fine_location_1 == "OP")[5]
                            elif code_pattern.fine_location_2 == "CF":
                                return calculate_neck_nij(c_fz, c_mocy, oop=code_pattern.fine_location_1 == "OP")[6]
                            elif code_pattern.fine_location_2 == "CE":
                                return calculate_neck_nij(c_fz, c_mocy, oop=code_pattern.fine_location_1 == "OP")[7]
                            elif code_pattern.fine_location_2 == "TF":
                                return calculate_neck_nij(c_fz, c_mocy, oop=code_pattern.fine_location_1 == "OP")[8]
                            elif code_pattern.fine_location_2 == "TE":
                                return calculate_neck_nij(c_fz, c_mocy, oop=code_pattern.fine_location_1 == "OP")[9]
                    else:
                        c_fz = self.get_channel(code_pattern.set(main_location="NECK", fine_location_1="UP", fine_location_2="00", physical_dimension="FO", direction="Z"))
                        c_mocy = self.get_channel(code_pattern.set(main_location="NECK", fine_location_1="UP", fine_location_2="00", physical_dimension="MO", direction="Y"))
                        if None not in (c_fz, c_mocy):
                            if code_pattern.fine_location_2 == "00":
                                return calculate_neck_nij(c_fz, c_mocy, oop=code_pattern.fine_location_1 == "OP")[0]
                            elif code_pattern.fine_location_2 == "CF":
                                return calculate_neck_nij(c_fz, c_mocy, oop=code_pattern.fine_location_1 == "OP")[1]
                            elif code_pattern.fine_location_2 == "CE":
                                return calculate_neck_nij(c_fz, c_mocy, oop=code_pattern.fine_location_1 == "OP")[2]
                            elif code_pattern.fine_location_2 == "TF":
                                return calculate_neck_nij(c_fz, c_mocy, oop=code_pattern.fine_location_1 == "OP")[3]
                            elif code_pattern.fine_location_2 == "TE":
                                return calculate_neck_nij(c_fz, c_mocy, oop=code_pattern.fine_location_1 == "OP")[4]

                # Shoulder Lateral Force (Y) (min/max of left and right)
                if code_pattern.main_location == "SHLD" and code_pattern.fine_location_1 == "00" and code_pattern.physical_dimension == "FO" and code_pattern.direction == "Y":
                    channel_left = self.get_channel(code_pattern.set(fine_location_1="LE"))
                    channel_right = self.get_channel(code_pattern.set(fine_location_1="RI"))
                    if None not in (channel_left, channel_right):
                        t = time_intersect(channel_left, channel_right)
                        y = np.array([channel_left.get_data(t=t), channel_right.get_data(t=t, unit=channel_left.unit)])
                        return Channel(code=channel_left.code.set(fine_location_1="00"),
                                       data=pd.DataFrame(y[np.argmax(np.abs(y), axis=0), np.arange(y.shape[1])], index=t),
                                       unit=channel_left.unit,
                                       info=channel_left.info)

                # Viscous Criterion (Chest and Abdomen) (min/max of fine_location_1=LE and fine_location_1=RI)
                if code_pattern.main_location in ("VCCR", "VCAR"):
                    # Viscous Criterion (Chest and Abdomen)
                    if code_pattern.main_location == "VCCR":
                        if code_pattern.filter_class == "X":
                            channel = self.get_channel(code_pattern.set(main_location="CHST", physical_dimension="DS", filter_class="C"))
                            if channel is not None:
                                return calculate_vc(channel)[1]
                            channel = self.get_channel(code_pattern.set(main_location="TRRI", physical_dimension="DS", filter_class="C"))
                            if channel is not None:
                                return calculate_vc(channel)[1]
                            channel = self.get_channel(code_pattern.set(main_location="RIBS", physical_dimension="DS", filter_class="C"))
                            if channel is not None:
                                return calculate_vc(channel)[1]
                        else:
                            channel = self.get_channel(code_pattern.set(main_location="CHST", physical_dimension="DS"))
                            if channel is not None:
                                return calculate_vc(channel)[0]
                            channel = self.get_channel(code_pattern.set(main_location="TRRI", physical_dimension="DS"))
                            if channel is not None:
                                return calculate_vc(channel)[0]
                            channel = self.get_channel(code_pattern.set(main_location="RIBS", physical_dimension="DS"))
                            if channel is not None:
                                return calculate_vc(channel)[0]

                        if code_pattern.fine_location_2 == "00":
                            if code_pattern.filter_class == "X":
                                channel_up = self.get_channel(code_pattern.set(fine_location_2="UP"))
                                channel_mi = self.get_channel(code_pattern.set(fine_location_2="MI"))
                                channel_lo = self.get_channel(code_pattern.set(fine_location_2="LO"))
                                if None not in (channel_up, channel_mi, channel_lo):
                                    t = time_intersect(channel_up, channel_mi, channel_lo)
                                    values = np.array([channel_up.get_data(t=t),
                                                       channel_mi.get_data(t=t, unit=channel_up.unit),
                                                       channel_lo.get_data(t=t, unit=channel_up.unit)])
                                    idx_max_abs = np.argmax(np.abs(values), axis=0)
                                    new_values = values[idx_max_abs, np.arange(values.shape[1])]
                                    return Channel(code=channel_up.code.set(fine_location_2="00"),
                                                   data=pd.DataFrame(new_values, index=t),
                                                   unit=channel_up.unit,
                                                   info=channel_up.info)

                                channel_01 = self.get_channel(code_pattern.set(fine_location_2="01", filter_class="C"))
                                channel_02 = self.get_channel(code_pattern.set(fine_location_2="02", filter_class="C"))
                                channel_03 = self.get_channel(code_pattern.set(fine_location_2="03", filter_class="C"))
                                if None not in (channel_01, channel_02, channel_03):
                                    value_01 = channel_01.get_data()[np.argmax(np.abs(channel_01.get_data()))]
                                    value_02 = channel_02.get_data(unit=channel_01.unit)[np.argmax(np.abs(channel_02.get_data(unit=channel_01.unit)))]
                                    value_03 = channel_03.get_data(unit=channel_01.unit)[np.argmax(np.abs(channel_03.get_data(unit=channel_01.unit)))]
                                    value = np.array([value_01, value_02, value_03])[np.argmax(np.abs([value_01, value_02, value_03]))]
                                    return Channel(code=channel_01.code.set(fine_location_2="00", filter_class="X"),
                                                   data=pd.DataFrame([value]),
                                                   unit=channel_01.unit)

                                channel_LO = self.get_channel(code_pattern.set(fine_location_2="LO", filter_class="C"))
                                channel_UP = self.get_channel(code_pattern.set(fine_location_2="UP", filter_class="C"))
                                if None not in (channel_LO, channel_UP):
                                    value_left = channel_LO.get_data()[np.argmax(np.abs(channel_LO.get_data()))]
                                    value_right = channel_UP.get_data(unit=channel_LO.unit)[np.argmax(np.abs(channel_UP.get_data(unit=channel_LO.unit)))]
                                    value = np.array([value_left, value_right])[np.argmax(np.abs([value_left, value_right]))]
                                    return Channel(code=channel_LO.code.set(fine_location_2="00", filter_class="X"),
                                                   data=pd.DataFrame([value]),
                                                   unit=channel_LO.unit)
                            else:
                                channel_up = self.get_channel(code_pattern.set(fine_location_2="UP"))
                                channel_mi = self.get_channel(code_pattern.set(fine_location_2="MI"))
                                channel_lo = self.get_channel(code_pattern.set(fine_location_2="LO"))
                                if None not in (channel_up, channel_mi, channel_lo):
                                    t = time_intersect(channel_up, channel_mi, channel_lo)
                                    values = np.array([channel_up.get_data(t=t),
                                                       channel_mi.get_data(t=t, unit=channel_up.unit),
                                                       channel_lo.get_data(t=t, unit=channel_up.unit)])
                                    new_values = values[np.argmax(np.abs(values), axis=0), np.arange(values.shape[1])]
                                    return Channel(code=channel_up.code.set(fine_location_2="00"),
                                                   data=pd.DataFrame(new_values, index=t),
                                                   unit=channel_up.unit,
                                                   info=channel_up.info)

                                channel_01 = self.get_channel(code_pattern.set(fine_location_2="01"))
                                channel_02 = self.get_channel(code_pattern.set(fine_location_2="02"))
                                channel_03 = self.get_channel(code_pattern.set(fine_location_2="03"))
                                if None not in (channel_01, channel_02, channel_03):
                                    t = time_intersect(channel_01, channel_02, channel_03)
                                    values = np.array([channel_01.get_data(t=t),
                                                       channel_02.get_data(t=t, unit=channel_01.unit),
                                                       channel_03.get_data(t=t, unit=channel_01.unit)])
                                    idx_max_abs = np.argmax(np.abs(values), axis=0)
                                    new_values = values[idx_max_abs, np.arange(values.shape[1])]
                                    return Channel(code=channel_01.code.set(fine_location_2="00"),
                                                   data=pd.DataFrame(new_values, index=t),
                                                   unit=channel_01.unit)

                                channel_LO = self.get_channel(code_pattern.set(fine_location_2="LO"))
                                channel_UP = self.get_channel(code_pattern.set(fine_location_2="UP"))
                                if None not in (channel_LO, channel_UP):
                                    t = time_intersect(channel_LO, channel_UP)
                                    values = np.array([channel_LO.get_data(t=t), channel_UP.get_data(t=t, unit=channel_LO.unit)])
                                    idx_max_abs = np.argmax(np.abs(values), axis=0)
                                    new_values = values[idx_max_abs, np.arange(values.shape[1])]
                                    return Channel(code=channel_LO.code.set(fine_location_2="00"),
                                                   data=pd.DataFrame(new_values, index=t),
                                                   unit=channel_LO.unit)

                    if code_pattern.main_location == "VCAR":
                        if code_pattern.filter_class == "X":
                            channel = self.get_channel(code_pattern.set(main_location="ABDO", physical_dimension="DS", filter_class="C"))
                            if channel is not None:
                                return calculate_vc(channel)[1]
                            channel = self.get_channel(code_pattern.set(main_location="ABRI", physical_dimension="DS", filter_class="C"))
                            if channel is not None:
                                return calculate_vc(channel)[1]
                        else:
                            channel = self.get_channel(code_pattern.set(main_location="ABDO", physical_dimension="DS"))
                            if channel is not None:
                                return calculate_vc(channel)[0]
                            channel = self.get_channel(code_pattern.set(main_location="ABRI", physical_dimension="DS"))
                            if channel is not None:
                                return calculate_vc(channel)[0]

                        if code_pattern.fine_location_2 == "00":
                            if code_pattern.filter_class == "X":
                                channel_01 = self.get_channel(code_pattern.set(fine_location_2="01", filter_class="C"))
                                channel_02 = self.get_channel(code_pattern.set(fine_location_2="02", filter_class="C"))
                                if None not in (channel_01, channel_02):
                                    value_left = channel_01.get_data()[np.argmax(np.abs(channel_01.get_data()))]
                                    value_right = channel_02.get_data(unit=channel_01.unit)[np.argmax(np.abs(channel_02.get_data(unit=channel_01.unit)))]
                                    value = np.array([value_left, value_right])[np.argmax(np.abs([value_left, value_right]))]
                                    return Channel(code=channel_01.code.set(fine_location_2="00", filter_class="X"),
                                                   data=pd.DataFrame([value]),
                                                   unit=channel_01.unit)
                            else:
                                channel_01 = self.get_channel(code_pattern.set(fine_location_2="01"))
                                channel_02 = self.get_channel(code_pattern.set(fine_location_2="02"))
                                if None not in (channel_01, channel_02):
                                    t = time_intersect(channel_01, channel_02)
                                    values = np.array([channel_01.get_data(t=t), channel_02.get_data(t=t, unit=channel_01.unit)])
                                    idx_max_abs = np.argmax(np.abs(values), axis=0)
                                    new_values = values[idx_max_abs, np.arange(values.shape[1])]
                                    return Channel(code=channel_01.code.set(fine_location_2="00"),
                                                   data=pd.DataFrame(new_values, index=t),
                                                   unit=channel_01.unit)

                    if code_pattern.fine_location_1 == "00":
                        if code_pattern.filter_class == "X":
                            channel_left = self.get_channel(code_pattern.set(fine_location_1="LE", filter_class="C"))
                            channel_right = self.get_channel(code_pattern.set(fine_location_1="RI", filter_class="C"))
                            if None not in (channel_left, channel_right):
                                value_left = channel_left.get_data()[np.argmax(np.abs(channel_left.get_data()))]
                                value_right = channel_right.get_data(unit=channel_left.unit)[np.argmax(np.abs(channel_right.get_data(unit=channel_left.unit)))]
                                value = np.array([value_left, value_right])[np.argmax(np.abs([value_left, value_right]))]
                                return Channel(code=channel_left.code.set(fine_location_1="00", filter_class="X"),
                                               data=pd.DataFrame([value]),
                                               unit=channel_left.unit)
                        else:
                            channel_left = self.get_channel(code_pattern.set(fine_location_1="LE"))
                            channel_right = self.get_channel(code_pattern.set(fine_location_1="RI"))
                            if None not in (channel_left, channel_right):
                                t = time_intersect(channel_left, channel_right)
                                values = np.array([channel_left.get_data(t=t),
                                                   channel_right.get_data(t=t, unit=channel_left.unit)])
                                idx_max_abs = np.argmax(np.abs(values), axis=0)
                                new_values = values[idx_max_abs, np.arange(values.shape[1])]
                                return Channel(code=channel_left.code.set(fine_location_1="00"),
                                               data=pd.DataFrame(new_values, index=t),
                                               unit=channel_left.unit)

                # ES-2 / ES-2re Abdomen Force (Min. of front/middle/rear)
                if code_pattern.main_location == "ABDO" and code_pattern.fine_location_2 == "00" and code_pattern.physical_dimension == "FO" and code_pattern.direction == "Y":
                    channel_re = self.get_channel(code_pattern.set(fine_location_2="RE"))
                    channel_mi = self.get_channel(code_pattern.set(fine_location_2="MI"))
                    channel_fr = self.get_channel(code_pattern.set(fine_location_2="FR"))
                    if None not in (channel_re, channel_mi, channel_fr):
                        t = time_intersect(channel_re, channel_mi, channel_fr)
                        values = np.min([channel_re.get_data(t), channel_mi.get_data(t, unit=channel_re.unit), channel_fr.get_data(t, unit=channel_re.unit)], axis=0)
                        return Channel(code=channel_re.code.set(fine_location_2="00"),
                                       data=pd.DataFrame(values, index=t),
                                       unit=channel_re.unit,
                                       info=channel_re.info)

                # Acetabulum Compression (Maximum of left and right)
                if code_pattern.main_location == "ACTB" and code_pattern.fine_location_1 == "00" and code_pattern.fine_location_2 == "00" and code_pattern.physical_dimension == "FO" and code_pattern.direction == "R":
                    channel_left = self.get_channel(code_pattern.set(fine_location_1="LE"))
                    channel_right = self.get_channel(code_pattern.set(fine_location_1="RI"))
                    if channel_left is not None and channel_right is not None:
                        time = time_intersect(channel_left, channel_right)
                        values = np.min([
                            channel_left.get_data(t=time),
                            channel_right.get_data(t=time, unit=channel_left.unit)], axis=0)
                        return Channel(code=channel_left.code.set(fine_location_1="00"),
                                       data=pd.DataFrame(values, index=time),
                                       unit=channel_left.unit)

                # KTH
                if code_pattern.main_location == "KTHC" and code_pattern.physical_dimension == "IM" and code_pattern.fine_location_1 == "00" and code_pattern.filter_class == "X":
                    channel_left = self.get_channel(code_pattern.set(fine_location_1="LE"))
                    channel_right = self.get_channel(code_pattern.set(fine_location_1="RI"))
                    if None not in (channel_left, channel_right):
                        idx_min = np.argmin([channel_left.get_data()[0], channel_right.get_data()[0]], axis=0)
                        channel_min = [channel_left, channel_right][idx_min]
                        return Channel(code=channel_min.code.set(fine_location_1="00"),
                                       data=channel_min.data,
                                       unit=channel_min.unit,
                                       info=channel_min.info)

                if code_pattern.main_location == "KTHC" and code_pattern.physical_dimension == "IM" and code_pattern.fine_location_1 != "00" and code_pattern.filter_class == "X":
                    channel_foz = self.get_channel(code_pattern.set(main_location="FEMR", physical_dimension="FO", filter_class="B"))
                    if channel_foz is not None:
                        return calculate_femur_impulse(channel_foz)

                # Femur Compression (Minimum of left and right)
                if code_pattern.main_location == "FEMR" and code_pattern.fine_location_1 == "00" and code_pattern.fine_location_2 == "00" and code_pattern.physical_dimension == "FO" and code_pattern.direction == "Z":
                    channel_left = self.get_channel(code_pattern.set(fine_location_1="LE"))
                    channel_right = self.get_channel(code_pattern.set(fine_location_1="RI"))
                    if channel_left is not None and channel_right is not None:
                        time = time_intersect(channel_left, channel_right)
                        values = np.min([
                            channel_left.get_data(t=time),
                            channel_right.get_data(t=time, unit=channel_left.unit)], axis=0)
                        return Channel(code=channel_left.code.set(fine_location_1="00"),
                                       data=pd.DataFrame(values, index=time),
                                       unit=channel_left.unit)

                # Knee Slider Compression / Displacement (Minimum of left and right)
                if code_pattern.main_location == "KNSL" and code_pattern.fine_location_1 == "00" and code_pattern.fine_location_2 == "00" and code_pattern.physical_dimension in ("FO", "DS") and code_pattern.direction == "X":
                    channel_left = self.get_channel(code_pattern.set(fine_location_1="LE"))
                    channel_right = self.get_channel(code_pattern.set(fine_location_1="RI"))
                    if channel_left is not None and channel_right is not None:
                        time = time_intersect(channel_left, channel_right)
                        values = np.min([
                            channel_left.get_data(t=time),
                            channel_right.get_data(t=time, unit=channel_left.unit)], axis=0)
                        return Channel(code=channel_left.code.set(fine_location_1="00"),
                                       data=pd.DataFrame(values, index=time),
                                       unit=channel_left.unit)

                # Tibia Index (Maximum of left and right)
                if code_pattern.main_location == "TIIN" and code_pattern.fine_location_1 == "00" and code_pattern.physical_dimension == "00" and code_pattern.direction == "0":
                    channel_left = self.get_channel(code_pattern.set(fine_location_1="LE"))
                    channel_right = self.get_channel(code_pattern.set(fine_location_1="RI"))
                    if channel_left is not None and channel_right is not None:
                        time = time_intersect(channel_left, channel_right)
                        values = np.max([
                            channel_left.get_data(t=time),
                            channel_right.get_data(t=time, unit=channel_left.unit)], axis=0)
                        return Channel(code=channel_left.code.set(fine_location_1="00"),
                                       data=pd.DataFrame(values, index=time),
                                       unit=channel_left.unit)

                # Tibia Index (Maximum of upper and lower)
                if code_pattern.main_location == "TIIN" and code_pattern.fine_location_2 == "00" and code_pattern.physical_dimension == "00" and code_pattern.direction == "0":
                    channel_upper = self.get_channel(code_pattern.set(fine_location_2="UP"))
                    channel_lower = self.get_channel(code_pattern.set(fine_location_2="LO"))
                    if channel_upper is not None and channel_lower is not None:
                        time = time_intersect(channel_upper, channel_lower)
                        values = np.max([
                            channel_upper.get_data(t=time),
                            channel_lower.get_data(t=time, unit=channel_upper.unit)], axis=0)
                        return Channel(code=channel_upper.code.set(fine_location_2="00"),
                                       data=pd.DataFrame(values, index=time),
                                       unit=channel_upper.unit)

                # Tibia Compression (Minimum of left and right)
                if code_pattern.main_location == "TIBI" and code_pattern.fine_location_1 == "00" and code_pattern.physical_dimension == "FO" and code_pattern.direction == "Z":
                    channel_left = self.get_channel(code_pattern.set(fine_location_1="LE"))
                    channel_right = self.get_channel(code_pattern.set(fine_location_1="RI"))
                    if channel_left is not None and channel_right is not None:
                        time = time_intersect(channel_left, channel_right)
                        values = np.min([
                            channel_left.get_data(t=time),
                            channel_right.get_data(t=time, unit=channel_left.unit)], axis=0)
                        return Channel(code=channel_left.code.set(fine_location_1="00"),
                                       data=pd.DataFrame(values, index=time),
                                       unit=channel_left.unit)

                # Tibia Compression (Minimum of upper and lower)
                if code_pattern.main_location == "TIBI" and code_pattern.fine_location_2 == "00" and code_pattern.physical_dimension == "FO" and code_pattern.direction == "Z":
                    channel_upper = self.get_channel(code_pattern.set(fine_location_2="UP"))
                    channel_lower = self.get_channel(code_pattern.set(fine_location_2="LO"))
                    if channel_upper is not None and channel_lower is not None:
                        time = time_intersect(channel_upper, channel_lower)
                        values = np.min([
                            channel_upper.get_data(t=time),
                            channel_lower.get_data(t=time, unit=channel_upper.unit)], axis=0)
                        return Channel(code=channel_upper.code.set(fine_location_2="00"),
                                       data=pd.DataFrame(values, index=time),
                                       unit=channel_upper.unit)

                # Tibia Index
                if code_pattern.main_location == "TIIN" and code_pattern.physical_dimension == "00" and code_pattern.direction == "0":
                    channel_MOX = self.get_channel(code_pattern.set(main_location="TIBI", physical_dimension="MO", direction="X"))
                    channel_MOY = self.get_channel(code_pattern.set(main_location="TIBI", physical_dimension="MO", direction="Y"))
                    channel_FOZ = self.get_channel(code_pattern.set(main_location="TIBI", physical_dimension="FO", direction="Z"))
                    channels = [channel_MOX, channel_MOY, channel_FOZ]
                    if None not in channels and all([channel.code.fine_location_3 in ("H3", "HF", "TH", "T3") for channel in channels]):
                        return calculate_tibia_index(channel_MOX, channel_MOY, channel_FOZ)

                # THOR Dummy Chest PCA Score
                if code_pattern.main_location == "CHST" and code_pattern.fine_location_1 == "00" and code_pattern.fine_location_2 == "PC" and code_pattern.physical_dimension == "DS" and code_pattern.filter_class != "X":
                    channel_le_up_ds = self.get_channel(code_pattern.set(fine_location_1="LE", fine_location_2="UP"))
                    channel_ri_up_ds = self.get_channel(code_pattern.set(fine_location_1="RI", fine_location_2="UP"))
                    channel_le_lo_ds = self.get_channel(code_pattern.set(fine_location_1="LE", fine_location_2="LO"))
                    channel_ri_lo_ds = self.get_channel(code_pattern.set(fine_location_1="RI", fine_location_2="LO"))
                    if None not in (channel_le_up_ds, channel_ri_up_ds, channel_le_lo_ds, channel_ri_lo_ds):
                        return calculate_chest_pc_score(channel_le_up_ds=channel_le_up_ds,
                                                        channel_ri_up_ds=channel_ri_up_ds,
                                                        channel_le_lo_ds=channel_le_lo_ds,
                                                        channel_ri_lo_ds=channel_ri_lo_ds)

                # THOR Dummy Chest/Abdomen Displacement (Minimum of individual IR-TRACC displacement)
                # page 31: https://www.humaneticsgroup.com/sites/default/files/2020-11/thor-50m_3d_ir-tracc_um-rev_c.pdf
                if code_pattern.main_location == "CHST" and code_pattern.fine_location_1 == "00" and code_pattern.fine_location_2 == "00" and code_pattern.physical_dimension == "DS":
                    channels = [self.get_channel(code_pattern.set(fine_location_1=fine_location_1, fine_location_2=fine_location_2)) for fine_location_1, fine_location_2 in (("LE","UP"), ("RI","UP"), ("LE","LO"), ("RI","LO"))]
                    if None not in channels and all(channel.code.fine_location_3 in ("TH", "T3", "00", "??") for channel in channels):
                        time = time_intersect(*channels)
                        values = np.min([channel.get_data(t=time, unit=channels[0].unit) for channel in channels], axis=0)
                        return Channel(code=channels[0].code.set(fine_location_1="00", fine_location_2="00"),
                                       data=pd.DataFrame(values, index=time),
                                       unit=channels[0].unit)
                if code_pattern.main_location == "ABDO" and code_pattern.fine_location_1 == "00" and code_pattern.fine_location_2 == "00" and code_pattern.physical_dimension == "DS":
                    channels = [self.get_channel(code_pattern.set(fine_location_1=fine_location_1, fine_location_2=fine_location_2)) for fine_location_1, fine_location_2 in (("LE","00"), ("RI","00"))]
                    if None not in channels and all(channel.code.fine_location_3 in ("TH", "T3", "00", "??") for channel in channels):
                        time = time_intersect(*channels)
                        values = np.min([channel.get_data(t=time, unit=channels[0].unit) for channel in channels], axis=0)
                        return Channel(code=channels[0].code.set(fine_location_1="00", fine_location_2="00"),
                                       data=pd.DataFrame(values, index=time),
                                       unit=channels[0].unit)

                # THOR Dummy Chest/Abdomen IR-TRACC Displacement
                # page 31: https://www.humaneticsgroup.com/sites/default/files/2020-11/thor-50m_3d_ir-tracc_um-rev_c.pdf
                if ((code_pattern.main_location == "CHST" and code_pattern.fine_location_1 in ("LE", "RI") and code_pattern.fine_location_2 in ("UP", "LO")) or (code_pattern.main_location == "ABDO" and code_pattern.fine_location_1 in ("LE", "RI") and code_pattern.fine_location_2 == "00")) and code_pattern.fine_location_3 in ("TH", "T3"):
                    if code_pattern.physical_dimension == "DC":
                        delta = 15.65 if code_pattern.fine_location_2 == "UP" else -15.65 if code_pattern.fine_location_2 == "LO" else 0  # [mm]
                        if code_pattern.direction == "X":
                            channel_dc0 = self.get_channel(code_pattern.set(direction="0"))
                            channel_any = self.get_channel(code_pattern.set(physical_dimension="AN", direction="Y"))
                            channel_anz = self.get_channel(code_pattern.set(physical_dimension="AN", direction="Z"))
                            if None not in (channel_dc0, channel_any, channel_anz):
                                time = time_intersect(channel_dc0, channel_any, channel_anz)
                                channel_any = channel_any.adjust_to_range(target_range=(-45, 45), unit="deg")
                                channel_anz = channel_anz.adjust_to_range(target_range=(-45, 45), unit="deg")
                                values = delta * np.sin(channel_any.get_data(t=time, unit="rad")) + channel_dc0.get_data(t=time, unit="mm") * np.cos(channel_any.get_data(t=time, unit="rad")) * np.cos(channel_anz.get_data(t=time, unit="rad"))
                                return Channel(code=channel_dc0.code.set(direction="X"),
                                               data=pd.DataFrame(values, index=time),
                                               unit="mm")
                        if code_pattern.direction == "Y":
                            channel_dc0 = self.get_channel(code_pattern.set(direction="0"))
                            channel_anz = self.get_channel(code_pattern.set(physical_dimension="AN", direction="Z"))
                            if None not in (channel_dc0, channel_anz):
                                time = time_intersect(channel_dc0, channel_anz)
                                channel_anz = channel_anz.adjust_to_range(target_range=(-45, 45), unit="deg")
                                values = channel_dc0.get_data(t=time, unit="mm") * np.sin(channel_anz.get_data(t=time, unit="rad"))
                                return Channel(code=channel_dc0.code.set(direction="Y"),
                                               data=pd.DataFrame(values, index=time),
                                               unit="mm")
                        if code_pattern.direction == "Z":
                            channel_dc0 = self.get_channel(code_pattern.set(direction="0"))
                            channel_any = self.get_channel(code_pattern.set(physical_dimension="AN", direction="Y"))
                            channel_anz = self.get_channel(code_pattern.set(physical_dimension="AN", direction="Z"))
                            if None not in (channel_dc0, channel_any, channel_anz):
                                time = time_intersect(channel_dc0, channel_any, channel_anz)
                                channel_any = channel_any.adjust_to_range(target_range=(-45, 45), unit="deg")
                                channel_anz = channel_anz.adjust_to_range(target_range=(-45, 45), unit="deg")
                                values = delta * np.cos((channel_any).get_data(t=time, unit="rad")) - channel_dc0.get_data(t=time, unit="mm") * np.sin(channel_any.get_data(t=time, unit="rad")) * np.cos(channel_anz.get_data(t=time, unit="rad"))
                                return Channel(code=channel_dc0.code.set(direction="Z"),
                                               data=pd.DataFrame(values, index=time),
                                               unit="mm")
                    if code_pattern.physical_dimension == "DS":
                        if code_pattern.direction == "0":
                            channel_dc0 = self.get_channel(code_pattern.set(physical_dimension="DC"))
                            if channel_dc0 is not None:
                                return (channel_dc0 - channel_dc0.get_data(t=0)).set_code(physical_dimension="DS")
                        if code_pattern.direction == "X":
                            channel_dcx = self.get_channel(code_pattern.set(physical_dimension="DC", direction="X"))
                            if channel_dcx is not None:
                                return (channel_dcx - channel_dcx.get_data(t=0)).set_code(physical_dimension="DS")
                        if code_pattern.direction == "Y":
                            channel_dcy = self.get_channel(code_pattern.set(physical_dimension="DC", direction="Y"))
                            if channel_dcy is not None:
                                return (channel_dcy - channel_dcy.get_data(t=0)).set_code(physical_dimension="DS")
                        if code_pattern.direction == "Z":
                            channel_dcz = self.get_channel(code_pattern.set(physical_dimension="DC", direction="Z"))
                            if channel_dcz is not None:
                                return (channel_dcz - channel_dcz.get_data(t=0)).set_code(physical_dimension="DS")

                # WorldSid Dummy Chest/Abdomen Displacement (Minimum of individual IR-TRACC displacment)
                if code_pattern.main_location == "TRRI" and code_pattern.fine_location_2 == "00" and code_pattern.fine_location_3 in ("WS", "??") and code_pattern.physical_dimension == "DS":
                    channel_01 = self.get_channel(code_pattern.set(fine_location_2="01"))
                    channel_02 = self.get_channel(code_pattern.set(fine_location_2="02"))
                    channel_03 = self.get_channel(code_pattern.set(fine_location_2="03"))
                    if None not in (channel_01, channel_02, channel_03):
                        time = time_intersect(channel_01, channel_02, channel_03)
                        values = np.min([channel.get_data(t=time, unit=channel_01.unit) for channel in (channel_01, channel_02, channel_03)], axis=0)
                        return Channel(code=channel_01.code.set(fine_location_2="00"),
                                       data=pd.DataFrame(values, index=time),
                                       unit=channel_01.unit,)  # TODO: info
                if code_pattern.main_location == "ABRI" and code_pattern.fine_location_2 == "00" and code_pattern.fine_location_3 in ("WS", "??") and code_pattern.physical_dimension == "DS":
                    channel_01 = self.get_channel(code_pattern.set(fine_location_2="01"))
                    channel_02 = self.get_channel(code_pattern.set(fine_location_2="02"))
                    if None not in (channel_01, channel_02):
                        time = time_intersect(channel_01, channel_02)
                        values = np.min([channel.get_data(t=time, unit=channel_01.unit) for channel in (channel_01, channel_02)], axis=0)
                        return Channel(code=channel_01.code.set(fine_location_2="00"),
                                       data=pd.DataFrame(values, index=time),
                                       unit=channel_01.unit)  # TODO info

                # WorldSid Dummy Rib IR-TRACC Lateral Length and Absolute/Lateral Displacement
                if code_pattern.main_location in ("TRRI", "ABRI") and code_pattern.fine_location_3 in ("WS", "??"):
                    if code_pattern.physical_dimension == "DC" and code_pattern.direction == "Y":
                        channel_dc0 = self.get_channel(code_pattern.set(physical_dimension="DC", direction="0"))
                        channel_anz = self.get_channel(code_pattern.set(physical_dimension="AN", direction="Z"))
                        if None not in (channel_dc0, channel_anz):
                            t = time_intersect(channel_dc0, channel_anz)
                            channel_anz = channel_anz.adjust_to_range(target_range=(-45, 45), unit="deg")
                            values = channel_dc0.get_data(t=t) * np.cos(channel_anz.get_data(t=t, unit="rad"))
                            return Channel(
                                code=channel_dc0.code.set(physical_dimension="DC", direction="Y"),
                                data=pd.DataFrame(values, index=t),
                                unit=channel_dc0.unit,
                                info=channel_dc0.info
                            )
                    if code_pattern.physical_dimension == "DS":
                        channel_dc = self.get_channel(code_pattern.set(physical_dimension="DC"))
                        if channel_dc is not None:
                            return (channel_dc - channel_dc.get_data(t=0)).set_code(physical_dimension="DS")

                # ES-2 / ES-2re Rib Deflection (Min. of upper/middle/lower)
                if code_pattern.main_location == "RIBS" and code_pattern.fine_location_2 == "00" and code_pattern.physical_dimension == "DS" and code_pattern.direction == "Y":
                    channel_up = self.get_channel(code_pattern.set(fine_location_2="UP"))
                    channel_mi = self.get_channel(code_pattern.set(fine_location_2="MI"))
                    channel_lo = self.get_channel(code_pattern.set(fine_location_2="LO"))
                    if None not in (channel_up, channel_mi, channel_lo):
                        t = time_intersect(channel_up, channel_mi, channel_lo)
                        values = np.min([channel_up.get_data(t), channel_mi.get_data(t, unit=channel_up.unit), channel_lo.get_data(t, unit=channel_up.unit)], axis=0)
                        return Channel(code=channel_up.code.set(fine_location_2="00"),
                                       data=pd.DataFrame(values, index=t),
                                       unit=channel_up.unit,
                                       info=channel_up.info)
                # ES-2 / ES-2re Abdomen Force (Min. of front/middle/rear)
                if code_pattern.main_location == "ABDO" and code_pattern.fine_location_2 == "00" and code_pattern.physical_dimension == "FO" and code_pattern.direction == "Y":
                    channel_re = self.get_channel(code_pattern.set(fine_location_2="RE"))
                    channel_mi = self.get_channel(code_pattern.set(fine_location_2="MI"))
                    channel_fr = self.get_channel(code_pattern.set(fine_location_2="FR"))
                    if None not in (channel_re, channel_mi, channel_fr):
                        t = time_intersect(channel_re, channel_mi, channel_fr)
                        values = np.min([channel_re.get_data(t), channel_mi.get_data(t, unit=channel_re.unit), channel_fr.get_data(t, unit=channel_re.unit)], axis=0)
                        return Channel(code=channel_re.code.set(fine_location_2="00"),
                                       data=pd.DataFrame(values, index=t),
                                       unit=channel_re.unit,
                                       info=channel_re.info)

                # Foot Resultant Acceleration (Max. of left and right)
                if code_pattern.main_location == "FOOT" and code_pattern.physical_dimension == "AC" and code_pattern.direction == "R":
                    channel_left = self.get_channel(code_pattern.set(fine_location_1="LE"))
                    channel_right = self.get_channel(code_pattern.set(fine_location_1="RI"))
                    if None not in (channel_left, channel_right):
                        t = time_intersect(channel_left, channel_right)
                        values = np.max([channel_left.get_data(t), channel_right.get_data(t, unit=channel_left.unit)], axis=0)
                        return Channel(code=channel_left.code.set(fine_location_1="00"),
                                       data=pd.DataFrame(values, index=t),
                                       unit=channel_left.unit,
                                       info=channel_left.info)

                # OLC
                if code_pattern.fine_location_1 == "0O" and code_pattern.fine_location_2 == "LC" and code_pattern.physical_dimension == "VE":
                    tmp = code_pattern.set(fine_location_1="??", fine_location_2="??")
                    if code_pattern.filter_class == "X":
                        tmp = code_pattern.set(filter_class="A")
                    channel = self.get_channel(tmp)

                    if channel is not None:
                        olc, olc_visual = calculate_olc(channel)
                        if code_pattern.filter_class == "X":
                            return olc
                        else:
                            return olc_visual

            # 4. Differentiate
            if differentiate:
                try:
                    return self.get_channel(code_pattern.integrate(), filter=filter, calculate=calculate, integrate=False).differentiate()
                except (AttributeError, NotImplementedError) as error:
                    logger.debug(error)

            # 5. Integrate
            if integrate:
                try:
                    return self.get_channel(code_pattern.differentiate(), filter=filter, calculate=calculate, differentiate=False).integrate()
                except (AttributeError, NotImplementedError) as error:
                    logger.debug(error)

            logger.info(f"No channel found for pattern: '{code_pattern}'")
        return None

    @debug_logging(logger)
    def get_channels(self, *code_patterns: str, filter: bool = True, calculate: bool = True, differentiate: bool = False, integrate: bool = False) -> list:
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
            except AssertionError:
                continue
            # 3. Calculate Channel
            if calculate:
                channel = self.get_channel(code_pattern)
                if channel is not None and channel not in channel_list:
                    channel_list.append(channel)

            # 4. Differentiate
            if differentiate:
                try:
                    for channel in self.get_channels(code_pattern.integrate(),
                                                     filter=filter,
                                                     calculate=calculate,
                                                     integrate=False):
                        channel_list.append(channel.differentiate())
                except (AttributeError, NotImplementedError) as error:
                    logger.debug(error)

            # 5. Integrate
            if integrate:
                try:
                    for channel in self.get_channels(code_pattern.differentiate(),
                                                     filter=filter,
                                                     calculate=calculate,
                                                     differentiate=False):
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
            print(f"\t{(idx+1):03}\t{channel.code}")

    def set_code(self, *args, **kwargs) -> Isomme:
        for channel in self.channels:
            channel.set_code(*args, **kwargs)
        return self

    def cfc(self, *args, **kwargs) -> Isomme:
        for channel in self.channels:
            channel.cfc(*args, **kwargs, return_copy=False)
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


def read(*paths, channel_code_patterns: list = None, recursive: bool = True, merge: bool = True) -> list[Isomme]:
    all_paths = []
    for path in paths:
        all_paths += glob.glob(path, recursive=recursive)
    all_paths = set(all_paths)

    channel_code_patterns = [] if channel_code_patterns is None else channel_code_patterns

    iso_list = []
    with logging_redirect_tqdm():
        for path in tqdm(all_paths, desc="Reading"):
            try:
                iso_list.append(Isomme().read(path, *channel_code_patterns))
            except Exception as e:
                logger.critical(e)

    if merge:
        iso_list = merge_duplicate_isommes(iso_list)
        for isomme in iso_list:
            isomme.delete_duplicates(filter_class_duplicates=True)
    return iso_list


def merge_duplicate_isommes(isommes: list[Isomme]) -> list:
    isommes_dict = {}
    for isomme in isommes:
        if isomme.test_number in isommes_dict:
            isommes_dict[isomme.test_number].extend(isomme)
        else:
            isommes_dict[isomme.test_number] = isomme
    return isommes
