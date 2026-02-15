"""Convert a Hunspell .dic + .aff file pair to a plain text wordlist."""

# Standard library
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AffixRule:
    """A single affix rule (one line of a PFX/SFX block)."""

    strip: str  # Characters to strip from the stem ("0" means none)
    add: str  # Characters to add
    condition: str  # Regex-style condition the stem must match


@dataclass
class AffixGroup:
    """A group of affix rules sharing one flag character."""

    kind: str  # "PFX" or "SFX"
    flag: str  # Single-character flag
    cross_product: bool  # Whether this can combine with other affixes
    rules: list[AffixRule] = field(default_factory=list)


@dataclass
class AffData:
    """All parsed data from a Hunspell .aff file."""

    affix_groups: dict[str, AffixGroup]
    nosuggest_flag: str  # Flag character for NOSUGGEST (profanity), "" if none
    onlyincompound_flag: str  # Flag character for ONLYINCOMPOUND, "" if none


@dataclass
class WordlistResult:
    """Result of converting a Hunspell dictionary to word lists."""

    words: list[str]  # Common words — lowercase stems (sorted, alpha-only)
    proper_nouns: list[str]  # Title-case stems, e.g. "Aaron" (sorted, alpha-only)
    acronyms: list[str]  # All-caps stems, e.g. "ABC" (sorted, alpha-only)
    profanity: list[str]  # NOSUGGEST words (sorted, alpha-only)


def parse_aff_file(aff_path: Path) -> AffData:
    """Parse a Hunspell .aff file and return affix data.

    Parses PFX/SFX rules plus NOSUGGEST and ONLYINCOMPOUND flags.
    Other directives (REP, COMPOUNDRULE, etc.) are ignored since they
    aren't needed for word expansion.

    Args:
        aff_path: Path to the .aff file.

    Returns:
        AffData containing affix groups and special flag characters.
    """
    groups: dict[str, AffixGroup] = {}
    nosuggest_flag = ""
    onlyincompound_flag = ""

    with open(aff_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            directive = parts[0]

            if directive == "NOSUGGEST":
                nosuggest_flag = parts[1]
                continue
            if directive == "ONLYINCOMPOUND":
                onlyincompound_flag = parts[1]
                continue

            if directive not in ("PFX", "SFX"):
                continue

            flag = parts[1]

            # Header line: PFX/SFX flag cross_product count
            if len(parts) == 4 and parts[3].isdigit():
                cross = parts[2] == "Y"
                groups[flag] = AffixGroup(
                    kind=directive, flag=flag, cross_product=cross
                )
                continue

            # Rule line: PFX/SFX flag strip add condition
            if len(parts) >= 5 and flag in groups:
                strip = parts[2]
                add = parts[3]
                condition = parts[4]
                groups[flag].rules.append(
                    AffixRule(strip=strip, add=add, condition=condition)
                )

    return AffData(
        affix_groups=groups,
        nosuggest_flag=nosuggest_flag,
        onlyincompound_flag=onlyincompound_flag,
    )


def _condition_to_regex(condition: str, kind: str) -> re.Pattern[str]:
    """Convert a Hunspell condition string to a compiled regex.

    Args:
        condition: Hunspell condition (e.g. ".", "[^aeiou]y", "e").
        kind: "PFX" or "SFX" — determines anchoring.

    Returns:
        Compiled regex pattern.
    """
    if condition == ".":
        # Matches anything
        return re.compile(".")

    # The condition is already mostly regex-compatible.
    # Anchor it to the start (prefix) or end (suffix) of the word.
    if kind == "PFX":
        return re.compile("^" + condition)
    else:
        return re.compile(condition + "$")


def apply_affix(stem: str, group: AffixGroup) -> list[str]:
    """Apply all rules in an affix group to a stem.

    Args:
        stem: The base word to apply affixes to.
        group: The affix group containing the rules.

    Returns:
        List of new words produced by applying matching rules.
    """
    results = []

    for rule in group.rules:
        pattern = _condition_to_regex(rule.condition, group.kind)
        if not pattern.search(stem):
            continue

        strip = "" if rule.strip == "0" else rule.strip
        add = "" if rule.add == "0" else rule.add

        if group.kind == "SFX":
            if strip:
                if stem.endswith(strip):
                    new_word = stem[: -len(strip)] + add
                else:
                    continue
            else:
                new_word = stem + add
        else:  # PFX
            if strip:
                if stem.startswith(strip):
                    new_word = add + stem[len(strip) :]
                else:
                    continue
            else:
                new_word = add + stem

        results.append(new_word)

    return results


def expand_word(
    stem: str, flags: str, affix_groups: dict[str, AffixGroup]
) -> set[str]:
    """Expand a stem with its affix flags into all possible word forms.

    Handles single prefixes, single suffixes, and cross-product
    combinations (prefix + suffix applied together).

    Args:
        stem: The base word.
        flags: String of single-character affix flags.
        affix_groups: All parsed affix groups from the .aff file.

    Returns:
        Set of all expanded words, including the stem itself.
    """
    words = {stem}

    prefix_groups = []
    suffix_groups = []

    for flag in flags:
        group = affix_groups.get(flag)
        if group is None:
            continue
        if group.kind == "PFX":
            prefix_groups.append(group)
        else:
            suffix_groups.append(group)

    # Apply each suffix to the stem, tracking which allow cross-product
    crossable_suffixed: list[str] = []
    for sfx_group in suffix_groups:
        new_words = apply_affix(stem, sfx_group)
        words.update(new_words)
        if sfx_group.cross_product:
            crossable_suffixed.extend(new_words)

    # Apply each prefix to the stem
    for pfx_group in prefix_groups:
        new_words = apply_affix(stem, pfx_group)
        words.update(new_words)

        # Cross-product: only combine prefix+suffix when BOTH allow it
        if pfx_group.cross_product:
            for sfx_word in crossable_suffixed:
                cross_words = apply_affix(sfx_word, pfx_group)
                words.update(cross_words)

    return words


def _is_acronym(stem: str) -> bool:
    """Check if a stem is an acronym (all caps, e.g. "ABC")."""
    return len(stem) > 1 and stem.isupper()


def _has_uppercase(stem: str) -> bool:
    """Check if a stem contains any uppercase letter."""
    return any(c.isupper() for c in stem)


def convert_dic_to_wordlist(dic_path: Path, aff_path: Path) -> WordlistResult:
    """Convert a Hunspell .dic + .aff pair into sorted word lists.

    Expands all stems using their affix flags, filters to alphabetic-only
    words with length >= 2, and classifies them based on stem case:
    - Lowercase stems → common words
    - All-caps stems → acronyms
    - Any other stem with uppercase (title case, camelCase, etc.) → proper nouns
    - NOSUGGEST-flagged stems → profanity (regardless of case)

    Single-letter words are excluded from all lists. Stems flagged
    ONLYINCOMPOUND are skipped entirely. Original case is preserved.

    Args:
        dic_path: Path to the .dic file.
        aff_path: Path to the .aff file.

    Returns:
        WordlistResult with .words, .proper_nouns, .acronyms, and .profanity.
    """
    aff_data = parse_aff_file(aff_path)
    affix_groups = aff_data.affix_groups
    common_words: set[str] = set()
    proper_noun_words: set[str] = set()
    acronym_words: set[str] = set()
    profanity_words: set[str] = set()

    with open(dic_path, encoding="utf-8") as f:
        lines = f.readlines()

    # First line is the word count — skip it
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        # Split into stem and flags
        if "/" in line:
            stem, flags = line.split("/", 1)
        else:
            stem, flags = line, ""

        # Skip ONLYINCOMPOUND stems (e.g. "1th", "2th", "3th")
        if aff_data.onlyincompound_flag and aff_data.onlyincompound_flag in flags:
            continue

        expanded = expand_word(stem, flags, affix_groups)

        # Classify based on NOSUGGEST flag first, then stem case
        if aff_data.nosuggest_flag and aff_data.nosuggest_flag in flags:
            profanity_words.update(expanded)
        elif _is_acronym(stem):
            acronym_words.update(expanded)
        elif _has_uppercase(stem):
            proper_noun_words.update(expanded)
        else:
            common_words.update(expanded)

    # Filter to alpha-only words with length >= 2, preserving original case
    def _filter_alpha(word_set: set[str]) -> set[str]:
        return {w for w in word_set if w.isalpha() and len(w) >= 2}

    profanity = _filter_alpha(profanity_words)
    acronyms = _filter_alpha(acronym_words) - profanity
    proper_nouns = _filter_alpha(proper_noun_words) - profanity - acronyms
    # Remove words claimed by higher-priority categories from common words
    words = _filter_alpha(common_words) - profanity - acronyms - proper_nouns

    return WordlistResult(
        words=sorted(words, key=str.casefold),
        proper_nouns=sorted(proper_nouns, key=str.casefold),
        acronyms=sorted(acronyms, key=str.casefold),
        profanity=sorted(profanity, key=str.casefold),
    )


def main() -> None:
    """Entry point: convert a .dic + .aff pair to a plain text wordlist."""
    if len(sys.argv) < 2:
        print("Usage: python convert_dic.py <prefix> [output_dir]")
        print("  e.g. python convert_dic.py wordlists/en_US")
        print("  reads wordlists/en_US.dic + .aff, writes en_US_common.txt + others")
        sys.exit(1)

    prefix = Path(sys.argv[1])
    dic_path = prefix.with_suffix(".dic")
    aff_path = prefix.with_suffix(".aff")
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else prefix.parent

    if not dic_path.exists():
        print(f"Error: {dic_path} not found")
        sys.exit(1)
    if not aff_path.exists():
        print(f"Error: {aff_path} not found")
        sys.exit(1)

    result = convert_dic_to_wordlist(dic_path, aff_path)

    def _write_list(words: list[str], path: Path, label: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for word in words:
                f.write(word + "\n")
        print(f"Wrote {len(words)} {label} to {path}")

    for label, word_list in [
        ("common", result.words),
        ("proper_nouns", result.proper_nouns),
        ("acronyms", result.acronyms),
        ("profanity", result.profanity),
    ]:
        if word_list:
            path = output_dir / f"{prefix.name}_{label}.txt"
            _write_list(word_list, path, label)


if __name__ == "__main__":
    main()
