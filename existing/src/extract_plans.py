"""Read a Polycam floor-plan DXF (inches) into plain JSON: rooms, walls, doors, windows, openings, fixtures per floor."""
import json
import re
import sys

import ezdxf
from shapely.geometry import Point, Polygon


def pts(e):
    return [(round(float(p[0]), 2), round(float(p[1]), 2)) for p in e.get_points()]


def main(dxf_path, out_path):
    doc = ezdxf.readfile(dxf_path)
    floors = {}
    for e in doc.modelspace():
        m = re.match(r"Polycam-Floor_(\d+)-(.+)", e.dxf.layer)
        if not m:
            continue
        f = floors.setdefault(int(m.group(1)), dict(rooms=[], walls=[], doors=[], windows=[], openings=[], fixtures=[], appliances=[],
                                                    furniture=[], labels=[], areas=[], door_arcs=[]))
        kind, t = m.group(2), e.dxftype()
        if t == "LWPOLYLINE":
            p = pts(e)
            key = {"Floors": "rooms", "Walls": "walls", "Openings-Doors": "doors", "Openings-Windows": "windows", "Openings-Openings": "openings",
                   "Objects-Fixtures": "fixtures", "Objects-Appliances": "appliances", "Objects-Furniture": "furniture"}.get(kind)
            if key:
                f[key].append(dict(pts=p, closed=bool(e.closed)))
        elif t == "MTEXT" and kind in ("Labels-Rooms", "Labels-Areas"):
            f["labels" if kind == "Labels-Rooms" else "areas"].append(dict(text=e.plain_text().strip(), at=(round(e.dxf.insert.x, 2), round(e.dxf.insert.y, 2))))
        elif t == "ELLIPSE" and kind == "Openings-Doors":
            c = e.dxf.center
            f["door_arcs"].append(dict(center=(round(c.x, 2), round(c.y, 2)), major=(round(e.dxf.major_axis.x, 2), round(e.dxf.major_axis.y, 2)),
                                       ratio=e.dxf.ratio, start=e.dxf.start_param, end=e.dxf.end_param))
    # name the rooms from the label that falls inside each polygon
    for n, f in floors.items():
        for r in f["rooms"]:
            poly = Polygon(r["pts"]).buffer(0)
            inside = [l for l in f["labels"] if poly.contains(Point(l["at"]))]
            near = min(f["labels"], key=lambda l: poly.distance(Point(l["at"]))) if f["labels"] else None
            lab = inside[0] if inside else near
            r["name"] = lab["text"] if lab else "?"
            r["area_sf"] = round(poly.area / 144, 1)
    json.dump({str(k): v for k, v in sorted(floors.items())}, open(out_path, "w"))
    for n, f in sorted(floors.items()):
        print("floor", n, {k: len(v) for k, v in f.items()}, "| rooms:", ", ".join(f"{r['name']} {r['area_sf']}" for r in f["rooms"])[:300])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
