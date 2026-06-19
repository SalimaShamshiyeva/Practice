"""Step 4 - Extract products.

For each detected product table: read cells by their canonical role, merge
multiline / continuation rows, drop section headers and totals, normalize
names, parse quantities, and remove duplicate rows.
"""

from __future__ import annotations

from .config import ParserConfig
from .models import DetectedTable, Product
from .text_utils import normalize_ws, normalize_name, parse_quantity


# Rows that are subtotals / totals / section dividers, not products.
_STOP_WORDS = (
    "итого", "всего", "total", "subtotal", "sum", "сумма прописью",
    "раздел", "section",
)


class ProductExtractor:
    def __init__(self, config: ParserConfig):
        self.config = config

    def extract(self, tables: list[DetectedTable]) -> list[Product]:
        products: list[Product] = []
        for table in tables:
            if not table.is_product_table:
                continue
            products.extend(self._extract_from_table(table))
        return self._dedupe(products)

    # ------------------------------------------------------------------ #
    def _extract_from_table(self, table: DetectedTable) -> list[Product]:
        cmap = table.column_map
        out: list[Product] = []

        def cell(row, field):
            idx = cmap.get(field)
            if idx is None or idx >= len(row):
                return ""
            return normalize_ws(row[idx])

        for row in table.rows:
            name = cell(row, "name")
            desc = cell(row, "description")
            code = cell(row, "code")
            qty_raw = cell(row, "quantity")
            unit = cell(row, "unit")
            item_no = cell(row, "item_no")

            joined = " ".join(c for c in row if c).lower()

            # skip total / section rows
            if any(sw in joined for sw in _STOP_WORDS) and not qty_raw:
                continue
            # skip empty rows
            if not any([name, desc, code, qty_raw]):
                continue

            quantity = parse_quantity(qty_raw)

            # Continuation row: only descriptive text, no identifiers/qty.
            is_continuation = (
                out
                and not code
                and not item_no
                and quantity is None
                and not unit
                and (bool(name) ^ bool(desc) or (name and not desc))
                and len((name + desc)) < 80
                and not name[:1].isdigit()
            )
            if is_continuation:
                prev = out[-1]
                extra = name or desc
                if extra:
                    if prev.description:
                        prev.description = normalize_name(prev.description + " " + extra)
                    elif prev.name and not desc:
                        prev.name = normalize_name(prev.name + " " + extra)
                    else:
                        prev.description = normalize_name(extra)
                continue

            # If there's no name but there is a description, promote it.
            if not name and desc:
                name, desc = desc, ""

            if not name and not code:
                continue

            out.append(
                Product(
                    name=normalize_name(name) if name else normalize_name(code),
                    description=normalize_name(desc),
                    code=code,
                    quantity=quantity,
                    unit=unit,
                    item_no=item_no,
                    source_page=table.page_number,
                    raw_row=row,
                )
            )
        return out

    @staticmethod
    def _dedupe(products: list[Product]) -> list[Product]:
        seen: set[tuple] = set()
        result: list[Product] = []
        for p in products:
            key = (
                p.name.lower(),
                p.code.lower(),
                p.unit.lower(),
                p.quantity,
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(p)
        return result
