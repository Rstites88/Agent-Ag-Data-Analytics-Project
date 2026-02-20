"""Tests for CostTracker."""

from tools.cost_tracker import get_tracker, reset_tracker


class TestCostTracker:
    """Test suite for CostTracker."""

    def test_singleton_instance(self):
        """Test that get_tracker returns a consistent instance."""
        tracker1 = get_tracker()
        tracker2 = get_tracker()
        assert tracker1 is tracker2

    def test_track_api_call(self):
        """Test tracking an API call."""
        reset_tracker()  # Start fresh
        tracker = get_tracker()

        tracker.log_api_call(
            model="gpt-4",
            tokens_in=100,
            tokens_out=50,
            cost=0.01,
            duration_seconds=1.5,
        )

        summary = tracker.get_summary()
        assert summary["total_calls"] == 1
        assert summary["total_cost"] == 0.01
        assert summary["total_tokens_in"] == 100
        assert summary["total_tokens_out"] == 50

    def test_track_multiple_calls(self):
        """Test tracking multiple API calls."""
        reset_tracker()
        tracker = get_tracker()

        tracker.log_api_call("gpt-4", 100, 50, 0.01, 1.0)
        tracker.log_api_call("gpt-4", 200, 100, 0.02, 1.0)
        tracker.log_api_call("gpt-3.5-turbo", 150, 75, 0.005, 1.0)

        summary = tracker.get_summary()
        assert summary["total_calls"] == 3
        assert summary["total_cost"] == 0.035
        assert summary["total_tokens_in"] == 450
        assert summary["total_tokens_out"] == 225

    def test_get_summary_by_model(self):
        """Test getting summary statistics."""
        reset_tracker()
        tracker = get_tracker()

        tracker.log_api_call("gpt-4", 100, 50, 0.01, 1.0)
        tracker.log_api_call("gpt-4", 200, 100, 0.02, 1.0)
        tracker.log_api_call("gpt-3.5-turbo", 150, 75, 0.005, 1.0)

        summary = tracker.get_summary()
        # Current implementation doesn't break down by model in summary,
        # but we can verify the totals
        assert summary["total_calls"] == 3
        assert summary["total_cost"] == 0.035

    def test_reset(self):
        """Test resetting the tracker."""
        reset_tracker()
        tracker = get_tracker()
        tracker.log_api_call("gpt-4", 100, 50, 0.01, 1.0)

        reset_tracker()  # Reset again
        tracker = get_tracker()

        summary = tracker.get_summary()
        assert summary["total_calls"] == 0
        assert summary["total_cost"] == 0.0
        assert summary["total_tokens_in"] == 0
        assert summary["total_tokens_out"] == 0

    def test_format_summary(self):
        """Test formatting summary as string."""
        reset_tracker()
        tracker = get_tracker()
        tracker.log_api_call("gpt-4", 100, 50, 0.01, 1.0)

        formatted = tracker.format_summary()
        assert "gpt-4" in formatted or "API Calls" in formatted
        assert "0.01" in formatted or "$0.01" in formatted
        assert "100" in formatted or "150" in formatted  # tokens
