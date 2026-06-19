"""End-to-end demo: analyze the sample PDF and produce a quotation."""

import os
import logging

from procurement_parser import Pipeline, PipelineConfig
from procurement_parser.config import ParserConfig
from procurement_parser.data_sources import (
    CompanyData, CsvDataSource,
    ROLE_PRODUCT_DB, ROLE_WAREHOUSE, ROLE_PURCHASE_HISTORY, ROLE_SUPPLIER_PRICES,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "sample_data")

# CSV column mapping (matches the bundled RU sample data).
COLMAP = {
    "name": "Наименование", "code": "Артикул", "unit": "Ед.",
    "warehouse_quantity": "Остаток", "cost_price": "Цена", "supplier": "Поставщик",
}
# purchase/product/supplier files have no "Остаток" column -> qty stays None there.


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    company = CompanyData(
        product_database=CsvDataSource(
            ROLE_PRODUCT_DB, os.path.join(DATA, "product_database.csv"), COLMAP),
        warehouse_inventory=CsvDataSource(
            ROLE_WAREHOUSE, os.path.join(DATA, "warehouse_inventory.csv"), COLMAP),
        purchase_history=CsvDataSource(
            ROLE_PURCHASE_HISTORY, os.path.join(DATA, "purchase_history.csv"), COLMAP),
        supplier_price_lists=CsvDataSource(
            ROLE_SUPPLIER_PRICES, os.path.join(DATA, "supplier_price_lists.csv"), COLMAP),
    )

    cfg = PipelineConfig(
        parser=ParserConfig(),
        tessdata_dir=os.path.join(ROOT, "..", "tessdata"),  # for OCR if needed
    )

    pipeline = Pipeline(company, cfg)
    pdf = os.path.join(HERE, "sample_engineering.pdf")
    out = os.path.join(HERE, "quotation_demo.xlsx")
    result = pipeline.run(pdf, out)

    print("\n=== PAGE ANALYSIS / CLASSIFICATION ===")
    print(pipeline.page_report(result))

    print("\n=== EXTRACTED PRODUCTS & MATCHES ===")
    for m in result.matches:
        p = m.product
        qty = f"{p.quantity:g}" if p.quantity is not None else "?"
        print(f"{m.status.emoji} {p.name[:42]:<42} qty={qty:<5} {p.unit:<4} "
              f"-> {m.status.value:<20} "
              f"cost={m.cost_price if m.cost_price is not None else '-'} "
              f"sup={m.supplier or '-'}")
    print(f"\nQuotation: {out}")


if __name__ == "__main__":
    main()
