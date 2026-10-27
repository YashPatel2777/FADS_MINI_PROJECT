"""
Phase 6: shared style for the report figures.

One look for every figure: light surface, hairline solid gridlines, 1.5 pt
(about 2 px) lines, markers of at least 8 px, text in ink colours (never the
series colour), and one y-axis per panel. Each case company keeps one colour,
one marker shape and a direct end label in every chart, so identity never
depends on colour alone (the red/green pair and the light amber need this
second cue; colours were checked with the dataviz palette validator).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # render to files, no window
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Chart chrome and ink
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# Case companies: colour, marker (fixed in every figure)
COMPANY_STYLE = {
    "Nvidia": {"color": "#008300", "marker": "o"},
    "AMD": {"color": "#e34948", "marker": "s"},
    "Intel": {"color": "#2a78d6", "marker": "^"},
    "Wolfspeed": {"color": "#eda100", "marker": "D"},
}
COMPANY_ORDER = ["Nvidia", "AMD", "Intel", "Wolfspeed"]

# Models (Figure 11): three validated categorical slots; the rest in ink greys
MODEL_STYLE = {
    "Random forest": {"color": "#2a78d6", "ls": "-"},
    "XGBoost": {"color": "#eb6834", "ls": "-"},
    "Logistic regression": {"color": "#1baf7a", "ls": "-"},
    "Decision tree": {"color": INK_2, "ls": "-"},
    "Baseline: current ratio < 1": {"color": MUTED, "ls": "--"},
    "Baseline: persistence (Z' < 1.23 now)": {"color": MUTED, "ls": ":"},
}

# Diverging blue <-> red with a neutral grey midpoint (correlations)
DIVERGING = LinearSegmentedColormap.from_list("blue_grey_red", ["#2a78d6", "#f0efec", "#e34948"])

LINE_W = 1.5      # points; about 2 px on screen
MARKER_SIZE = 6   # points; about 8 px


def apply_style():
    """Set matplotlib defaults for every figure."""
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans", "font.size": 9,
        "text.color": INK, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
        "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK_2, "ytick.labelcolor": INK_2,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
        "axes.axisbelow": True,
        "legend.frameon": False, "legend.fontsize": 8, "legend.labelcolor": INK_2,
        "lines.linewidth": LINE_W, "lines.markersize": MARKER_SIZE,
        "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
    })


def company_line(ax, x, y, company, filled=None, label=True, **kw):
    """Plot one case company's series with its colour and marker.

    `filled`: optional boolean array; False draws a hollow marker (used in
    Figure 13 to show years that were not actually distressed).
    Points with a blank value are left as gaps.
    """
    st = COMPANY_STYLE[company]
    x, y = np.asarray(x), np.asarray(y, dtype=float)
    ax.plot(x, y, color=st["color"], lw=LINE_W, label=company if label else None, zorder=3, **kw)
    face = np.full(len(x), st["color"], dtype=object)
    if filled is not None:
        face[~np.asarray(filled, dtype=bool)] = SURFACE
    ok = ~np.isnan(y)
    for xi, yi, fc in zip(x[ok], y[ok], face[ok]):
        ax.plot(xi, yi, marker=st["marker"], ms=MARKER_SIZE, mfc=fc, mec=st["color"], mew=1.2, zorder=4,
                linestyle="none")


def end_labels(ax, series, min_gap_px=11, pad_px=6):
    """Direct labels at the right end of each line, nudged apart so they never overlap.

    `series`: {company: (last_x, last_y)}. Labels use ink colour beside a
    small marker key in the company's colour. Positions are spread in screen
    space, so this works on linear and log axes alike.
    """
    fig = ax.figure
    fig.canvas.draw()
    pts = []
    for name, (x, y) in series.items():
        if y is None or np.isnan(y):
            continue
        px = ax.transData.transform((x, y))
        pts.append([name, px[0], px[1]])
    pts.sort(key=lambda p: p[2])
    for i in range(1, len(pts)):  # push labels up until they are min_gap apart
        if pts[i][2] - pts[i - 1][2] < min_gap_px:
            pts[i][2] = pts[i - 1][2] + min_gap_px
    inv = ax.transData.inverted()
    for name, px, py in pts:
        x_data, y_data = inv.transform((px + pad_px, py))
        ax.annotate(name, xy=(x_data, y_data), xycoords="data", fontsize=8, color=INK_2, va="center",
                    ha="left", annotation_clip=False)


def year_axis(ax, years):
    """Integer label-year ticks with room on the right for end labels."""
    years = sorted(set(int(y) for y in years))
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) if (y - years[0]) % 2 == 0 else "" for y in years])
    ax.set_xlim(years[0] - 0.4, years[-1] + 1.6)
    ax.set_xlabel("Label year")


def ref_line(ax, y, text, va="bottom"):
    """Horizontal reference line (e.g. current ratio = 1) with a small ink label."""
    ax.axhline(y, color=INK_2, lw=0.9, ls="--", zorder=2)
    if text is None:  # the line is explained in the panel title instead
        return
    ax.annotate(text, xy=(0.005, y), xycoords=("axes fraction", "data"), fontsize=7.5, color=INK_2,
                va=va, ha="left", xytext=(0, 2 if va == "bottom" else -2), textcoords="offset points")


def save(fig, path):
    """Save a figure as a 300 dpi PNG; returns the path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path
