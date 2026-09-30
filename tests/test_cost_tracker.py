"""
Unit tests for the CostTracker service.
Tests pricing calculations, accumulation, merge, and summary output.
"""
import pytest
from app.services.cost_tracker import CostTracker, LLM_PRICING, DOCAI_PRICING


class TestCostTrackerPricing:
    """Verify pricing constants are sensible"""

    def test_llm_pricing_has_expected_models(self):
        assert "gemini-flash" in LLM_PRICING
        assert "llama-scout" in LLM_PRICING
        assert "gpt-oss" in LLM_PRICING

    def test_docai_pricing_has_expected_parsers(self):
        assert "layout" in DOCAI_PRICING
        assert "form" in DOCAI_PRICING


class TestRecordLLMCall:
    """Verify LLM call recording and cost computation"""

    def test_single_call_cost(self):
        tracker = CostTracker(document_id="test-1")
        # 1M input tokens * $0.15/M = $0.15
        # 500K output tokens * $0.60/M = $0.30
        cost = tracker.record_llm_call("gemini-flash", 1_000_000, 500_000, phase="analysis")
        assert round(cost, 6) == 0.45

    def test_accumulation_across_calls(self):
        tracker = CostTracker(document_id="test-2")
        tracker.record_llm_call("gemini-flash", 5000, 1200, phase="analysis")
        tracker.record_llm_call("gemini-flash", 3000, 800, phase="critique")

        summary = tracker.get_summary()
        model_data = summary["llm_costs"]["per_model"]["gemini-flash"]
        assert model_data["input_tokens"] == 8000
        assert model_data["output_tokens"] == 2000
        assert model_data["call_count"] == 2

    def test_multiple_models(self):
        tracker = CostTracker(document_id="test-3")
        tracker.record_llm_call("gemini-flash", 1000, 500, phase="analysis")
        tracker.record_llm_call("llama-scout", 1000, 500, phase="analysis")

        summary = tracker.get_summary()
        assert len(summary["llm_costs"]["per_model"]) == 2
        assert summary["llm_costs"]["total_calls"] == 2

    def test_unknown_model_zero_cost(self):
        tracker = CostTracker(document_id="test-4")
        cost = tracker.record_llm_call("unknown-model", 1000, 500, phase="analysis")
        assert cost == 0.0

    def test_phase_breakdown(self):
        tracker = CostTracker(document_id="test-5")
        tracker.record_llm_call("gemini-flash", 5000, 1000, phase="analysis")
        tracker.record_llm_call("gemini-flash", 3000, 800, phase="critique")
        tracker.record_llm_call("gemini-flash", 2000, 600, phase="report")

        summary = tracker.get_summary()
        assert "analysis" in summary["phase_breakdown"]
        assert "critique" in summary["phase_breakdown"]
        assert "report" in summary["phase_breakdown"]


class TestRecordDocAIPages:
    """Verify Document AI page cost recording"""

    def test_layout_parser_cost(self):
        tracker = CostTracker(document_id="test-6")
        # 5 pages * $0.01/page = $0.05
        cost = tracker.record_docai_pages(5, parser_type="layout")
        assert cost == 0.05

    def test_form_parser_cost(self):
        tracker = CostTracker(document_id="test-7")
        # 5 pages * $0.03/page = $0.15
        cost = tracker.record_docai_pages(5, parser_type="form")
        assert cost == 0.15

    def test_docai_cost_in_extraction_phase(self):
        tracker = CostTracker(document_id="test-8")
        tracker.record_docai_pages(5, parser_type="layout")
        summary = tracker.get_summary()
        assert "extraction" in summary["phase_breakdown"]


class TestGetSummary:
    """Verify the full summary output structure"""

    def test_empty_tracker_summary(self):
        tracker = CostTracker(document_id="test-9")
        summary = tracker.get_summary()

        assert summary["total_cost_usd"] == 0.0
        assert summary["llm_costs"]["total_usd"] == 0.0
        assert summary["llm_costs"]["total_calls"] == 0
        assert summary["docai_costs"]["total_usd"] == 0.0
        assert summary["document_id"] == "test-9"
        assert "elapsed_seconds" in summary

    def test_total_cost_includes_all_components(self):
        tracker = CostTracker(document_id="test-10")
        tracker.record_llm_call("gemini-flash", 1_000_000, 0, phase="analysis")  # $0.15
        tracker.record_docai_pages(10, parser_type="layout")  # $0.10
        tracker.record_docai_pages(10, parser_type="form")  # $0.30

        total = tracker.get_total_cost()
        expected = 0.15 + 0.10 + 0.30
        assert round(total, 6) == round(expected, 6)

    def test_summary_serializable(self):
        """Summary must be JSON-serializable for JSONB storage"""
        import json
        tracker = CostTracker(document_id="test-11")
        tracker.record_llm_call("gemini-flash", 5000, 1200, phase="analysis")
        tracker.record_docai_pages(5, parser_type="layout")

        summary = tracker.get_summary()
        # Should not raise
        json_str = json.dumps(summary)
        assert isinstance(json_str, str)

        # Round-trip
        parsed = json.loads(json_str)
        assert parsed["total_cost_usd"] == summary["total_cost_usd"]


class TestMerge:
    """Verify merging two trackers (used for cross-iteration accumulation)"""

    def test_merge_combines_llm_usage(self):
        tracker1 = CostTracker(document_id="parent")
        tracker1.record_llm_call("gemini-flash", 1000, 500, phase="analysis")

        tracker2 = CostTracker(document_id="iter-2")
        tracker2.record_llm_call("gemini-flash", 2000, 800, phase="analysis")
        tracker2.record_llm_call("llama-scout", 1000, 300, phase="critique")

        tracker1.merge(tracker2)
        summary = tracker1.get_summary()

        assert summary["llm_costs"]["per_model"]["gemini-flash"]["input_tokens"] == 3000
        assert summary["llm_costs"]["per_model"]["gemini-flash"]["output_tokens"] == 1300
        assert summary["llm_costs"]["per_model"]["gemini-flash"]["call_count"] == 2
        assert "llama-scout" in summary["llm_costs"]["per_model"]
        assert summary["llm_costs"]["total_calls"] == 3

    def test_merge_combines_docai_pages(self):
        tracker1 = CostTracker(document_id="parent")
        tracker1.record_docai_pages(5, parser_type="layout")

        tracker2 = CostTracker(document_id="iter-2")
        tracker2.record_docai_pages(5, parser_type="layout")

        tracker1.merge(tracker2)
        summary = tracker1.get_summary()

        assert summary["docai_costs"]["parsers"]["layout"]["pages"] == 10

    def test_merge_combines_phase_costs(self):
        tracker1 = CostTracker(document_id="parent")
        tracker1.record_llm_call("gemini-flash", 1000, 500, phase="analysis")

        tracker2 = CostTracker(document_id="iter-2")
        tracker2.record_llm_call("gemini-flash", 1000, 500, phase="analysis")

        tracker1.merge(tracker2)
        summary = tracker1.get_summary()

        # Phase cost should be doubled
        expected_single = (1000 / 1e6) * 0.15 + (500 / 1e6) * 0.60
        expected_double = expected_single * 2
        assert round(summary["phase_breakdown"]["analysis"], 6) == round(expected_double, 6)


class TestRealWorldScenario:
    """Simulate a realistic 5-page DOCX policy analysis"""

    def test_five_page_docx_cost_estimate(self):
        """
        Simulates: 5-page DOCX → Document AI (layout + form) → 
        multi-model analysis → critique → redraft → report
        """
        tracker = CostTracker(document_id="scenario-1")

        # Document AI: 5-page PDF processed by layout + form parser
        tracker.record_docai_pages(5, parser_type="layout")   # $0.05
        tracker.record_docai_pages(5, parser_type="form")      # $0.15

        # Analysis phase: single model (gemini-flash), ~5 elements
        # Typical prompt: ~8K tokens, response: ~2K tokens per element
        for _ in range(5):
            tracker.record_llm_call("gemini-flash", 8000, 2000, phase="analysis")

        # Critique phase: 10 findings critiqued
        for _ in range(10):
            tracker.record_llm_call("gemini-flash", 3000, 800, phase="critique")

        # Redraft phase: 1 call
        tracker.record_llm_call("gemini-flash", 12000, 4000, phase="redraft")

        # Quality scoring: 1 call
        tracker.record_llm_call("gemini-flash", 5000, 1000, phase="redraft")

        # Report generation: 1 call
        tracker.record_llm_call("gemini-flash", 10000, 3000, phase="report")

        summary = tracker.get_summary()

        # Verify structure
        assert summary["total_cost_usd"] > 0
        assert summary["llm_costs"]["total_calls"] == 18
        assert summary["docai_costs"]["parsers"]["layout"]["pages"] == 5
        assert summary["docai_costs"]["parsers"]["form"]["pages"] == 5

        # Verify total cost is reasonable (should be well under $1 for 5 pages)
        assert summary["total_cost_usd"] < 1.0
        assert summary["total_cost_usd"] > 0.01  # But not negligible

        # Verify all phases are tracked
        assert set(summary["phase_breakdown"].keys()) == {"extraction", "analysis", "critique", "redraft", "report"}
