"""
Plotting functionality for the DGPC tool based on Matplotlib.
"""
import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from matplotlib import pyplot as plt


def get_colour(label: str) -> Optional[str]:
    """Given the label of the thing to plot, determine the colour."""
    if "given investment" in label:
        return "orange"
    if "all-in day one" in label:
        return "blue"
    if "cash" in label:
        return "red"
    if "nominal account" in label:
        return "magenta"
    if "account" in label:
        return "green"
    return None


def plot(dates: List[datetime.date], absolute_data: Dict[str, np.ndarray],
         relative_data: Dict[str, np.ndarray], output_file: Path, plot_size_y: int = 1080,
         hide_eur_values: bool = False) -> None:
    """Creates a two-sub-plot with a shared x-axis with absolute data on top (measured in EUR), and relative data in
    the bottom (measured in percentages). The plot size can be determined in pixels with a standard 16:9 aspect ratio"""
    # pylint: disable=too-many-arguments

    # Sets the plotting sizes
    plot_size_x = plot_size_y * 16 / 9
    plt.figure(figsize=(plot_size_x / 100, plot_size_y / 100))
    num_labels_x = int(plot_size_x // 80)  # roughly every 80 pixels one x-label

    # Sets the x-data
    x_label_freq = max(1, len(dates) // num_labels_x)
    x_values = np.arange(0, len(dates))

    # Absolute values plot
    plt.subplot(211)
    axis = plt.gca()
    plt.title("[DGPC] DeGiro Performance Chart, obtained using 'https://github.com/CNugteren/DGPC'")
    for name, values in absolute_data.items():
        plt.plot(x_values, values, label=name, color=get_colour(name))
    plt.ylabel("EUR")
    plt.xticks(x_values[::x_label_freq], labels="" * len(x_values[::x_label_freq]))
    axis.set_xlim(xmin=0, xmax=len(x_values))
    if hide_eur_values:
        axis.yaxis.set_ticklabels([])
    plt.grid(True)
    plt.legend(loc="upper left")

    # Relative values plot
    plt.subplot(212)
    axis = plt.gca()
    for name, values in relative_data.items():
        plt.plot(x_values, 100 * values - 100, label=name, color=get_colour(name))
    plt.ylabel("Performance (%)")
    plt.xticks(x_values[::x_label_freq], labels=dates[::x_label_freq], rotation=45)
    axis.set_xlim(xmin=0, xmax=len(x_values))
    plt.grid(True)
    plt.legend(loc="upper left")

    # Larger plots can do with smaller margins
    if plot_size_y > 800:
        plt.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.10, hspace=0.05)
    else:
        plt.subplots_adjust(left=0.09, right=0.96, top=0.93, bottom=0.16, hspace=0.05)

    # Final output to file
    plt.savefig(output_file, dpi=100)
