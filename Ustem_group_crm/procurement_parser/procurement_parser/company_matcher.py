"""Step 5 - Match extracted products against company data.

Fuzzy matching with configurable thresholds (rapidfuzz). Status is decided by
*where* the product was found:

    warehouse (qty > 0) -> On Stock        (green)
    purchase history     -> Previously Purchased (yellow)
    nowhere              -> New Product      (red)

Cost price / supplier are enriched from company sources only. No prices are
ever invented and no external lookups are performed.
"""

from __future__ import annotations

from typing import Optional

from rapidfuzz import fuzz, process

from .config import ParserConfig
from .data_sources import CompanyData, CompanyRecord
from .models import Product, MatchResult, MatchStatus
from .text_utils import normalize_name


class CompanyMatcher:
    def __init__(self, config: ParserConfig, company_data: CompanyData):
        self.config = config
        self.company = company_data

    def match_all(self, products: list[Product]) -> list[MatchResult]:
        return [self.match(p) for p in products]

    # ------------------------------------------------------------------ #
    def match(self, product: Product) -> MatchResult:
        # Search every source; remember the best hit per role.
        wh_rec, wh_score = self._best(product, self.company.warehouse_inventory)
        ph_rec, ph_score = self._best(product, self.company.purchase_history)
        pdb_rec, pdb_score = self._best(product, self.company.product_database)
        sup_rec, sup_score = self._best(product, self.company.supplier_price_lists)

        low = self.config.match_threshold_low

        # Decide status by location of a confident-enough match.
        status: MatchStatus
        matched_name = ""
        similarity = 0.0
        source = ""

        if wh_rec and wh_score >= low and (wh_rec.warehouse_quantity or 0) > 0:
            status = MatchStatus.ON_STOCK
            matched_name, similarity, source = (
                wh_rec.name, wh_score, wh_rec.source_role
            )
        elif ph_rec and ph_score >= low:
            status = MatchStatus.PREVIOUSLY_PURCHASED
            matched_name, similarity, source = (
                ph_rec.name, ph_score, ph_rec.source_role
            )
        elif wh_rec and wh_score >= low:
            # known item but currently zero stock -> treat as previously handled
            status = MatchStatus.PREVIOUSLY_PURCHASED
            matched_name, similarity, source = (
                wh_rec.name, wh_score, wh_rec.source_role + " (0 stock)"
            )
        elif pdb_rec and pdb_score >= low:
            status = MatchStatus.PREVIOUSLY_PURCHASED
            matched_name, similarity, source = (
                pdb_rec.name, pdb_score, pdb_rec.source_role
            )
        else:
            status = MatchStatus.NEW_PRODUCT

        # Enrich cost / supplier / warehouse qty from any company source.
        warehouse_quantity = wh_rec.warehouse_quantity if wh_rec and wh_score >= low else None
        cost_price = self._first_price(
            (wh_rec, wh_score), (pdb_rec, pdb_score),
            (ph_rec, ph_score), (sup_rec, sup_score), threshold=low,
        )
        supplier = self._first_supplier(
            (wh_rec, wh_score), (pdb_rec, pdb_score),
            (ph_rec, ph_score), (sup_rec, sup_score), threshold=low,
        )

        comments = self._build_comments(
            status, similarity,
            {"warehouse": (wh_rec, wh_score), "purchase": (ph_rec, ph_score),
             "catalog": (pdb_rec, pdb_score), "supplier": (sup_rec, sup_score)},
        )

        return MatchResult(
            product=product,
            status=status,
            matched_name=matched_name,
            similarity=round(similarity, 1),
            source=source,
            warehouse_quantity=warehouse_quantity,
            cost_price=cost_price,
            supplier=supplier,
            comments=comments,
        )

    # ------------------------------------------------------------------ #
    def _best(self, product, source) -> tuple[Optional[CompanyRecord], float]:
        records = self.company.get(source)
        if not records:
            return None, 0.0

        q_name = normalize_name(product.name).lower()
        q_code = (product.code or "").strip().lower()

        best_rec = None
        best_score = 0.0
        for rec in records:
            # exact code match is the strongest possible signal
            if q_code and rec.code and q_code == rec.code.strip().lower():
                return rec, 100.0
            cand = normalize_name(rec.name).lower()
            if not cand:
                continue
            score = max(
                fuzz.token_sort_ratio(q_name, cand),
                fuzz.partial_ratio(q_name, cand),
            )
            if score > best_score:
                best_score = score
                best_rec = rec
        return best_rec, best_score

    @staticmethod
    def _first_price(*pairs, threshold) -> Optional[float]:
        for rec, score in pairs:
            if rec and score >= threshold and rec.cost_price is not None:
                return rec.cost_price
        return None

    @staticmethod
    def _first_supplier(*pairs, threshold) -> str:
        for rec, score in pairs:
            if rec and score >= threshold and rec.supplier:
                return rec.supplier
        return ""

    def _build_comments(self, status, similarity, hits) -> str:
        parts = []
        high = self.config.match_threshold_high
        if status == MatchStatus.NEW_PRODUCT:
            # mention nearest near-miss to help a human reviewer
            near = max(
                ((r, s, k) for k, (r, s) in hits.items() if r),
                key=lambda x: x[1],
                default=None,
            )
            if near and near[1] >= 50:
                parts.append(
                    f"No confident match; closest in {near[2]} "
                    f'"{near[0].name}" ({near[1]:.0f}%)'
                )
            else:
                parts.append("No match found in company data")
        else:
            confidence = "high" if similarity >= high else "approximate"
            parts.append(f"{confidence} match ({similarity:.0f}%)")
        return "; ".join(parts)
