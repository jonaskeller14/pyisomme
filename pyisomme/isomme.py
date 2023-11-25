import os
from pathlib import Path
import fnmatch
from glob import glob
import zipfile
import logging
import shutil
from pyisomme.parsing import parse_mme, parse_chn, parse_xxx
from pyisomme.channel import create_sample
from pyisomme.calculate import *

logging.getLogger().addHandler(logging.StreamHandler())


class Isomme:
    def __init__(self, test_number=None, test_info=None, channels=None, channel_info=None):
        """
        Create empty Isomme object.
        """
        self.test_number = test_number
        self.test_info = {} if test_info is None else test_info
        self.channels = [] if channels is None else channels
        self.channel_info = {} if channel_info is None else channel_info

    def get_test_info(self, *labels):
        """
        Get test info by giving one or multiple label(s) to identify information.
        Regex patterns possible.
        :param labels: key to find information in dict
        :return: first match or None
        """
        for label in labels:
            for key in self.test_info:
                if re.match(label, key):
                    return self.test_info[key]
        return None

    def get_channel_info(self, *labels):
        """
        Get channel info by giving one or multiple label(s) to identify information.
        Regex pattern possible.
        :param labels: key to find information in dict
        :return: first match or None
        """
        for label in labels:
            for key in self.channel_info:
                if re.match(label, key):
                    return self.channel_info[key]
        return None

    def read(self, path:str, *channel_code_patterns):
        """
        path must reference...
        - a zip which contains .mme-file
        - a folder which contains .mme-file
        - a .mme file
        :param path:
        :return:
        """
        def read_from_mme(path:Path):
            # MME
            self.test_number = path.stem
            with open(path, "r") as mme_file:
                self.test_info = parse_mme(mme_file)
            # CHN
            chn_files = glob(str(path.parent.joinpath("**", "*.chn")), recursive=True)
            if len(chn_files) == 0:
                logging.warning("No .chn file found.")
            else:
                if len(chn_files) > 1:
                    logging.warning("Multiple .chn files found. First will be used, others ignored.")
                chn_filepath = chn_files[0]
                with open(chn_files[0], "r") as chn_file:
                    self.channel_info = parse_chn(chn_file)
            # 001
            self.channels = []  # in case channel exist trough constructor
            for key in fnmatch.filter(self.channel_info.keys(), "Name of channel *"):
                code = self.channel_info[key].split()[0].split("/")[0]
                if len(channel_code_patterns) == 0:
                    skip = False
                else:
                    skip = True
                    for channel_code_pattern in channel_code_patterns:
                        if fnmatch.fnmatch(code, channel_code_pattern):
                            skip = False
                if not skip:
                    xxx = key.replace("Name of channel", "").replace(" ", "")
                    if xxx.isdigit() and len(glob(str(Path(chn_filepath).parent.joinpath(f"*.{xxx}")))) >= 1:
                        with open(glob(str(Path(chn_filepath).parent.joinpath(f"*.{xxx}")))[0], "r") as xxx_file:
                            self.channels.append(parse_xxx(xxx_file, self.test_number))

        def read_from_folder(path:Path):
            if len(list(path.glob("**/*.mme"))) > 1:
                logging.warning("Multiple .mme files found. First will be used, others ignored.")
            read_from_mme(Path(list(path.glob("**/*.mme"))[0]))

        def read_from_zip(path:Path):
            archive = zipfile.ZipFile(path, "r")
            # MME
            for filepath in archive.namelist():
                if fnmatch.fnmatch(filepath, "*.mme"):
                    self.test_number = Path(filepath).stem
                    with archive.open(filepath, "r") as mme_file:
                        self.test_info = parse_mme(mme_file)
                    break
            if self.test_number is None:
                logging.error("No .mme file found.")
                self.test_number = path.stem
            # CHN
            for filepath in archive.namelist():
                if fnmatch.fnmatch(filepath, "*.chn"):
                    chn_filepath = filepath
                    with archive.open(filepath, "r") as chn_file:
                        self.channel_info = parse_chn(chn_file)
                    break
            # 001
            self.channels = []  # in case channel exist trough constructor
            for key in fnmatch.filter(self.channel_info.keys(), "Name of channel *"):
                code = self.channel_info[key].split()[0].split("/")[0]
                if len(channel_code_patterns) == 0:
                    skip = False
                else:
                    skip = True
                    for channel_code_pattern in channel_code_patterns:
                        if fnmatch.fnmatch(code, channel_code_pattern):
                            skip = False
                if not skip:
                    xxx = key.replace("Name of channel", "").replace(" ", "")
                    if xxx.isdigit() and len(fnmatch.filter(archive.namelist(), str(Path(chn_filepath).parent.joinpath(f"*.{xxx}")))) >= 1:
                        with archive.open(fnmatch.filter(archive.namelist(), str(Path(chn_filepath).parent.joinpath(f"*.{xxx}")))[0], "r") as xxx_file:
                            self.channels.append(parse_xxx(xxx_file, self.test_number))

        path = Path(path)
        if path.suffix == ".mme":
            read_from_mme(path)
        elif path.is_dir and len(list(path.glob("**/*.mme"))) >= 1:
            read_from_folder(path)
        elif path.suffix in (".zip",):
            read_from_zip(path)
        else:
            raise FileNotFoundError("File not .zip or .mme or Folder not containing .mme file.")
        logging.info(f"Reading '{path}' done. Number of channel: {len(self.channels)}")
        return self

    def write(self, path, *channel_code_patterns):
        """
        #TODO
        :param path:
        :return:
        """
        def write_info(file, name_value_dict):
            """
            Pattern:
            <NAME>    :<VALUE>
            :param file:
            :param name_value_dict:
            :return:
            """
            for name, value in name_value_dict.items():
                if len(name) > 29:
                    logging.warning(f"Variable-Name '{name}' too long. It will be shorten to '{name[:29]}'")
                    name = name[:29]
                space = " "*(29 - len(name))
                file.write(f"{name}{space}:{value}\n")
            return file

        # Main
        path = Path(path)
        if path.suffix == ".mme":
            assert path.stem == self.test_number
            os.makedirs(path.parent, exist_ok=True)
            # MME
            with open(path, "w") as mme_file:
                write_info(mme_file, self.test_info)

            # Channel-Folder
            os.makedirs(path.parent.joinpath("Channel"), exist_ok=True)

            # Update Channel Info
            for name in list(self.channel_info.keys()):
                if "Name of channel" in name:
                    del self.channel_info[name]
            self.channel_info["Number of channels"] = len(self.channels)

            # 001 - iterate over channels
            for channel_idx, channel in enumerate(self.channels):
                self.channel_info[f"Name of channel {(channel_idx+1):03}"] = channel.code + (f' / {channel.get_info("Name of the channel")}' if channel.get_info("Name of the channel") is not None else "")
                with open(path.parent.joinpath("Channel", f"{self.test_number}.{(channel_idx+1):03}"), "w") as xxx_file:
                    channel.info["Channel code"] = channel.code
                    # TODO: Time interval etc. anpassen anhand channel.data
                    xxx_file = write_info(xxx_file, channel.info)
                    xxx_file.write(channel.data.to_string(header=False, index=False).replace(" ", ""))

            # TODO: channel files with higher idx than written

            # CHN
            with open(path.parent.joinpath("Channel", f"{self.test_number}.chn"), "w") as chn_file:
                write_info(chn_file, self.channel_info)

        elif path.is_dir and path.suffix not in (".zip",):
            self.write(path.joinpath(f"{self.test_number}.mme"))
        elif path.suffix in (".zip",):
            # 1. write by folder
            folder_path = path.parent.joinpath(self.test_number)  # foldername="<test_number>"
            self.write(folder_path)

            # # 2. zip folder
            shutil.make_archive(str(path.parent.joinpath(path.stem)), 'zip', str(folder_path))

            # # 3. remove unzipped folder
            shutil.rmtree(folder_path)

        return self

    def extend(self, *others):
        """
        Extend channel list with channels of other Isomme-object, with a single Channel-object or a list/tuple of Channel-objects.
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

    def delete_duplicates(self, filterclass_duplicates=False):
        """
        Delete channel duplicates (same channel code). The last added one will be deleted first.
        :param filterclass_duplicates: # TODO
        :return: self
        """
        code_list = [channel.code for channel in self.channels]
        for idx in reversed(range(len(code_list))):
            code = code_list[idx]
            if code_list.count(code) > 1:
                self.channels.pop(idx)
                code_list.pop(idx)
        if filterclass_duplicates:
            pass  # TODO
        return self

    def __eq__(self, other):
        return self.test_number == other.test_number

    def __ne__(self, other):
        return not __eq__(self, other)

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

    def get_channel(self, *channel_code_patterns: str, filter: bool = True, calculate: bool = True) -> Channel:
        """
        Get channel by channel code pattern.
        First match will be returned, although multiple matches may exist.
        If channel does not exist, it will be created through filtering and calculations if possible.
        :param channel_code_patterns:
        :param filter: create channel by filtering if channel does not exist yet
        :param calculate: create channel by calculation if channel does not exist yet
        :return: Channel object or None
        """
        for channel_code_pattern in channel_code_patterns:
            # 1. Channel does exist already
            for channel in self.channels:
                if fnmatch.fnmatch(channel.code, channel_code_pattern):
                    return channel
            # 2. Filter Channel
            if filter and fnmatch.fnmatch(channel_code_pattern, "*[ABCD]"):
                for channel in self.channels:
                    if fnmatch.fnmatch(channel.code, channel_code_pattern[:-1] + "?"):
                        return channel.cfc(channel_code_pattern[-1])
            # 3. Calculate Channel
            if calculate:
                # Resultant Channel
                if fnmatch.fnmatch(channel_code_pattern, "??????????????R?"):
                    xyz_channel = [self.get_channel(channel_code_pattern[:14] + xyz + channel_code_pattern[15]) for xyz in "XYZ"]
                    if None not in xyz_channel:
                        return calculate_resultant(*xyz_channel)
                # HIC
                if fnmatch.fnmatch(channel_code_pattern, "??HICR??????????"):
                    head_channel = self.get_channel(f"{channel_code_pattern[:2]}HEAD??????ACR?")
                    if head_channel is not None:
                        return calculate_hic(head_channel)
                # TODO a3ms
            # TODO: 4. Differentiate
        return None

    def get_channels(self, *channel_code_patterns:str) -> list:
        """
        Get all channels by channel code patter. All Wildcards are supported.
        A list of all matching channels will be returned.
        Filtering and Calculations are not supported yet. See 'get_channel()' instead.
        :param channel_code_patterns:
        :return: list of Channels
        """
        channel_list = []
        for channel_code_pattern in channel_code_patterns:
            # 1. Channel does exist already
            for channel in self.channels:
                if fnmatch.fnmatch(channel.code, channel_code_pattern):
                    channel_list.append(channel)
            # TODO: 2. Filter Channel
            # TODO: 3. Calculate Channel
            # TODO: 4. Differentiate
        return channel_list

    def add_sample_channel(self, code="SAMPLE??????????", t_range: tuple = (0, 0.01, 1000), y_range: tuple = (0, 10), mode: str = "sin", unit=None):
        self.channels.append(create_sample(code, t_range, y_range, mode, unit))
        return self

    def print_channel_list(self):
        """
        Print all channel codes to console.
        :return: None
        """
        print(f"{self.test_number} - Channel List:")
        for idx, channel in enumerate(self.channels):
            print(f"\t{(idx+1):03}\t{channel.code}")
