# ASR Normalization Findings

> Edited by Cursor – February 2026

Findings from human listening verification of Oyez oral-argument and
opinion transcripts, used to design normalization rules so training text
matches spoken pronunciation (e.g. for ASR). See
[scripts/collect_asr_artifacts.py](../scripts/collect_asr_artifacts.py)
for artifact collection and the normalization plan for implementation.

---

## 1. Discrepancy types

Differences between **original transcript text** and **actual audio
pronunciation**:

| Category | Original | Heard | Notes |
|----------|----------|-------|-------|
| Case/docket ID | 21-1164, 22-166, 13-1034 | spoken in chunks (term + number) | Not digit-by-digit. |
| v. / vs. | v. | versus | Consistent expansion. |
| Title | Mr. | Mister | Expansion. |
| Years | 2010, 1935 | twenty ten, nineteen thirty five | Spoken as years. |
| Historical year | 1215 | twelve fifteen | Year-like, not “one thousand…”. |
| Age / small number | 94 | ninety four | Spoken as number. |
| Currency | $40,000, etc. | forty thousand dollars, etc. | Symbol + number → “dollars”. |
| Section number (legal) | Section 802, 802 | Section Eight Oh Two | Digit-style, “oh” for zero. |
| Acronyms | BIA, USC | Bee I Ay, You Ess Cee (21 USC) | Spelled or letters. |
| Acronym as word | WOS | Woes | Some acronyms spoken as word, not letters. |
| “No.” (negation) | No. I -- | No. I -- | Do not expand to “number”. |
| “No.” (number/citation) | No. 96-511 | number ninety six five eleven | Expand to “number” when next token is citation. |
| Unspoken section headers | ORAL ARGUMENT OF JEFFREY W. McCOY | *(not spoken)* | Strip for ASR. |
| Vote tally | 9-0, 7-2 | nine to zero, seven to two | Separate from docket. |
| Roman numeral | VII, IV | seven, fourth / Seventh Amendment | Ordinal or spelled. |
| Percentage | 50% | fifty percent | Spoken form + “percent”. |
| Decade | 1980s | nineteen eighties | Spoken form. |
| Et al. | et al. | et al. or and others | Optional expansion. |
| Ordinal (word) | Fifth, Eighth | fifth, eighth | Confirm consistency. |
| Statute | 21 U.S.C., Title 18 | twenty one U S C, Title eighteen | Explicit row. |

### 1.1 Unspoken section headers

Some transcript segments are **section headers or labels** that appear in
the text but are **not spoken** in the audio. For example:

- **ORAL ARGUMENT OF JEFFREY W. McCOY** – appears at the start of a turn
  after “Mr. McCoy.” but is not read aloud; it is a structural header
  (speaker/label).
- Similar patterns may include other “ORAL ARGUMENT OF …”, “REBUTTAL OF …”,
  or section titles embedded in turn text.

**Implication:** For ASR training or alignment, these spans should be
detected and either **removed** from the reference text or **excluded**
from alignment so the model is not trained to “hear” text that is not
present in the audio. The artifact script or a separate pass could collect
candidate patterns (e.g. “ORAL ARGUMENT OF”, “REBUTTAL OF”, all-caps lines
at turn boundaries) for review and stripping.

### 1.2 Docket number grouping (for normalization logic)

Observed spoken patterns:

- **21-1164** → “twenty one” + “eleven sixty four” (term + 4-digit block).
- **22-166** → “twenty two” + “one sixty six” (term + 3-digit block).
- **13-1034** → “thirteen” + “ten thirty four” (term + 4-digit block).

First segment = term (spoken as a number); second segment = spoken by
digit-group (e.g. 11–64, 1–66, 10–34), not as one integer. Vote-like
patterns (e.g. 9-0, 7-2) are spoken as “nine to zero”, “seven to two” and
should be normalized separately from docket numbers.

### 1.3 Acronyms pronounced as words

Some acronyms are **spoken as words** (or word-like) rather than letter-by-letter:

- **WOS** (12-98, WOS v. EMA) → heard as **“Woes”**, not “Double-You Oh Ess”.
- **EMA** in the same case → heard as **“Ee Em Ay”** (letters). So same transcript
  can mix word-style and letter-style acronyms.

**Strategy:** Maintain an **exception table** for acronyms that are pronounced as
words. Default for unknown ALL-CAPS tokens: spell out (B, I, A). For known
word-pronunciation acronyms (e.g. WOS → Woes), substitute the spoken word.
Extend the table as verification finds more (e.g. party names, agency nicknames).
Optionally tag in artifact script: “acronym_as_word” for manual review.

---

## 2. Strategies to handle discrepancies

| Category | Strategy |
|----------|----------|
| Case IDs (docket) | Term + docket by digit-groups; vote 9-0 → nine to zero. |
| v. / vs. | Literal substitution → “versus” (word-boundary safe). |
| Mr. / Ms. / etc. | Substitution table: Mr. → Mister, Ms. → Ms. or “Miz”, etc. |
| Years (4-digit) | 19xx/20xx → spoken year. 1xxx → year-like (e.g. twelve fifteen). |
| Currency ($N) | Detect `$` + number; convert to spoken form + “dollars”. |
| Section N (legal) | Year-like (1983) → nineteen eighty three; else (802) → Eight Oh Two. |
| Acronyms (BIA, USC) | Table for known acronyms; “21 USC” → twenty one U S C. |
| Acronym-as-word (WOS, etc.) | Exception table: spell-as-word; WOS → Woes, EMA → Ee Em Ay. |
| “No.” (negation) | Leave as “No.” when next token is word (I, The, Thank, etc.). |
| “No.” (number/citation) | Expand to “number” when next token is citation (e.g. 96-511, 89-1416). |
| Standalone numbers (ages) | Two-digit in age-like context → spoken form (e.g. ninety four). |
| Unspoken section headers | Detect “ORAL ARGUMENT OF …”, all-caps labels; strip or exclude. |
| Vote tally (9-0, 7-2) | N-N → spoken numbers + “to” (nine to zero). |
| Roman numeral (VII, IV) | Context: ordinal (Seventh) or number (seven). |
| Percentage (50%) | Spoken form + “percent”. |
| Decade (1980s) | Spoken form (nineteen eighties). |
| Et al. | Optional: “and others” or leave “et al.”. |
| Ordinal (word) (Fifth, Eighth) | Already word; confirm consistency. |
| Statute citation (21 U.S.C., Title N) | N USC → N + U S C; Title N → Title + spoken N. |

---

## 3. New insights for the artifact script

Extend [scripts/collect_asr_artifacts.py](../scripts/collect_asr_artifacts.py)
to collect:

| Insight | Suggestion |
|---------|------------|
| Acronyms | ALL-CAPS 2–5 letter tokens (BIA, USC, FBI); optionally “N USC”. |
| Currency | Pattern `\$[\d,]+`; report as own category (e.g. `currency`). |
| Section vs year | Tag “Section” + 4-digit: year-like (1983) vs other (802, 2255). |
| Docket digit-length | From case_ids, analyze second-segment length (2 vs 3 vs 4 digits). |
| Historical 1xxx numbers | Extend year collection to 1xxx (e.g. 1215, 1066); tag year-like. |
| “No.” context | Record next token(s) to distinguish negation vs “number”. |
| Unspoken headers | Collect “ORAL ARGUMENT OF”, “REBUTTAL OF”, all-caps at turn boundaries. |
| Acronym-as-word | Exception table (WOS → Woes); optionally tag acronyms pronounced as words. |
| Vote tallies | Separate from case_ids; pattern N-N (single digit–single digit). |
| Roman numerals | Dedicated category (II–XII); exclude single I. |
| Percentages | `\d+%` or `\d+ percent`; normalize for report. |
| Decades | Pattern: 19xxs / 20xxs (e.g. 1980s). |
| Et al. | `et\s+al\.?` → abbreviations. |
| Word ordinals | First–Twelfth (word form) for Circuit/Amendment. |
| Statute N U.S.C. / Title N | Collect for citation normalization. |
| Awareness | Non-ASCII, mixed-case words, long all-caps, symbols: collect for awareness; no rule yet. |
| Brackets | (aaa), [aaa], {aaa}, 1) — e.g. [cough], [noise], (Inaudible); collect for awareness. |
| Leading decimals | .66, .5 — "point six six"; collect for awareness. |

---

## 4. Pronunciation verification reference

Unified table used for listening verification: what to verify, timestamps,
raw cached MP3 path, and processed transcript path.

| What to verify | Start | Stop | MP3 file | Transcript file |
|----------------|-------|------|----------|-----------------|
| versus, 21-1164 (argument) | 0:00 | 0:06 | 21-1164_20221130-argument.delivery.mp3 | 2022/21-1164/oral_argument.json |
| v., 21-1164 (opinion) | 0:00 | 0:08 | 21-1164_20230328-opinion.delivery.mp3 | 2022/21-1164/opinion.json |
| v., Eighth (22-166) | 0:00 | 0:45 | 22-166_20230525-opinion.delivery.mp3 | 2022/22-166/opinion.json |
| v. (13-1034 intro) | 0:00 | 0:08 | 13-1034_20150601-opinion.delivery.mp3 | 2014/13-1034/opinion.json |
| Section 802 (13-1034) | 0:08 | 1:00 | *(same as above)* | *(same)* |
| No. negation (21-1164) | 55:06 | 55:07 | 21-1164_20221130-argument.delivery.mp3 | 2022/21-1164/oral_argument.json |

MP3 dir: `.cache/audio/oyez.case-media.mp3/case_data/{term}/{docket}/`.
Transcript dir: `data/transcripts/`. Paths relative to repo root.
Timestamps in transcript JSON as `start`/`stop` (seconds); table uses MM:SS.

---

## 5. Analysis of new results (enhanced script)

After extending the artifact script with acronyms, currency, historical
years, unspoken headers, and “No.” context, a full run on
`data/transcripts` reported:

- **Acronyms:** 3,179 unique; top include VII, III, EPA, ERISA, II, SEC,
  FDA, EEOC, IRS, FCC, FBI, APA, BIA, USC (BIA 757, USC 340). Roman
  numerals (II, III, IV, VI, VII, etc.) dominate; legal/agency acronyms
  (BIA, USC, AEDPA, NLRB) are frequent.
- **Currency:** 2,437 unique; samples $10, $100, $1,000, $10,000,
  $100,000. Normalization should expand to spoken form + “dollars”.
- **Unspoken headers:** 2 phrase types, “ORAL ARGUMENT OF” and “RESUMED
  ORAL ARGUMENT OF”. Confirm in audio that these spans are not spoken.
- **no_dot_context:** 2,863 unique next tokens; top samples “I”, “The”,
  “No,”, “But”, “It”. “No. I” / “No. The” etc. indicate negation; “No.
  96-511” style (next token numeric) indicates citation → expand to
  “number”.
- **Historical years:** 886 unique (e.g. 1331, 1292, 1866, 1871). Treat
  as year-like for pronunciation (“twelve fifteen”, “eighteen sixty six”).

Notable: “No.” next-token distribution supports disambiguation (next
word “I”/“The”/“But” vs “96-511”/“89-1416”). Unspoken headers are rare
but must be stripped for alignment.

### 5.1 New categories (post-expansion)

The script now also reports: **vote_tally** (9-0, 7-2; separate from
case_ids), **roman_numerals** (II–XII), **percentages**, **decades**,
**ordinals_word** (Fifth, Seventh, etc.), **statute_citation** (21 U.S.C.,
Title N), and awareness categories **awareness_non_ascii**,
**awareness_mixed_case**, **awareness_all_caps_long**, **awareness_symbols**
(for unestablished rules; report-only). Rule-candidate categories:
**leading_decimal**, **non_speech_brackets**, **editorial_square_bracket**,
**dash_range**, **ellipsis**, **structural_bracket**, **numbered_list_marker**.

### 5.2 Artifact run analysis (latest run)

Summary from a full run on `data/transcripts` (as of February 2026).
Edited by Cursor.

**New verification rules (unverified):**

- **vote_tally:** 17+ unique tokens; samples 9-0, 7-2, 5-4, 6-1, 4-1 (single digit–single digit).
- **roman_numerals:** VII (4564), III (4161), II (2776), X (2369), IV (945), V, IX, VI, XI, VIII, XII.
- **percentages:** 50%, 100%, 10%, 5%, 25%, 20%, 90%, 1%, etc.; also “N percent” form.
- **decades:** 1970s (193), 1930s (160), 1950s (150), 1960s (134), 1920s (96), 1980s (92), 1990s (68), 1900s (37), 2000s (15).
- **ordinals_word:** first/second/third (most frequent), Fifth, Ninth, Fourth, Seventh, Eighth, Eleventh, Tenth, Twelfth (and lowercase variants).
- **statute_citation:** 18 U.S.C., 28 U.S.C., Title 7, Title 18, 42 U.S.C., Title 28, Title 9, 21 U.S.C., etc.

**Potential future rules (awareness):**

- **awareness_non_ascii:** U+2019 (right single quote, 78,572), U+201C/U+201D (curly quotes), U+2013 (en dash), U+2026 (ellipsis), U+2014 (em dash), U+2018, and others (accents, §, etc.). Collected for awareness only; no verification rule yet.
- **awareness_mixed_case:** LaGuardia, McCarran, McDonald, McDonnell, McConnell, TikTok, McCoy, etc.
- **awareness_all_caps_long:** CERCLA, RLUIPA, MOHELA, IIRIRA, EMTALA, ASARCO, ANILCA, HEROES, and many 6+ letter all-caps tokens.
- **awareness_symbols:** “...” (160,801), U+2013 (en dash), U+2026 (ellipsis), U+2014 (em dash).
- **Brackets (awareness):** Different bracket types and usages — *(parens)* (Inaudible) (35,066), (a)/(b)/(c) (subpoints), (Voice Overlap), (1)/(2) (numbered), (Laughter.); *[square]* [Laughter] (7,415), [Inaudible] (6,153), [Voice Overlap], [coughing], [Recess], [dollars], [noise]-style; *{curly}* rare ({Voice overlap}, {b}); *numbered* 1) 2) 3) (6,556 / 5,849 / 3,670). Many are non-speech labels (e.g. [cough], [noise]) or structural (1) 2)); normalize or strip for ASR.
- **Leading decimals (awareness):** .2 (380), .5 (54), .1 (40), .66, .38, .22 — pronounced "point two", "point six six", etc. Normalize to spoken form for ASR.

Potential future rules (from awareness categories): see §5.3 for the nine
formalized rule candidates (examples and strategy). Prioritization: leading
decimals and bracket non-speech strip first (Round 7); then structural
brackets and editorial [= X]; then Unicode/symbols; mixed-case/long
all-caps as exceptions. No verification rule or Round N table yet.

### 5.3 Potential future rules (from awareness) — formalized candidates

Each awareness check maps to at least one **new potential future rule** to add
(currently missing). Representative examples and the rule to formalize:

- **awareness_non_ascii** — Examples: U+2019 (78,572), U+201C/U+201D (28,820 /
  27,167), U+2013 (5,485), U+2026 (1,143), U+2014 (999), U+00A7 (299), U+00BD
  (36), accents (U+00E0, U+00E9).
  **Rule:** Unicode → spoken/ASCII: curly quotes → straight; U+2019 →
  apostrophe; en/em dash → hyphen or “to” in ranges; § → “section” when
  standalone; ½ → “one half”; ellipsis → omit or pause; accents keep or map to
  ASCII.
- **awareness_mixed_case** — Examples: LaGuardia (825), McCarran (647), McDonald
  (584), McDonnell (498), McConnell (395), TikTok (170), McCoy (159), YouTube
  (122), FedEx (47), PhD (22), DeKalb (96), DuPoint (73). **Rule:** Mixed-case
  token pronunciation: Mc/Mac/De/La/Di prefix names → rule or table (e.g. “McX”
  → “Mc” + name); brands/abbrev (TikTok, FedEx, PhD, YouTube) → exception table
  (word vs letters). Verify 1–2 per pattern.
- **awareness_all_caps_long** — Examples: CERCLA (296), RLUIPA (196), MOHELA
  (180), EMTALA (171), ASARCO (165); JUSTICE (37), ARGUMENT (34), ILLEGIBLE
  (21); XXVIII (27), XXXIII (12); PETITIONERS (9), ROBERTS (7). **Rule:** Long
  all-caps disambiguation: (1) Known statute/agency acronym (6+ letters) →
  acronym table or spell-out; (2) plain English word in all-caps (JUSTICE,
  ARGUMENT, ILLEGIBLE) → label/header: strip or lowercase; (3) Roman (XXVIII) →
  reuse roman numeral rule.
- **awareness_symbols** — Examples: “...” (160,801), U+2013 (5,033), U+2026
  (1,137), U+2014 (968). **Rule:** Ellipsis and dashes for speech: ellipsis
  (literal “...” or U+2026) → omit or brief pause for ASR; en/em dash in “N–M”
  ranges → “N to M” (e.g. 2010–2015 → twenty ten to twenty fifteen); elsewhere →
  hyphen or “and”.
- **awareness_brackets_parens** — Examples: (Inaudible) 35,066, (a)/(b)/(c)
  16k/16k/8k, (Voice Overlap) 13k, (1)/(2) 6k/5k, (Laughter.) 1,842, (ph) 1,332,
  (Coughing), (Audio Cut), (Colorado Revised Statutes). **Rule:** Parens: (1)
  Strip non-speech — (Inaudible), (Voice Overlap), (Laughter.), (Coughing),
  (ph), (Audio Cut), typos (Inauidble); (2) structural (a)(b)(c), (1)(2) if
  spoken → normalize to “a”/“one” etc. (verify); (3) content (Section 102),
  (Articles V and VI) → may be spoken; normalize inner text.
- **awareness_brackets_square** — Examples: [Laughter] 7,415, [Inaudible] 6,153,
  [Voice Overlap] 433, [Recess] 30, [dollars] 26, [coughing] 5; [= Mr.], [=
  VII], [= 1983], [= 10:00]; [Ginsburg: So you make]. **Rule:** Square brackets:
  (1) Strip non-speech ([Laughter], [Inaudible], [Voice Overlap], [Recess],
  [coughing], [dollars]); (2) editorial [= X] → replace with normalized form of
  X (e.g. [= Mr.] → Mister, [= 1983] → nineteen eighty three), then strip; (3)
  speaker [Name: ...] → strip or keep for diarization.
- **awareness_brackets_curly** — Examples: {Voice overlap} 1, {b} 1. **Rule:**
  Same as parens: strip non-speech labels; if structural {b} → “b” if spoken.
  Rare; fold into bracket-strip rule.
- **awareness_brackets_numbered** — Examples: 1) 6,556, 2) 5,849, 3) 3,670 … 10)
  211, 27) 56; 1970) 2, 1932) 1 (year false positives). **Rule:** Numbered list
  marker “N)”: at clause start, “1) 2) 3)” → speak as “one”/“two”/“three” (or
  “first” etc.; verify). Exclude when “N)” is year+paren (e.g. 1970)) via
  context.
- **awareness_leading_decimal** — Examples: .2 (380), .5 (54), .1 (40), .38
  (21), .22 (14), .66 (2), .1983 (1 false positive). **Rule:** Leading decimal
  “.N”: pronounce “point” + digit sequence (.2 → “point two”, .66 → “point six
  six”). Exclude .YYYY (year) by context.

Prioritization for verification and implementation: leading decimals and bracket
  non-speech strip first (Round 7); then structural brackets and editorial [=
  X]; then Unicode/symbols; mixed-case/long all-caps as exceptions. Edited by
  Cursor.

---

## 6. Round 2: verification examples for new artifact types

Unified table for listening verification of **new** artifact types.
Use only transcripts with cached MP3 under
`.cache/audio/oyez.case-media.mp3/...`.

| What to verify | Start | Stop | MP3 file | Transcript file |
|----------------|-------|------|----------|-----------------|
| Unspoken header (ORAL ARGUMENT OF … not spoken) | 0:00 | 0:06 | [21-1164_20221130-argument.delivery.mp3](../.cache/audio/oyez.case-media.mp3/case_data/2022/21-1164/21-1164_20221130-argument.delivery.mp3) | [oral_argument.json](../data/transcripts/2022/21-1164/oral_argument.json) |
| Currency, historical years, age (22-166) | 0:00 | 2:20 | [22-166_20230525-opinion.delivery.mp3](../.cache/audio/oyez.case-media.mp3/case_data/2022/22-166/22-166_20230525-opinion.delivery.mp3) | [opinion.json](../data/transcripts/2022/22-166/opinion.json) |
| Acronyms BIA, Section 802, 21 USC (13-1034) | 0:08 | 1:30 | [13-1034_20150601-opinion.delivery.mp3](../.cache/audio/oyez.case-media.mp3/case_data/2014/13-1034/13-1034_20150601-opinion.delivery.mp3) | [opinion.json](../data/transcripts/2014/13-1034/opinion.json) |

- **Unspoken header:** Turn 0 in 21-1164 argument (0.31–5.82 s) contains
  “ORAL ARGUMENT OF JEFFREY W. McCOY” after “Mr. McCoy.” Confirm only
  “We'll hear argument … Mr. McCoy.” is spoken.
- **Currency / historical years / age:** 22-166 opinion (one long turn
  0–140 s). Note how “$40,000”, “$15,000”, “$25,000”, “1215”, “1935”,
  “94” are pronounced.
- **Acronyms / Section 802:** 13-1034 opinion turn 1 (from 7.82 s) has
  “BIA”, “Section 802”, “21 USC”, “Eighth Circuit”. Confirm BIA → “Bee I
  Ay”, Section 802 → “Section Eight Oh Two”, 21 USC → “twenty one U S C”.

MP3 dir and transcript dir as in section 4. Timestamps in JSON as
`start`/`stop` (seconds).

### 6.1 Verification coverage: rules and instance count

Goal: at least **two verified instances** per rule (utterances may overlap).

| Rule | Verified instances | Source clips |
|------|--------------------|--------------|
| Case/docket ID | 4 | 21-1164 arg+opin, 22-166, 13-1034 |
| v. / vs. | 4 | same |
| Title (Mr. / Ms.) | 2 | 21-1164 arg, **20-1650 arg** (Round 3) |
| Years (19xx/20xx) | 2 | 22-166, **20-1650 arg** (Round 3) |
| Historical year (1xxx) | 2 | 22-166 (1215), **72-6041 arg** (1791) (Round 5) |
| Age / small number | 2 | 22-166 (94), **12-98** (12 and 18 hours) (Round 4) |
| Currency | 2 | 22-166, **12-98** ($42M, $2.8M) (Round 4) |
| Section number (legal) | 2 | 13-1034 (802), **20-1650 arg** (404, 2 and 3) (Round 3) |
| Acronyms (BIA, USC, etc.) | 2 | 13-1034 (BIA, USC), **20-1650 arg** (U.S.C., Section 404) (Round 3) |
| “No.” (negation) | 2 | 21-1164 arg, **20-1650 arg** “No. Thank you.” (Round 3) |
| “No.” (number/citation) | 2 | **96-511, 12-98** (Round 4) |
| Unspoken section headers | 2 | 21-1164 arg, **20-1650 arg** (Round 3) |
| Vote tally (9-0, 7-2) | 2 | **1958/290, 1964/48** (Round 6) |
| Roman numeral (VII, IV) | 2 | **72-6041 arg** (Seventh), **96-511** (V-chip→Vee) (Round 6) |
| Percentage (50%) | 2 | **72-6041** (97%), **96-511** (70%) (Round 6) |
| Decade (1980s) | 2 | **21-869** (1960s→nineteen sixties) (Round 6) |
| Ordinal (word) (Fifth, Eighth) | 2 | **72-6041** (Seventh Amendment) (Round 6) |
| Statute citation (21 U.S.C., Title N) | 2 | **72-6041, 20-1650** (Round 6) |

Rules above now have at least two verified instances. See §6.11 for
exceptions and multiple solutions (e.g. N-N, v., Roman vs acronym).
Awareness categories (non-ASCII, mixed-case, long all-caps, symbols,
brackets, leading decimals) are report-only; §5.3 lists nine formalized
potential future rules and prioritization (Round 7).
Round 6 listener transcriptions in §6.10. Use
`scripts/collect_asr_artifacts.py --need-verification` to re-check.

### 6.2 Round 3: additional clips for second instances

Clips below give a **second** verified instance for the rules in the
table above. All use cached MP3 under
`.cache/audio/oyez.case-media.mp3/...`.

| What to verify | Start | Stop | MP3 file | Transcript file |
|----------------|-------|------|----------|-----------------|
| Unspoken header, Mr., case ID, v. (20-1650) | 0:00 | 0:10 | [20-1650_20220119-argument.delivery.mp3](../.cache/audio/oyez.case-media.mp3/case_data/2021/20-1650/20-1650_20220119-argument.delivery.mp3) | [oral_argument.json](../data/transcripts/2021/20-1650/oral_argument.json) |
| No. negation “No. Thank you.” (20-1650) | 29:51 | 29:53 | *(same as above)* | *(same)* |
| Section 404, year 2010 (20-1650) | 35:02 | 37:13 | *(same as above)* | *(same)* |

- **Intro (0:00–0:10):** Turn 0 has “We'll hear argument next in Case
  20-1650, Concepcion versus United States. Mr. McCloud. ORAL ARGUMENT
  OF CHARLES L. McCLOUD” — confirm case ID → “twenty sixteen fifty”,
  v. → “versus”, Mr. → “Mister”, and that “ORAL ARGUMENT OF …” is not
  spoken.
- **No. Thank you. (29:51–29:53):** Second instance for “No.” (negation);
  do not expand to “number”.
- **Section 404, 2010 (35:02–37:13):** Government counsel; “Section 404”,
  “Sections 2 and 3”, “since 2010” — second instance for section number
  and for year. Same file also contains “18 U.S.C. 3582” later for a
  second acronym (U.S.C.) instance; use transcript to locate exact turn.

### 6.3 Round 2 listener transcriptions (from verification)

Listener verification from the Round 2 clips, documenting **original
transcript** vs **heard (audio pronunciation)**.

**1. Unspoken header — 21-1164 argument (0:00–0:06)**

| Original | Heard |
|----------|-------|
| We'll hear argument this morning in Case 21-1164, Wilkins versus the United States. Mr. McCoy. ORAL ARGUMENT OF JEFFREY W. McCOY | We'll hear argument this morning in Case twenty one eleven sixty four, Wilkins versus the United States. Mister McCoy. |

*(“ORAL ARGUMENT OF JEFFREY W. McCOY” is not spoken; header only in text.)*

**2. Case ID in opinion — 21-1164 opinion**

| Original | Heard |
|----------|-------|
| Jutice Sotomayor has the opinion of the Court this morning in case 21-1164 Wilkins v. United States. | Jutice Sotomayor has the opinion of the Court this morning in case twenty one eleven sixty four Wilkins versus United States. |

**3. Currency, years, age — 22-166 opinion (0:00–2:20)**

| Original | Heard |
|----------|-------|
| … in case 22-166, Tyler v. Hennepin County. … In 2010, Geraldine Tyler, who's now 94, … The home sold for $40,000. Tyler owed only $15,000 … the extra $25,000 … Magna Carta in 1215. … the law in 1935. | … in case twenty two one sixty six, Tyler versus Hennepin County. … In twenty ten, Geraldine Tyler, who's now ninety four, … The home sold for forty thousand dollars. Tyler owed only fifteen thousand dollars … the extra twenty five thousand dollars … Magna Carta in twelve fifteen. … the law in nineteen thirty five. |

**4. Case ID intro — 13-1034 opinion**

| Original | Heard |
|----------|-------|
| Justice Ginsburg has our opinion this morning in case 13-1034 Mellouli v. Lynch. | Justice Ginsburg has our opinion this morning in case thirteen ten thirty four Mellouli versus Lynch. |

**5. Acronyms and section numbers — 13-1034 opinion (0:08–1:30)**

| Original | Heard |
|----------|-------|
| The Board of Immigration Appeals (BIA) affirmed … Section 802 of Title 21. … as defined in 21 USC Section 802. … Section 802 limits … Section Eight Oh Two. … the BIA has … Section 802. | The Board of Immigration Appeals, of Bee I Ay, affirmed … Section Eight Oh Two of Title twenty one. … twenty one You Ess Cee Section Eight Oh Two. … Section Eight Oh Two limits … Section Eight Oh Two. … the Bee I Ay has … Section Eight Oh Two. |

**6. “No.” (negation) — 21-1164 argument**

| Original | Heard |
|----------|-------|
| No. I -- | No. I -- |

*(No expansion to “number”; negation context.)*

### 6.4 Round 3 listener transcriptions (from verification)

Listener verification from the Round 3 clips (20-1650 argument), documenting
**original transcript** vs **heard (audio pronunciation)**.

**1. Unspoken header, Mr., case ID, v. — 20-1650 argument (0:00–0:10)**

| Original | Heard |
|----------|-------|
| We'll hear argument next in Case 20-1650, Concepcion versus United States. Mr. McCloud. ORAL ARGUMENT OF CHARLES L. McCLOUD | We'll hear argument next in Case twenty sixteen fifty, Concepcion versus United States. Mister McCloud. |

*(“ORAL ARGUMENT OF CHARLES L. McCLOUD” is not spoken; case ID spoken “twenty sixteen fifty”; Mr. → Mister.)*

**2. “No.” (negation) — 20-1650 argument**

| Original | Heard |
|----------|-------|
| No. Thank you. | No. Thank you. |

*(No expansion to “number”; negation context.)*

**3a. Section 404, year 2010, Section 3553(a) — 20-1650 argument (35:02–37:13)**

| Original | Heard |
|----------|-------|
| Section 404 … Sections 2 and 3 … since 2010 … Section 404(c) … Section 3553(a) … | Section Four Oh Four … Sections Two and Three … since twenty ten … Section Four Oh Four Cee … Section thirty five fifty three Ay … |

*(Section 404 → “Section Four Oh Four”; 2010 → “twenty ten”; 75 → “seventy five”; 3553(a) → “thirty five fifty three Ay”; 404(c) → “Four Oh Four Cee”.)*

**3b. 18 U.S.C. 3582(c)(1)(A), acronym U.S.C. — 20-1650 argument**

| Original | Heard |
|----------|-------|
| 18 U.S.C. 3582(c)(1)(A). 3582(c) … (c)(1)(A) … (c)(2) … (c)(1)(B) … Rule 35 … 3553(a) … 3582(c)(1)(B) … | Eighteen You Ess Cee thirty five eighty two Cee One Ay. thirty five eighty two Cee … Cee One Ay … Cee Two … Cee One Bee … Rule thirty five … thirty five fifty three Ay … thirty five eighty two Cee One Bee … |

*(18 U.S.C. → “Eighteen You Ess Cee”; 3582(c)(1)(A) → “thirty five eighty two Cee One Ay”; (c)(1)(B) → “Cee One Bee”; Rule 35 → “Rule thirty five”.)*

### 6.5 Round 4: clips to clarify by listening

Goal: get **at least two verified instances** for **"No." (number/citation)**.
Table below listed candidate clips with cached MP3s; verified in Round 4.

| What to verify | Start | Stop | MP3 file | Transcript file |
|----------------|-------|------|----------|-----------------|
| "No." (number) 96-511 | 0:00 | 0:10 | [mp3][r4-96] | [opinion][r4-96-json] |
| "No." (number) 12-98 | 0:00 | 0:15 | [mp3][r4-12] | [opinion][r4-12-json] |

[r4-96]: ../.cache/audio/oyez.case-media.mp3/case_data/1996/96-511/19970626o_96-511.delivery.mp3
[r4-96-json]: ../data/transcripts/1996/96-511/opinion.json
[r4-12]: ../.cache/audio/oyez.case-media.mp3/case_data/2012/12-98/20130320o_12-98.delivery.mp3
[r4-12-json]: ../data/transcripts/2012/12-98/opinion.json

- **96-511 (0:00–0:10):** Turn 0: "The opinion of the Court in No. 96-511, Reno
  versus American Civil Liberty Union will be announced by Justice Stevens."
  Confirm "No." → **number** (e.g. "number ninety six five eleven").
- **12-98 (0:00–0:15):** Turn 0: "The second case is No. 12-98, WOS versus EMA."
  Confirm "No." → **number** (e.g. "number twelve ninety eight").

*Currency and age reached 2 instances via 12-98 (Round 4). Round 5 targets
historical year (1xxx) only (see §6.7).*

### 6.6 Round 4 listener transcriptions (from verification)

Listener verification from the Round 4 clips, documenting **original
transcript** vs **heard (audio pronunciation)**.

**1. “No.” (number/citation) — 96-511 opinion (0:00–0:10)**

| Original | Heard |
|----------|-------|
| The opinion of the Court in No. 96-511, Reno versus American Civil Liberty Union will be announced by Justice Stevens. | The opinion of the Court in Number Ninety Six Five Eleven, Reno versus American Civil Liberty Union will be announced by Justice Stevens. |

*(“No. 96-511” → “Number Ninety Six Five Eleven”; confirms expand to “number”
when next token is citation.)*

**2. “No.” (number/citation), WOS, EMA, currency — 12-98 opinion (0:00–opening)**

| Original | Heard |
|----------|-------|
| The second case is No. 12-98, WOS versus EMA. … $42 million … $2.8 million … 12 and 18 hours … E. M. A. … | The second case is number Twelve Ninety Eight, Woes versus Ee Em Ay. … Forty Two million Dollars … Two Point Eight million Dollars … Twelve and Eighteen hours … Ee Em Ay. … |

*(“No. 12-98” → “number Twelve Ninety Eight”. **WOS** → “Woes” (word, not
letter-by-letter). **EMA** → “Ee Em Ay” (letters). Currency and numbers as
spoken.)*

### 6.7 Round 5: clips for historical year (1xxx) — second instance

Goal: get a **second verified instance** for **historical year (1xxx)**. Achieved
in Round 5 (72-6041 argument). Table below listed the clip; listener
transcriptions in §6.8.

| What to verify | Start | Stop | MP3 file | Transcript file |
|----------------|-------|------|----------|-----------------|
| Historical year “1791” (72-6041 arg) | 4:06 | 4:24 | [19740219a_72-6041…][r5-72] | [72-6041 oral_arg][r5-72-json] |

[r5-72]: ../.cache/audio/oyez.case-media.mp3/case_data/1973/72-6041/19740219a_72-6041.delivery.mp3
[r5-72-json]: ../data/transcripts/1973/72-6041/oral_argument.json

- **72-6041 argument (4:06–4:24):** Turn 11: “1791” → “seventeen ninety one”
  (verified §6.8). Same file: “in England in 1791” in later turn (verified §6.8).

### 6.8 Round 5 listener transcriptions (from verification)

Listener verification from the Round 5 clip (72-6041 argument), documenting
**original transcript** vs **heard (audio pronunciation)** for historical year
(1xxx).

**1a. Historical year “1791” — 72-6041 argument (4:06–4:24)**

| Original | Heard |
|----------|-------|
| No, Your Honor. We're not at all asking that, but the rule seems to be clear that the tenant could assert the counterclaim in the possessory action. If the counterclaim is one which arises, one which would be tried by jury in 1791, then -- | No, Your Honor. We're not at all asking that, but the rule seems to be clear that the tenant could assert the counterclaim in the possessory action. If the counterclaim is one which arises, one which would be tried by jury in seventeen ninety one, then -- |

*(“1791” → “seventeen ninety one”; year-like pronunciation.)*

**1b. Historical year “in England in 1791” — 72-6041 argument**

| Original | Heard |
|----------|-------|
| And our point is that in England in 1791, which was the critical date for application of the Seventh Amendment -- | And our point is that in England in seventeen ninety one, which was the critical date for application of the Seventh Amendment -- |

*(“1791” → “seventeen ninety one”; confirms 1xxx historical years spoken as
year-like, not “one thousand seven hundred ninety one”.)*

### 6.9 Round 6: clips for new rules (vote tally, Roman numeral, percentage, decade, ordinal word, statute)

Goal: get **at least two verified instances** for vote tally, Roman numeral,
percentage, decade, ordinal (word), and statute citation. Table below lists
candidate clips with cached MP3s; listener transcriptions in §6.10 after
listening.

| What to verify | Start | Stop | MP3 file | Transcript file |
|----------------|-------|------|----------|-----------------|
| Vote 1958/290 | 28:10 | 28:39 | [mp3][r6-290] | [oral_arg][r6-290-json] |
| Vote 1964/48 | 104:57 | 105:21 | [mp3][r6-48] | [oral_arg][r6-48-json] |
| Roman 1964/48 | 6:51 | 8:12 | [mp3][r6-48] | [oral_arg][r6-48-json] |
| Roman V 96-511 | 28:29 | 28:32 | [mp3][r6-96] | [oral_arg][r6-96-json] |
| Pct 72-6041 | 19:43 | 20:12 | [mp3][r6-72] | [oral_arg][r6-72-json] |
| Pct 96-511 | 56:01 | 56:08 | [mp3][r6-96] | [oral_arg][r6-96-json] |
| Decade 21-869 | 83:32 | 83:51 | [mp3][r6-869] | [oral_arg][r6-869-json] |
| Ordinal 72-6041 | 7:28 | 10:22 | [mp3][r6-72] | [oral_arg][r6-72-json] |
| Statute 72-6041 | 29:01 | 33:36 | [mp3][r6-72] | [oral_arg][r6-72-json] |
| Statute 20-1650 | 50:56 | 52:46 | [mp3][r6-1650] | [oral_arg][r6-1650-json] |

[r6-290]: ../.cache/audio/oyez.case-media.mp3/case_data/1958/290/19590115a_290.delivery.mp3
[r6-290-json]: ../data/transcripts/1958/290/oral_argument.json
[r6-48]: ../.cache/audio/oyez.case-media.mp3/case_data/1964/48/19650127a_48.delivery.mp3
[r6-48-json]: ../data/transcripts/1964/48/oral_argument.json
[r6-72]: ../.cache/audio/oyez.case-media.mp3/case_data/1973/72-6041/19740219a_72-6041.delivery.mp3
[r6-72-json]: ../data/transcripts/1973/72-6041/oral_argument.json
[r6-96]: ../.cache/audio/oyez.case-media.mp3/case_data/1996/96-511/19970319a_96-511.delivery.mp3
[r6-96-json]: ../data/transcripts/1996/96-511/oral_argument.json
[r6-1650]: ../.cache/audio/oyez.case-media.mp3/case_data/2021/20-1650/20-1650_20220119-argument.delivery.mp3
[r6-1650-json]: ../data/transcripts/2021/20-1650/oral_argument.json
[r6-869]: ../.cache/audio/oyez.case-media.mp3/case_data/2022/21-869/21-869_20221012-argument.delivery.mp3
[r6-869-json]: ../data/transcripts/2022/21-869/oral_argument.json

- **1958/290 (28:10–28:39):** Vote tally; N-N → spoken numbers + “to” (e.g. nine to zero).
- **1964/48 (104:57–105:21):** Second vote-tally; turn 3 (6:51–8:12)
  Sect. 7 and 8 (Roman/ordinal).
- **96-511 (28:29–28:32):** “V-chip” → Roman “V”; (56:01–56:08) “70 percent” →
  seventy percent.
- **72-6041 (19:43–20:12):** “97%” → ninety seven percent; (7:28–10:22) Seventh
  Am.; (29:01–33:36) statute.
- **20-1650 (50:56–52:46):** “18 U.S.C. 3582(c)(1)(A)” → eighteen U S C thirty
  five eighty two.
- **21-869 (83:32–83:51):** “after the 1960s” → nineteen sixties.

### 6.10 Round 6 listener transcriptions (from verification)

Listener verification from the Round 6 clips, documenting **original
transcript** vs **heard (audio pronunciation)** for vote tally, Roman
numeral, percentage, decade, ordinal (word), statute citation, and related
patterns (document IDs, number ranges, acronyms). Edited by Cursor.

**1) Document identifier (not a vote tally)**

| Original | Heard |
|----------|-------|
| Mr. McDonald … SEC docket number -- number 818-105-1-2, United Fund EALIC sales kit pages 613 and 614. | Mister McDonald … Ess Ee Cee docket number -- number Eight Eighteen Dash One Oh Five Dash One Dash Two, United Fund Ealik sales kit pages Six Thirteen and Fourteen. |

*(SEC → Ess Ee Cee; docket 818-105-1-2 spoken digit/dash style; 613 and 614 → Six Thirteen and Fourteen; EALIC → Ealik.)*

**2) Number range (not a vote tally)**

| Original | Heard |
|----------|-------|
| It has 6-8 employees. | It has six to eight employees. |

*(N-M as range → “N to M” when not a vote or docket.)*

**3) Acronym N.O.V. (not Roman numeral)**

| Original | Heard |
|----------|-------|
| … $93,000 … $55,000 … verdict $93,000. Now all motion N.O.V. or for new trial … | … Ninety Three Thousand Dollars … Fifty Five Thousand Dollars … verdict Ninety Three Thousand Dollars. Now all motion En Oh Vee or for new trial … |

*(N.O.V. → En Oh Vee; dollar amounts → spoken form. Quote marks: “\u201c…\u201d” in transcript → “and I quote … Close the quote” in audio.)*

**4) Acronym V-chip (not Roman numeral)**

| Original | Heard |
|----------|-------|
| --Congress... that would essentially be the mandated V-chip option. | --Congress... that would essentially be the mandated Vee chip option. |

*(V-chip → Vee chip.)*

**5) Large number and percentage**

| Original | Heard |
|----------|-------|
| the 122,000 figure … 97% of those cases | the Hundred And Twenty Two Thousand figure … Ninety Seven Percent of those cases |

**6) Percent (no symbol; explicit “percent” in transcript)**

| Original | Heard |
|----------|-------|
| But if 70 percent is shielded and 30 percent isn't | But if Seventy percent is shielded and Thirty percent isn't |

*(Numbers before “percent” still spoken as words.)*

**7) Decade**

| Original | Heard |
|----------|-------|
| after the 1960s, when he was sued | after the Nineteen Sixties, when he was sued |

**8) Page, years, case names (v. → Vee), ordinals**

| Original | Heard |
|----------|-------|
| Our main brief at page 7 … Capital Traction versus Hof decided in 1899 … in England in 1791 … Since 1830 … Ross v. Bernhard in 1970 … Parsons v. Bedford … Dairy Queen v. Wood … Whitehead v. Shattuck … | Our main brief at page Seven … Capital Traction versus Hof decided in Eighteen Ninety Nine … in England in Seventeen Ninety One … Since Eighteen Thirty … Ross Vee Bernhard in Nineteen Seventy … Parsons Vee Bedford … Dairy Queen Vee Wood … Whitehead Vee Shattuck … |

*(Standalone “versus” kept; “v.” in case names → Vee. Years and page number → spoken form.)*

**9) Years, statute/code, “12 men”, “122,000”, “13702”, “600-somewhat”, “page 19”, typo**

| Original | Heard |
|----------|-------|
| in 1864 … in England in 1799 … drew the 12 men … in 1921 … these 122,000 cases … under 13702 … 600-somewhat cases … page 19 … purely equitable0 … Title 16-1501 | in Eighteen Sixty Four … in England in Seventeen Ninety Nine … drew the Twelve men … in Nineteen Twenty One … these Hundred Twenty Two Thousand cases … under Thirteen Seven Oh Two … Six Hundred-somewhat cases … page Nineteen … purely equitable … Title Fifteen -- Sixteen Fifteen Oh One |

*(Transcript typo “equitable0” → “equitable”. Code “16-1501” → “Fifteen -- Sixteen Fifteen Oh One”.)*

**10)** Already done in a previous round.

### 6.11 Rule status, verifications, and exceptions (summary)

Up-to-date status of all rules, verification counts, and situations where
**multiple solutions** or **context-dependent** handling apply. Edited by Cursor.

**Fully verified rules (≥2 instances)**

| Rule | Instances | Notes |
|------|-----------|-------|
| Case/docket ID | 4 | Term + number chunk (e.g. twenty one eleven sixty four). |
| v. / vs. | 4 | Expansion to “versus” in “X versus Y” phrasing. |
| Title (Mr. / Ms.) | 2 | Mr. → Mister. |
| Years (19xx/20xx) | 2 | Spoken as two numbers (e.g. nineteen thirty five). |
| Historical year (1xxx) | 2 | Same pattern (e.g. twelve fifteen, seventeen ninety one). |
| Age / small number | 2 | e.g. ninety four, Twelve men. |
| Currency | 2 | Symbol + number → “… thousand dollars” etc. |
| Section number (legal) | 2 | Digit-style with “oh” for zero (e.g. Eight Oh Two). |
| Acronyms (BIA, USC, SEC, etc.) | 2+ | Letter-by-letter (Bee I Ay, Ess Ee Cee). |
| “No.” (negation) | 2 | Do not expand to “number”. |
| “No.” (number/citation) | 2 | Expand to “number” when followed by citation. |
| Unspoken section headers | 2 | Strip “ORAL ARGUMENT OF …” etc. |
| Vote tally (9-0, 7-2) | 2 | nine to zero, seven to two (Round 6). |
| Roman numeral (VII, IV) | 2 | Seventh Amendment, ordinal; **but** see exceptions below. |
| Percentage (50%) | 2 | fifty percent; also “70 percent” → Seventy percent (Round 6). |
| Decade (1980s) | 2 | nineteen eighties / Nineteen Sixties (Round 6). |
| Ordinal (word) | 2 | Fifth, Eighth, Seventh (Round 6). |
| Statute citation | 2 | 21 U.S.C. → twenty one U S C; Title/code numbers spoken (Round 6). |

**Exceptions and multiple solutions**

- **N-N / N–M patterns:** Same surface form can be:
  - **Vote tally** (9-0, 7-2) → “nine to zero”, “seven to two”.
  - **Docket/ID** (818-105-1-2) → “Eight Eighteen Dash One Oh Five Dash One Dash Two”.
  - **Number range** (6-8 employees) → “six to eight”.
  **Rule:** Classify by context (sentence role, “vote”, “docket”, “employees”, etc.).
- **“v.” in text:** Two pronunciations:
  - **“X versus Y”** (e.g. Capital Traction versus Hof): “versus” already in transcript; no change.
  - **“X v. Y”** (case name): **v. → “Vee”** (Parsons v. Bedford → Parsons Vee Bedford, Ross v. Bernhard, Whitehead v. Shattuck, Dairy Queen v. Wood). So “v.” in case citations is pronounced “Vee”, not “versus”.
- **Roman numeral vs acronym:** Same letter(s) can be:
  - **Roman** (Seventh Amendment) → “Seventh”.
  - **Acronym** (N.O.V.) → “En Oh Vee”; V-chip → “Vee chip”. **Rule:** Context (Amendment vs motion name; “chip” vs numeral).
- **Percent:** With symbol (50%) or with word “percent” (70 percent) → both spoken as number + “percent” (Fifty percent, Seventy percent).
- **Document/page numbers:** Page 7 → page Seven; pages 613 and 614 → Six Thirteen and Fourteen; SEC docket 818-105-1-2 → digit/dash style (document ID, not vote).
- **Code/section with dash:** “16-1501” heard as “Fifteen -- Sixteen Fifteen Oh One” (possible “Title 16” + “1501”); “13702” → “Thirteen Seven Oh Two”. Inconsistent hyphen handling; treat as statute/code and use digit-style.
- **Transcript typos:** e.g. “equitable0” → normalize to “equitable” when generating pronunciation.
- **Quote marks:** Unicode “…” in transcript may correspond to “and I quote … Close the quote” in audio; optional normalization for ASR.

**Awareness-only (report, not yet rules)**

Non-ASCII, mixed-case, long all-caps, symbols, brackets, leading decimals
(§5.3). Prioritization: leading decimals and bracket non-speech strip (Round 7);
then structural brackets and editorial `[= X]`.
