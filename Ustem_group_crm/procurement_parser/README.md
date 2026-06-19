# Intelligent PDF Procurement Parser

A layout-independent parser that reads **any** engineering / procurement PDF —
regardless of page count, page order, layout, or language (Russian + English
out of the box) — finds the pages that actually contain equipment/product
tables, extracts the products, matches them against **your company's own data**,
and produces an Excel quotation.

It implements the full 6-step specification:

| Step | What it does | Module |
|------|--------------|--------|
| 1 | Analyze every page (table? text? OCR needed? rows/cols? keywords? graphics? procurement-confidence) | `page_analyzer.py` |
| 2 | Classify each page into one of 11 categories; only continue for the 4 procurement categories | `page_classifier.py` |
| 3 | Detect product tables by **semantic** header matching (not exact column names) | `table_detector.py` |
| 4 | Extract products — merge multiline cells, clean, dedupe, normalize names, extract qty/unit, keep descriptions | `product_extractor.py` |
| 5 | Fuzzy-match against company data → 🟢 On Stock / 🟡 Previously Purchased / 🔴 New Product | `company_matcher.py` |
| 6 | Generate the Excel quotation (your template or a styled default) | `excel_generator.py` |

## Guarantees

- **No fixed page numbers.** Pages are found by content, not position.
- **No exact-header dependency.** Headers are matched semantically/fuzzily, so
  `Наименование`, `Описание`, `Qty`, `Ед.`, `Артикул`, `Part Number`, … all map
  to the right canonical field even with typos or mixed languages.
- **Only the 4 procurement categories are processed** (Equipment Specification,
  Bill of Materials, Product Table, Price Table). Everything else (cover, TOC,
  technical description, regulations, drawings, floor plans, unknown) is ignored.
- **Never searches the internet.** There is no network code anywhere.
- **Never invents prices.** Cost/supplier/stock come *only* from your company
  data. If a product isn't found, its price is left blank.
- **Works on vector-text and scanned PDFs.** Vector tables are preferred; if a
  page is image-only, OCR (Tesseract, `rus+eng`) reconstructs the table grid.

## Install

```bash
pip install -r requirements.txt
# system dependency for scanned PDFs:
#   sudo apt-get install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

Python 3.10+ recommended.

## Quick start (CLI)

```bash
python -m procurement_parser.cli INPUT.pdf -o quotation.xlsx \
    --product-db        sample_data/product_database.csv \
    --warehouse         sample_data/warehouse_inventory.csv \
    --purchase-history  sample_data/purchase_history.csv \
    --supplier-prices   sample_data/supplier_price_lists.csv \
    --report
```

`--report` prints the per-page analysis/classification and the extracted
products with their match status.

### Mapping your CSV columns

The CSV loaders need to know which column is the name / code / unit / stock /
price / supplier. Defaults are Russian (`Наименование`, `Артикул`, `Ед.`,
`Остаток`, `Цена`, `Поставщик`); override any of them:

```bash
python -m procurement_parser.cli INPUT.pdf \
    --warehouse  warehouse.csv \
    --col-name "Item Name" --col-code "SKU" --col-unit "UOM" \
    --col-stock "On Hand" --col-price "Unit Cost" --col-supplier "Vendor"
```

### Using your own quotation template

```bash
python -m procurement_parser.cli INPUT.pdf --template my_template.xlsx -o out.xlsx
```

The generator locates the header row in your template (it recognizes
multilingual aliases for the 9 output columns) and appends rows beneath it,
preserving your styling. If no template is given, a clean styled workbook is
created with the specified columns:

> Client Product · Quantity · Unit · Analysis Result · Status ·
> Warehouse Quantity · Cost Price · Supplier · Comments

Status cells are color-coded (green / yellow / red).

## Quick start (library)

```python
from procurement_parser import Pipeline, PipelineConfig
from procurement_parser.config import ParserConfig
from procurement_parser.data_sources import CompanyData, CsvDataSource

company = CompanyData(
    product_database=CsvDataSource("sample_data/product_database.csv"),
    warehouse=CsvDataSource("sample_data/warehouse_inventory.csv"),
    purchase_history=CsvDataSource("sample_data/purchase_history.csv"),
    supplier_prices=CsvDataSource("sample_data/supplier_price_lists.csv"),
)

pipe = Pipeline(company, PipelineConfig(
    parser=ParserConfig(),                  # tune thresholds here
    tessdata_dir="/home/claude/tessdata",   # only needed for scanned PDFs
    template_path=None,                     # or "my_template.xlsx"
))

# run() performs all 6 steps and writes the Excel quotation to the output path
result = pipe.run("INPUT.pdf", "quotation.xlsx")
print(pipe.page_report(result))

for m in result.matches:
    print(m.status.emoji, m.product.name, "->", m.status.value)
```

## Plugging in real company data

`CompanyData` takes any object implementing the `CompanyDataSource` interface.
Three implementations ship:

- `CsvDataSource(path, col_map=...)` — CSV files
- `JsonDataSource(path, ...)` — JSON list of records
- `InMemoryDataSource([...])` — Python dicts (e.g. from your DB/ERP)

To connect a database or ERP, subclass `CompanyDataSource` and implement
`records()` returning `CompanyRecord(name, code, unit, stock, price, supplier,
extra)`. The matcher treats the four sources by role: warehouse stock decides
🟢 On Stock; purchase history / known catalog gives 🟡 Previously Purchased;
otherwise 🔴 New Product. Cost & supplier are filled in priority order
warehouse → catalog → purchase history → supplier price list.

## Tuning

All thresholds live in `ParserConfig` (`config.py`):

- `header_fuzzy_threshold` (82) — header→field matching strictness
- `match_threshold_high` (88) — score at/above ⇒ confident product match
- `match_threshold_low` (72) — score below ⇒ treated as New Product
- `ocr_dpi` (300), `ocr_languages` (`"rus+eng"`), text/graphics heuristics

## Scanned (OCR) PDFs

If a page has little/no selectable text, it is rasterized and OCR'd, and the
table grid is reconstructed from word bounding boxes. Recognition quality
depends on scan quality; the vector-text path is always preferred and more
reliable for quantities and dedup. Install the `rus`+`eng` tessdata and point
`--tessdata` / `tessdata_dir` at it.

## Architecture

```
PDF ─► PageAnalyzer (Step 1) ─► TableDetector (Step 3, candidate pages only)
        │                              │
        ▼                              ▼
   PageClassifier (Step 2) ──► ProductExtractor (Step 4, processable pages only)
                                       │
                                       ▼
                            CompanyMatcher (Step 5) ─► ExcelGenerator (Step 6)
```

Table detection runs before final classification so the classifier can
recognize a genuine product table; **extraction only runs on the 4 processable
categories**, satisfying "ignore all other pages."

## Run the tests / demo

```bash
PYTHONPATH=. python tests.py        # 7 unit tests
PYTHONPATH=. python examples/demo.py # end-to-end on the bundled test PDF
```

`examples/make_test_pdf.py` generates a 6-page mixed RU/EN test document
(cover, TOC, prose technical description, regulations with ГОСТ/СНиП/ISO, a
vector drawing page, and an equipment-specification table with a multiline
continuation row and a duplicate row) to exercise every stage.
