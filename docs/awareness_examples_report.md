# Awareness categories: 3 examples + context per category

Categories have no normalization rule (awareness/review only).
Only occurrences **not covered** by any normalization rule (no overlapping rule span).

Context is transcript turn text around the matched span.

## Mixed case (e.g. McCloud) (`awareness_mixed_case`)

**Total:** 9,150 occurrences.

**Example 1** — span: 'McLaughlin'

- Path: `1967/639/oral_argument.json` turn index 1, start_index 3329
- Context: `…egislate of the area of sexual conduct. It was so stated in McLaughlin versus State of Florida. The Federal Government in all of t…`

**Example 2** — span: 'McCoy'

- Path: `2017/16-8255/oral_argument.json` turn index 164, start_index 185
- Context: `…wanted was inextricably intertwined with the alibi that Mr. McCoy wanted, that it was not purely a questionable --`

**Example 3** — span: 'TikTok'

- Path: `2024/24-656/oral_argument.json` turn index 24, start_index 57
- Context: `All right. So, if we get to that side of the issue, that TikTok U.S.A. has some sort of First Amendment right, taking your …`

## Word with digits and letters (e.g. H1N1, 2nd) (`awareness_digit_letter_mixed`)

**Total:** 5,167 occurrences.

**Example 1** — span: '2d'

- Path: `1977/77-5176/oral_argument.json` turn index 109, start_index 2511
- Context: `…ry rule by means of case law, Rickards versus State , 77 A. 2d 199 (1950). This is prior to Map. Now, our supreme court, …`

**Example 2** — span: '2d'

- Path: `1974/73-1461/oral_argument.json` turn index 97, start_index 1628
- Context: `… October of last year, it's Baggs versus Anderson in 528 P. 2d 141, that was since the briefs were filed in this case. More…`

**Example 3** — span: '640L'

- Path: `1960/18/oral_argument.json` turn index 97, start_index 1351
- Context: `…ould like to. But I have read and reread and reread Section 640L A2 of 12 U.S.C. and the way I read it, it has no application…`

## Brackets (parentheses) (`awareness_brackets_parens`)

**Total:** 2,843 occurrences.

**Example 1** — span: '(ph)'

- Path: `1970/96/oral_argument.json` turn index 174, start_index 165
- Context: `… if it gives that opportunity it ought not dilute the diets (ph) it ought to be fair. It should not weigh one man's vote gre…`

**Example 2** — span: '(.)'

- Path: `2008/08-322/oral_argument.json` turn index 250, start_index 654
- Context: `… that really runs with the land is (.) is something that we (.) we think is inherently unjustifiable. I'd also like to addr…`

**Example 3** — span: '(iv)'

- Path: `2016/16-349/oral_argument.json` turn index 29, start_index 68
- Context: `… couple other responses. One is that's not a solution to (F)(iv), to be clear, because --`

## Long all-caps (6+ letters) (`awareness_all_caps_long`)

**Total:** 1,653 occurrences.

**Example 1** — span: 'PROMESA'

- Path: `2019/18-1334/oral_argument.json` turn index 270, start_index 80
- Context: `…, you cannot say that at the same time that you've read the PROMESA statute itself. And this Court --`

**Example 2** — span: 'ASARCO'

- Path: `2004/03-1696/oral_argument.json` turn index 140, start_index 316
- Context: `…think that this... the discussion of Rooker-Feldman and the ASARCO case can be dismissed as dictum in that it was a specific r…`

**Example 3** — span: 'XXXIII'

- Path: `1973/72-6902/oral_argument.json` turn index 51, start_index 665
- Context: `…application for the warrant made out in offense under Title XXXIII of the District of Columbia Code. The issue was whether evi…`

## Brackets (square) (`awareness_brackets_square`)

**Total:** 927 occurrences.

**Example 1** — span: '[Luncheon Break]'

- Path: `1974/73-689/oral_argument.json` turn index 40, start_index 22
- Context: `If I may, Your Honor--[Luncheon Break]`

**Example 2** — span: '[Generallaughter.]'

- Path: `1987/86-1715/oral_argument.json` turn index 73, start_index 8
- Context: `--No. 0 [Generallaughter.] No, they are excellent judges. I think they regarded it as …`

**Example 3** — span: '[Generallaughter.]'

- Path: `1983/82-485/oral_argument.json` turn index 106, start_index 47
- Context: `Why don't you go to Guam while you're at it? 0 [Generallaughter.]`

## Numbered bracket (e.g. 1)) (`awareness_brackets_numbered`)

**Total:** 259 occurrences.

**Example 1** — span: '1)'

- Path: `1999/99-244/oral_argument.json` turn index 17, start_index 106
- Context: `…t happened in this particular case. The question is, given, 1) that Congress came in and categorically repudiated all of i…`

**Example 2** — span: '1)'

- Path: `1998/97-1287/oral_argument.json` turn index 21, start_index 816
- Context: `…reated a question of fact. But I think the point is is that 1) we're not bound by colloquialisms like that, and second, pe…`

**Example 3** — span: '1)'

- Path: `1994/94-6187/oral_argument.json` turn index 28, start_index 120
- Context: `…ell me the difference in the time served among these three: 1) We have an indictment for both crimes, 2) we have an indict…`

## Non-ASCII character (`awareness_non_ascii`)

**Total:** 255 occurrences.

**Example 1** — span: '′′'

- Path: `2013/12-1128/oral_argument.json` turn index 3, start_index 158
- Context: `…‵ burden of proof ′′ -- I think the word ‵‵ burden of proof ′′ used in the opinion below could be thought to be addressed …`

**Example 2** — span: '§'

- Path: `1994/94-286/opinion.json` turn index 1, start_index 1082
- Context: `…lerk today, we affirm the judgment of the Court of Appeals. § 1392(d) of 15 of the U. S. C. prohibits the state from esta…`

**Example 3** — span: '〝'

- Path: `2013/12-3/oral_argument.json` turn index 11, start_index 70
- Context: `…or, our view of this is that the -- the meaning of the term 〝 employee ″ depends on the context in which it's used and it…`

## Character other than letter, digit, or punctuation (`awareness_other_char`)

**Total:** 216 occurrences.

**Example 1** — span: '§2'

- Path: `2022/21-1086/opinion.json` turn index 0, start_index 4255
- Context: `…a also argues that its changes are necessary to ensure that §2 does not require racial proportionality in districting. Just…`

**Example 2** — span: '′′'

- Path: `2013/12-574/oral_argument.json` turn index 167, start_index 851
- Context: `… The ‵‵ shoot the gun ′′ example, the ‵‵ defraud the victim ′′ example.`

**Example 3** — span: 'Cond�'

- Path: `2022/21-869/opinion.json` turn index 1, start_index 1643
- Context: `… portrait of Prince on the cover of a magazine published by Cond� Nast. Cond� Nast's parent company is Vanity Fair. The year …`

## Leading decimal (.66) (`awareness_leading_decimal`)

**Total:** 59 occurrences.

**Example 1** — span: '.38'

- Path: `1979/78-1076/oral_argument.json` turn index 129, start_index 112
- Context: `…ballistic tests on a sawed-off shotgun the way you can on a .38 caliber pistol; is that possible?`

**Example 2** — span: '.22'

- Path: `1960/236/oral_argument.json` turn index 41, start_index 521
- Context: `… and left some of his clothes and these things, including a .22 caliber revolver, in the room. And when she discovered that…`

**Example 3** — span: '.06'

- Path: `2014/14-7955/oral_argument.json` turn index 201, start_index 183
- Context: `…drug in doses of .02 to .06, and what it showed was that at .06 dose, there was less effect than at .02. And he said, this …`

## Brackets (curly) (`awareness_brackets_curly`)

**Total:** 1 occurrences.

**Example 1** — span: '{b}'

- Path: `2009/08-1119/oral_argument.json` turn index 25, start_index 145
- Context: `…slative history or otherwise, that Congress intended the 707{b} standard to be the standard that governs what the lawyer ca…`

## Typographic/legal symbol (`awareness_symbols`)

**Total:** 0 occurrences.

*No occurrences.*
