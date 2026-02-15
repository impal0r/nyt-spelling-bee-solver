"""NYT Spelling Bee solver — find all valid words for a given puzzle."""

# Standard library imports
import argparse
from pathlib import Path

WORDLISTS_DIR = Path(__file__).parent / "wordlists"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed namespace with letters, show_profanity, and hide_acronyms.
    """
    parser = argparse.ArgumentParser(
        description="Solve NYT Spelling Bee puzzles.",
    )
    parser.add_argument(
        "letters",
        help="7 unique letters; the first is the required main letter (e.g. LAERTIV)",
    )
    parser.add_argument(
        "--show-profanity",
        action="store_true",
        default=False,
        help="Include profanity section in output",
    )
    parser.add_argument(
        "--hide-acronyms",
        action="store_true",
        default=False,
        help="Exclude acronyms section from output",
    )
    args = parser.parse_args(argv)

    letters = args.letters.upper()
    if len(letters) != 7:
        parser.error(f"expected exactly 7 letters, got {len(letters)}")
    if not letters.isalpha():
        parser.error("letters must be alphabetic characters only")
    if len(set(letters)) != 7:
        parser.error("all 7 letters must be unique")

    args.letters = letters
    return args


def load_wordlist(path: Path) -> list[str]:
    """Read a wordlist file, returning one word per non-empty line.

    Args:
        path: Path to the wordlist file.

    Returns:
        List of words (preserving original casing).
    """
    words = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word:
                words.append(word)
    return words


def is_valid_word(word: str, letter_set: set[str], main_letter: str) -> bool:
    """Check whether a word is a valid Spelling Bee answer.

    Args:
        word: The candidate word.
        letter_set: Set of 7 allowed letters (lowercase).
        main_letter: The required main letter (lowercase).

    Returns:
        True if the word satisfies all puzzle constraints.
    """
    lower = word.lower()
    if len(lower) < 4:
        return False
    if main_letter not in lower:
        return False
    if not set(lower) <= letter_set:
        return False
    return True


def is_pangram(word: str, letter_set: set[str]) -> bool:
    """Check whether a word uses all 7 puzzle letters.

    Args:
        word: The candidate word.
        letter_set: Set of 7 allowed letters (lowercase).

    Returns:
        True if the word contains every letter in the set
        (and no others).
    """
    return set(word.lower()) == letter_set


def solve(
    letters: str,
    show_profanity: bool = False,
    hide_acronyms: bool = False,
) -> dict[str, list[str]]:
    """Find all valid Spelling Bee words, grouped by section.

    Args:
        letters: 7 uppercase letters; first is the main letter.
        show_profanity: Whether to include the profanity section.
        hide_acronyms: Whether to exclude the acronyms section.

    Returns:
        Dict mapping section name to sorted list of words.
    """
    main_letter = letters[0].lower()
    letter_set = set(letters.lower())

    # Wordlists in priority order (earlier sections claim words first)
    wordlist_sections: list[tuple[str, Path]] = []
    wordlist_sections.append(("Common words", WORDLISTS_DIR / "en_US_common.txt"))
    if show_profanity:
        wordlist_sections.append(
            ("Profanity", WORDLISTS_DIR / "en_US_profanity.txt")
        )
    wordlist_sections.append(
        ("Proper nouns", WORDLISTS_DIR / "en_US_proper_nouns.txt")
    )
    if not hide_acronyms:
        wordlist_sections.append(
            ("Acronyms", WORDLISTS_DIR / "en_US_acronyms.txt")
        )
    wordlist_sections.append(("Other words", WORDLISTS_DIR / "words_alpha.txt"))

    # Collect valid words per section, deduplicating across sections
    seen: set[str] = set()
    section_words: dict[str, list[str]] = {}
    all_valid: list[str] = []

    for section_name, path in wordlist_sections:
        words = load_wordlist(path)
        valid = []
        for word in words:
            if is_valid_word(word, letter_set, main_letter):
                key = word.lower()
                if key not in seen:
                    seen.add(key)
                    valid.append(word)
                    all_valid.append(word)
        section_words[section_name] = valid

    # Extract pangrams from all valid words
    pangrams_lower: set[str] = set()
    pangram_list: list[str] = []
    for word in all_valid:
        if is_pangram(word, letter_set):
            pangrams_lower.add(word.lower())
            pangram_list.append(word)

    # Remove pangrams from their original sections
    for section_name in section_words:
        section_words[section_name] = [
            w for w in section_words[section_name] if w.lower() not in pangrams_lower
        ]

    # Build final ordered output
    result: dict[str, list[str]] = {}
    result["Pangrams"] = sorted(pangram_list, key=lambda w: w.lower())

    for section_name, _ in wordlist_sections:
        words = section_words[section_name]
        if words:
            result[section_name] = sorted(words, key=lambda w: w.lower())

    return result


def format_output(sections: dict[str, list[str]]) -> str:
    """Format solver results as a human-readable string.

    Args:
        sections: Dict mapping section name to sorted list of words.

    Returns:
        Formatted multi-line string with section headers and indented words.
    """
    lines: list[str] = []
    for section_name, words in sections.items():
        if not words:
            continue
        lines.append(f"{section_name}:")
        for word in words:
            lines.append(f"  {word}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """Entry point: parse args, solve the puzzle, print results."""
    args = parse_args(argv)
    sections = solve(args.letters, args.show_profanity, args.hide_acronyms)
    output = format_output(sections)
    if output:
        print(output)


if __name__ == "__main__":
    main()
