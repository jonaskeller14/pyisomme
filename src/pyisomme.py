import zipfile
import glob
import numpy as np
import matplotlib.pyplot as plt
import logging
# TODO logging setup --> Read print infos


def read_channels(path: str) -> list:
    """
    Reads Channel data from ISO-MME.zip file.
    :param path: path to ISO-MME.zip file
    :return: list of channels
    """
    archive = zipfile.ZipFile(path, "r")
    channels = []
    for filepath in archive.namelist():
        if "Channel" in filepath.split("/")[-2] and filepath[-3:].isdigit():
            data = {"suffix": filepath[-3:]}
            with archive.open(filepath) as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    if line.decode("utf-8").strip() != "" and ":" in line.decode("utf-8").strip():
                        line_parts = line.decode("utf-8").strip().split(":")
                        data[line_parts[0].strip()] = line_parts[1].strip()
                    else:
                        idx = i
                        break
            # meta data convert to float if possible
            for key, value in data.items():
                try:
                    data[key] = float(value)
                except ValueError:
                    continue

            # decoding + converting to numpy array
            array_values = np.array([float(line.decode("utf-8").strip()) for line in lines[idx:]], dtype="float64")  # TODO: filter for empty lines especially at the end
            data["VALUES_RAW"] = array_values
            assert len(array_values) == data["Number of samples"]
            array_time = np.linspace(data["Time of first sample"], data["Number of samples"] * data["Sampling interval"], int(data["Number of samples"]))
            data["TIME_RAW"] = array_time


            channels.append(data)
    return channels


def apply_cfc_filter(channels: list, cfc: int) -> list:
    pass


def plot(channels: list, save_path: str = None, **kwargs) -> None:
    # TODO: check if same dimension and unit
    # TODO: integrate kwargs
    # TODO: annotate max/min with argmax/argmin https://stackoverflow.com/questions/43374920/how-to-automatically-annotate-maximum-value-in-pyplot/43375405

    fig, axs = plt.subplots(1, 1)
    for channel in channels:
        axs.plot(channel["TIME_RAW"]*1e3, channel["VALUES_RAW"], label=channel["Channel code"])

    axs.set_xlabel('Time [ms]')
    axs.set_ylabel(f"{channels[0]['Dimension']} [{channels[0]['Unit']}]")
    axs.grid(axis="x")
    axs.legend()
    fig.tight_layout()

    # Save or Show Plot
    if save_path is not None:
        plt.savefig(save_path)
    else:
        plt.show()
    plt.close()
