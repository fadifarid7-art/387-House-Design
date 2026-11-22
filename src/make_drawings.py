"""Build the 387 Baird St concept drawing set: drawings/387-Baird-St_Concept-Set.pdf + PNG sheets."""
import os
from matplotlib.backends.backend_pdf import PdfPages

import building_sheets as b
import cover_sheet as c
import site_sheets as s
from common import ROOT

OUT = os.path.join(ROOT, "drawings", "387-Baird-St_Concept-Set.pdf")
TMP = OUT + ".tmp"
with PdfPages(TMP) as pdf:
    # site sheets first to obtain computed metrics, cover is re-ordered below
    with PdfPages(os.devnull) as scratch:
        m = s.sheet_c102(scratch)
    c.sheet_g001(pdf, m)
    s.sheet_c101(pdf)
    s.sheet_c102(pdf)
    b.sheet_a101(pdf)
    b.sheet_a102(pdf)
    b.sheet_a103(pdf)
    b.sheet_a201(pdf)
    b.sheet_a301(pdf)
    b.sheet_a401(pdf)
    d = pdf.infodict()
    d["Title"] = "387 Baird Street, Morgantown WV: concept drawing set"
    d["Subject"] = "Feasibility concept, not for construction"
os.replace(TMP, OUT)
print("wrote", OUT, m)
