"""QEN Bolkestein Sovereign Scoring Router — ADR-CLE-004."""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from loguru import logger

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sovereign_engine import score_entity

logger.add("logs/router.log", rotation="500 MB")


@dataclass
class ScoreResult:
    business_name: str
    vertical: str
    vs_score: float
    va_score: float
    vt_score: float
    qen_score: float
    confidence: float
    model_used: str


class SovereignRouter:
    """Deterministic local router based on QEN rules and intelligible data."""

    ENGINE_NAME = "qen-bolkestein-sovereign-v1"

    @staticmethod
    def _description(business: dict[str, Any]) -> str:
        fields = (
            business.get("name"),
            business.get("vertical"),
            business.get("city"),
            business.get("address"),
            business.get("website"),
        )
        return " | ".join(str(value) for value in fields if value)

    @staticmethod
    def _base_scores(business: dict[str, Any]) -> tuple[float, float, float]:
        confidence = float(business.get("confidence") or 0.0)

        completeness = sum(
            bool(business.get(field))
            for field in ("name", "city", "address", "phone", "website")
        )

        vs = 45.0 + completeness * 5.0
        va = 45.0
        vt = 50.0

        if business.get("phone"):
            vs += 5.0

        if business.get("website"):
            vs += 5.0
            va += 5.0

        if business.get("city"):
            vt += 10.0

        if business.get("address"):
            vt += 10.0

        if confidence:
            adjustment = max(-10.0, min(10.0, (confidence - 0.5) * 20.0))
            vs += adjustment
            vt += adjustment

        vertical = str(business.get("vertical") or "").lower()

        if vertical == "balneare":
            va += 5.0
            vt += 5.0
        elif vertical == "ristorazione":
            vt += 5.0
        elif vertical == "alberghiero":
            va += 5.0

        return tuple(max(0.0, min(100.0, value)) for value in (vs, va, vt))

    async def route_and_score(
        self,
        business: dict[str, Any],
        scoring_context_fn: Callable[[dict[str, Any]], str] | None = None,
    ) -> ScoreResult:
        name = str(business.get("name") or "Unknown")
        vertical = str(business.get("vertical") or "unknown")
        description = self._description(business)

        if scoring_context_fn is not None:
            description = f"{description} | {scoring_context_fn(business)}"

        vs, va, vt = self._base_scores(business)

        result = score_entity(
            name=name,
            description=description,
            sector=vertical,
            vs=vs,
            va=va,
            vt=vt,
        )

        source_confidence = float(business.get("confidence") or 0.5)
        confidence = round(max(0.35, min(0.95, source_confidence)), 2)

        logger.info(
            "QEN Sovereign: {} ({}) = {:.2f}",
            name,
            vertical,
            result["qen_score"],
        )

        return ScoreResult(
            business_name=name,
            vertical=vertical,
            vs_score=float(result["vs"]),
            va_score=float(result["va"]),
            vt_score=float(result["vt"]),
            qen_score=float(result["qen_score"]),
            confidence=confidence,
            model_used=self.ENGINE_NAME,
        )


class BatchProcessor:
    def __init__(self, max_workers: int = 10):
        self.router = SovereignRouter()
        self.semaphore = asyncio.Semaphore(max_workers)

    async def process_batch(self, businesses, scoring_context_fn=None):
        tasks = [
            self._process(business, scoring_context_fn)
            for business in businesses
        ]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def _process(self, business, scoring_context_fn):
        async with self.semaphore:
            return await self.router.route_and_score(
                business,
                scoring_context_fn,
            )
