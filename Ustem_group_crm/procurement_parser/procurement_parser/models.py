"""Data models shared across the pipeline.

Everything that flows between stages is a typed dataclass so the pipeline is
inspectable at every step (useful for debugging "why was page 7 ignored?").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PageCategory(str, Enum):
    """Step 2 page categories."""

    COVER_PAGE = "Cover Page"
    TABLE_OF_CONTENTS = "Table of Contents"
    TECHNICAL_DESCRIPTION = "Technical Description"
    REGULATIONS = "Regulations"
    DRAWINGS = "Drawings"
    FLOOR_PLANS = "Floor Plans"
    EQUIPMENT_SPECIFICATION = "Equipment Specification"
    BILL_OF_MATERIALS = "Bill of Materials"
    PRODUCT_TABLE = "Product Table"
    PRICE_TABLE = "Price Table"
    UNKNOWN = "Unknown"

    @property
    def is_processable(self) -> bool:
        """Only these four categories continue past Step 2."""
        return self in {
            PageCategory.EQUIPMENT_SPECIFICATION,
            PageCategory.BILL_OF_MATERIALS,
            PageCategory.PRODUCT_TABLE,
            PageCategory.PRICE_TABLE,
        }


class MatchStatus(str, Enum):
    """Step 5 result of matching an extracted product to company data."""

    ON_STOCK = "On Stock"                      # found in warehouse inventory
    PREVIOUSLY_PURCHASED = "Previously Purchased"
    NEW_PRODUCT = "New Product"                # not found anywhere

    @property
    def emoji(self) -> str:
        return {
            MatchStatus.ON_STOCK: "\U0001F7E2",            # green
            MatchStatus.PREVIOUSLY_PURCHASED: "\U0001F7E1",  # yellow
            MatchStatus.NEW_PRODUCT: "\U0001F534",          # red
        }[self]


# Canonical column roles. Real headers (in any language) get mapped onto these.
CANONICAL_FIELDS = (
    "item_no",      # row / position number
    "code",         # article / part number / model / SKU
    "name",         # product / equipment name
    "description",  # longer description / specs
    "quantity",     # qty
    "unit",         # unit of measure
    "price",        # unit price (kept but never used to invent prices)
)


@dataclass
class PageAnalysis:
    """Step 1 output for a single page."""

    page_number: int                 # 1-based
    has_table: bool = False
    has_selectable_text: bool = False
    ocr_required: bool = False
    row_count: int = 0
    column_count: int = 0
    keyword_hits: list[str] = field(default_factory=list)
    is_mostly_graphics: bool = False
    text_char_count: int = 0
    image_area_ratio: float = 0.0    # fraction of page covered by raster images
    vector_drawing_count: int = 0
    procurement_confidence: float = 0.0   # 0..1
    text_sample: str = ""            # first ~500 chars, for classification/debug
    notes: list[str] = field(default_factory=list)


@dataclass
class DetectedTable:
    """A table found on a page, with headers mapped to canonical roles."""

    page_number: int
    header: list[str]
    rows: list[list[str]]
    # maps canonical field name -> column index in `header`/`rows`
    column_map: dict[str, int] = field(default_factory=dict)
    source: str = "vector"           # "vector" (pdfplumber) or "ocr"
    table_confidence: float = 0.0    # 0..1 that this is a real product table

    @property
    def is_product_table(self) -> bool:
        # A product table must at least identify *what* the product is.
        return ("name" in self.column_map) or ("description" in self.column_map)


@dataclass
class Product:
    """Step 4 cleaned product extracted from a table row."""

    name: str
    description: str = ""
    code: str = ""
    quantity: Optional[float] = None
    unit: str = ""
    item_no: str = ""
    source_page: int = 0
    raw_row: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    """Step 5 outcome for one product."""

    product: Product
    status: MatchStatus
    matched_name: str = ""
    similarity: float = 0.0          # 0..100 (rapidfuzz scale)
    source: str = ""                 # which company data source matched
    warehouse_quantity: Optional[float] = None
    cost_price: Optional[float] = None
    supplier: str = ""
    comments: str = ""


@dataclass
class DocumentResult:
    """Everything the pipeline learned about one PDF."""

    pdf_path: str
    page_analyses: list[PageAnalysis] = field(default_factory=list)
    page_categories: dict[int, PageCategory] = field(default_factory=dict)
    detected_tables: list[DetectedTable] = field(default_factory=list)
    products: list[Product] = field(default_factory=list)
    matches: list[MatchResult] = field(default_factory=list)

    @property
    def processable_pages(self) -> list[int]:
        return [p for p, c in self.page_categories.items() if c.is_processable]
