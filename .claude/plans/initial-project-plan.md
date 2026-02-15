This project will result in a command-line utility which can solve word puzzles in the format of the NYT Spelling Bee.

Inputs:
- The 7 letters in the puzzle
- The "main" letter (this will always be given as the first one of the seven)

Outputs (in order):
- Pangrams (words using all 7 letters)
- Common words (from `wordlists/en_US_common.txt`)
- Profanity (from `wordlists/en_US_profanity.txt`, opt-in with `--show-profanity`)
- Proper nouns (from `wordlists/en_US_proper_nouns.txt`)
- Acronyms (from `wordlists/en_US_acronyms.txt`, opt-out with `--no-acronyms`)
- Other words (from `wordlists/words_alpha.txt`, excluding words already shown)

## Puzzle rules

- In the original puzzle the player is presented with 7 letters arranged in a hexagonal pattern. One letter (the "main" letter) is in the centre, with 6 others around it.
- In this command-line version, the letters are instead presented in a string where "main" letter comes first
- The 7 given letters are always different, e.g. AABCDEF is an invalid puzzle
- The goal of the puzzle is to find as many valid words as possible based on the 7 given letters
- Valid words contain only the given letters, and no others
- Valid words must contain the "main" letter at least once
- Letters can be repeated in a valid word
- Valid words must be at least 4 letters long
- A valid word that contains each of the 7 letters at least once is called a pangram.
- A given puzzle may contain 0 or more pangrams
- For example if the puzzle is LAERTIV:
  - REAL is a valid word
  - LITTLE is a valid word
  - TIRE is an invalid word, because it doesn't contain the "main" letter L
  - LET is an inavlid word, because it's less than 4 letters long
  - LAYER is an invalid word, because it contains the letter Y, which isn't in the puzzle
  - RELATIVE is a pangram
  - RELATIVELY is an invalid word, because it contains the letter Y, which isn't in the puzzle

## Text-based output format

```
Pangrams:
  ...
Common words:
  ...
Profanity:           (only shown with --show-profanity flag)
  ...
Proper nouns:
  ...
Acronyms:            (hidden with --no-acronyms flag)
  ...
Other words:
  ...
```

- Sections appear in the order above. Each section only lists words not already shown in a prior section.
- Words could be output on separate lines, or perhaps in a grid. Alphabetical order is desirable in each section.
- Pangrams should be on separate lines - there are usually one or two, perhaps up to five, so they won't take up much space.
- The words are indented by two spaces, maintaining a hierarchical structure with the headings.
- **`--show-profanity`**: Include profanity section (excluded by default).
- **`--no-acronyms`**: Exclude acronyms section (included by default).
- "Other words" contains anything from words_alpha.txt not already covered by earlier sections.

## Wordlists

All wordlist files live in the `wordlists/` directory.

In this project, the aim is to find ALL words which would solve the puzzle. We use two sources for this purpose:

### Source 1: Hunspell dictionary (en_US.dic + en_US.aff)

**Source:** Open-source English word list downloaded from http://wordlist.aspell.net/dicts/, "normal size" dictionaries (SCOWL size 60). These are Hunspell dictionary files, used by spellcheckers in LibreOffice, Firefox, Chrome, etc.

**Conversion:** `convert_dic.py` expands the Hunspell stems using affix rules and produces four plain-text wordlists, classified by stem case. The converter has been verified against spylls (an independent Hunspell implementation) with zero discrepancies. Run it with: `python convert_dic.py wordlists/en_US`

**Output files (plain text, one word per line, sorted case-insensitively):**

| File | Content | Count |
|------|---------|-------|
| `en_US_common.txt` | Common words from lowercase stems | ~78k |
| `en_US_proper_nouns.txt` | Proper nouns and brand names (any stem with uppercase that isn't all-caps: title case, camelCase, etc.) | ~11k |
| `en_US_acronyms.txt` | Acronyms from all-caps stems (e.g. NASA, FBI) | ~700 |
| `en_US_profanity.txt` | Words from NOSUGGEST-flagged stems | ~50 |

Single-letter words are excluded from all lists. When a word is produced by multiple stems with different classifications, higher-priority categories win (profanity > acronyms > proper nouns > common).

### Source 2: words_alpha.txt (~370k words)

**Source:** https://github.com/dwyl/english-words, with original credit to InfoChimps at
https://web.archive.org/web/20131118073324/https://www.infochimps.com/datasets/word-list-350000-simple-english-words-excel-readable (archived).

**File format:** Plain text, one lowercase word per line. No metadata or annotations. Can be read directly with simple line-by-line parsing.

**Content:** An all-encompassing wordlist for spellcheckers, filtered to include words only made up of letters (no hyphens or other symbols).
It lists a lot of words which would never show up in a dictionary.

### Why two sources?

We want to output a list of common, familiar dictionary words, followed by less common words that the user might also know. This mirrors the NYT Spelling Bee experience (which uses a curated dictionary) while going a step further to capture words the NYT list might miss.

- **en_US wordlists** provide the core results — common words, proper nouns, acronyms, and profanity, all from a curated dictionary.
- **words_alpha.txt** provides a broad net to catch any remaining valid words (shown in the "Other words" section), including domain-specific or uncommon words that might still be familiar to some users.

No single word list is perfect for everyone, since vocabulary is personal and shaped by background, profession, and interests. Using multiple tiers lets users focus on the common words first, then scan the broader list for any they recognise.

## Implementation considerations

- **Hunspell expansion:** Done. `convert_dic.py` is a verified custom parser that expands en_US.dic stems using affix rules from en_US.aff. It handles PFX/SFX rules, cross-product (only when both prefix and suffix allow it), NOSUGGEST, and ONLYINCOMPOUND flags. Cross-validated against spylls with zero discrepancies.
- **Deduplication:** Each output section should only show words not already listed in a prior section.
- **Performance:** Not a primary concern. Up to ~10 seconds per run is acceptable. No need to optimise for speed unless it exceeds that threshold.
