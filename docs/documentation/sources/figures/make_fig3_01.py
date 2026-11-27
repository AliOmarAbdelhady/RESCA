"""Draw Figure 3-1, the proposed RescueVision workflow, as a 200 dpi PNG.

    python docs/documentation/sources/figures/make_fig3_01.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).with_name("fig3-01_workflow.png")

STEPS = [
    ("1  Open the incident", "A lead-agency Commander opens\none shared incident and invites\nthe other agencies"),
    ("2  Bring in imagery", "An Analyst uploads drone or\nsatellite images; analysis runs\nas background jobs"),
    ("3  Review the map", "Damage, people, hazards and\nroads appear on one 2D/3D map,\neach with its source and age"),
    ("4  Confirm or correct", "Analysts confirm, correct or\nreject each AI result; nothing\nacts until a person confirms"),
    ("5  Coordinate", "Commanders open cases and\nmissions, assign teams and plan\nroutes; alerts close roads"),
    ("6  Act and update", "Field Responders follow routes,\nupdate cases and send reports\nfrom the mobile application"),
]
SIDE = [
    ("Citizen requests", "verified by an Analyst", 3),
    ("Report", "approved by a Commander\nand shared with agencies", 6),
]

INK, EDGE, ACCENT, FILL = "#1a1a1a", "#555555", "#1f5fa8", "#e8f0fa"


def box(ax, x, y, w, h, title, body, fill="white", edge=EDGE, lw=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fill, ec=edge, lw=lw))
    ax.text(x + w / 2, y + h - 0.18, title, ha="center", va="top", fontsize=10.5,
            fontweight="bold", color=INK, family="DejaVu Sans")
    ax.text(x + w / 2, y + h - 0.52, body, ha="center", va="top", fontsize=8.6,
            color=INK, family="DejaVu Sans", linespacing=1.35)


def arrow(ax, a, b, style="-|>", color=EDGE, rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=13, color=color, lw=1.2,
                                 linestyle=ls, connectionstyle=f"arc3,rad={rad}"))


def main():
    fig, ax = plt.subplots(figsize=(10.5, 5.6), dpi=200)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    w, h = 3.0, 1.45
    xs = [0.3, 3.75, 7.2]
    ys = [3.75, 1.55]
    pos = {}
    for i, (title, body) in enumerate(STEPS):
        row, col = divmod(i, 3)
        x = xs[col] if row == 0 else xs[2 - col]
        y = ys[row]
        hi = i in (2, 3)
        box(ax, x, y, w, h, title, body, fill=FILL if hi else "white",
            edge=ACCENT if hi else EDGE, lw=1.8 if hi else 1.2)
        pos[i + 1] = (x, y)
    # main flow
    arrow(ax, (xs[0] + w, ys[0] + h / 2), (xs[1], ys[0] + h / 2))
    arrow(ax, (xs[1] + w, ys[0] + h / 2), (xs[2], ys[0] + h / 2))
    arrow(ax, (xs[2] + w / 2, ys[0]), (xs[2] + w / 2, ys[1] + h))
    arrow(ax, (xs[2], ys[1] + h / 2), (xs[1] + w, ys[1] + h / 2))
    arrow(ax, (xs[1], ys[1] + h / 2), (xs[0] + w, ys[1] + h / 2))
    # feedback: field updates return to the shared map
    gap_y = (ys[1] + h + ys[0]) / 2
    ax.plot([xs[0] + w / 2, xs[0] + w / 2, xs[2] + 0.6], [ys[1] + h, gap_y, gap_y],
            color=ACCENT, lw=1.2, ls="--")
    arrow(ax, (xs[2] + 0.6, gap_y), (xs[2] + 0.6, ys[0]), color=ACCENT, ls="--")
    ax.text(3.75 + w / 2, gap_y + 0.07, "field updates return to the shared map", ha="center",
            fontsize=8.4, color=ACCENT, style="italic", family="DejaVu Sans")
    # side inputs and outputs
    box(ax, 0.3, 0.15, 3.0, 0.95, "Citizen requests", "phone sign-in; verified by an Analyst\nbefore they become cases",
        fill="white", edge=EDGE)
    arrow(ax, (3.3, 0.62), (xs[1] + 0.35, ys[1]), ls="--")
    box(ax, 7.2, 0.15, 3.0, 0.95, "Reports", "frozen figures, approved by\na Commander, shared with agencies",
        fill="white", edge=EDGE)
    arrow(ax, (xs[1] + w - 0.35, ys[1]), (7.2, 0.62), ls="--")
    ax.text(0.3, 5.47, "Proposed RescueVision workflow: from imagery to coordinated assistance",
            fontsize=11.5, fontweight="bold", color=INK, va="top", family="DejaVu Sans")
    fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
    print(OUT)


if __name__ == "__main__":
    main()
