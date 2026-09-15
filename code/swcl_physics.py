# -*- coding: utf-8 -*-
"""Shared wet-gas physics: real-gas density and wet-gas over-reading models.

Imported by swcl_monte_carlo.py and worked_example.py so both use identical
physics.
"""
import numpy as np


# ----------------------------------------------------------------- constants
R = 8.314462618          # J/(mol K)
PSI_PER_KGCM2 = 14.2233
BAR_PER_KGCM2 = 0.980665

# Challenge operating envelope
P_KGCM2 = (60.0, 85.0)
T_C = (30.0, 60.0)

# Representative rich gas meeting the challenge's "wet gas" thresholds
# (C3 > 4%, total C4 > 1%, total C5 > 0.3%, C6+ > 0.2%)
MW_GAS = 20.3e-3         # kg/mol
GAMMA_G = MW_GAS / 28.96e-3
RHO_L = (640.0, 720.0)   # condensate density, kg/m3


# ------------------------------------------------------- compressibility (DAK)
def z_dak(ppr, tpr, iters=60):
    """Dranchuk-Abou-Kassem Z-factor, vectorised fixed-point solution."""
    A = (0.3265, -1.0700, -0.5339, 0.01569, -0.05165,
         0.5475, -0.7361, 0.1844, 0.1056, 0.6134, 0.7210)
    z = np.full_like(ppr, 0.9)
    for _ in range(iters):
        rr = 0.27 * ppr / (z * tpr)
        z_new = (1.0
                 + (A[0] + A[1]/tpr + A[2]/tpr**3 + A[3]/tpr**4 + A[4]/tpr**5) * rr
                 + (A[5] + A[6]/tpr + A[7]/tpr**2) * rr**2
                 - A[8] * (A[6]/tpr + A[7]/tpr**2) * rr**5
                 + A[9] * (1.0 + A[10]*rr**2) * (rr**2 / tpr**3) * np.exp(-A[10]*rr**2))
        z = 0.5 * z + 0.5 * z_new          # damped for stability
    return z


def gas_density(p_pa, t_k):
    """Real-gas density via Standing pseudo-criticals + DAK."""
    tpc_r = 168.0 + 325.0*GAMMA_G - 12.5*GAMMA_G**2     # deg R
    ppc_psia = 677.0 + 15.0*GAMMA_G - 37.5*GAMMA_G**2   # psia
    tpr = (t_k * 9.0/5.0) / tpc_r
    ppr = (p_pa / 6894.757) / ppc_psia
    z = z_dak(ppr, tpr)
    return p_pa * MW_GAS / (z * R * t_k), z


# --------------------------------------------------- wet-gas over-reading models
def phi_chisholm(X, rho_g, rho_l, n=0.25):
    """Chisholm two-phase multiplier -- orifice plate (AGA 3)."""
    C = (rho_l/rho_g)**n + (rho_g/rho_l)**n
    return np.sqrt(1.0 + C*X + X**2)


def phi_deleeuw(X, rho_g, rho_l, fr_g):
    """de Leeuw venturi correlation, Froude-number dependent exponent."""
    n = np.where(fr_g < 1.5, 0.41, 0.606*(1.0 - np.exp(-0.746*fr_g)))
    C = (rho_l/rho_g)**n + (rho_g/rho_l)**n
    return np.sqrt(1.0 + C*X + X**2)


def phi_ultrasonic(X):
    """USM (AGA 9) wet-gas over-reading.

    Liquid holdup reduces the open area seen by the acoustic paths and the
    film drags the near-wall chords. Published loop data show an approximately
    linear rise in indicated gas velocity with X over the wet-gas region, with
    materially more scatter than a DP meter because the response is
    path-geometry dependent.
    """
    return 1.0 + 1.10 * X


def phi_coriolis(X, rho_g, rho_l):
    """Coriolis (AGA 11) gas-rate error when total mass is split using the
    indicated mixture density. The meter reads total mass well; the error is
    dominated by resolving the liquid fraction from the density reading."""
    mr = X * np.sqrt(rho_l/rho_g)          # liquid/gas mass ratio
    return 1.0 + mr


