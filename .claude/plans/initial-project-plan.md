This project will result in a command-line utility which can solve word puzzles in the format of the NYT Spelling Bee.

Inputs:
- The 7 letters in the puzzle
- The "main" letter (this will always be given as the first one of the seven)

Outputs:
- A list of verified US English words which solve the puzzle (these come from the wordlist in en_US.dic)
- A list of unverified English words which solve the puzzle (these come from the wordlist in words_alpha.txt)

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
Dictionary words:
  ...
Other words:
  ...
```

- Words could be output on separate lines, or perhaps in a grid. Alphabetical order is desirable in each section.
- Pangrams should be on separate lines - there are usually one or two, perhaps up to five, so they won't take up much space.
- The words are indented by two spaces, maintaining a hierarchical structure with the three headings.

## Wordlists

In this project, the aim is to find ALL words which would solve the puzzle. We have two wordlists for this purpose:

### 1. words_alpha.txt (~370k words)

**Source:** https://github.com/dwyl/english-words, with original credit to InfoChimps at
https://web.archive.org/web/20131118073324/https://www.infochimps.com/datasets/word-list-350000-simple-english-words-excel-readable (archived).

**File format:** Plain text, one lowercase word per line. No metadata or annotations. Can be read directly with simple line-by-line parsing.

**Content:** An all-encompassing wordlist for spellcheckers, filtered to include words only made up of letters (no hyphens or other symbols).
It lists a lot of words which would never show up in a dictionary.

### 2. en_US.dic + en_US.aff (~49k stems, expands to many more words)

**Source:** Open-source English word list downloaded from http://wordlist.aspell.net/dicts/, "normal size" dictionaries (SCOWL size 60).

**Content:** Carefully filtered to contain only dictionary words, in their US English spellings.

**File format:** These are Hunspell dictionary files, used by spellcheckers in LibreOffice, Firefox, Chrome, etc. The two files work together:

- **en_US.dic** contains word stems with optional affix flags after a `/`. The first line is the approximate word count. Examples:
  - `abandon/LSDG` — the stem "abandon" with suffix flags L, S, D, G
  - `abacus/MS` — the stem "abacus" with suffix flags M, S
  - `AAA` — a word with no affix flags (used as-is)

- **en_US.aff** defines affix rules that the flags refer to. Each rule specifies how to transform a stem into inflected forms. For example:
  - Flag `S` defines pluralisation rules (e.g. add "s", or replace "y" with "ies")
  - Flag `G` defines "-ing" suffixation (e.g. strip "e" and add "ing", or just add "ing")
  - Flag `D` defines past tense rules (e.g. add "d", add "ed", replace "y" with "ied")
  - Prefix flags like `A` (re-), `U` (un-), `I` (in-) add common prefixes

**Implication for this project:** To get the full set of dictionary words, we need to expand the stems using the affix rules. For example, `abandon/LSDG` expands to: abandon, abandons, abandoned, abandoning, etc. We should either use a Hunspell library (e.g. `spylls` — a pure-Python Hunspell implementation) or write our own affix expansion logic.

### Why two word lists?

We want to output a list of common, familiar dictionary words, followed by less common words that the user might also know. This mirrors the NYT Spelling Bee experience (which uses a curated dictionary) while going a step further to capture words the NYT list might miss.

- **en_US.dic** provides the "dictionary words" — common, widely-recognised words that form the core results.
- **words_alpha.txt** provides a broad net to catch any remaining valid words, including domain-specific or uncommon words that might still be familiar to some users.

No single word list is perfect for everyone, since vocabulary is personal and shaped by background, profession, and interests. Using two tiers lets users focus on the common words first, then scan the broader list for any they recognise.

## Implementation considerations

- **Hunspell expansion:** Processing en_US.dic requires expanding stems with affix rules from en_US.aff. Evaluate whether a library like `spylls` is suitable, or whether a simpler custom parser covering the subset of rules in our .aff file would suffice.
- **Word filtering:** Both wordlists may contain uppercase entries (proper nouns, acronyms). The Spelling Bee only uses lowercase common words, so these should be filtered out.
- **Deduplication:** Words appearing in both lists should only be shown in the "Dictionary words" section, not repeated in "Other words".
- **Performance:** words_alpha.txt is ~4MB. For a CLI tool, loading time should still be fast, but if it becomes a concern, consider pre-filtering or indexing.
