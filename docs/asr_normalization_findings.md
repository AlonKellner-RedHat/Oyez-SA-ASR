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
| “No.” (negation) | No. I -- | No. I -- | Do not expand to “number”. |
| Unspoken section headers | ORAL ARGUMENT OF JEFFREY W. McCOY | *(not spoken)* | Strip for ASR. |

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
| “No.” (negation) | Expand to “number” only in citation context; leave as “No.” otherwise. |
| Standalone numbers (ages) | Two-digit in age-like context → spoken form (e.g. ninety four). |
| Unspoken section headers | Detect “ORAL ARGUMENT OF …”, all-caps labels; strip or exclude. |

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
