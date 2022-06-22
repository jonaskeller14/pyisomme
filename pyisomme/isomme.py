from pathlib import Path
import fnmatch
from glob import glob
import zipfile
import logging

import pyisomme.channel
from pyisomme.parsing import parse_mme, parse_chn, parse_xxx
from pyisomme.channel import create_sample

# logging.basicConfig(
#     filename="pyisomme.py.log",
#     level="INFO",
#     filemode='w',
# )
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
                print("sdfsdf")
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
            logging.error("File not .zip or .mme or Folder not containing .mme file.")
            return self
        logging.info(f"Reading '{path}' done. Number of channel: {len(self.channels)}")
        return self

    def write(self, path):
        # folder or zip
        # create files and second step is zip
        # TODO
        return self

    def extend(self, other):
        """
        Extend Isomme
        #TODO: test info -> change test_number ??
        :param other:
        :return:
        """
        # Extend channel list
        self.channels += other.channels

    def __eq__(self, other):
        return self.test_number == other.test_numer

    def __ne__(self, other):
        return not __eq__(self, other)

    def get_channel(self, *channel_code_patterns:str, filter:bool=True):
        """
        Get channel by channel code patter. Wildcards such as '?' or '*' are supported.
        First match will be returned, although multiple matches exist.
        :param channel_code_patterns:
        :param filter:
        :return: Channel
        """
        for channel_code_pattern in channel_code_patterns:
            for channel in self.channels:
                if fnmatch.fnmatch(channel.code, channel_code_pattern):
                    return channel
                if filter and channel_code_pattern[-1] in "ABCD" and fnmatch.fnmatch(channel.code, channel_code_pattern[:-1] + "?"):
                    return channel.cfc(channel_code_pattern[-1])


    def get_channels(self, *channel_code_patterns:str, filter:bool=True):
        """
        Get all channels by channel code patter. Wildcards such as '?' or '*' are supported.
        A list of all matching channels will be returned.
        :param channel_code_patterns:
        :return: list of Channels
        """
        #TODO: filter
        channel_list = []
        for channel_code_pattern in channel_code_patterns:
            for channel in self.channels:
                if fnmatch.fnmatch(channel.code, channel_code_pattern):
                    channel_list.append(channel)

        return channel_list

    def add_sample_channel(self, code="SAMPLE??????????", t_range:tuple=(0,0.01,1000), y_range:tuple=(0,10), mode:str="sin", unit=None):
        self.channels.append(create_sample(code, t_range, y_range, mode, unit))
        return self
