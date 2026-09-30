"""
Cost Tracker Service - Real-time cost tracking for document analysis

Tracks token usage from LLM API responses, Document AI page processing,
and computes dollar costs using Vertex AI Model Garden pricing (2026).
"""
import time
import threading
from typing import Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Vertex AI Model Garden pricing (per 1M tokens) - 2026 rates
LLM_PRICING = {
    "llama-scout": {
        "input_per_million": 0.25,
        "output_per_million": 0.70,
    },
    "gemini-flash": {
        "input_per_million": 0.15,
        "output_per_million": 0.60,
    },
    "gpt-oss": {
        "input_per_million": 0.15,
        "output_per_million": 0.60,
    },
}

# Google Cloud Document AI pricing (per page) - 2026 rates
DOCAI_PRICING = {
    "layout": 0.01,   # Layout Parser: $10 per 1,000 pages
    "form": 0.03,      # Form Parser: $30 per 1,000 pages
}


class CostTracker:
    """
    Accumulates cost data for a single document analysis run.

    Thread-safe: uses a lock for concurrent LLM call tracking.

    Usage:
        tracker = CostTracker(document_id="abc-123")
        tracker.record_llm_call("gemini-flash", 5000, 1200, phase="analysis")
        tracker.record_docai_pages(5, "layout")
        summary = tracker.get_summary()
    """

    def __init__(self, document_id: str = ""):
        self.document_id = document_id
        self._lock = threading.Lock()
        self._start_time = time.monotonic()

        # Per-model token tracking: {model_key: {input_tokens, output_tokens, call_count, cost_usd}}
        self._llm_usage: Dict[str, Dict[str, Any]] = {}

        # Per-phase cost tracking: {phase: cost_usd}
        self._phase_costs: Dict[str, float] = {}

        # Document AI tracking
        self._docai_pages: Dict[str, int] = {
            "layout": 0,
            "form": 0,
        }

        # Total LLM call counter
        self._total_llm_calls = 0

    def record_llm_call(
        self,
        model_key: str,
        input_tokens: int,
        output_tokens: int,
        phase: str = "analysis",
    ) -> float:
        """
        Record a single LLM API call with actual token usage.

        Args:
            model_key: Model identifier (e.g., "gemini-flash", "llama-scout")
            input_tokens: Number of prompt/input tokens consumed
            output_tokens: Number of completion/output tokens generated
            phase: Analysis phase (extraction, analysis, critique, redraft, report)

        Returns:
            Cost in USD for this individual call
        """
        pricing = LLM_PRICING.get(model_key)
        if not pricing:
            logger.warning(
                f"No pricing data for model '{model_key}', cost will be recorded as $0.00",
                extra={"model_key": model_key},
            )
            call_cost = 0.0
        else:
            input_cost = (input_tokens / 1_000_000) * pricing["input_per_million"]
            output_cost = (output_tokens / 1_000_000) * pricing["output_per_million"]
            call_cost = input_cost + output_cost

        with self._lock:
            # Per-model accumulation
            if model_key not in self._llm_usage:
                self._llm_usage[model_key] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "call_count": 0,
                    "cost_usd": 0.0,
                }
            self._llm_usage[model_key]["input_tokens"] += input_tokens
            self._llm_usage[model_key]["output_tokens"] += output_tokens
            self._llm_usage[model_key]["call_count"] += 1
            self._llm_usage[model_key]["cost_usd"] += call_cost

            # Per-phase accumulation
            self._phase_costs[phase] = self._phase_costs.get(phase, 0.0) + call_cost

            self._total_llm_calls += 1

        logger.info(
            "LLM call cost recorded",
            extra={
                "model": model_key,
                "phase": phase,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "call_cost_usd": round(call_cost, 6),
                "document_id": self.document_id,
            },
        )

        return call_cost

    def record_docai_pages(self, page_count: int, parser_type: str = "layout") -> float:
        """
        Record Document AI page processing.

        Args:
            page_count: Number of pages processed
            parser_type: Parser type — "layout" or "form"

        Returns:
            Cost in USD for this processing
        """
        per_page_cost = DOCAI_PRICING.get(parser_type, 0.0)
        total_cost = page_count * per_page_cost

        with self._lock:
            self._docai_pages[parser_type] = self._docai_pages.get(parser_type, 0) + page_count
            self._phase_costs["extraction"] = self._phase_costs.get("extraction", 0.0) + total_cost

        logger.info(
            "Document AI cost recorded",
            extra={
                "parser_type": parser_type,
                "pages": page_count,
                "cost_usd": round(total_cost, 6),
                "document_id": self.document_id,
            },
        )

        return total_cost

    def merge(self, other: "CostTracker") -> None:
        """
        Merge another CostTracker's data into this one.
        Useful for accumulating costs across iterations.
        """
        with self._lock:
            for model_key, usage in other._llm_usage.items():
                if model_key not in self._llm_usage:
                    self._llm_usage[model_key] = {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "call_count": 0,
                        "cost_usd": 0.0,
                    }
                self._llm_usage[model_key]["input_tokens"] += usage["input_tokens"]
                self._llm_usage[model_key]["output_tokens"] += usage["output_tokens"]
                self._llm_usage[model_key]["call_count"] += usage["call_count"]
                self._llm_usage[model_key]["cost_usd"] += usage["cost_usd"]

            for phase, cost in other._phase_costs.items():
                self._phase_costs[phase] = self._phase_costs.get(phase, 0.0) + cost

            for parser_type, pages in other._docai_pages.items():
                self._docai_pages[parser_type] = self._docai_pages.get(parser_type, 0) + pages

            self._total_llm_calls += other._total_llm_calls

    def get_total_cost(self) -> float:
        """Get total cost in USD across all components."""
        with self._lock:
            llm_total = sum(u["cost_usd"] for u in self._llm_usage.values())
            docai_total = sum(
                self._docai_pages.get(p, 0) * DOCAI_PRICING.get(p, 0)
                for p in DOCAI_PRICING
            )
            return round(llm_total + docai_total, 6)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get full cost breakdown as a serializable dict.

        Returns a dict suitable for JSON storage in the document meta field.
        """
        elapsed = time.monotonic() - self._start_time

        with self._lock:
            llm_total = sum(u["cost_usd"] for u in self._llm_usage.values())
            total_input_tokens = sum(u["input_tokens"] for u in self._llm_usage.values())
            total_output_tokens = sum(u["output_tokens"] for u in self._llm_usage.values())

            docai_costs = {}
            docai_total = 0.0
            for parser_type, pages in self._docai_pages.items():
                cost = pages * DOCAI_PRICING.get(parser_type, 0)
                docai_costs[parser_type] = {
                    "pages": pages,
                    "cost_usd": round(cost, 6),
                }
                docai_total += cost

            total_cost = llm_total + docai_total

            # Round per-model costs for clean output
            llm_breakdown = {}
            for model_key, usage in self._llm_usage.items():
                llm_breakdown[model_key] = {
                    "input_tokens": usage["input_tokens"],
                    "output_tokens": usage["output_tokens"],
                    "call_count": usage["call_count"],
                    "cost_usd": round(usage["cost_usd"], 6),
                }

            phase_breakdown = {
                phase: round(cost, 6)
                for phase, cost in self._phase_costs.items()
            }

            return {
                "total_cost_usd": round(total_cost, 6),
                "llm_costs": {
                    "total_usd": round(llm_total, 6),
                    "total_input_tokens": total_input_tokens,
                    "total_output_tokens": total_output_tokens,
                    "total_calls": self._total_llm_calls,
                    "per_model": llm_breakdown,
                },
                "docai_costs": {
                    "total_usd": round(docai_total, 6),
                    "parsers": docai_costs,
                },
                "phase_breakdown": phase_breakdown,
                "elapsed_seconds": round(elapsed, 2),
                "document_id": self.document_id,
            }
