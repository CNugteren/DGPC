"""
Plotting functionality for the DGPC tool based on Matplotlib.
"""
import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np
from matplotlib import pyplot as plt


def plot(dates: List[datetime.date], absolute_data: Dict[str, np.ndarray],
         relative_data: Dict[str, np.ndarray], output_file: Path) -> None:
    """Creates a two-sub-plot with a shared x-axis with absolute data on top (measured in EUR), and relative data in
    the bottom (measured in percentages)."""

    plt.figure(figsize=(20, 10))

    # Sets the x-data
    x_label_freq = max(1, len(dates) // 20)
    x_values = np.arange(0, len(dates))

    # Absolute values plot
    plt.subplot(211)
    plt.title("DeGiro performance data")
    for name, values in absolute_data.items():
        plt.plot(x_values, values, label=name)
    plt.ylabel("EUR")
    plt.xticks(x_values[::x_label_freq], labels="" * len(x_values[::x_label_freq]))
    plt.grid(True)
    plt.legend(loc="upper left")

    # Relative values plot
    plt.subplot(212)
    for name, values in relative_data.items():
        plt.plot(x_values, 100 * values - 100, label=name)
    plt.ylabel("Performance (%)")
    plt.xticks(x_values[::x_label_freq], labels=dates[::x_label_freq], rotation=45)
    plt.grid(True)
    plt.legend(loc="upper left")

    # Final output to file
    plt.savefig(output_file, dpi=100)
