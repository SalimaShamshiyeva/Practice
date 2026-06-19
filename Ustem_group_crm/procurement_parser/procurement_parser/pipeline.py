"""The Pipeline ties the six steps together.

    Step 1  PageAnalyzer      -> analyze every page
    Step 3* TableDetector     -> detect tables on candidate pages
    Step 2  PageClassifier    -> classify pages (uses table info)
    (keep only processable categories)
    Step 4  ProductExtractor  -> extract products from processable tables
    Step 5  CompanyMatcher    -> match against company data
    Step 6  ExcelGenerator    -> write the quotation

(*Detection is computed before classification so the classifier can recognize a
real product table, but extraction only runs on processable pages.)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from .config import ParserConfig
from .models import DocumentResult, PageCategory
from .page_analyzer import PageAnalyzer
from .table_detector import TableDetector
from .page_classifier import PageClassifier
from .product_extractor import ProductExtractor
from .company_matcher import CompanyMatcher
from .excel_generator import ExcelGenerator
from .data_sources import CompanyData

logger = logging.getLogger("procurement_parser")


@dataclass
class PipelineConfig:
    parser: ParserConfig = field(default_factory=ParserConfig)
    tessdata_dir: Optional[str] = None       # dir containing *.traineddata
    template_path: Optional[str] = None      # company quotation template (.xlsx)


class Pipeline:
    def __init__(self, company_data: CompanyData, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()
        self.company_data = company_data
        cfg = self.config.parser
        td = self.config.tessdata_dir
        self.analyzer = PageAnalyzer(cfg, td)
        self.detector = TableDetector(cfg, td)
        self.classifier = PageClassifier(cfg)
        self.extractor = ProductExtractor(cfg)
        self.matcher = CompanyMatcher(cfg, company_data)
        self.excel = ExcelGenerator()

    def run(self, pdf_path: str, output_path: str) -> DocumentResult:
        result = DocumentResult(pdf_path=pdf_path)

        # --- Step 1: analyze all pages ---
        result.page_analyses = self.analyzer.analyze(pdf_path)
        logger.info("Analyzed %d pages", len(result.page_analyses))

        # --- Step 3 (pre-pass): detect tables on candidate pages ---
        candidate_pages = [
            pa.page_number
            for pa in result.page_analyses
            if pa.has_table or pa.ocr_required
        ]
        all_tables = self.detector.detect(pdf_path, candidate_pages)
        # best product table per page (for classification)
        table_by_page: dict[int, object] = {}
        for t in all_tables:
            cur = table_by_page.get(t.page_number)
            if cur is None or t.table_confidence > cur.table_confidence:
                table_by_page[t.page_number] = t

        # --- Step 2: classify every page ---
        total = len(result.page_analyses)
        for pa in result.page_analyses:
            cat = self.classifier.classify(
                pa, table_by_page.get(pa.page_number), total
            )
            result.page_categories[pa.page_number] = cat

        logger.info(
            "Processable pages: %s", result.processable_pages or "none"
        )

        # --- keep only tables on processable pages ---
        processable = set(result.processable_pages)
        result.detected_tables = [
            t for t in all_tables
            if t.page_number in processable and t.is_product_table
        ]

        # --- Step 4: extract products ---
        result.products = self.extractor.extract(result.detected_tables)
        logger.info("Extracted %d products", len(result.products))

        # --- Step 5: match against company data ---
        result.matches = self.matcher.match_all(result.products)

        # --- Step 6: generate Excel ---
        self.excel.generate(
            result.matches, output_path, self.config.template_path
        )
        logger.info("Wrote quotation: %s", output_path)
        return result

    # convenience: human-readable page report
    def page_report(self, result: DocumentResult) -> str:
        lines = ["Page  Category                  Conf  Table  Rows×Cols  OCR  KW"]
        for pa in result.page_analyses:
            cat = result.page_categories.get(pa.page_number, PageCategory.UNKNOWN)
            mark = "*" if cat.is_processable else " "
            lines.append(
                f"{pa.page_number:>3}{mark} {cat.value:<24} "
                f"{pa.procurement_confidence:>4.2f}  "
                f"{'yes' if pa.has_table else ' no':>3}  "
                f"{pa.row_count:>3}×{pa.column_count:<3}   "
                f"{'yes' if pa.ocr_required else ' no'}  "
                f"{len(pa.keyword_hits):>2}"
            )
        return "\n".join(lines)
