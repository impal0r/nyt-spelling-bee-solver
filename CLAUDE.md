# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A command-line solver for NYT Spelling Bee puzzles. Given 7 letters (first = required "main" letter), finds all valid words (4+ letters, using only those letters, must include main letter). Outputs are tiered: pangrams first, then common words, profanity (opt-in), proper nouns, acronyms (opt-out), and other words.

## Commands

Uses **uv** for dependency management. Either activate the venv first, or prefix commands with `uv run`.

```bash
# Install/sync dependencies
uv sync

# Run tests (from repo root)
uv run python -m pytest tests/

# Run a single test file
uv run python -m pytest tests/test_convert_dic.py

# Run a single test
uv run python -m pytest tests/test_convert_dic.py::TestApplyAffix::test_plural_regular

# Spylls cross-validation tests (slow, requires spylls)
uv run python -m pytest tests/test_convert_dic.py::TestSpyllsCrossValidation

# Regenerate wordlists from Hunspell dictionary
uv run python convert_dic.py wordlists/en_US

# Lint
uv run python -m ruff check .

# Add a dependency
uv add <package>
uv add --group dev <package>
```

## Architecture

**Current state:** The solver logic (`main.py`) is a stub. `convert_dic.py` and the wordlists it produces are complete.

- `convert_dic.py` — Hunspell `.dic`+`.aff` → plain text wordlists. Parses affix rules (PFX/SFX), expands stems, classifies by case (common/proper/acronym) and NOSUGGEST flag (profanity). Cross-validated against spylls with zero discrepancies.
- `wordlists/` — Source dictionaries (`en_US.dic`, `en_US.aff`, `words_alpha.txt`) and generated wordlists (`en_US_common.txt`, `en_US_proper_nouns.txt`, `en_US_acronyms.txt`, `en_US_profanity.txt`). The generated `.txt` files are one word per line, sorted case-insensitively.
- `tests/test_convert_dic.py` — Tests for `convert_dic.py`. Uses real `en_US` dictionary files as fixtures.

**Word classification priority:** profanity > acronyms > proper nouns > common. Each output section only shows words not in prior sections.

## Key Decisions

- Python 3.13+, no runtime dependencies. Dev deps: pytest, ruff, spylls (for cross-validation only).
- Uses **uv** for dependency management with a `.venv` virtual environment. `pyproject.toml` sets `pythonpath = ["."]` so imports work from repo root.
- Test files mirror source files in a `tests/` directory (e.g. `test_convert_dic.py` tests `convert_dic.py`).
- Detailed code style rules are in `.claude/rules/code-style.md`.
- Project plan with puzzle rules and output format spec is in `.claude/plans/initial-project-plan.md`.
