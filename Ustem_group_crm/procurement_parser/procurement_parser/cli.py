"""Command-line interface.

Example:
    python -m procurement_parser.cli input.pdf -o quotation.xlsx \\
        --product-db data/products.csv \\
        --warehouse data/warehouse.csv \\
        --purchase-history data/history.csv \\
        --supplier-prices data/suppliers.csv \\
        --template company_template.xlsx \\
        --tessdata ./tessdata --report

CSV column mapping is configurable via --col-* flags (defaults shown below fit
the bundled sample data: RU headers Наименование/Артикул/Ед./Остаток/Цена/Поставщик).
"""

from __future__ import annotations

import argparse
import logging
import sys

from .config import ParserConfig
from .pipeline import Pipeline, PipelineConfig
from .data_sources import (
    CompanyData, CsvDataSource,
    ROLE_PRODUCT_DB, ROLE_WAREHOUSE, ROLE_PURCHASE_HISTORY, ROLE_SUPPLIER_PRICES,
)


def _default_colmap(args):
    return {
        "name": args.col_name,
        "code": args.col_code,
        "unit": args.col_unit,
        "warehouse_quantity": args.col_qty,
        "cost_price": args.col_price,
        "supplier": args.col_supplier,
    }


def build_company_data(args) -> CompanyData:
    cm = _default_colmap(args)
    src = lambda role, path: CsvDataSource(role, path, cm) if path else None
    return CompanyData(
        product_database=src(ROLE_PRODUCT_DB, args.product_db),
        warehouse_inventory=src(ROLE_WAREHOUSE, args.warehouse),
        purchase_history=src(ROLE_PURCHASE_HISTORY, args.purchase_history),
        supplier_price_lists=src(ROLE_SUPPLIER_PRICES, args.supplier_prices),
    )


def main(argv=None):
    p = argparse.ArgumentParser(description="Intelligent PDF procurement parser")
    p.add_argument("pdf", help="input PDF path")
    p.add_argument("-o", "--output", default="quotation.xlsx")
    p.add_argument("--template", help="company quotation template (.xlsx)")
    p.add_argument("--tessdata", help="directory with *.traineddata for OCR")
    p.add_argument("--no-ocr", action="store_true", help="disable OCR")
    p.add_argument("--report", action="store_true", help="print per-page report")

    p.add_argument("--product-db")
    p.add_argument("--warehouse")
    p.add_argument("--purchase-history")
    p.add_argument("--supplier-prices")

    # CSV column names (defaults match bundled sample data)
    p.add_argument("--col-name", default="Наименование")
    p.add_argument("--col-code", default="Артикул")
    p.add_argument("--col-unit", default="Ед.")
    p.add_argument("--col-qty", default="Остаток")
    p.add_argument("--col-price", default="Цена")
    p.add_argument("--col-supplier", default="Поставщик")

    p.add_argument("--match-high", type=float, default=88.0)
    p.add_argument("--match-low", type=float, default=72.0)
    p.add_argument("-v", "--verbose", action="store_true")

    args = p.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )

    parser_cfg = ParserConfig(
        ocr_enabled=not args.no_ocr,
        match_threshold_high=args.match_high,
        match_threshold_low=args.match_low,
    )
    cfg = PipelineConfig(
        parser=parser_cfg, tessdata_dir=args.tessdata, template_path=args.template
    )
    company = build_company_data(args)
    pipeline = Pipeline(company, cfg)

    result = pipeline.run(args.pdf, args.output)

    if args.report:
        print(pipeline.page_report(result))
        print()
    print(f"Products extracted: {len(result.products)}")
    print(f"Quotation written:  {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
