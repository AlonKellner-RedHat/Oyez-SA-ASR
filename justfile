
set positional-arguments

alias p := pre-commit
alias pa := pre-commit-all
alias t := test
alias c := coverage

# pre-commit the current changes
pre-commit *ARGS:
    git add .
    pre-commit {{ARGS}}

# pre-commit all repo files
pre-commit-all:
    git add .
    pre-commit run --all

# test the specified path (uses latest Python)
test *ARGS:
    tox -e path -- {{ARGS}}

# run coverage tests
coverage:
    git add .
    pre-commit run tox

# run typos on transcripts (check-only); rebuild candidates with all corrections + distances (see docs/asr_normalization_plan.md §4.4)
# typos exits non-zero when it finds typos, so first line may fail
typos-transcripts:
    - uvx typos -c config/typos-transcripts.toml --format json data/transcripts > data/typos_transcripts_report.json
    python scripts/rebuild_typo_candidates_with_corrections.py

# build rule correction candidates from transcripts (vote_tally, years, roman_numerals, etc.); writes data/<rule_id>_candidates.json (see docs §4.5)
rule-candidates:
    python -m scripts.build_rule_candidates

# build awareness-only candidates (no normalization); writes data/awareness_*_candidates.json with corrections: [] (see docs §4.5)
awareness-candidates:
    python -m scripts.build_awareness_candidates

# regenerate awareness examples report (10 examples + context per category, uncovered-only); writes docs/awareness_examples_report.md
awareness-report *ARGS:
    python -m scripts.awareness_examples_report -o docs/awareness_examples_report.md {{ARGS}}

# build legal words list from LexPredict + Open Legal Dictionary; writes data/legal_words.txt (see docs/legal_dictionary.md)
legal-dict:
    python -m scripts.build_legal_dict
