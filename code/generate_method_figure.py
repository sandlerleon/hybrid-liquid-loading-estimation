# -*- coding: utf-8 -*-
"""Figure 1 for the journal manuscript: the estimation and decision flow.
Deliberately simpler than the industrial deployment diagram; this one shows the
method, not the installation."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.dirname(os.path.abspath(__file__))
C_IN, C_EST, C_FUSE, C_DEC, C_OUT = "#DCE3EC", "#CFE0D2", "#E8BFBF", "#EFE1C9", "#F2DFA7"
EDGE, TXT = "#3A3A3A", "#1A1A1A"


def box(ax, x, y, w, h, t, c, fs=7.8, bold=False, lw=0.9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.010,rounding_size=0.015",
                                lw=lw, edgecolor=EDGE, facecolor=c, zorder=2))
    ax.text(x + w/2, y + h/2, t, ha="center", va="center", fontsize=fs, color=TXT,
            zorder=3, fontweight="bold" if bold else "normal", linespacing=1.35)


def arr(ax, x1, y1, x2, y2, lw=1.0, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=10,
                                 lw=lw, color=EDGE, linestyle=ls, zorder=4,
                                 shrinkA=3, shrinkB=3))


fig, ax = plt.subplots(figsize=(7.4, 7.6))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

# inputs
yA = 0.905
box(ax, 0.045, yA, 0.28, 0.070, "Gas composition $z$\nPressure $P$, Temperature $T$", C_IN, fs=7.4)
box(ax, 0.675, yA, 0.28, 0.070, "Meter signals\n$\\Delta P$, $\\sigma_{\\Delta P}$, PLR, $Q_{ind}$", C_IN, fs=7.4)

# estimators
yB = 0.760
box(ax, 0.045, yB, 0.28, 0.082,
    "Thermodynamic estimator\n$X^{(1)}=f_{EOS}(P,T,z)$\nEOS flash", C_EST, fs=7.4)
box(ax, 0.675, yB, 0.28, 0.082,
    "Diagnostic estimator\n$X^{(2)}=f_\\theta(\\mathbf{x})$\nfitted mapping", C_EST, fs=7.4)
arr(ax, 0.185, yA, 0.185, yB + 0.082)
arr(ax, 0.815, yA, 0.815, yB + 0.082)

ax.text(0.185, yB - 0.022, "$X^{(1)},\\ \\sigma_1$", ha="center", fontsize=7.6)
ax.text(0.815, yB - 0.022, "$X^{(2)},\\ \\sigma_2$", ha="center", fontsize=7.6)

# reference calibration, feeding the estimators rather than the real-time path
box(ax, 0.375, yB, 0.25, 0.082,
    "Reference data\nseparator tests,\nallocation balance", C_IN, fs=7.4)
arr(ax, 0.375, yB + 0.041, 0.325, yB + 0.041, ls=(0, (3, 2)))
arr(ax, 0.625, yB + 0.041, 0.675, yB + 0.041, ls=(0, (3, 2)))
ax.text(0.50, yB - 0.020, "periodic calibration and drift control", ha="center",
        fontsize=6.8, style="italic", color="#555")

# fusion
yC = 0.610
box(ax, 0.230, yC, 0.54, 0.086,
    "Uncertainty-aware fusion\n"
    "$X_f$, $\\sigma_f$   and   consistency index $Z=|X^{(1)}-X^{(2)}|/\\sqrt{\\sigma_1^2+\\sigma_2^2}$",
    C_FUSE, fs=7.6, bold=True, lw=1.6)
arr(ax, 0.185, yB, 0.330, yC + 0.086, lw=1.2)
arr(ax, 0.815, yB, 0.670, yC + 0.086, lw=1.2)

# decision
yD = 0.478
box(ax, 0.330, yD, 0.34, 0.068, "Consistency test\n$Z \\leq Z_{max}$ ?", C_DEC, fs=7.8, bold=True)
arr(ax, 0.5, yC, 0.5, yD + 0.068, lw=1.2)

yE = 0.340
box(ax, 0.055, yE, 0.34, 0.072,
    "ACCEPT\napply wet-gas correction", C_EST, fs=7.6, bold=True)
box(ax, 0.610, yE, 0.34, 0.072,
    "REJECT\nreport uncorrected value,\nflag low confidence", C_FUSE, fs=7.4, bold=True)
arr(ax, 0.400, yD + 0.020, 0.225, yE + 0.072)
arr(ax, 0.600, yD + 0.020, 0.780, yE + 0.072)
ax.text(0.305, 0.432, "yes", fontsize=7.2, color="#2F5A33")
ax.text(0.672, 0.432, "no", fontsize=7.2, color="#7A2F2F")

# correction
yF = 0.206
box(ax, 0.055, yF, 0.34, 0.076,
    "Wet-gas correlation\n$Q_G = Q_{ind}\\,/\\,\\phi(X_f,\\rho_G/\\rho_L,Fr_G)$", C_OUT, fs=7.4)
arr(ax, 0.225, yE, 0.225, yF + 0.076)

yG = 0.062
box(ax, 0.155, yG, 0.69, 0.078,
    "Corrected gas rate $Q_G$  ·  expanded uncertainty $U(Q_G)$  ·  status flag",
    C_OUT, fs=8.0, bold=True)
arr(ax, 0.225, yF, 0.360, yG + 0.078)
arr(ax, 0.780, yE, 0.660, yG + 0.078)

fig.savefig(os.path.join(OUT, "figG_method.png"), dpi=300,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print("figG written")
