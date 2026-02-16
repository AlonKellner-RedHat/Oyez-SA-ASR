# Edited by Cursor: split from test_cli_dataset_simple for lintok.
"""Tests for dataset simple CLI - group."""

from oyez_sa_asr.cli_dataset_simple import _group_utterances_by_recording


class TestGroupUtterancesByRecording:
    """Tests for utterance grouping logic.

    Edited by Claude: Updated tests to use 3-tuple key (term, docket, transcript_type).
    """

    def test_groups_by_term_docket_type(self) -> None:
        """Groups utterances by (term, docket, transcript_type) key."""
        utterances = [
            {
                "term": "2024",
                "docket": "22-123",
                "transcript_type": "oral_argument",
                "text": "a",
                "start_sec": 0.0,
            },
            {
                "term": "2024",
                "docket": "22-123",
                "transcript_type": "oral_argument",
                "text": "b",
                "start_sec": 5.0,
            },
            {
                "term": "2024",
                "docket": "22-456",
                "transcript_type": "opinion",
                "text": "c",
                "start_sec": 0.0,
            },
            {
                "term": "2023",
                "docket": "21-789",
                "transcript_type": "oral_argument",
                "text": "d",
                "start_sec": 0.0,
            },
        ]

        grouped = _group_utterances_by_recording(utterances)

        assert len(grouped) == 3
        assert len(grouped[("2024", "22-123", "oral_argument")]) == 2
        assert len(grouped[("2024", "22-456", "opinion")]) == 1
        assert len(grouped[("2023", "21-789", "oral_argument")]) == 1

    def test_separates_oral_argument_and_opinion(self) -> None:
        """Separates oral_argument and opinion for same case."""
        utterances = [
            {
                "term": "2022",
                "docket": "21-86",
                "transcript_type": "oral_argument",
                "text": "We will hear argument",
                "start_sec": 0.0,
            },
            {
                "term": "2022",
                "docket": "21-86",
                "transcript_type": "opinion",
                "text": "Justice Kagan has the opinion",
                "start_sec": 0.0,
            },
        ]

        grouped = _group_utterances_by_recording(utterances)

        # Should be separate groups, not combined
        assert len(grouped) == 2
        assert len(grouped[("2022", "21-86", "oral_argument")]) == 1
        assert len(grouped[("2022", "21-86", "opinion")]) == 1
        assert (
            grouped[("2022", "21-86", "oral_argument")][0]["text"]
            == "We will hear argument"
        )
        assert (
            grouped[("2022", "21-86", "opinion")][0]["text"]
            == "Justice Kagan has the opinion"
        )

    def test_preserves_utterance_data(self) -> None:
        """Preserves all utterance fields when grouping."""
        utterances = [
            {
                "term": "2024",
                "docket": "22-123",
                "transcript_type": "oral_argument",
                "text": "hello",
                "speaker_name": "Roberts",
                "start_sec": 1.0,
                "end_sec": 3.5,
            }
        ]

        grouped = _group_utterances_by_recording(utterances)

        utt = grouped[("2024", "22-123", "oral_argument")][0]
        assert utt["text"] == "hello"
        assert utt["speaker_name"] == "Roberts"
        assert utt["start_sec"] == 1.0
        assert utt["end_sec"] == 3.5

    def test_empty_list(self) -> None:
        """Handles empty utterances list."""
        grouped = _group_utterances_by_recording([])
        assert grouped == {}

    def test_missing_transcript_type_defaults_to_unknown(self) -> None:
        """Uses 'unknown' for missing transcript_type."""
        utterances = [
            {"term": "2024", "docket": "22-123", "text": "no type", "start_sec": 0.0},
        ]

        grouped = _group_utterances_by_recording(utterances)

        assert len(grouped) == 1
        assert ("2024", "22-123", "unknown") in grouped
