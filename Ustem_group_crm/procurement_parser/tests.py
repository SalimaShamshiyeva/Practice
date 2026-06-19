"""Lightweight tests for the parser. Run: PYTHONPATH=. pytest -q (or python tests.py)."""

from procurement_parser.config import ParserConfig
from procurement_parser.text_utils import (
    map_headers, parse_quantity, normalize_name, best_canonical_field,
)
from procurement_parser.models import DetectedTable, PageCategory, MatchStatus
from procurement_parser.product_extractor import ProductExtractor
from procurement_parser.company_matcher import CompanyMatcher
from procurement_parser.data_sources import (
    CompanyData, InMemoryDataSource, CompanyRecord,
    ROLE_WAREHOUSE, ROLE_PURCHASE_HISTORY,
)

cfg = ParserConfig()


def test_header_mapping_multilingual():
    hdr = ["№", "Артикул", "Наименование", "Кол-во", "Ед.", "Price"]
    m = map_headers(hdr, cfg)
    assert m.get("item_no") == 0
    assert m.get("code") == 1
    assert m.get("name") == 2
    assert m.get("quantity") == 3
    assert m.get("unit") == 4
    assert m.get("price") == 5


def test_header_synonyms_fuzzy():
    # English equivalents and a near-miss
    assert best_canonical_field("Quantity", cfg)[0] == "quantity"
    assert best_canonical_field("Qty", cfg)[0] == "quantity"
    assert best_canonical_field("Part Number", cfg)[0] == "code"
    assert best_canonical_field("Description", cfg)[0] == "description"


def test_short_synonym_not_substring():
    # "ед" must NOT match inside the word "следует"
    assert best_canonical_field("следует", cfg)[0] != "unit"


def test_parse_quantity_formats():
    assert parse_quantity("12") == 12
    assert parse_quantity("1 500") == 1500
    assert parse_quantity("3,5") == 3.5
    assert parse_quantity("2 шт") == 2
    assert parse_quantity("") is None


def test_extract_merges_and_dedupes():
    table = DetectedTable(
        page_number=1,
        header=["№", "Наименование", "Кол-во", "Ед."],
        rows=[
            ["1", "Насос Grundfos", "2", "шт"],
            ["", "класс A", "", ""],            # continuation -> merged
            ["2", "Кран DN50", "5", "шт"],
            ["2", "Кран DN50", "5", "шт"],      # duplicate -> removed
            ["", "Итого", "", ""],              # total -> skipped
        ],
        column_map={"item_no": 0, "name": 1, "quantity": 2, "unit": 3},
        table_confidence=0.9,
    )
    products = ProductExtractor(cfg).extract([table])
    names = [p.name for p in products]
    assert len(products) == 2
    assert "класс A" in products[0].name  # continuation merged into name
    assert products[1].quantity == 5


def test_matching_status_levels():
    company = CompanyData(
        warehouse_inventory=InMemoryDataSource(ROLE_WAREHOUSE, [
            CompanyRecord(name="Насос циркуляционный Grundfos UPS 25-60",
                          code="GR-25-60", warehouse_quantity=10, cost_price=18000,
                          supplier="Grundfos RU"),
        ]),
        purchase_history=InMemoryDataSource(ROLE_PURCHASE_HISTORY, [
            CompanyRecord(name="Автоматический выключатель ABB S203 C16",
                          code="ABB-S203-C16", cost_price=1450, supplier="ABB"),
        ]),
    )
    matcher = CompanyMatcher(cfg, company)
    from procurement_parser.models import Product

    on_stock = matcher.match(Product(name="Насос циркуляционный Grundfos UPS 25-60"))
    assert on_stock.status == MatchStatus.ON_STOCK
    assert on_stock.cost_price == 18000

    prev = matcher.match(Product(name="Выключатель автоматический ABB S203 C16"))
    assert prev.status == MatchStatus.PREVIOUSLY_PURCHASED

    new = matcher.match(Product(name="Совершенно неизвестный артикул XYZ"))
    assert new.status == MatchStatus.NEW_PRODUCT
    assert new.cost_price is None  # never invents a price


def test_processable_categories():
    assert PageCategory.EQUIPMENT_SPECIFICATION.is_processable
    assert PageCategory.BILL_OF_MATERIALS.is_processable
    assert PageCategory.PRODUCT_TABLE.is_processable
    assert PageCategory.PRICE_TABLE.is_processable
    assert not PageCategory.COVER_PAGE.is_processable
    assert not PageCategory.DRAWINGS.is_processable


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} tests passed")
