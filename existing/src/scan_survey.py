"""Wall-face survey from the 3D scan (used on 27 Nov 2026 to correct the middle flat's bedroom side and to check the lower flat).

The phone-scan floor plan assumes 4 in. walls and squares every room, so it can be 6 to 18 in. off where walls are thick or the scan drifted.
This reads the wall faces straight from the 3D points instead:
  1. turn one block of rooms until its walls are square to the axes (tilt() gives the angle of any wall face),
  2. slide it so two outside-wall faces sit on their plan coordinates,
  3. list the wall faces met along probe lines (hits / probes), or draw the points over the plan walls (picture).
Distances inside one room are good to about 2 in.; positions across the whole floor drift by up to about 6 in.

Input: work/lvl<level>.npz in the folder S below, made from the 3D scan by register.py / analyze_390.py (B = points in the level's plan frame,
feet; h = height above that level's floor). The scan itself is too large to keep in the repository.
"""
import os
import sys

import numpy as np

S = os.environ.get("SCAN_WORK", ".")          # folder that holds work/lvl<level>.npz
def load(fl, band=(6.2, 7.3)):
    d = np.load(f"{S}/work/lvl{fl}.npz"); B = d["B"].astype(float); h = d["h"].astype(float)
    m = (h > band[0]) & (h < band[1]); return B[m]
def rot(P, deg, piv=(0.0, 0.0)):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a); Q = P - np.array(piv)
    return np.c_[Q[:, 0] * c - Q[:, 1] * s, Q[:, 0] * s + Q[:, 1] * c] + np.array(piv)
def tilt(P, xr, yr, along="x"):
    """Angle (deg) of the wall face inside the window, from a robust line fit."""
    k = (P[:, 0] > xr[0]) & (P[:, 0] < xr[1]) & (P[:, 1] > yr[0]) & (P[:, 1] < yr[1]); Q = P[k]
    if len(Q) < 80: return None
    c = Q.mean(0); _, _, vt = np.linalg.svd(Q - c, full_matrices=False); dv = vt[0]
    for _ in range(6):
        n = np.array([-dv[1], dv[0]]); r = (Q - c) @ n; kk = np.abs(r - np.median(r)) < 0.1
        if kk.sum() < 60: break
        c = Q[kk].mean(0); _, _, vt = np.linalg.svd(Q[kk] - c, full_matrices=False); dv = vt[0]
    a = np.degrees(np.arctan2(dv[1], dv[0])) % 180
    return a if along == "x" else a - 90
def hits(P, lo, hi, a0, a1, axis):
    """Wall faces met along a probe: axis 0 = probe runs in y at x in [lo, hi]; axis 1 = probe runs in x at y in [lo, hi]."""
    u, v = (0, 1) if axis == 0 else (1, 0)
    k = (P[:, u] > lo) & (P[:, u] < hi) & (P[:, v] > a0) & (P[:, v] < a1); y = P[k, v]
    if len(y) < 30: return []
    hist, e = np.histogram(y, bins=np.arange(a0, a1 + 0.04, 0.04)); thr = max(8, 0.22 * hist.max()); out = []
    for i in np.where(hist >= thr)[0]:
        yv = e[i] + 0.02
        if out and yv - out[-1][1] <= 0.09: out[-1][1] = yv; out[-1][2] += int(hist[i]); out[-1][3] += yv * hist[i]
        else: out.append([yv, yv, int(hist[i]), yv * hist[i]])
    return [round(o[3] / o[2], 2) for o in out]


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sheetx as sx, draw_existing as de
def cloud(fl):
    d = np.load(f"{S}/work/lvl{fl}.npz"); return d["B"].astype(float), d["h"].astype(float)
def picture(name, fl, deg, sh, win, bands, scale=0.62):
    B, h = cloud(fl); G, _ = sx.regularize(de.P390[str(fl)], de.T390(fl)); x0, x1, y0, y1 = win
    fig, axs = plt.subplots(1, len(bands), figsize=(len(bands) * (x1 - x0) * scale, (y1 - y0) * scale + 0.5), dpi=100)
    if len(bands) == 1: axs = [axs]
    for ax, (a, b) in zip(axs, bands):
        k = (h > a) & (h < b); Q = rot(B[k], deg) + np.array(sh); m = (Q[:, 0] > x0) & (Q[:, 0] < x1) & (Q[:, 1] > y0) & (Q[:, 1] < y1)
        ax.scatter(Q[m, 0], Q[m, 1], c="k", s=0.35, linewidths=0)
        for w in G["walls"]:
            q = np.array(w["pts"])
            if len(q) >= 3: ax.fill(q[:, 0], q[:, 1], fc=(1, 0, 0, 0.10), ec=(1, 0, 0, 0.55), lw=0.5)
        ax.set_title(f"level {fl}, turned {deg} deg, heights {a}-{b} ft (red = phone-scan plan)", fontsize=8); ax.set_aspect("equal"); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
        ax.set_xticks(np.arange(np.ceil(x0), x1 + .01, 1)); ax.set_yticks(np.arange(np.ceil(y0), y1 + .01, 1)); ax.grid(True, lw=0.3, color="#0a0"); ax.tick_params(labelsize=6)
    fig.tight_layout(); fig.savefig(f"{S}/work/{name}.png"); plt.close(fig)
def probes(fl, deg, sh, band, xs=(), ys=(), xr=(-3, 40), yr=(-4, 32)):
    B, h = cloud(fl); k = (h > band[0]) & (h < band[1]); Q = rot(B[k], deg) + np.array(sh)
    for x in xs: print(f"   across at x {x:5.1f}: {[float(v) for v in hits(Q, x, x + 0.5, yr[0], yr[1], 0)]}")
    for y in ys: print(f"   along  at y {y:5.1f}: {[float(v) for v in hits(Q, y, y + 0.5, xr[0], xr[1], 1)]}")
