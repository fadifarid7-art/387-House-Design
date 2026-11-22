"""Build the 387 Baird St head-start set (Rev E): drawings/387-Baird-St_Permit-Head-Start-Set.pdf + PNG sheets."""
import glob
import importlib
import os
import warnings

from matplotlib.backends.backend_pdf import PdfPages

warnings.filterwarnings("ignore")
import model as m  # noqa: E402
from common import ROOT  # noqa: E402
from index import INDEX  # noqa: E402

m.check()            # stops here if furniture, doors, fixtures or setbacks do not fit
OUT_PDF = os.path.join(ROOT, "drawings", "387-Baird-St_Permit-Head-Start-Set.pdf")
TMP = OUT_PDF + ".tmp"
mods, fns = {}, {}
for number, title, mod in INDEX:
    if mod not in mods:
        mods[mod] = importlib.import_module(mod)
        fns.update(dict(mods[mod].SHEETS))
missing = [n for n, _, _ in INDEX if n not in fns]
if missing:
    raise SystemExit(f"sheets without a drawing function: {missing}")
for f in glob.glob(os.path.join(ROOT, "drawings", "png", "*.png")):
    os.remove(f)
with PdfPages(TMP) as pdf:
    for number, title, mod in INDEX:
        fns[number](pdf)
    d = pdf.infodict()
    d["Title"] = "387 Baird Street, Morgantown WV: two-family dwelling head-start set, Rev E"
    d["Subject"] = "Preliminary, not for construction"
os.replace(TMP, OUT_PDF)
print("wrote", OUT_PDF, len(INDEX), "sheets")
