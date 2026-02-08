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

1. words_alpha.txt

This is from https://github.com/dwyl/english-words, with original credit to InfoChimps at
https://web.archive.org/web/20131118073324/https://www.infochimps.com/datasets/word-list-350000-simple-english-words-excel-readable (archived).

words_alpha.txt is an all-encompassing wordlist for spellcheckers, filtered to include words only made up of letters (no hyphens or other symbols).
It lists a lot of words which would never show up in a dictionary.

2. en_US.dic (and the associated file en_US.aff)

This is an open-source English word list downloaded from http://wordlist.aspell.net/dicts/, and they are the "normal size" dictionaries (SCOWL size 60).

This list has been carefully filtered to contain only dictionary words, in their US English spellings.

### Why two word lists?

So why two word lists? In an ideal world, we could personalise the word list for every user. Then, everyone would be able to find all the words they already know and love,
and maybe learn one or two new ones. However, this is out of scope for this little project.

Using the biggest word list possible would mean we wouldn't miss any words that a given user knows and likes. However, that would also
mean we include lots of rare, outdated, or jargon words that would confuse most people and take away from the joy of finding familiar words in the puzzle. What we really want is
to output a list of common, mostly familiar words, followed by other words that the user might also know. This way, users can focus on the common words, looking up ones
they don't already know. Then, they can scan through the list of uncommon words, picking out a few that they like.

The dictionary wordlist plays the role of the list of common words. The designers of the original NYT Spelling Bee game stopped here, picking a single dictionary list for
everyone to play with. This ensured consistency and kept the game closed-ended, allowing for a carefully curated and clean experience. The NYT probably uses a slightly different
word list to the open-source one we have, but that doesn't matter.

We go one step further and include a very broad list of all English words. This makes our suggested solutions more open-ended, but allows us to capture all possible words,
making sure we don't miss any out.

### General thoughts about language - or a long justification for including the big wordlist

Language is a cultural phenomenon, and every person acquires words from those around them based on the communities they interact with and the activities they take part in.
For example, software developers are likely to know a different set of words to historians. Despite this, there is a common set of English words that is shared
between most of us, except for a few regional differences. Dictionary editors pick a certain set of words that are deemed to be in common use, based on a threshold for
how frequently they appear in writing, meaning anyone reading a dictionary will likely know some words that the dictionary doesn't contain. Of course, the dictionary might
in turn contain words that a given reader might not know.

I refrained from using the word jargon in the last paragraph. Jargon refers to words that are only used within a specific field, like software development. The word "jargon" often
has a negative connotation, because people outside the field use "jargon" to refer to words they don't understand and that they want software developers to stop
using around them. And I agree: when speaking to someone, it's a good idea to pick words that the other person will understand. However, that's not a reason to hate on all
jargon. People create words to talk about shared concepts, and software developers have plenty of shared concepts they need to talk about at work. Moreover, jargon
words often end up diffusing into general usage. Even before they do, they end up forming part of everyday lexicon for the people in the field. This just means that
software developers end up with their own mini-dialect, in a similar way to regional dialects like the English spoken in Scotland. There's nothing wrong with this: language
is a continuum, and personal preference plays a big role in which words someone chooses to include in their repertoire.

This is all to say that even the weirdest words in the big broad wordlist might be someone's favourite word that they use every day, so it's worth including.
