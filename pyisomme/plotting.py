import copy
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import logging


COLORS = mcolors.TABLEAU_COLORS.values()


def plot_1(isomme_list:list, code, limits=None, xlim:tuple=(None, None), y_unit=None, figsize=(10,10), colors=COLORS):
    """
    Create fig and plot Channels of all Isomme-objects
    :param isomme_list: list of Isomme-objects
    :param code: code to identify channel
    :param limits:
    :param xlim:
    :param figsize:
    :param colors:
    :return: figure
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize, layout="constrained")
    ax.set_title(f"{code}")
    codes_plotted = {ax: []}
    for isomme, c in zip(isomme_list, colors):
        channel = isomme.get_channel(code)
        if channel is None:
            continue
        if y_unit is None:
            y_unit = channel.unit
        tmp_data = copy.deepcopy(channel.convert_unit(y_unit).data)
        tmp_data.index *= 1000
        ax.plot(tmp_data, c=c, label=f"{isomme.test_number} - {channel.code}")
        ax.set_xlabel('Time [ms]')
        ax.set_ylabel(f"{channel.get_info('Dimension')} [{channel.unit}]")
        codes_plotted[ax].append(channel.code)

    xlim = ax.get_xlim() if xlim == (None, None) else xlim
    ylim = ax.get_ylim()
    if limits is not None:
        ylim = plot_limits(ax, limits, codes_plotted[ax], xlim=xlim, ylim=ylim, x_unit="ms", y_unit=y_unit)
    ax.legend()
    ax.yaxis.set_tick_params(labelleft=True)
    ax.grid(True)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    return fig


def plot_nxn(isomme_list:list, code_list:list, nrows=2, ncols=2, limits=None, xlim:tuple=(None, None), figsize=(10,10), sharey=False, colors=COLORS):
    """
    :param isomme_list:
    :param code_list:
    :param nrows:
    :param ncols:
    :param limits:
    :param xlim:
    :param figsize:
    :param sharey:
    :param colors:
    :return:
    """
    fig, axs = plt.subplots(nrows, ncols, figsize=figsize, sharey=sharey, layout="constrained")
    codes_plotted = {}
    y_units = {}
    for isomme, c in zip(isomme_list, colors):
        for ax, code in zip(axs.flat, code_list):
            codes_plotted[ax] = []
            y_units[ax] = None
            channel = isomme.get_channel(code)
            if channel is None:
                continue
            if y_units.get(ax) is None:
                y_units[ax] = channel.unit
            tmp_data = copy.deepcopy(channel.convert_unit(y_units[ax]).data)
            tmp_data.index *= 1000
            ax.plot(tmp_data, c=c, label=isomme.test_number)
            ax.set_title(f"{code}")
            ax.set_xlabel('Time [ms]')
            ax.set_ylabel(f"{channel.get_info('Dimension')} [{y_units[ax]}]")
            codes_plotted[ax].append(channel.code)

    for idx, ax in enumerate(axs.flat):
        if idx >= len(code_list):
            ax.remove()
            break
        xlim = ax.get_xlim() if xlim == (None, None) else xlim
        ylim = ax.get_ylim()
        if limits is not None:
            ylim = plot_limits(ax, limits, codes_plotted[ax], xlim=xlim, ylim=ylim, x_unit="ms", y_unit=y_units[ax])
        ax.legend()
        ax.yaxis.set_tick_params(labelleft=True)
        ax.grid(True)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    return fig


def plot_2x2(isomme_list:list, code_list:list, *args, **kwargs):
    return plot_nxn(isomme_list, code_list, nrows=2, ncols=2, *args, **kwargs)


def plot_4x1(isomme_list:list, code_list:list, *args, **kwargs):
    return plot_nxn(isomme_list, code_list, nrows=4, ncols=1, *args, **kwargs)


def plot_1x4(isomme_list:list, code_list:list, *args, **kwargs):
    return plot_nxn(isomme_list, code_list, nrows=1, ncols=4, *args, **kwargs)


def plot_1_xyzr(isomme_list:list, code, limits=None, xlim:tuple=(None, None), y_unit=None, figsize=(10,10), colors=COLORS):
    """
    :param isomme_list:
    :param code:
    :param limits:
    :param xlim:
    :param y_unit:
    :param figsize:
    :param colors:
    :return:
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize, layout="constrained")
    ax.set_title(f"{code}")
    codes_plotted = {ax: []}
    for isomme, c in zip(isomme_list, colors):
        for xyzr, ls in zip("XYZR", ("--", "-.", ":", "-")):
            code = code[:14] + xyzr + code[15]
            channel = isomme.get_channel(code)
            if channel is None:
                continue
            if y_unit is None:
                y_unit = channel.unit
            tmp_data = copy.deepcopy(channel.convert_unit(y_unit).data)
            tmp_data.index *= 1000
            ax.plot(tmp_data, label=f"{isomme.test_number} - {xyzr}", linestyle=ls, c=c)
            ax.set_xlabel('Time [ms]')
            ax.set_ylabel(f"{channel.get_info('Dimension')} [{y_unit}]")
            codes_plotted[ax].append(channel.code)

    xlim = ax.get_xlim() if xlim == (None, None) else xlim
    ylim = ax.get_ylim()
    if limits is not None:
        ylim = plot_limits(ax, limits, codes_plotted[ax], xlim=xlim, ylim=ylim, x_unit="ms", y_unit=y_unit)
    ax.legend()
    ax.yaxis.set_tick_params(labelleft=True)
    ax.grid(True)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    return fig


def plot_nxn_xyzr(isomme_list:list, code, nrows=2, ncols=2, limits=None, xlim: tuple=(None, None), y_unit=None, figsize=(10,10), sharey=True, colors=COLORS):
    """
    :param isomme_list:
    :param code:
    :param nrows:
    :param ncols:
    :param limits:
    :param xlim:
    :param y_unit:
    :param figsize:
    :param sharey:
    :param colors:
    :return:
    """
    fig, axs = plt.subplots(nrows, ncols, figsize=figsize, sharey=sharey, layout="constrained")
    codes_plotted = {}
    for isomme, c in zip(isomme_list, colors):
        for ax, ryxz in zip(axs.flat, "XYZR"):
            codes_plotted[ax] = []
            code = code[:14] + ryxz + code[15]
            channel = isomme.get_channel(code)
            ax.set_title(f"{code}")
            if channel is None:
                continue
            if y_unit is None:
                y_unit = channel.unit
            tmp_data = copy.deepcopy(channel.convert_unit(y_unit).data)
            tmp_data.index *= 1000
            ax.plot(tmp_data, c=c, label=isomme.test_number)
            ax.set_xlabel('Time [ms]')
            ax.set_ylabel(f"{channel.get_info('Dimension')} [{y_unit}]")
            codes_plotted[ax].append(channel.code)

    for ax in axs.flat:
        xlim = ax.get_xlim() if xlim == (None, None) else xlim
        ylim = ax.get_ylim()
        if limits is not None:
            ylim = plot_limits(ax, limits, codes_plotted[ax], xlim=xlim, ylim=ylim, x_unit="ms", y_unit=y_unit)
        ax.legend()
        ax.yaxis.set_tick_params(labelleft=True)
        ax.grid(True)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    return fig


def plot_2x2_xyzr(isomme_list:list, code, *args, **kwargs):
    return plot_nxn_xyzr(isomme_list, code, nrows=2, ncols=2, *args, **kwargs)


def plot_4x1_xyzr(isomme_list:list, code, *args, **kwargs):
    return plot_nxn_xyzr(isomme_list, code, nrows=4, ncols=1, *args, **kwargs)


def plot_1x4_xyzr(isomme_list:list, code, *args, **kwargs):
    return plot_nxn_xyzr(isomme_list, code, nrows=1, ncols=4, *args, **kwargs)


def plot_limits(ax, limits, code_list: list, xlim: tuple, ylim: tuple, label=False, fill=True, x_unit=None, y_unit=None):
    """
    Search for Limits and add them to the plot-axes.
    :param ax:
    :param limits:
    :param code_list:
    :param xlim:
    :param ylim:
    :param label:
    :param fill:
    :param x_unit:
    :param y_unit:
    :return:
    """
    limits = limits.get_limits(*code_list)
    limits = sorted(limits, key=lambda l: (l.func(0), -1 if l.upper else 1 if l.lower else 0))

    x_min, x_max = xlim
    y_min, y_max = ylim

    x = np.linspace(x_min, x_max, 1000)

    # Overwrite y_lim if limits exist which would not be visible
    limit_values = np.array([limit.get_data(x, x_unit=x_unit, y_unit=y_unit) for limit in limits])
    if len(limit_values) != 0 and np.min(limit_values) < y_min:
        y_min = np.min(limit_values)
    if len(limit_values) != 0 and np.max(limit_values) > y_max:
        y_max = np.max(limit_values)
    ylim = (y_min, y_max)

    # Fill
    if fill:
        for idx, limit in enumerate(limits):
            # Fill to minus infinity
            if idx == 0 and limit.upper:
                y = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                if np.all(y_min > x):
                    continue
                ax.fill(np.concatenate([[x[0]], x, [x[-1]]]),
                        np.concatenate([[y_min], y, [y_min]]),
                        color=limit.color, alpha=0.2)

            # Prevent double fill (because transparency)
            elif idx >= 1 and limit.upper and limits[idx-1].lower:
                logging.debug(f"Preventing double fill: {limit} and {limits[idx-1]}")
                continue

            # Filter Duplicate Limits (same func and both upper or lower)
            elif idx >= 1 and (limit.upper == limits[idx-1].upper or limit.lower == limits[idx-1].lower) and np.all(limit.get_data(x, x_unit=x_unit, y_unit=y_unit) == limits[idx-1].get_data(x, x_unit=x_unit, y_unit=y_unit)):
                logging.debug("Not filling twice. Ignore duplicate limit.")
                continue

            # Fill to plus infinity
            elif idx == len(limits)-1 and limit.lower:
                y = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                if np.all(y_max < y):
                    continue
                ax.fill(np.concatenate([[x[0]], x, [x[-1]]]),
                        np.concatenate([[y_max], y, [y_max]]),
                        color=limit.color, alpha=0.2)

            # All other cases
            elif limit.upper:
                previous_limit = limits[idx-1]
                y_1 = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                x_2 = x[::-1]
                y_2 = previous_limit.get_data(x_2, x_unit=x_unit, y_unit=y_unit)
                ax.fill(np.concatenate([x, x_2]),
                        np.concatenate([y_1, y_2]),
                        color=limit.color, alpha=0.2)
            elif limit.lower:
                next_limit = limits[idx+1]
                y_1 = limit.get_data(x, x_unit=x_unit, y_unit=y_unit)
                x_2 = x[::-1]
                y_2 = next_limit.get_data(x_2, x_unit=x_unit, y_unit=y_unit)
                ax.fill(np.concatenate([x, x_2]),
                        np.concatenate([y_1, y_2]),
                        color=limit.color, alpha=0.2)

    # Plot Lines
    # TODO: Check if visible, or include text annotations in auto_scale --> see layout=contrained error
    for limit in limits:
        ax.plot(x, limit.get_data(x, x_unit=x_unit, y_unit=y_unit), color=limit.color, linestyle=limit.linestyle, label=limit.name if label else None)
        if limit.name is not None:
            text = ax.text(10, limit.get_data([0], x_unit=x_unit, y_unit=y_unit)[0], limit.name, color="black", bbox={"facecolor": limit.color, "edgecolor": "black", "linewidth": 1}, verticalalignment="top" if limit.upper else "bottom" if limit.lower else "center")
            # TODO: y offset
            # offset = 1.5 * text.get_fontsize() if limit.lower else -1.5 * text.get_fontsize() if limit.upper else 0
            # text.set_y(limit.get_data([0], x_unit=x_unit, y_unit=y_unit)[0] + offset)
    return ylim