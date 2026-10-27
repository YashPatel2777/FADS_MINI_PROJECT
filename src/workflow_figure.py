"""
Figure 14: overall workflow of the project (report Chapter 4.1).

A flowchart drawn with matplotlib in the same style as Figures 1-13
(src/plots.py). Every count in the boxes comes from the data log.
Run from the project root:  python -m src.workflow_figure
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from src import config
from src import plots as P

# Box fills: data stages light, analysis outputs in the case-blue tint
FILL_DATA = "#f0efec"
FILL_OUT = "#e3eefb"


def box(ax, x, y, w, h, title, body, fill=FILL_DATA):
    """Rounded box centred on (x, y) with a bold title line and smaller body text."""
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                facecolor=fill, edgecolor=P.AXIS, linewidth=1.0))
    ax.text(x, y + h / 2 - 0.17, title, ha="center", va="top", fontsize=9, fontweight="bold", color=P.INK)
    ax.text(x, y + h / 2 - 0.45, body, ha="center", va="top", fontsize=7.6, color=P.INK_2, linespacing=1.35)


def arrow(ax, start, end, text=None):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, color=P.INK_2, linewidth=1.1,
                                 shrinkA=0, shrinkB=0))
    if text:
        ax.text((start[0] + end[0]) / 2 + 0.08, (start[1] + end[1]) / 2, text, ha="left", va="center",
                fontsize=7, color=P.MUTED, fontstyle="italic")


def main(path=config.FIGURES_DIR / "fig14_workflow.png"):
    P.apply_style()
    fig, ax = plt.subplots(figsize=(8.2, 10.2))
    ax.set_xlim(0, 10.4)
    ax.set_ylim(0, 13.4)
    ax.axis("off")

    W, H = 5.8, 1.15
    cx = 5.0  # main column centred over the middle branch
    # Main pipeline, top to bottom
    stages = [
        (12.6, "1. SEC Financial Statement Data Sets", "49 quarterly zips, 2014 Q3 to 2026 Q3\n337,436 submissions, 152.3 million reported values"),
        (11.05, "2. Filing selection", "SIC 3674, Form 10-K and 10-K/A, identified by CIK\n1,128 annual filings from 167 companies"),
        (9.5, "3. Fiscal year alignment", "label_year from the fiscal year-end month\nJan to May = previous year; Jun to Dec = same year"),
        (7.95, "4. Preprocessing", "Consolidated full-year USD values, latest filing kept,\nno filled values: 1,028 company-years, 161 companies"),
        (6.4, "5. Ratios and profit and loss summary", "14 ratios (zero or negative denominators left blank)\nP&L summary for the four case companies"),
        (4.85, "6. Distress label", "Altman Z' < 1.23 in year t+1, features from year t\n749 labelled company-years (670 operating)"),
    ]
    for y, t, b in stages:
        box(ax, cx, y, W, H, t, b)
    for (y1, *_), (y2, *_) in zip(stages, stages[1:]):
        arrow(ax, (cx, y1 - H / 2), (cx, y2 + H / 2))

    # Side check: 10-K verification against stage 5
    box(ax, 9.25, 6.4, 1.95, H, "10-K check", "Case companies vs\nEDGAR statements:\n99 + 32 match", fill=FILL_OUT)
    arrow(ax, (cx + W / 2, 6.4), (9.25 - 1.95 / 2, 6.4))

    # Three branches from the label stage
    by = 2.75
    branches = [
        (1.65, "Ratio and case analysis", "Figures 1-9, sector trends,\nfour case studies\n(Chapters 5 and 6)"),
        (5.0, "Machine learning", "Time-based split, 4 models\n+ 2 baselines, SHAP,\nwalk-forward (Chapter 7)"),
        (8.35, "Dashboard", "CSV exports with 29 checks,\nPower BI, 4 pages\n(Chapter 8)"),
    ]
    bw, bh = 3.05, 1.35
    top = 4.85 - H / 2
    for x, t, b in branches:
        box(ax, x, by, bw, bh, t, b, fill=FILL_OUT)
        arrow(ax, (cx, top), (x, by + bh / 2))

    # Conclusion
    box(ax, 5.0, 0.6, 6.4, 0.95, "Conclusion, limitations and future scope", "Chapter 9: sector picture, case summaries, algorithm comparison")
    for x, *_ in branches:
        arrow(ax, (x, by - bh / 2), (5.0 + (x - 5.0) * 0.55, 0.6 + 0.95 / 2))

    ax.set_title("Overall workflow of the SemiFin project", loc="left", pad=6)
    P.save(fig, path)
    print("saved", path)


if __name__ == "__main__":
    main()
