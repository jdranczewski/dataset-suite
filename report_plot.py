"""
A set of tools and matplotlib defaults to make plotting figures for your
thesis easier. Have a look at the comments below, explaining what each
section does.

We assume you would run `import report_plot as rp` at the top of your
plotting file.

Originally from https://github.com/jdranczewski/phd-thesis/blob/main/figures/report_plot.py
"""

import os
from functools import wraps

import numpy as np
import matplotlib # This lets you do rp.matplotlib if needed in your files
import matplotlib.pyplot as plt
from matplotlib.axes import Axes # Useful for type hinting
from mpl_toolkits.mplot3d.axes3d import Axes3D
from matplotlib.gridspec import GridSpec

# Use a consistent matplotlib style file
plt.style.use(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'report.mplstyle'
))
# See here for things that you can customise by editing the
# `report.mplstyle` file:
# https://matplotlib.org/stable/users/explain/customizing.html

# Default values
width = 6.29921
height = 2.756
figsize = (width, height)

letters = 'abcdefghijklmnopqrstuvwxyz'

# Colour cycle
# This is slightly updated from matplotlib's default tab cycle, with
# slightly more muted, pleasant colours, but keeping the good readability.
# See https://jrnold.github.io/ggthemes/reference/tableau_color_pal.html
# and also https://github.com/matplotlib/matplotlib/issues/21840 for discussion
# on why these are not the current matplotlib default.
tab10x = {
    'tabx:blue': "#4e79a7",
    'tabx:orange': "#f28e2b",
    'tabx:red': "#e15759",
    'tabx:cyan': "#76b7b2",
    'tabx:green': "#59a14f",
    'tabx:yellow': "#edc948",
    'tabx:purple': "#b07aa1",
    'tabx:pink': "#ff9da7",
    'tabx:brown': "#9c755f",
    'tabx:grey': "#bab0ac",
}
tab10x_cycle = [tab10x[key] for key in tab10x]


####################
# Helper functions #
####################

# Plotting

def axes_plotter(function):
    """
    Enables a function to plot on an Axes, and if None are given,
    creates a placeholder one.

    See `z_example_a_name/example.py` for example usage.
    """
    @wraps(function)
    def make_or_pass_ax(ax: None | Axes = None, **kwargs):
        if ax is None:
            fig, ax = plt.subplots(figsize=(width/2, height))
        value = function(ax, **kwargs)
        return value
    return make_or_pass_ax

def axes_plotter_3d(function):
    """
    Enables a function to plot on a 3D Axes, and if None are given,
    creates a placeholder one.
    """
    @wraps(function)
    def make_or_pass_ax(ax: None | Axes = None, **kwargs):
        if ax is None:
            fig = plt.figure(figsize=(width/2, height))
            ax = fig.add_subplot(1, 1, 1, projection="3d")
        value = function(ax, **kwargs)
        return value
    return make_or_pass_ax

# Colour management

def hex2rgb(hex: str):
    hex = hex.lstrip("#")
    return np.array(tuple((int(hex[i:i+2], 16) for i in (0, 2, 4))))

@axes_plotter
def plot_colours(ax: Axes):
    """
    Preview the current colour cycle.
    """
    ax.scatter(
        np.arange(10)%5, np.arange(10)//5,
        c=[f"C{i}" for i in range(10)], s=500
    )
    for i in range(10):
        ax.text(
            i%5, i//5, i, ha="center", va="center"
        )
    ax.set_ylim(2, -1)
