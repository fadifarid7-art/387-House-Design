"""Assemble the 390 Forest Ave builder set: existing/drawings/390-Forest_Builder-Set.pdf"""
import importlib
import os
import sys
import warnings

from matplotlib.backends.backend_pdf import PdfPages

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build390 as b  # noqa: E402
import b390_g as g  # noqa: E402

fns = {n: f for n, _t, f in g.SHEETS}
fns.update({n: f for n, _t, f in b.SHEETS_A})
for mod in ("b390_e", "b390_m", "b390_p"):
    try:
        m = importlib.import_module(mod)
        fns.update({n: f for n, _t, f in m.SHEETS})
    except ModuleNotFoundError:
        print("not built yet:", mod)
out = os.path.join(b.HERE, "drawings", "390-Forest_Builder-Set.pdf")
done = []
with PdfPages(out) as pdf:
    for n, _t in g.INDEX:
        if n in fns:
            fns[n](pdf); done.append(n)
    d = pdf.infodict(); d["Title"] = "390 Forest Ave, Morgantown WV: builder set, 8 bedrooms 7 baths"
print("wrote", out, len(done), "sheets;", "missing:", [n for n, _ in g.INDEX if n not in fns])
