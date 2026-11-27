"""Line up each Polycam plan floor of 390 Forest with the matching level of the 3D scan (same building frame for all)."""
import json
import math
import sys

import laspy
import numpy as np
from matplotlib.path import Path

RES = 0.04                      # metres per pixel
LEVELS = {3: -7.08, 4: -4.23, 5: -1.56, 6: 1.35}     # plan floor -> scan floor level (z, metres)
IN = 0.0254


def raster_cloud(x, y, z, z0):
    m = (z > z0 + 1.0) & (z < z0 + 1.7)
    H, xe, ye = np.histogram2d(x[m], y[m], bins=[np.arange(-8, 10, RES), np.arange(-13, 7, RES)])
    return (H > 2).astype(np.float32), xe[0], ye[0]


def raster_plan(walls, ang, mirror, shape, org):
    """Rotate wall polygons about their centroid; return mask on a grid the size of `shape` (centre-placed)."""
    allp = np.array([p for w in walls for p in w["pts"]], float) * IN
    c = allp.mean(0)
    ca, sa = math.cos(ang), math.sin(ang)
    mask = np.zeros(shape, np.float32)
    gx, gy = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), indexing="ij")
    pix = np.column_stack([gx.ravel(), gy.ravel()])
    for w in walls:
        p = np.array(w["pts"], float) * IN - c
        if mirror:
            p[:, 0] = -p[:, 0]
        q = np.column_stack([p[:, 0] * ca - p[:, 1] * sa, p[:, 0] * sa + p[:, 1] * ca])
        q = q / RES + np.array(shape) / 2
        if len(q) < 3:
            continue
        lo = np.floor(q.min(0)).astype(int) - 1
        hi = np.ceil(q.max(0)).astype(int) + 2
        lo = np.maximum(lo, 0); hi = np.minimum(hi, shape)
        if (hi <= lo).any():
            continue
        sx, sy = np.meshgrid(np.arange(lo[0], hi[0]), np.arange(lo[1], hi[1]), indexing="ij")
        inside = Path(q).contains_points(np.column_stack([sx.ravel(), sy.ravel()]), radius=0.8).reshape(sx.shape)
        mask[lo[0]:hi[0], lo[1]:hi[1]] = np.maximum(mask[lo[0]:hi[0], lo[1]:hi[1]], inside)
    return mask, c


def best_shift(cloud, plan):
    F = np.fft.rfft2(cloud) * np.conj(np.fft.rfft2(plan))
    cc = np.fft.irfft2(F, s=cloud.shape)
    i = np.unravel_index(np.argmax(cc), cc.shape)
    return cc[i] / max(plan.sum(), 1), i


def main(laz, plan_json, out):
    las = laspy.read(laz)
    x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
    plan = json.load(open(plan_json))
    res = {}
    for fl, z0 in LEVELS.items():
        cloud, x0, y0 = raster_cloud(x, y, z, z0)
        walls = plan[str(fl)]["walls"]
        best = (-1,)
        for mirror in (False, True):
            for deg in np.arange(0, 360, 2.0):
                pm, c = raster_plan(walls, math.radians(deg), mirror, cloud.shape, None)
                s, sh = best_shift(cloud, pm)
                if s > best[0]:
                    best = (s, deg, mirror, sh)
        s, deg0, mirror, sh = best
        for deg in np.arange(deg0 - 2, deg0 + 2.01, 0.25):
            pm, c = raster_plan(walls, math.radians(deg), mirror, cloud.shape, None)
            s2, sh2 = best_shift(cloud, pm)
            if s2 > best[0]:
                best = (s2, deg, mirror, sh2)
        s, deg, mirror, sh = best
        pm, c = raster_plan(walls, math.radians(deg), mirror, cloud.shape, None)
        dx = sh[0] if sh[0] < cloud.shape[0] / 2 else sh[0] - cloud.shape[0]
        dy = sh[1] if sh[1] < cloud.shape[1] / 2 else sh[1] - cloud.shape[1]
        # plan point p (inches) -> cloud metres: R*(p*IN - c) (mirrored first) + t
        t = (x0 + (cloud.shape[0] / 2 + dx) * RES, y0 + (cloud.shape[1] / 2 + dy) * RES)
        res[fl] = dict(z_floor=z0, rot_deg=float(deg), mirror=bool(mirror), centre_in=[float(c[0] / IN), float(c[1] / IN)], t_m=[float(t[0]), float(t[1])], score=float(s))
        print("plan floor", fl, "-> scan level z=%.2f: rotate %.2f deg, mirror %s, overlap score %.2f" % (z0, deg, mirror, s))
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:4])
