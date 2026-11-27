"""Transforms between Polycam plan inches, scan metres and the building frame (feet, walls square to the axes)."""
import json
import math
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = 0.0254
FT = 0.3048


def load_reg(name="390"):
    return {int(k): v for k, v in json.load(open(os.path.join(HERE, "data", f"{name}_registration.json"))).items()}


def plan_to_scan(reg):
    a = math.radians(reg["rot_deg"])
    ca, sa = math.cos(a), math.sin(a)
    cx, cy = reg["centre_in"]
    tx, ty = reg["t_m"]
    s = -1 if reg["mirror"] else 1

    def f(p):
        x, y = (p[0] - cx) * IN * s, (p[1] - cy) * IN
        return (x * ca - y * sa + tx, x * sa + y * ca + ty)
    return f
