import matplotlib.pyplot as plt
import copy


def plot_4_xyzr(isomme_list:list, code, nrows=2, ncols=2, figsize=(10,10), sharey=True) -> None:
    """
    # TODO
    :param isomme_list:
    :param code:
    :return:
    """
    fig, axs = plt.subplots(nrows, ncols, figsize=figsize, sharey=sharey)
    for isomme in isomme_list:
        for ax, ryxz in zip(axs.flat, "XYZR"):
            code = code[:14] + ryxz + code[15]
            channel = isomme.get_channel(code)
            if channel is not None:
                tmp_data = copy.deepcopy(channel.data)
                tmp_data.index *= 1000
                ax.plot(tmp_data, label=isomme.test_number)
                ax.set_title(f"{code}")
                # ax.set_title(f"{ryxz.upper()}-{channel.get_info('Dimension')}\n{code}")
                ax.set(xlabel='Time [ms]', ylabel=f"{channel.get_info('Dimension')} [{channel.get_info('Unit')}]")
                ax.legend()
    for ax in axs.flatten():
        ax.yaxis.set_tick_params(labelleft=True)
        ax.grid(True)
    fig.tight_layout()


def plot_1(isomme_list:list, code, figsize=(10,10)) -> None:
    """
    # TODO
    :param isomme_list:
    :param code:
    :return:
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    for isomme in isomme_list:
        channel = isomme.get_channel(code)
        if channel is not None:
            tmp_data = copy.deepcopy(channel.data)
            tmp_data.index *= 1000
            ax.plot(tmp_data, label=isomme.test_number)
            ax.set_title(f"{code}")
            # ax.set_title(f"{ryxz.upper()}-{channel.get_info('Dimension')}\n{code}")
            ax.set(xlabel='Time [ms]', ylabel=f"{channel.get_info('Dimension')} [{channel.get_info('Unit')}]")
            ax.legend()
    ax.yaxis.set_tick_params(labelleft=True)
    ax.grid(True)
    fig.tight_layout()


def plot_1_xyzr(isomme_list:list, code, figsize=(10,10)) -> None:
    """
    # TODO
    :param isomme_list:
    :param code:
    :param figsize:
    :return:
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    for isomme in isomme_list:
        c = None
        for xyzr, ls in zip("XYZR", ("--", "-.", ":", "-")):
            code = code[:14] + xyzr + code[15]
            channel = isomme.get_channel(code)
            if channel is not None:
                tmp_data = copy.deepcopy(channel.data)
                tmp_data.index *= 1000
                p = ax.plot(tmp_data, label=f"{isomme.test_number} - {xyzr}", linestyle=ls, color=c)
                c = p[0].get_color()
                ax.set_title(f"{code}")
                ax.set(xlabel='Time [ms]', ylabel=f"{channel.get_info('Dimension')} [{channel.get_info('Unit')}]")
    ax.legend()
    ax.grid(True)
    fig.tight_layout()

