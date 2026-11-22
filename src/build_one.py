"""Build the sheets of one module for review: python3 build_one.py sheets_p [P-101 ...]"""
import importlib
import os
import sys
import warnings

from matplotlib.backends.backend_pdf import PdfPages

warnings.filterwarnings("ignore")
import model as m  # noqa: E402

m.check()
mod = importlib.import_module(sys.argv[1])
only = set(sys.argv[2:])
with PdfPages(os.devnull) as pdf:
    for number, fn in mod.SHEETS:
        if only and number not in only:
            continue
        fn(pdf)
        print("built", number)
