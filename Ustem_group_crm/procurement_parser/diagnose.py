"""Diagnostic dump: shows, for each page, what the table detector sees and
why it accepts or rejects the page as a product table.

Usage:
    python3 diagnose.py "path/to/your.pdf" > diag_output.txt

Then send diag_output.txt back. It contains ONLY structural info (header rows,
column counts, why a page was accepted/rejected) -- enough to fix the parser.
"""
import sys
import pdfplumber

from procurement_parser.config import ParserConfig
from procurement_parser.text_utils import map_headers, normalize_ws

cfg = ParserConfig()

_LINES = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
_TEXT = {"vertical_strategy": "text", "horizontal_strategy": "text"}


def extract_tables(page):
    for settings in (_LINES, _TEXT):
        try:
            found = page.extract_tables(settings)
        except Exception:
            found = []
        cleaned_tables = []
        for t in found or []:
            cleaned = [[normalize_ws(c) if c else "" for c in row] for row in t]
            cleaned = [r for r in cleaned if any(c for c in r)]
            if len(cleaned) >= 2 and max((len(r) for r in cleaned), default=0) >= 2:
                cleaned_tables.append(cleaned)
        if cleaned_tables:
            return cleaned_tables
    return []


def main():
    if len(sys.argv) < 2:
        print("usage: python3 diagnose.py file.pdf")
        return 1
    path = sys.argv[1]
    pdf = pdfplumber.open(path)
    print(f"TOTAL PAGES: {len(pdf.pages)}")
    print(f"header_fuzzy_threshold = {cfg.header_fuzzy_threshold}")
    print("=" * 70)

    for i, page in enumerate(pdf.pages):
        pnum = i + 1
        tables = extract_tables(page)
        if not tables:
            print(f"\nPAGE {pnum}: no raw tables")
            continue

        for ti, raw in enumerate(tables):
            width = max(len(r) for r in raw)
            grid = [r + [""] * (width - len(r)) for r in raw]
            print(f"\nPAGE {pnum} table[{ti}]: {len(grid)} rows x {width} cols")

            # try to find best header in first 4 rows
            best_map, best_idx, best_count = {}, 0, -1
            for hidx in range(min(8, len(grid))):
                cmap = map_headers(grid[hidx], cfg)
                if len(cmap) > best_count:
                    best_count, best_map, best_idx = len(cmap), cmap, hidx

            # show the first 4 rows raw (these contain the header)
            for r in range(min(8, len(grid))):
                cells = [c[:22] for c in grid[r]]
                print(f"   row{r}: {cells}")

            print(f"   --> best header row index: {best_idx}")
            print(f"   --> mapped columns: {best_map}")

            has_identity = ("name" in best_map) or ("description" in best_map)
            if not best_map:
                print("   --> REJECTED: no columns recognized")
            elif not has_identity or len(best_map) < 2:
                print(f"   --> REJECTED: needs identity + 1 more (have {list(best_map)})")
            else:
                print("   --> ACCEPTED as product table")

    return 0


if __name__ == "__main__":
    sys.exit(main())
