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
    if "account" in label:
        return "green"
    if "given investment" in label:
        return "orange"
    if "all-in day one" in label:
        return "blue"
    if "cash" in label:
        return "red"
    if "invested" in label:
        return "magenta"
    return None


def plot(dates: List[datetime.date], absolute_data: Dict[str, np.ndarray],
         relative_data: Dict[str, np.ndarray], output_file: Path, num_labels_x: int = 24) -> None:
    """Creates a two-sub-plot with a shared x-axis with absolute data on top (measured in EUR), and relative data in
    the bottom (measured in percentages)."""

    plt.figure(figsize=(19.2, 10.8))

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

    # Final output to file
    plt.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.10, hspace=0.05)
    plt.savefig(output_file, dpi=100)
