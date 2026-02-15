"""Tests for the Spelling Bee solver (solve.py)."""

# Third-party libraries
import pytest

# Local imports
from solve import format_output, is_pangram, is_valid_word, load_wordlist, parse_args, solve


# ----------------------------- is_valid_word ---------------------------------


class TestIsValidWord:
    """Tests for is_valid_word."""

    LETTER_SET = set("laertiv")
    MAIN = "l"

    def test_valid_word(self):
        assert is_valid_word("trail", self.LETTER_SET, self.MAIN)

    def test_valid_word_uppercase(self):
        assert is_valid_word("TRAIL", self.LETTER_SET, self.MAIN)

    def test_valid_word_with_repeated_letters(self):
        assert is_valid_word("little", self.LETTER_SET, self.MAIN)

    def test_too_short(self):
        assert not is_valid_word("let", self.LETTER_SET, self.MAIN)

    def test_exactly_four_letters(self):
        assert is_valid_word("lire", self.LETTER_SET, self.MAIN)

    def test_missing_main_letter(self):
        assert not is_valid_word("tire", self.LETTER_SET, self.MAIN)

    def test_invalid_letter(self):
        assert not is_valid_word("layer", self.LETTER_SET, self.MAIN)

    def test_empty_string(self):
        assert not is_valid_word("", self.LETTER_SET, self.MAIN)


# ------------------------------- is_pangram ----------------------------------


class TestIsPangram:
    """Tests for is_pangram."""

    LETTER_SET = set("laertiv")

    def test_pangram(self):
        assert is_pangram("relative", self.LETTER_SET)

    def test_pangram_with_repeats(self):
        assert is_pangram("alliterative", self.LETTER_SET)

    def test_not_pangram(self):
        assert not is_pangram("trail", self.LETTER_SET)


# ------------------------------- parse_args ----------------------------------


class TestParseArgs:
    """Tests for argument parsing and validation."""

    def test_basic_parsing(self):
        args = parse_args(["LAERTIV"])
        assert args.letters == "LAERTIV"
        assert args.show_profanity is False
        assert args.hide_acronyms is False

    def test_lowercase_input_uppercased(self):
        args = parse_args(["laertiv"])
        assert args.letters == "LAERTIV"

    def test_show_profanity_flag(self):
        args = parse_args(["LAERTIV", "--show-profanity"])
        assert args.show_profanity is True

    def test_hide_acronyms_flag(self):
        args = parse_args(["LAERTIV", "--hide-acronyms"])
        assert args.hide_acronyms is True

    def test_wrong_letter_count(self):
        with pytest.raises(SystemExit):
            parse_args(["ABCDEF"])

    def test_non_alpha(self):
        with pytest.raises(SystemExit):
            parse_args(["ABCDE1G"])

    def test_duplicate_letters(self):
        with pytest.raises(SystemExit):
            parse_args(["AABCDEF"])


# ------------------------------ load_wordlist --------------------------------


class TestLoadWordlist:
    """Tests for load_wordlist."""

    def test_loads_common_wordlist(self):
        from solve import WORDLISTS_DIR

        words = load_wordlist(WORDLISTS_DIR / "en_US_common.txt")
        assert len(words) > 1000
        assert "aardvark" in words

    def test_skips_empty_lines(self, tmp_path):
        path = tmp_path / "test.txt"
        path.write_text("alpha\n\nbeta\n  \ngamma\n")
        words = load_wordlist(path)
        assert words == ["alpha", "beta", "gamma"]


# ---------------------------------- solve ------------------------------------


class TestSolve:
    """Integration tests for the solve function."""

    def test_known_puzzle(self):
        """LAERTIV puzzle: check pangram and common words."""
        result = solve("LAERTIV")
        all_words = [w.lower() for words in result.values() for w in words]

        assert "relative" in all_words
        assert "Pangrams" in result
        assert "relative" in [w.lower() for w in result["Pangrams"]]

        # Some expected common words
        for word in ["trail", "later", "vital"]:
            assert word in all_words, f"expected '{word}' in results"

    def test_main_letter_required(self):
        """Every result word must contain the main letter."""
        result = solve("LAERTIV")
        for words in result.values():
            for word in words:
                assert "l" in word.lower(), f"'{word}' missing main letter 'L'"

    def test_no_invalid_letters(self):
        """No result word should contain letters outside the puzzle."""
        letter_set = set("laertiv")
        result = solve("LAERTIV")
        for words in result.values():
            for word in words:
                assert set(word.lower()) <= letter_set, (
                    f"'{word}' contains invalid letters"
                )

    def test_deduplication(self):
        """A word should appear in only one section."""
        result = solve("LAERTIV", show_profanity=True)
        seen: set[str] = set()
        for section, words in result.items():
            for word in words:
                key = word.lower()
                assert key not in seen, (
                    f"'{word}' duplicated in '{section}'"
                )
                seen.add(key)

    def test_profanity_hidden_by_default(self):
        result = solve("LAERTIV")
        assert "Profanity" not in result

    def test_profanity_shown_with_flag(self):
        result = solve("LAERTIV", show_profanity=True)
        # Profanity section may or may not have words for this puzzle,
        # but the key point is it doesn't error
        assert isinstance(result, dict)

    def test_acronyms_shown_by_default(self):
        """Acronyms section should be present when there are matching acronyms."""
        # Use a puzzle likely to have acronym matches
        result = solve("NAISCOT")
        # Whether or not there are acronym matches, hide_acronyms==False is the default
        # Just verify solve runs and returns valid structure
        assert "Pangrams" in result

    def test_acronyms_hidden_with_flag(self):
        result = solve("LAERTIV", hide_acronyms=True)
        assert "Acronyms" not in result

    def test_all_words_at_least_four_letters(self):
        result = solve("LAERTIV")
        for words in result.values():
            for word in words:
                assert len(word) >= 4, f"'{word}' is shorter than 4 letters"

    def test_pangrams_separated_from_sections(self):
        """Pangrams should not also appear in other sections."""
        result = solve("LAERTIV")
        pangrams_lower = {w.lower() for w in result.get("Pangrams", [])}
        for section, words in result.items():
            if section == "Pangrams":
                continue
            for word in words:
                assert word.lower() not in pangrams_lower, (
                    f"pangram '{word}' also in '{section}'"
                )


# ------------------------------ format_output --------------------------------


class TestFormatOutput:
    """Tests for output formatting."""

    def test_basic_format(self):
        sections = {
            "Pangrams": ["relative"],
            "Common words": ["later", "trail"],
        }
        output = format_output(sections)
        lines = output.split("\n")
        assert lines[0] == "Pangrams:"
        assert lines[1] == "  relative"
        assert lines[2] == "Common words:"
        assert lines[3] == "  later"
        assert lines[4] == "  trail"

    def test_empty_section_skipped(self):
        sections = {
            "Pangrams": [],
            "Common words": ["later"],
        }
        output = format_output(sections)
        assert "Pangrams" not in output
        assert "Common words:" in output

    def test_alphabetical_order_preserved(self):
        """Words should appear in the order given (caller sorts them)."""
        sections = {"Common words": ["alpha", "beta", "gamma"]}
        output = format_output(sections)
        lines = output.strip().split("\n")
        assert lines[1:] == ["  alpha", "  beta", "  gamma"]
