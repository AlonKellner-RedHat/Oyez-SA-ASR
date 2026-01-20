# Edited by Claude
"""Tests for utterance filtering."""

from oyez_sa_asr.utterance_filter import (
    filter_utterances,
)


def make_utterance(
    start: float = 0,
    end: float = 10,
    words: int = 100,
    term: str = "2023",
    docket: str = "22-123",
    transcript_type: str = "oral_argument",
) -> dict:
    """Create a test utterance."""
    return {
        "term": term,
        "docket": docket,
        "transcript_type": transcript_type,
        "start_sec": start,
        "end_sec": end,
        "duration_sec": end - start,
        "word_count": words,
        "text": "test " * words,
    }


class TestFilterUtterances:
    """Test the main filter_utterances function."""

    def test_empty_list(self) -> None:
        """Empty list returns empty."""
        filtered, stats = filter_utterances([])
        assert filtered == []
        assert stats.total == 0
        assert stats.passed == 0

    def test_valid_utterances_pass(self) -> None:
        """Valid utterances pass through."""
        utterances = [
            make_utterance(start=0, end=10, words=20),  # 120 wpm
            make_utterance(start=15, end=25, words=25),  # 150 wpm
        ]
        filtered, stats = filter_utterances(utterances)
        assert len(filtered) == 2
        assert stats.passed == 2

    def test_invalid_timestamps_filtered(self) -> None:
        """Invalid timestamps are filtered."""
        utterances = [
            make_utterance(start=10, end=5, words=20),  # end < start
            make_utterance(start=-1, end=0, words=20),  # negative start (no overlap)
            make_utterance(start=20, end=30, words=20),  # valid
            make_utterance(start=50, end=100, words=100),  # valid, extends recording
        ]
        filtered, stats = filter_utterances(utterances)
        assert len(filtered) == 2
        assert stats.invalid_timestamps == 2

    def test_abnormal_wpm_low_filtered(self) -> None:
        """WPM < 30 filtered for utterances > 10s."""
        utterances = [
            # 20s utterance with 5 words = 15 wpm (too slow)
            make_utterance(start=0, end=20, words=5),
            # 20s utterance with 50 words = 150 wpm (normal)
            make_utterance(start=25, end=45, words=50),
        ]
        filtered, stats = filter_utterances(utterances)
        assert len(filtered) == 1
        assert stats.abnormal_wpm == 1

    def test_abnormal_wpm_high_filtered(self) -> None:
        """WPM > 600 filtered."""
        utterances = [
            # 20s utterance with 300 words = 900 wpm (too fast)
            make_utterance(start=0, end=20, words=300),
            # 20s utterance with 50 words = 150 wpm (normal)
            make_utterance(start=25, end=45, words=50),
        ]
        filtered, stats = filter_utterances(utterances)
        assert len(filtered) == 1
        assert stats.abnormal_wpm == 1

    def test_short_utterance_wpm_not_checked(self) -> None:
        """WPM not checked for utterances < 10s."""
        utterances = [
            # 5s with 1 word = 12 wpm, but too short to filter
            make_utterance(start=0, end=5, words=1),
            # Add another to avoid too_long_ratio filter
            make_utterance(start=50, end=100, words=100),
        ]
        filtered, stats = filter_utterances(utterances)
        assert len(filtered) == 2
        assert stats.abnormal_wpm == 0

    def test_overlapping_filtered(self) -> None:
        """Overlapping utterances (>3s) are filtered."""
        utterances = [
            make_utterance(start=0, end=20, words=40),
            make_utterance(start=10, end=30, words=40),  # 10s overlap with above
        ]
        filtered, stats = filter_utterances(utterances)
        assert len(filtered) == 0
        assert stats.overlapping == 2

    def test_small_overlap_allowed(self) -> None:
        """Small overlaps (<3s) are allowed."""
        utterances = [
            make_utterance(start=0, end=10, words=20),
            make_utterance(start=8, end=18, words=20),  # 2s overlap
            make_utterance(start=50, end=100, words=100),  # extends recording
        ]
        filtered, stats = filter_utterances(utterances)
        assert len(filtered) == 3
        assert stats.overlapping == 0

    def test_too_long_ratio_filtered(self) -> None:
        """Utterance > 50% of recording filtered."""
        utterances = [
            # Only one utterance in this recording, 100% duration
            make_utterance(start=0, end=100, words=200, docket="22-999"),
        ]
        filtered, stats = filter_utterances(utterances)
        assert len(filtered) == 0
        assert stats.too_long_ratio == 1

    def test_reasonable_ratio_allowed(self) -> None:
        """Utterance < 50% of recording allowed."""
        utterances = [
            make_utterance(start=0, end=40, words=80),  # 40%
            make_utterance(start=50, end=100, words=100),  # 50%
        ]
        filtered, stats = filter_utterances(utterances)
        assert len(filtered) == 2
        assert stats.too_long_ratio == 0

    def test_different_recordings_not_overlap(self) -> None:
        """Utterances from different recordings don't overlap."""
        utterances = [
            make_utterance(start=0, end=20, words=40, docket="22-111"),
            make_utterance(start=50, end=100, words=100, docket="22-111"),  # same rec
            make_utterance(start=0, end=20, words=40, docket="22-222"),  # diff rec
            make_utterance(start=50, end=100, words=100, docket="22-222"),  # same rec
        ]
        filtered, stats = filter_utterances(utterances)
        assert len(filtered) == 4
        assert stats.overlapping == 0

    def test_stats_correct(self) -> None:
        """Stats are correctly computed."""
        utterances = [
            make_utterance(start=0, end=10, words=20),  # valid
            make_utterance(start=10, end=5, words=20),  # invalid timestamp
            make_utterance(start=20, end=40, words=5),  # low wpm
        ]
        _, stats = filter_utterances(utterances)
        assert stats.total == 3
        assert stats.passed == 1
        assert stats.invalid_timestamps == 1
        assert stats.abnormal_wpm == 1
