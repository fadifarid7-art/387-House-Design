"""Build the 387 Baird St head-start set (Rev D): drawings/387-Baird-St_Permit-Head-Start-Set.pdf + PNG sheets."""
import glob
import os

from matplotlib.backends.backend_pdf import PdfPages

import arch_sheets as a
import cover_sheet as c
import mep_sheets as mp
import site_sheets as s
import struct_sheets as st
from common import ROOT

OUT_PDF = os.path.join(ROOT, "drawings", "387-Baird-St_Permit-Head-Start-Set.pdf")
TMP = OUT_PDF + ".tmp"
for f in glob.glob(os.path.join(ROOT, "drawings", "png", "*.png")):
    os.remove(f)
with PdfPages(TMP) as pdf:
    with PdfPages(os.devnull) as scratch:
        m = s.sheet_c102(scratch)
    c.sheet_g001(pdf, m)
    c.sheet_g002(pdf, m)
    s.sheet_c101(pdf)
    s.sheet_c102(pdf)
    s.sheet_c103(pdf)
    for fn in (a.sheet_a101, a.sheet_a102, a.sheet_a103, a.sheet_a201, a.sheet_a301,
               st.sheet_s001, st.sheet_s101, st.sheet_s102, st.sheet_s103, st.sheet_s104, st.sheet_s301, mp.sheet_p101):
        fn(pdf)
    mp.unit_plumbing_sheet(pdf, "P-102", "A")
    mp.unit_plumbing_sheet(pdf, "P-103", "B")
    mp.sheet_p201(pdf)
    mp.sheet_m101(pdf)
    mp.unit_hvac_sheet(pdf, "M-102", "A")
    mp.unit_hvac_sheet(pdf, "M-103", "B")
    mp.sheet_e101(pdf)
    mp.unit_power_sheet(pdf, "E-102", "A")
    mp.unit_power_sheet(pdf, "E-103", "B")
    mp.sheet_e201(pdf)
    d = pdf.infodict()
    d["Title"] = "387 Baird Street, Morgantown WV: two-family dwelling head-start set, Rev D"
    d["Subject"] = "Preliminary, not for construction"
os.replace(TMP, OUT_PDF)
print("wrote", OUT_PDF, len(c.INDEX), "sheets")
