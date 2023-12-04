import copy
import logging
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np


COLORS = mcolors.TABLEAU_COLORS.values()


def plot_1(isomme_list:list, code, limits=None, xlim:tuple=(None, None), figsize=(10,10), colors=COLORS):
    """
    Create fig and plot all Channels of all Isomme-objects
    :param isomme_list: list of Isomme-objects
    :param code: code to identify channel
    :param limits:
    :param xlim:
    :param figsize:
    :param colors:
    :return: figure
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.set_title(f"{code}")
    codes_plotted = {ax: []}
    for isomme, c in zip(isomme_list, colors):
        for channel in isomme.get_channels(code):
            tmp_data = copy.deepcopy(channel.data)
            tmp_data.index *= 1000
            ax.plot(tmp_data, c=c, label=f"{isomme.test_number} - {channel.code}")
            ax.set(xlabel='Time [ms]', ylabel=f"{channel.get_info('Dimension')} [{channel.get_info('Unit')}]")
            codes_plotted[ax].append(channel.code)

    xlim = ax.get_xlim() if xlim == (None, None) else xlim
    ylim = ax.get_ylim()
    if limits is not None:
        plot_limits(ax, limits, codes_plotted[ax], xlim=xlim, ylim=ylim)

    ax.legend()
    ax.yaxis.set_tick_params(labelleft=True)
    ax.grid(True)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    fig.tight_layout()
    return fig


def plot_nxn(isomme_list:list, code_list:list, nrows=2, ncols=2, limits=None, xlim:tuple=(None, None), figsize=(10,10), sharey=False, colors=COLORS):
    """
    # TODO: test
    :param isomme_list:
    :param code_list:
    :param nrows:
    :param ncols:
    :param figsize:
    :param sharey:
    :return:
    """
    fig, axs = plt.subplots(nrows, ncols, figsize=figsize, sharey=sharey)
    codes_plotted = {}
    for isomme, c in zip(isomme_list, colors):
        for ax, code in zip(axs.flat, code_list):
            codes_plotted[ax] = []
            channel = isomme.get_channel(code)
            if channel is not None:
                tmp_data = copy.deepcopy(channel.data)
                tmp_data.index *= 1000
                ax.plot(tmp_data, c=c, label=isomme.test_number)
                ax.set_title(f"{code}")
                ax.set(xlabel='Time [ms]', ylabel=f"{channel.get_info('Dimension')} [{channel.get_info('Unit')}]")
                codes_plotted[ax].append(channel.code)

    for ax in axs.flat:
        xlim = ax.get_xlim() if xlim == (None, None) else xlim
        ylim = ax.get_ylim()
        if limits is not None:
            plot_limits(ax, limits, codes_plotted[ax], xlim=xlim, ylim=ylim)
        ax.legend()
        ax.yaxis.set_tick_params(labelleft=True)
        ax.grid(True)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    fig.tight_layout()
    return fig


def plot_2x2(isomme_list:list, code_list:list, *args, **kwargs):
    return plot_nxn(isomme_list, code_list, nrows=2, ncols=2, *args, **kwargs)


def plot_4x1(isomme_list:list, code_list:list, *args, **kwargs):
    return plot_nxn(isomme_list, code_list, nrows=4, ncols=1, *args, **kwargs)


def plot_1x4(isomme_list:list, code_list:list, *args, **kwargs):
    return plot_nxn(isomme_list, code_list, nrows=1, ncols=4, *args, **kwargs)


def plot_1_xyzr(isomme_list:list, code, limits=None, xlim:tuple=(None, None), figsize=(10,10), colors=COLORS):
    """
    # TODO
    :param isomme_list:
    :param code:
    :param figsize:
    :return:
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.set_title(f"{code}")
    codes_plotted = {ax: []}
    for isomme, c in zip(isomme_list, colors):
        for xyzr, ls in zip("XYZR", ("--", "-.", ":", "-")):
            code = code[:14] + xyzr + code[15]
            channel = isomme.get_channel(code)
            if channel is not None:
                tmp_data = copy.deepcopy(channel.data)
                tmp_data.index *= 1000
                ax.plot(tmp_data, label=f"{isomme.test_number} - {xyzr}", linestyle=ls, c=c)
                ax.set(xlabel='Time [ms]', ylabel=f"{channel.get_info('Dimension')} [{channel.get_info('Unit')}]")
                codes_plotted[ax].append(channel.code)

    xlim = ax.get_xlim() if xlim == (None, None) else xlim
    ylim = ax.get_ylim()
    if limits is not None:
        plot_limits(ax, limits, codes_plotted[ax], xlim=xlim, ylim=ylim)

    ax.legend()
    ax.yaxis.set_tick_params(labelleft=True)
    ax.grid(True)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    fig.tight_layout()
    return fig


def plot_nxn_xyzr(isomme_list:list, code, nrows=2, ncols=2, limits=None, xlim: tuple=(None, None), figsize=(10,10), sharey=True, colors=COLORS):
    """
    # TODO
    :param isomme_list:
    :param code:
    :return:
    """
    fig, axs = plt.subplots(nrows, ncols, figsize=figsize, sharey=sharey)
    codes_plotted = {}
    for isomme, c in zip(isomme_list, colors):
        for ax, ryxz in zip(axs.flat, "XYZR"):
            codes_plotted[ax] = []
            code = code[:14] + ryxz + code[15]
            channel = isomme.get_channel(code)
            ax.set_title(f"{code}")
            if channel is not None:
                tmp_data = copy.deepcopy(channel.data)
                tmp_data.index *= 1000
                ax.plot(tmp_data, c=c, label=isomme.test_number)
                ax.set(xlabel='Time [ms]', ylabel=f"{channel.get_info('Dimension')} [{channel.get_info('Unit')}]")
                codes_plotted[ax].append(channel.code)

    for ax in axs.flat:
        xlim = ax.get_xlim() if xlim == (None, None) else xlim
        ylim = ax.get_ylim()
        if limits is not None:
            plot_limits(ax, limits, codes_plotted[ax], xlim=xlim, ylim=ylim)
        ax.legend()
        ax.yaxis.set_tick_params(labelleft=True)
        ax.grid(True)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    fig.tight_layout()
    return fig


def plot_2x2_xyzr(isomme_list:list, code, *args, **kwargs):
    return plot_nxn_xyzr(isomme_list, code, nrows=2, ncols=2, *args, **kwargs)


def plot_4x1_xyzr(isomme_list:list, code, *args, **kwargs):
    return plot_nxn_xyzr(isomme_list, code, nrows=4, ncols=1, *args, **kwargs)


def plot_1x4_xyzr(isomme_list:list, code, *args, **kwargs):
    return plot_nxn_xyzr(isomme_list, code, nrows=1, ncols=4, *args, **kwargs)


def plot_limits(ax, limits, code_list: list, xlim: tuple, ylim: tuple, label=False, fill=True):
    """
    Search for Limits and add them to the plot-axes.
    :param ax:
    :param limits:
    :param code_list:
    :param xlim:
    :param ylim:
    :param label:
    :param fill:
    :return:
    """
    x_min, x_max = xlim
    y_min, y_max = ylim

    limits = limits.get_limits(*code_list)
    limits = sorted(limits, key=lambda l: l.func(0))

    x = list(np.linspace(x_min, x_max, 1000))

    # Fill
    if fill:
        for idx, limit in enumerate(limits):
            if idx == 0 and limit.upper:
                y = limit.func(x)
                ax.fill([x[0]] + x + [x[-1]], [y_min] + y + [y_min], color=limit.color)
            elif idx == len(limits)-1 and limit.lower:
                y = limit.func(x)
                ax.fill([x[0]] + x + [x[-1]], [y_max] + y + [y_max], color=limit.color)
            elif limit.upper:
                previous_limit = limits[idx-1]
                y_1 = limit.func(x)
                x_2 = x[::-1]
                y_2 = previous_limit.func(x_2)
                ax.fill(x + x_2, y_1 + y_2, color=limit.color)
            elif limit.lower:
                next_limit = limits[idx+1]
                y_1 = limit.func(x)
                x_2 = x[::-1]
                y_2 = next_limit.func(x_2)
                ax.fill(x + x_2, y_1 + y_2, color=limit.color)
            else:
                logging.warning(f"Could not plot the filling of the limit: {limit}, because it is not specified as upper or lower limit.")

    # Plot Lines
    for limit in limits:
        ax.plot(x, limit.func(x), color=limit.color, linestyle=limit.linestyle, label=limit.name if label else None)
        if limit.name is not None:
            ax.text(6, limit.func(0) + (20 if limit.lower else -20 if limit.upper else 0), limit.name, color="black", bbox={"facecolor": limit.color, "edgecolor": "black", "linewidth": 1}, verticalalignment="top" if limit.upper else "bottom" if limit.lower else "center")
    return ax