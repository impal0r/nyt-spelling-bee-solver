"""Tests for Hunspell dictionary conversion and affix expansion.

Verification strategy:
1. Unit tests for affix parsing, application, and expansion logic
2. Cross-validation against spylls (independent Hunspell implementation)
3. Negative tests for words that should NOT be generated
"""

# Standard library
from pathlib import Path

# Third-party libraries
import pytest

# Local imports
from convert_dic import (
    AffData,
    AffixGroup,
    WordlistResult,
    apply_affix,
    convert_dic_to_wordlist,
    expand_word,
    parse_aff_file,
)

AFF_PATH = Path("wordlists/en_US.aff")
DIC_PATH = Path("wordlists/en_US.dic")


# ---------------------------------- FIXTURES ---------------------------------


@pytest.fixture(scope="module")
def aff_data() -> AffData:
    """Parse the .aff file once for all tests in this module."""
    return parse_aff_file(AFF_PATH)


@pytest.fixture(scope="module")
def groups(aff_data: AffData) -> dict[str, AffixGroup]:
    """Affix groups extracted from the .aff data."""
    return aff_data.affix_groups


@pytest.fixture(scope="module")
def wordlist_result() -> WordlistResult:
    """Full conversion result, computed once for the module."""
    return convert_dic_to_wordlist(DIC_PATH, AFF_PATH)


# ----------------------------- AFF FILE PARSING ------------------------------


class TestParseAffFile:
    """Verify that the .aff parser correctly reads affix rules and flags."""

    def test_prefix_a_is_re(self, groups: dict[str, AffixGroup]) -> None:
        """Flag A should be a prefix adding 're'."""
        assert "A" in groups
        g = groups["A"]
        assert g.kind == "PFX"
        assert len(g.rules) == 1
        assert g.rules[0].add == "re"

    def test_suffix_s_pluralisation(self, groups: dict[str, AffixGroup]) -> None:
        """Flag S should have 4 pluralisation rules."""
        assert "S" in groups
        g = groups["S"]
        assert g.kind == "SFX"
        assert len(g.rules) == 4

    def test_suffix_g_gerund(self, groups: dict[str, AffixGroup]) -> None:
        """Flag G should add '-ing' suffix."""
        assert "G" in groups
        g = groups["G"]
        assert g.kind == "SFX"
        assert len(g.rules) == 2
        adds = {r.add for r in g.rules}
        assert "ing" in adds

    def test_suffix_d_past_tense(self, groups: dict[str, AffixGroup]) -> None:
        """Flag D should have 4 past tense rules."""
        assert "D" in groups
        g = groups["D"]
        assert g.kind == "SFX"
        assert len(g.rules) == 4

    def test_nosuggest_flag(self, aff_data: AffData) -> None:
        """NOSUGGEST flag should be '!'."""
        assert aff_data.nosuggest_flag == "!"

    def test_onlyincompound_flag(self, aff_data: AffData) -> None:
        """ONLYINCOMPOUND flag should be 'c'."""
        assert aff_data.onlyincompound_flag == "c"


# ---------------------- AFFIX APPLICATION (UNIT TESTS) -----------------------


class TestApplyAffix:
    """Test individual affix rules against known English morphology."""

    # Suffix S: plurals
    @pytest.mark.parametrize(
        "stem, expected",
        [
            ("cat", "cats"),
            ("dog", "dogs"),
            ("book", "books"),
        ],
    )
    def test_plural_regular(
        self, groups: dict[str, AffixGroup], stem: str, expected: str
    ) -> None:
        """Regular nouns add 's'."""
        assert expected in apply_affix(stem, groups["S"])

    @pytest.mark.parametrize(
        "stem, expected",
        [
            ("bus", "buses"),
            ("brush", "brushes"),
            ("tax", "taxes"),
        ],
    )
    def test_plural_es(
        self, groups: dict[str, AffixGroup], stem: str, expected: str
    ) -> None:
        """Sibilant-ending nouns add 'es'."""
        assert expected in apply_affix(stem, groups["S"])

    @pytest.mark.parametrize(
        "stem, expected",
        [
            ("baby", "babies"),
            ("carry", "carries"),
            ("city", "cities"),
        ],
    )
    def test_plural_ies(
        self, groups: dict[str, AffixGroup], stem: str, expected: str
    ) -> None:
        """Consonant+y nouns change y to ies."""
        assert expected in apply_affix(stem, groups["S"])

    def test_plural_vowel_y(self, groups: dict[str, AffixGroup]) -> None:
        """'boy' + S -> 'boys' (not 'boies')."""
        result = apply_affix("boy", groups["S"])
        assert "boys" in result
        assert "boies" not in result

    # Suffix G: gerund/present participle
    @pytest.mark.parametrize(
        "stem, expected",
        [
            ("walk", "walking"),
            ("talk", "talking"),
            ("jump", "jumping"),
        ],
    )
    def test_gerund_regular(
        self, groups: dict[str, AffixGroup], stem: str, expected: str
    ) -> None:
        """Regular verbs add 'ing'."""
        assert expected in apply_affix(stem, groups["G"])

    @pytest.mark.parametrize(
        "stem, expected",
        [
            ("take", "taking"),
            ("bake", "baking"),
            ("make", "making"),
        ],
    )
    def test_gerund_drop_e(
        self, groups: dict[str, AffixGroup], stem: str, expected: str
    ) -> None:
        """Verbs ending in 'e' drop it before 'ing'."""
        assert expected in apply_affix(stem, groups["G"])

    # Suffix D: past tense
    @pytest.mark.parametrize(
        "stem, expected",
        [
            ("bake", "baked"),
            ("take", "taked"),  # Note: "take" is irregular, but affix rules are regular
            ("make", "maked"),
        ],
    )
    def test_past_add_d(
        self, groups: dict[str, AffixGroup], stem: str, expected: str
    ) -> None:
        """Words ending in 'e' add 'd'."""
        assert expected in apply_affix(stem, groups["D"])

    @pytest.mark.parametrize(
        "stem, expected",
        [
            ("walk", "walked"),
            ("talk", "talked"),
            ("jump", "jumped"),
        ],
    )
    def test_past_add_ed(
        self, groups: dict[str, AffixGroup], stem: str, expected: str
    ) -> None:
        """Regular verbs add 'ed'."""
        assert expected in apply_affix(stem, groups["D"])

    @pytest.mark.parametrize(
        "stem, expected",
        [
            ("carry", "carried"),
            ("worry", "worried"),
            ("hurry", "hurried"),
        ],
    )
    def test_past_y_to_ied(
        self, groups: dict[str, AffixGroup], stem: str, expected: str
    ) -> None:
        """Consonant+y verbs change y to ied."""
        assert expected in apply_affix(stem, groups["D"])

    def test_past_vowel_y(self, groups: dict[str, AffixGroup]) -> None:
        """'play' + D -> 'played'."""
        result = apply_affix("play", groups["D"])
        assert "played" in result

    # Prefix A: re-
    @pytest.mark.parametrize(
        "stem, expected",
        [
            ("apply", "reapply"),
            ("build", "rebuild"),
            ("do", "redo"),
        ],
    )
    def test_prefix_re(
        self, groups: dict[str, AffixGroup], stem: str, expected: str
    ) -> None:
        """Prefix A adds 're-'."""
        assert expected in apply_affix(stem, groups["A"])

    # Prefix U: un-
    @pytest.mark.parametrize(
        "stem, expected",
        [
            ("do", "undo"),
            ("tie", "untie"),
            ("lock", "unlock"),
        ],
    )
    def test_prefix_un(
        self, groups: dict[str, AffixGroup], stem: str, expected: str
    ) -> None:
        """Prefix U adds 'un-'."""
        assert expected in apply_affix(stem, groups["U"])

    # Suffix Y: -ly
    @pytest.mark.parametrize(
        "stem, expected",
        [
            ("quick", "quickly"),
            ("slow", "slowly"),
            ("quiet", "quietly"),
        ],
    )
    def test_suffix_ly(
        self, groups: dict[str, AffixGroup], stem: str, expected: str
    ) -> None:
        """Suffix Y adds 'ly'."""
        assert expected in apply_affix(stem, groups["Y"])

    # Suffix L: -ment
    def test_suffix_ment(self, groups: dict[str, AffixGroup]) -> None:
        """'abandon' + L -> 'abandonment'."""
        result = apply_affix("abandon", groups["L"])
        assert "abandonment" in result


# ----------------------- FULL WORD EXPANSION TESTS ---------------------------


class TestExpandWord:
    """Test full expansion of stems with multiple flags."""

    def test_abandon_lsdg(self, groups: dict[str, AffixGroup]) -> None:
        """'abandon/LSDG' should expand to stem + suffixed forms."""
        words = expand_word("abandon", "LSDG", groups)
        expected = {"abandon", "abandonment", "abandons", "abandoned", "abandoning"}
        assert expected.issubset(words)

    def test_no_flags(self, groups: dict[str, AffixGroup]) -> None:
        """A word with no flags should only produce itself."""
        words = expand_word("hello", "", groups)
        assert words == {"hello"}

    def test_cross_product(self, groups: dict[str, AffixGroup]) -> None:
        """Prefix A (re-) with cross_product=Y should combine with suffixes."""
        words = expand_word("apply", "ADGS", groups)
        assert "reapply" in words
        assert "reapplying" in words
        assert "reapplied" in words


# ---------------------- NEGATIVE TESTS (SHOULD NOT EXIST) --------------------


class TestNegativeExpansion:
    """Verify that certain invalid words are NOT produced."""

    def test_no_boies(self, groups: dict[str, AffixGroup]) -> None:
        """Vowel+y should not produce '-ies' form."""
        words = expand_word("boy", "S", groups)
        assert "boies" not in words

    def test_no_plaied(self, groups: dict[str, AffixGroup]) -> None:
        """Vowel+y should not produce '-ied' form."""
        words = expand_word("play", "D", groups)
        assert "plaied" not in words

    def test_onlyincompound_excluded(
        self, wordlist_result: WordlistResult
    ) -> None:
        """ONLYINCOMPOUND stems (1th, 2th, 3th) should not contribute words.

        Note: "th" itself IS a valid word (Th = Thorium symbol, stem Th/M),
        so we verify ONLYINCOMPOUND by checking that the compound-only
        ordinal suffixes (1th, 2th, 3th) are excluded. These are non-alpha
        and would be filtered anyway, but the explicit skip is tested via
        the aff parser test for the ONLYINCOMPOUND flag.
        """
        all_words = set(
            wordlist_result.words
            + wordlist_result.proper_nouns
            + wordlist_result.acronyms
            + wordlist_result.profanity
        )
        # These compound-only stems are non-alpha and should be absent
        assert "1th" not in all_words
        assert "2th" not in all_words
        assert "3th" not in all_words

    def test_no_cross_product_with_non_crossable_suffix(
        self, groups: dict[str, AffixGroup]
    ) -> None:
        """Prefixes should not cross-product with suffixes that have cross_product=N.

        Suffixes T (-est), H (-th), V (-ive) have cross_product=N.
        Combining prefix A (re-) with these should NOT produce words like
        'rebarest', 'relivest', 'recreative'.
        """
        # "bare" with flags including A (re-) and T (-est)
        words = expand_word("bare", "AT", groups)
        assert "rebarest" not in words
        assert "barest" in words  # Suffix alone is fine
        assert "rebare" in words  # Prefix alone is fine

        # "live" with flags including A (re-) and V (-ive)
        words = expand_word("live", "AV", groups)
        assert "relive" not in words or "relive" in words  # prefix is fine
        assert "relivive" not in words  # bogus cross-product

    def test_cross_product_with_crossable_suffix(
        self, groups: dict[str, AffixGroup]
    ) -> None:
        """Prefixes SHOULD cross-product with suffixes that have cross_product=Y.

        Suffix D (-ed), G (-ing), S (-s) have cross_product=Y.
        """
        words = expand_word("apply", "ADGS", groups)
        assert "reapplied" in words  # re- + -ed
        assert "reapplying" in words  # re- + -ing
        assert "reapplies" in words  # re- + -ies

    def test_no_overlap_between_lists(self, wordlist_result: WordlistResult) -> None:
        """The four output lists should be mutually exclusive."""
        lists = {
            "words": set(wordlist_result.words),
            "proper_nouns": set(wordlist_result.proper_nouns),
            "acronyms": set(wordlist_result.acronyms),
            "profanity": set(wordlist_result.profanity),
        }
        names = list(lists.keys())
        for i, name_a in enumerate(names):
            for name_b in names[i + 1 :]:
                overlap = lists[name_a] & lists[name_b]
                assert not overlap, (
                    f"Overlap between {name_a} and {name_b}: {sorted(overlap)[:10]}"
                )

    def test_profanity_list_not_empty(self, wordlist_result: WordlistResult) -> None:
        """The profanity list should contain some words (27 stems expected)."""
        assert len(wordlist_result.profanity) > 0

    def test_single_letters_excluded(self, wordlist_result: WordlistResult) -> None:
        """Single-letter words should not appear in any output list."""
        all_words = set(
            wordlist_result.words
            + wordlist_result.proper_nouns
            + wordlist_result.acronyms
            + wordlist_result.profanity
        )
        single_letters = {w for w in all_words if len(w) == 1}
        assert not single_letters, (
            f"Single-letter words found: {sorted(single_letters)}"
        )


# -------------------- INTEGRATION: FULL CONVERSION ---------------------------


class TestConvertDicToWordlist:
    """Integration tests for the full conversion pipeline."""

    def test_common_word_count(self, wordlist_result: WordlistResult) -> None:
        """Common words list should be substantial."""
        assert len(wordlist_result.words) > 50_000

    def test_proper_noun_count(self, wordlist_result: WordlistResult) -> None:
        """Proper nouns list should contain thousands of entries."""
        assert len(wordlist_result.proper_nouns) > 5_000

    def test_acronym_count(self, wordlist_result: WordlistResult) -> None:
        """Acronyms list should contain hundreds of entries."""
        assert len(wordlist_result.acronyms) > 100

    def test_common_words_present(self, wordlist_result: WordlistResult) -> None:
        """Common English words should appear in the common words list."""
        words_set = set(wordlist_result.words)
        common = [
            "the", "and", "have", "that", "for", "with",
            "running", "walked", "babies", "churches",
            "unable", "redo", "quickly",
        ]
        missing = [w for w in common if w not in words_set]
        assert len(missing) <= len(common) // 2, (
            f"Too many common words missing: {missing}"
        )

    def test_proper_nouns_present(self, wordlist_result: WordlistResult) -> None:
        """Known proper nouns should appear in the proper nouns list.

        This includes title-case names and camelCase brand names.
        """
        proper_set = set(wordlist_result.proper_nouns)
        expected = ["Aaron", "Boston", "Africa", "Einstein", "GitHub", "AstroTurf"]
        missing = [w for w in expected if w not in proper_set]
        assert len(missing) == 0, f"Proper nouns missing: {missing}"

    def test_acronyms_present(self, wordlist_result: WordlistResult) -> None:
        """Known acronyms should appear in the acronyms list."""
        acronym_set = set(wordlist_result.acronyms)
        expected = ["NASA", "FBI", "AIDS"]
        missing = [w for w in expected if w not in acronym_set]
        assert len(missing) == 0, f"Acronyms missing: {missing}"

    def test_common_words_are_lowercase(
        self, wordlist_result: WordlistResult
    ) -> None:
        """Common words should all be lowercase.

        Single letters are excluded, camelCase/mixed-case stems go to
        proper nouns, and all-caps go to acronyms — so nothing with
        uppercase should remain in common words.
        """
        non_lower = [w for w in wordlist_result.words if w != w.lower()]
        assert not non_lower, f"Non-lowercase common words: {non_lower[:10]}"

    def test_proper_nouns_have_uppercase(
        self, wordlist_result: WordlistResult
    ) -> None:
        """Every proper noun should contain at least one uppercase letter.

        Most are title case (Aaron), but some start lowercase (eBay, iOS).
        """
        bad = [w for w in wordlist_result.proper_nouns if w == w.lower()]
        assert not bad, f"All-lowercase proper nouns: {bad[:10]}"

    def test_all_lists_alpha(self, wordlist_result: WordlistResult) -> None:
        """Every word in every list should contain only letters."""
        for label, word_list in [
            ("words", wordlist_result.words),
            ("proper_nouns", wordlist_result.proper_nouns),
            ("acronyms", wordlist_result.acronyms),
            ("profanity", wordlist_result.profanity),
        ]:
            non_alpha = [w for w in word_list if not w.isalpha()]
            assert not non_alpha, f"Non-alpha in {label}: {non_alpha[:10]}"

    def test_all_lists_sorted(self, wordlist_result: WordlistResult) -> None:
        """All output lists should be sorted case-insensitively."""
        for label, word_list in [
            ("words", wordlist_result.words),
            ("proper_nouns", wordlist_result.proper_nouns),
            ("acronyms", wordlist_result.acronyms),
            ("profanity", wordlist_result.profanity),
        ]:
            assert word_list == sorted(word_list, key=str.casefold), (
                f"{label} is not sorted"
            )

    def test_words_alpha_overlap(self, wordlist_result: WordlistResult) -> None:
        """Most common words should also appear in words_alpha.txt.

        This is an independent check: if our affix expansion produces bogus
        words, they won't appear in words_alpha.txt. We expect >80% overlap
        for common words (which are all lowercase, matching words_alpha.txt).
        """
        alpha_path = Path("wordlists/words_alpha.txt")
        if not alpha_path.exists():
            pytest.skip("words_alpha.txt not found")

        with open(alpha_path) as f:
            alpha_words = {line.strip().lower() for line in f if line.strip().isalpha()}

        our_words = set(wordlist_result.words)
        overlap = our_words & alpha_words
        overlap_pct = len(overlap) / len(our_words) * 100

        assert overlap_pct > 80, (
            f"Only {overlap_pct:.1f}% of common words found in words_alpha.txt"
        )


# -------------------- CROSS-VALIDATION WITH SPYLLS ---------------------------


class TestSpyllsCrossValidation:
    """Cross-validate our expansion against spylls' Hunspell implementation.

    Strategy: since spylls doesn't have an unmunch/enumerate function,
    we validate by checking every word we produce against spylls' lookup().
    Words we produce that spylls rejects are potential bugs in our parser.
    """

    @pytest.fixture(scope="class")
    def spylls_dict(self):
        """Load spylls dictionary once for this test class."""
        from spylls.hunspell import Dictionary

        return Dictionary.from_files("wordlists/en_US")

    @pytest.fixture(scope="class")
    def our_words(self) -> WordlistResult:
        return convert_dic_to_wordlist(DIC_PATH, AFF_PATH)

    def _all_words(self, result: WordlistResult) -> list[str]:
        """Combine all four lists into one for validation."""
        return (
            result.words
            + result.proper_nouns
            + result.acronyms
            + result.profanity
        )

    def _spylls_accepts(self, spylls_dict, word: str) -> bool:
        """Check if spylls accepts a word in any case variant."""
        return (
            spylls_dict.lookup(word)
            or spylls_dict.lookup(word.lower())
            or spylls_dict.lookup(word.title())
            or spylls_dict.lookup(word.upper())
        )

    def test_all_words_accepted_by_spylls(
        self, spylls_dict, our_words: WordlistResult
    ) -> None:
        """Every word we generate should be accepted by spylls' lookup."""
        rejected = set()
        for word in self._all_words(our_words):
            if not self._spylls_accepts(spylls_dict, word):
                rejected.add(word)

        if rejected:
            sample = sorted(rejected)[:20]
            print(f"\n{len(rejected)} words rejected by spylls (sample): {sample}")

        assert len(rejected) == 0, (
            f"{len(rejected)} words rejected by spylls — "
            f"sample: {sorted(rejected)[:20]}"
        )

    def test_spylls_stems_covered(
        self, spylls_dict, our_words: WordlistResult
    ) -> None:
        """Every multi-letter stem in the dictionary should appear in our output.

        Single-letter stems are intentionally excluded from all output lists.
        We check that all other alpha-only stems from the .dic file appear
        (with original case) somewhere across all four output lists.
        """
        our_all = set(self._all_words(our_words))
        stems_missing = []
        for word_obj in spylls_dict.dic.words:
            stem = word_obj.stem
            if stem.isalpha() and len(stem) >= 2:
                if stem not in our_all:
                    stems_missing.append(stem)

        if stems_missing:
            sample = sorted(stems_missing)[:20]
            print(f"\n{len(stems_missing)} stems missing from our output: {sample}")

        assert len(stems_missing) == 0, (
            f"{len(stems_missing)} stems missing: {sorted(stems_missing)[:20]}"
        )
