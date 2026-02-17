# Edited by Cursor: split from test_cli_process_normrules (lintok).
"""Tests for process normrules failure and --allow-no-enchant."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from oyez_sa_asr.cli import app
from tests.test_cli_process_helpers import runner


def _make_scripts_root(root: Path) -> None:
    (root / "scripts").mkdir()
    (root / "scripts" / "build_legal_dict.py").write_text("")
    (root / "scripts" / "build_rule_candidates.py").write_text("")
    (root / "scripts" / "build_awareness_candidates.py").write_text("")


class TestProcessNormrulesScriptFailures:
    """Tests when legal dict, rule or awareness script fails."""

    def test_process_normrules_exits_nonzero_if_legal_dict_script_fails(self) -> None:
        """Exits non-zero when legal dict script fails; does not run rule or awareness."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_scripts_root(root)
            input_dir = root / "transcripts"
            output_dir = root / "normrules"
            input_dir.mkdir()
            output_dir.mkdir()
            mock_result = MagicMock()
            mock_result.returncode = 1
            with (
                patch(
                    "oyez_sa_asr.cli_process_normrules._project_root",
                    return_value=root,
                ),
                patch(
                    "oyez_sa_asr.cli_process_normrules.subprocess.run",
                    return_value=mock_result,
                ) as run_mock,
            ):
                result = runner.invoke(
                    app,
                    [
                        "process",
                        "normrules",
                        "--output-dir",
                        str(output_dir),
                        "--input-dir",
                        str(input_dir),
                    ],
                )
        assert result.exit_code != 0
        assert run_mock.call_count == 1

    def test_process_normrules_exits_nonzero_if_rule_script_fails(self) -> None:
        """Exits non-zero when rule candidates script fails; does not run awareness."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_scripts_root(root)
            input_dir = root / "transcripts"
            output_dir = root / "normrules"
            input_dir.mkdir()
            output_dir.mkdir()

            def side_effect(*args: object, **_kwargs: object) -> MagicMock:
                mock = MagicMock()
                cmd = args[0] if args else []
                cmd_str = (
                    " ".join(str(x) for x in cmd) if isinstance(cmd, list) else str(cmd)
                )
                mock.returncode = 0 if "build_legal_dict" in cmd_str else 1
                return mock

            with (
                patch(
                    "oyez_sa_asr.cli_process_normrules._project_root",
                    return_value=root,
                ),
                patch(
                    "oyez_sa_asr.cli_process_normrules.subprocess.run",
                    side_effect=side_effect,
                ) as run_mock,
            ):
                result = runner.invoke(
                    app,
                    [
                        "process",
                        "normrules",
                        "--output-dir",
                        str(output_dir),
                        "--input-dir",
                        str(input_dir),
                    ],
                )
        assert result.exit_code != 0
        assert run_mock.call_count == 2

    def test_process_normrules_exits_nonzero_if_awareness_script_fails(self) -> None:
        """Exits non-zero when awareness script fails after legal dict and rule succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_scripts_root(root)
            input_dir = root / "transcripts"
            output_dir = root / "normrules"
            input_dir.mkdir()
            output_dir.mkdir()

            def side_effect(*args: object, **_kwargs: object) -> MagicMock:
                mock = MagicMock()
                cmd = args[0] if args else []
                cmd_str = (
                    " ".join(str(x) for x in cmd) if isinstance(cmd, list) else str(cmd)
                )
                mock.returncode = (
                    0
                    if (
                        "build_legal_dict" in cmd_str
                        or "build_rule_candidates" in cmd_str
                    )
                    else 1
                )
                return mock

            with (
                patch(
                    "oyez_sa_asr.cli_process_normrules._project_root",
                    return_value=root,
                ),
                patch(
                    "oyez_sa_asr.cli_process_normrules.subprocess.run",
                    side_effect=side_effect,
                ) as run_mock,
            ):
                result = runner.invoke(
                    app,
                    [
                        "process",
                        "normrules",
                        "--output-dir",
                        str(output_dir),
                        "--input-dir",
                        str(input_dir),
                    ],
                )
        assert result.exit_code != 0
        assert run_mock.call_count == 3


class TestProcessNormrulesAllowNoEnchant:
    """Tests for --allow-no-enchant flag propagation."""

    def test_allow_no_enchant_flag_passed_to_subprocesses(self) -> None:
        """Passes --allow-no-enchant to rule and awareness scripts (not legal dict) when specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_scripts_root(root)
            input_dir = root / "transcripts"
            output_dir = root / "normrules"
            input_dir.mkdir()
            output_dir.mkdir()
            mock_result = MagicMock()
            mock_result.returncode = 0
            with (
                patch(
                    "oyez_sa_asr.cli_process_normrules._project_root",
                    return_value=root,
                ),
                patch(
                    "oyez_sa_asr.cli_process_normrules.subprocess.run",
                    return_value=mock_result,
                ) as run_mock,
            ):
                result = runner.invoke(
                    app,
                    [
                        "process",
                        "normrules",
                        "--output-dir",
                        str(output_dir),
                        "--input-dir",
                        str(input_dir),
                        "--allow-no-enchant",
                    ],
                )
        assert result.exit_code == 0
        assert run_mock.call_count == 3
        calls_with_flag = [
            call
            for call in run_mock.call_args_list
            if "--allow-no-enchant" in call[0][0]
        ]
        assert len(calls_with_flag) == 2
