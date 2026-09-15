# -*- coding: utf-8 -*-
"""Figure 6: where SWCL sits in the existing measurement and control topology.
Drawn rather than borrowed, so the proposal carries no vendor branding and no
third-party image rights."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

OUT = os.path.dirname(os.path.abspath(__file__))
C_PROC = "#CFE0D2"
C_SOFT = "#D8DAEC"
C_NEW = "#E8BFBF"
C_OUT = "#F2DFA7"
EDGE, TXT = "#3A3A3A", "#1A1A1A"


def box(ax, x, y, w, h, t, c, fs=7.4, bold=False, lw=0.9, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.012",
                                lw=lw, edgecolor=EDGE, facecolor=c, zorder=2, linestyle=ls))
    ax.text(x + w/2, y + h/2, t, ha="center", va="center", fontsize=fs, color=TXT,
            zorder=3, fontweight="bold" if bold else "normal", linespacing=1.35)


def arr(ax, x1, y1, x2, y2, ls="-", lw=1.0, col=None):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=10,
                                 lw=lw, color=col or EDGE, linestyle=ls, zorder=4,
                                 shrinkA=3, shrinkB=3))


fig, ax = plt.subplots(figsize=(7.8, 5.4))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.text(0.5, 0.988, "Where SWCL attaches: read-only, downstream of the flow computer",
        ha="center", va="top", fontsize=10.5, fontweight="bold", color=TXT)

# ---------------------------------------------------------------- the pipe run
ax.add_patch(Rectangle((0.06, 0.72), 0.88, 0.058, facecolor="#E8E8E8",
                       edgecolor=EDGE, lw=1.0, zorder=1))
ax.text(0.075, 0.749, "gas", fontsize=7, va="center", color="#555")
arr(ax, 0.10, 0.749, 0.16, 0.749, lw=1.4)
# orifice plate
ax.add_patch(Rectangle((0.404, 0.706), 0.010, 0.090, facecolor="#8A8A8A",
                       edgecolor=EDGE, lw=0.8, zorder=3))
ax.text(0.409, 0.812, "orifice plate", fontsize=6.8, ha="center", color="#333")
for x, lab in ((0.34, "upstream tap"), (0.47, "downstream tap"), (0.60, "P, T")):
    ax.plot([x, x], [0.778, 0.806], color=EDGE, lw=0.8, zorder=3)
    ax.text(x, 0.690, lab, fontsize=6.4, ha="center", va="top", color="#333")
    ax.plot([x, x], [0.720, 0.700], color=EDGE, lw=0.8, zorder=3)
ax.text(0.90, 0.749, "to plant", fontsize=7, va="center", ha="right", color="#555")

# ---------------------------------------------------------- existing equipment
y1 = 0.520
box(ax, 0.055, y1, 0.25, 0.090,
    "DP, P, T transmitters\nand gas chromatograph\n(existing)", C_PROC)
box(ax, 0.375, y1, 0.25, 0.090,
    "Flow computer\nAGA 3 / 8 / 9 / 11\n(existing, untouched)", C_PROC, bold=True)
box(ax, 0.695, y1, 0.25, 0.090,
    "RTU / PLC and\nSCADA historian\n(existing)", C_PROC)
arr(ax, 0.18, 0.720, 0.18, y1 + 0.090)
arr(ax, 0.305, y1 + 0.045, 0.375, y1 + 0.045)
arr(ax, 0.625, y1 + 0.045, 0.695, y1 + 0.045)

# ------------------------------------------------------------------- the layer
y2 = 0.300
box(ax, 0.215, y2, 0.57, 0.140,
    "SWCL edge service  (new — software only)\n\n"
    "reads: raw DP, P, T, composition, meter diagnostics\n"
    "writes: nothing to the flow computer or to the process",
    C_NEW, fs=7.8, bold=True, lw=1.8)
arr(ax, 0.50, y1, 0.50, y2 + 0.140, lw=1.3)
ax.text(0.515, (y1 + y2 + 0.140) / 2, "read-only tap", fontsize=6.8,
        ha="left", va="center", color="#7A2F2F", style="italic")

# the explicit non-connection
arr(ax, 0.30, y2 + 0.140, 0.42, y1, ls=(0, (3, 2)), lw=1.0, col="#B5544E")
ax.text(0.245, 0.468, "no write path", fontsize=6.6, color="#B5544E",
        ha="center", style="italic")
ax.plot([0.352, 0.372], [0.452, 0.472], color="#B5544E", lw=1.6, zorder=6)
ax.plot([0.352, 0.372], [0.472, 0.452], color="#B5544E", lw=1.6, zorder=6)

# ------------------------------------------------------------------- outputs
y3 = 0.120
box(ax, 0.055, y3, 0.25, 0.108,
    "Custody quantity\nunchanged, straight from\nthe flow computer", C_PROC, fs=7.2)
box(ax, 0.375, y3, 0.25, 0.108,
    "SWCL parallel series\ncorrected rate, X_LM,\nuncertainty, flags", C_OUT, fs=7.2, bold=True)
box(ax, 0.695, y3, 0.25, 0.108,
    "Operator display and\nallocation system\nvia OPC-UA / Modbus TCP", C_SOFT, fs=7.2)
arr(ax, 0.82, y1, 0.82, y3 + 0.108)
arr(ax, 0.42, y2, 0.42, y3 + 0.108)
arr(ax, 0.625, y3 + 0.054, 0.695, y3 + 0.054)
arr(ax, 0.18, y1, 0.18, y3 + 0.108, ls=(0, (4, 2)))

ax.text(0.5, 0.062,
        "The custody-transfer path on the left is unaltered in Stage 1. SWCL publishes a second, "
        "fully audited series beside it.",
        ha="center", va="top", fontsize=7.2, color="#333333")

fig.savefig(os.path.join(OUT, "fig6_deployment_topology.png"), dpi=300,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print("fig6 written")
