"""Measure 390 Forest from the 3D scan: per-room ceiling heights, attic headroom, window sills, partition thickness,
true north, and the transform that stacks every floor in one building frame. Writes data/390_fixed.json."""
import json
import math
import sys

import laspy
import numpy as np
from matplotlib.path import Path
from shapely.geometry import Polygon

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from xform import IN, FT, load_reg, plan_to_scan  # noqa: E402

LOCAL, GEO, PLAN, OUT = sys.argv[1:5]
las = laspy.read(LOCAL)
X, Y, Z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
plan = json.load(open(PLAN))
reg = load_reg()
out = dict(floors={}, notes={})


def R(a, p):
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


# ---- true north in the scan frame, from the geo-referenced copy of the same points ----
g = laspy.read(GEO)
idx = np.arange(0, len(X), 997)
lon, lat = np.asarray(g.x)[idx], np.asarray(g.y)[idx]
e = (lon - lon.mean()) * 111320 * math.cos(math.radians(lat.mean()))
n = (lat - lat.mean()) * 110950
A = np.column_stack([X[idx] - X[idx].mean(), Y[idx] - Y[idx].mean()])
M, *_ = np.linalg.lstsq(A, np.column_stack([e, n]), rcond=None)       # [x y] @ M = [e n]
north_scan = np.linalg.solve(M.T, np.array([0.0, 1.0]))               # scan-frame vector that points north
north_scan /= np.linalg.norm(north_scan)

# ---- building frame: floor 5 squared, origin at its lower-left outside corner, feet ----
th5 = math.radians(reg[5]["rot_deg"])
T5 = plan_to_scan(reg[5])
P5 = np.array([R(-th5, T5(q)) for w in plan["5"]["walls"] for q in w["pts"]])
org = P5.min(0)
NEXT = {3: reg[4]["z_floor"], 4: reg[5]["z_floor"], 5: reg[6]["z_floor"]}
twist = {3: 12.0, 4: -0.5, 5: 0.0, 6: 1.0}       # degrees each floor is turned back to sit square (3 = scan stitching error)


def to_building(fl):
    T = plan_to_scan(reg[fl])
    pts = np.array([R(-th5, T(q)) for w in plan[str(fl)]["walls"] for q in w["pts"]])
    c = pts.mean(0)
    a = math.radians(twist[fl])

    def f(p):
        q = np.array(R(-th5, T(p))) - c
        q = np.array(R(a, q)) + c - org
        return (float(q[0] / FT), float(q[1] / FT))
    return f


shift = {}
ref = None
for fl in (5, 4, 6, 3):
    f = to_building(fl)
    B = np.array([f(q) for w in plan[str(fl)]["walls"] for q in w["pts"]])
    if fl == 5:
        ref = (B.min(0), B.max(0))
        shift[fl] = (0.0, 0.0)
    elif fl == 3:
        # the lowest flat is twisted 12 deg in the scan: seat it on the footprint by matching the outline's centre
        shift[fl] = tuple(((ref[0] + ref[1]) / 2 - (B.min(0) + B.max(0)) / 2).tolist())
    else:
        shift[fl] = (0.0, 0.0)
    print("floor", fl, "building-frame extents ft: x %.1f..%.1f y %.1f..%.1f  size %.1f x %.1f  shift %s" % (
        B[:, 0].min() + shift[fl][0], B[:, 0].max() + shift[fl][0], B[:, 1].min() + shift[fl][1], B[:, 1].max() + shift[fl][1],
        np.ptp(B[:, 0]), np.ptp(B[:, 1]), np.round(shift[fl], 2)))
nb = R(-th5, north_scan)
out["north_in_building_frame"] = [float(nb[0]), float(nb[1])]
out["twist_deg"] = twist
out["origin_scan_m"] = org.tolist()
out["th5_deg"] = reg[5]["rot_deg"]
out["shift_ft"] = {str(k): v for k, v in shift.items()}


def in_poly(poly_scan, shrink=0.2):
    p = Polygon(poly_scan).buffer(0).buffer(-shrink)
    if p.is_empty:
        p = Polygon(poly_scan).buffer(0)
    if p.geom_type == "MultiPolygon":
        p = max(p.geoms, key=lambda g_: g_.area)
    x0, y0, x1, y1 = p.bounds
    m = (X > x0) & (X < x1) & (Y > y0) & (Y < y1)
    ii = np.where(m)[0]
    ok = Path(np.array(p.exterior.coords)).contains_points(np.column_stack([X[ii], Y[ii]]))
    return ii[ok]


def peak(zs, lo, hi):
    h, e_ = np.histogram(zs, bins=np.arange(lo, hi + 0.02, 0.02))
    if h.sum() == 0:
        return None, 0
    i = int(np.argmax(h))
    return float(e_[i] + 0.01), int(h[i])


for fl in (3, 4, 5, 6):
    T = plan_to_scan(reg[fl])
    z0 = reg[fl]["z_floor"]
    rooms = []
    for r in plan[str(fl)]["rooms"]:
        ii = in_poly([T(q) for q in r["pts"]])
        zs = Z[ii]
        zf, nf = peak(zs, z0 - 0.12, z0 + 0.14)
        if fl == 6:
            # sloped ceiling: grid the top surface
            xs, ys = X[ii], Y[ii]
            gx = np.floor(xs / 0.25).astype(int); gy = np.floor(ys / 0.25).astype(int)
            top = {}
            sel = zs > (zf or z0) + 1.2
            for a_, b_, c_ in zip(gx[sel], gy[sel], zs[sel]):
                k = (a_, b_)
                if c_ > top.get(k, -99):
                    top[k] = c_
            hts = np.array(list(top.values())) - (zf or z0)
            hts = hts[(hts > 1.2) & (hts < 3.2)]
            rooms.append(dict(name=r["name"], floor_z=zf, ceil_min_ft=float(np.percentile(hts, 5) / FT) if len(hts) else None,
                              ceil_max_ft=float(np.percentile(hts, 95) / FT) if len(hts) else None,
                              share_7ft=float((hts >= 7 * FT).mean()) if len(hts) else None,
                              cells=[[float(k[0] * 0.25 + 0.125), float(k[1] * 0.25 + 0.125), float(v - (zf or z0))] for k, v in top.items()]))
        else:
            # ceiling = the highest strong flat surface below the next floor level
            zn = NEXT[fl] - 0.12
            base = zf if zf is not None else z0
            h, e_ = np.histogram(zs, bins=np.arange(base + 1.8, zn + 0.02, 0.02))
            zc = None
            if h.sum() > 200:
                strong = np.where(h >= 0.4 * h.max())[0]
                zc = float(e_[strong.max()] + 0.01)
            rooms.append(dict(name=r["name"], floor_z=zf, ceil_ft=(zc - base) / FT if zc else None, pts=int(len(ii))))
    # windows: sill and head from the gap in wall returns
    wins = []
    W = plan[str(fl)]["windows"]
    for w in W:
        q = np.array([T(p) for p in w["pts"]])
        if len(q) < 4:
            continue
        poly = Polygon(q).buffer(0)
        if poly.area < 0.02:
            continue
        ii = in_poly(np.array(poly.buffer(0.10).exterior.coords), shrink=0.0)
        zs = Z[ii] - z0
        h, e_ = np.histogram(zs, bins=np.arange(0.0, 2.6, 0.05))
        base = np.median(h[2:9]) if len(h) > 9 else 0
        sill = head = None
        if base > 5:
            low = h < 0.35 * base
            run = 0
            for i in range(6, len(h)):
                run = run + 1 if low[i] else 0
                if run >= 8 and sill is None:
                    sill = float(e_[i - run + 1])
                if sill is not None and not low[i] and e_[i] - sill > 0.5:
                    head = float(e_[i])
                    break
        mrr = poly.minimum_rotated_rectangle.exterior.coords
        L = max(math.dist(mrr[0], mrr[1]), math.dist(mrr[1], mrr[2]))
        wins.append(dict(centre_scan=[float(poly.centroid.x), float(poly.centroid.y)], width_in=L / IN, sill_in=sill / IN if sill else None,
                         head_in=head / IN if head else None, n=int(len(ii))))
    # partition thickness: walls with scan returns on both faces
    th = []
    for w in plan[str(fl)]["walls"]:
        q = np.array([T(p) for p in w["pts"]])
        if len(q) != 5 and len(q) != 4:
            continue
        mr = Polygon(q).buffer(0).minimum_rotated_rectangle
        c = list(mr.exterior.coords)
        e1, e2 = math.dist(c[0], c[1]), math.dist(c[1], c[2])
        if max(e1, e2) < 1.5 or min(e1, e2) > 0.3:
            continue
        a_, b_ = (c[0], c[1]) if e1 > e2 else (c[1], c[2])
        u = np.array([b_[0] - a_[0], b_[1] - a_[1]]); u /= np.linalg.norm(u)
        nrm = np.array([-u[1], u[0]]); ctr = np.array(mr.centroid.coords[0])
        ii = in_poly(np.array(mr.buffer(0.3).exterior.coords), shrink=0.0)
        sel = (Z[ii] > z0 + 1.0) & (Z[ii] < z0 + 1.8)
        d = (np.column_stack([X[ii][sel], Y[ii][sel]]) - ctr) @ nrm
        s = (np.column_stack([X[ii][sel], Y[ii][sel]]) - ctr) @ u
        d = d[np.abs(s) < max(e1, e2) / 2 - 0.3]
        if len(d) < 400:
            continue
        h, e_ = np.histogram(d, bins=np.arange(-0.3, 0.3, 0.01))
        neg, pos = h[:30], h[30:]
        if neg.max() > 60 and pos.max() > 60:
            t = (e_[30 + int(np.argmax(pos))] + 0.005) - (e_[int(np.argmax(neg))] + 0.005)
            if 0.06 < t < 0.3:
                th.append(float(t / IN))
    out["floors"][str(fl)] = dict(rooms=rooms, windows=wins, partition_in=th)
    print("floor", fl, "| ceilings:", ", ".join("%s %s" % (r["name"], ("%.1f" % r["ceil_ft"]) if r.get("ceil_ft") else (("%.1f-%.1f (%.0f%% >=7ft)" % (r["ceil_min_ft"], r["ceil_max_ft"], 100 * r["share_7ft"])) if r.get("ceil_max_ft") else "?")) for r in rooms))
    print("     windows (width, sill, head in.):", [(round(w["width_in"]), round(w["sill_in"]) if w["sill_in"] else None, round(w["head_in"]) if w["head_in"] else None) for w in wins])
    print("     partition thickness in.: n=%d median %.1f" % (len(th), np.median(th) if th else 0), [round(t, 1) for t in th][:14])
json.dump(out, open(OUT, "w"))
print("north in building frame:", np.round(nb, 3))
