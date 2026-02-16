# Edited by Cursor: split from test_rule_normalizations (lintok; no new exclusions).
"""Tests for fraction, section, typo_levenshtein, title, mixed_case, fixes, website, bracket, name, pascal, bracket_acronym, inline_typo, short_mixed_acronym."""

from scripts.rule_normalizations import (
    normalize_bracket_acronym,
    normalize_bracket_sentence_unwrap,
    normalize_fraction,
    normalize_inline_typo,
    normalize_invalid_question_mark_fix,
    normalize_mixed_case_accept_6plus,
    normalize_name_pattern_di,
    normalize_pascal_case_accept,
    normalize_replacement_char_fix,
    normalize_section_header,
    normalize_short_mixed_acronym,
    normalize_title_abbreviation,
    normalize_website_dot,
)
from scripts.rule_normalizations.typo_levenshtein_scan import (
    scan_turn_typo_levenshtein,
)


def test_normalize_fraction() -> None:
    """Fractions 1/3, 2/5, ½ -> spoken form; invalid returns span."""
    result_13 = normalize_fraction("1/3")
    assert "one third" in result_13
    assert "a third" in result_13
    assert "two fifths" in normalize_fraction("2/5")
    result_half = normalize_fraction("½")
    assert "one half" in result_half and "a half" in result_half
    result_quarter = normalize_fraction("¼")
    assert "one fourth" in result_quarter and "one quarter" in result_quarter
    result_three_quarters = normalize_fraction("¾")
    assert (
        "three fourths" in result_three_quarters
        and "three quarters" in result_three_quarters
    )
    assert normalize_fraction("3/0") == ["3/0"]
    assert normalize_fraction("11/5") == ["eleven fifths"]


def test_normalize_section_header() -> None:
    """Section header span -> empty (remove)."""
    assert normalize_section_header("REBUTTAL ARGUMENT OF MATTHEW D. McGILL") == [""]


def test_scan_turn_typo_levenshtein() -> None:
    """Token with one digit and exactly one 1-Lev match -> emitted with correction."""
    transcript_words = {"General", "Motors", "Electric", "case", "between", "and"}
    out = scan_turn_typo_levenshtein(
        "a case between G1eneral Ferguson, General Motors and General Electric",
        "sample/oral_argument.json",
        transcript_words,
    )
    assert len(out) >= 1
    g1 = next((r for r in out if r[2] == "G1eneral"), None)
    assert g1 is not None
    assert g1[4] == "General"


def test_normalize_title_abbreviation() -> None:
    """Mr.->Mister, Dr.->Doctor, Mrs.->Misses, Jr.->Junior, Ms.->Miss, Sr.->Senior."""
    assert normalize_title_abbreviation("Mr.") == ["Mister"]
    assert normalize_title_abbreviation("Dr.") == ["Doctor"]
    assert normalize_title_abbreviation("Mrs.") == ["Misses"]
    assert normalize_title_abbreviation("Jr.") == ["Junior"]
    assert normalize_title_abbreviation("Ms.") == ["Miss"]
    assert normalize_title_abbreviation("Sr.") == ["Senior"]


def test_normalize_mixed_case_accept_6plus() -> None:
    """Mixed case 6+ letters -> identity (PowerEx, RadLAX). Reject 5-letter (DoD)."""
    assert normalize_mixed_case_accept_6plus("PowerEx") == ["PowerEx"]
    assert normalize_mixed_case_accept_6plus("RadLAX") == ["RadLAX"]
    assert normalize_mixed_case_accept_6plus("CoBank") == ["CoBank"]
    assert normalize_mixed_case_accept_6plus("OnDisc") == ["OnDisc"]
    assert normalize_mixed_case_accept_6plus("DoD") == ["DoD"]


def test_normalize_invalid_question_mark_fix() -> None:
    """\ufffd? -> ?."""
    assert normalize_invalid_question_mark_fix("\ufffd?") == ["?"]
    assert normalize_invalid_question_mark_fix("\ufffd ?") == ["?"]


def test_normalize_replacement_char_fix() -> None:
    """Cond\ufffd Nast -> Condé Nast; Cond\ufffd -> Condé. Other U+FFFD unchanged."""
    assert normalize_replacement_char_fix("Cond\ufffd Nast") == ["Condé Nast"]
    assert normalize_replacement_char_fix("Cond\ufffd") == ["Condé"]
    assert normalize_replacement_char_fix("unknown\ufffd") == ["unknown\ufffd"]


def test_normalize_website_dot() -> None:
    """[xxxDOTyyy] -> xxx dot yyy; trailing punctuation inside brackets preserved."""
    assert normalize_website_dot("[befairDOTorg,]") == ["befair dot org,"]
    assert normalize_website_dot("[supremecourtusDOTgov,]") == [
        "supremecourtus dot gov,"
    ]


def test_normalize_bracket_sentence_unwrap() -> None:
    """Bracket 4+ words -> inner text only."""
    assert normalize_bracket_sentence_unwrap("(which may itself be true)") == [
        "which may itself be true"
    ]
    assert normalize_bracket_sentence_unwrap(
        "(federal voters who have not paid their poll taxes)"
    ) == ["federal voters who have not paid their poll taxes"]


def test_normalize_name_pattern_di() -> None:
    """Di + name (DiBona, DiMaria) -> identity. Reject Dice, Director."""
    assert normalize_name_pattern_di("DiBona") == ["DiBona"]
    assert normalize_name_pattern_di("DiMaria") == ["DiMaria"]
    assert normalize_name_pattern_di("DiCenso") == ["DiCenso"]


def test_normalize_pascal_case_accept() -> None:
    """PascalCase 6+ letters, each segment 3+ -> identity."""
    assert normalize_pascal_case_accept("CattleAnd") == ["CattleAnd"]
    assert normalize_pascal_case_accept("ConRail") == ["ConRail"]
    assert normalize_pascal_case_accept("ByteDance") == ["ByteDance"]
    assert normalize_pascal_case_accept("TransUnion") == ["TransUnion"]
    assert normalize_pascal_case_accept("FirsTier") == ["FirsTier"]
    assert normalize_pascal_case_accept("DoD") == ["DoD"]
    assert normalize_pascal_case_accept("iPhone") == ["iPhone"]


def test_normalize_bracket_acronym() -> None:
    """(MPSC), (NRDC), (ERISA) -> letter-by-letter; (i) identity."""
    assert normalize_bracket_acronym("(MPSC)") == ["em pee ess cee"]
    assert normalize_bracket_acronym("(NRDC)") == ["en ar dee cee"]
    assert normalize_bracket_acronym("(ERISA)") == ["ee ar eye ess ay"]
    assert normalize_bracket_acronym("(i)") == ["(i)"]


def test_normalize_inline_typo() -> None:
    """word[: correction] and word, [: correction] -> correction."""
    assert normalize_inline_typo("interaconnection[:interconnection]") == [
        "interconnection"
    ]
    assert normalize_inline_typo("repretented [: represented]") == ["represented"]
    assert normalize_inline_typo("word[:multi word correction]") == [
        "multi word correction"
    ]
    assert normalize_inline_typo("abnormamality, [:abnormality]") == ["abnormality,"]
    assert normalize_inline_typo(", [:abnormality]") == [", abnormality"]


def test_normalize_short_mixed_acronym() -> None:
    """Short mixed-case 2-5 letters, half+ caps -> letter-by-letter."""
    assert normalize_short_mixed_acronym("DoD") == ["dee oh dee"]
    assert normalize_short_mixed_acronym("DiRe") == ["dee eye ar ee"]
    assert normalize_short_mixed_acronym("SPaRE") == ["ess pee ay ar ee"]
    assert normalize_short_mixed_acronym("PhD") == ["pee aych dee"]
    assert normalize_short_mixed_acronym("CattleAnd") == ["CattleAnd"]
    assert normalize_short_mixed_acronym("iPhone") == ["iPhone"]
    assert normalize_short_mixed_acronym("a") == ["a"]
    assert normalize_short_mixed_acronym("ByteDance") == ["ByteDance"]
