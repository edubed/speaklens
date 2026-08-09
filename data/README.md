# Data

## `cefrj-vocabulary-profile-1.5.csv`

7,798 English headwords mapped to a CEFR level, used by the level estimator (DEC-005)
to compute which frequency bands a speaker actually reaches, instead of asking a small
language model to guess a level it cannot justify.

| Level | Words |
|-------|------:|
| A1    | 1,164 |
| A2    | 1,411 |
| B1    | 2,446 |
| B2    | 2,778 |

**Ceiling:** the CEFR-J profile stops at B2. SpeakLens therefore cannot distinguish C1
from C2, which is fine for its target user but must not be misrepresented in the report.
The [Octanove Vocabulary Profile](https://github.com/openlanguageprofiles/olp-en-octanove)
(CC BY-SA 4.0) covers C1/C2 and could lift the ceiling later.

**Sanity check.** Median Zipf frequency falls monotonically as the level rises, which is
what it should do if the level labels and independent frequency data agree:

| Level | Median Zipf |
|-------|------------:|
| A1    | 5.03 |
| A2    | 4.58 |
| B1    | 4.19 |
| B2    | 3.77 |

### Attribution

CEFR-J Vocabulary Profile, redistributed by
[Open Language Profiles](https://github.com/openlanguageprofiles/olp-en-cefrj).
Copyright belongs to **Tono Laboratory, Tokyo University of Foreign Studies (TUFS)**.
Free for research and commercial use provided the dataset is cited. Neither CEFR-J nor
Open Language Profiles is liable for inaccuracies in the data.

## `prompts.yaml`

The five elicitation prompts (DEC-008) and the unscored warm-up question.

## Word frequencies

Supplied at runtime by [`wordfreq`](https://github.com/rspeer/wordfreq), which ships its
wordlists inside the package and needs no network access. Used for words absent from the
CEFR-J profile, where the Zipf value stands in for a level band.
