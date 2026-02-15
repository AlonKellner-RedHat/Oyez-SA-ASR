# Legal dictionary

The dictionary cascade (used for concatenated-word split and awareness) includes an optional **legal dict** step. When `data/legal_words.txt` exists, words in that file are accepted as valid after enchant and WordNet.

## Sources (official only)

The legal word list is built **only** from these official sources. No hand-curated allowlist is used.

- **LexPredict legal dictionary** (CC-BY-SA 4.0) — [GitHub](https://github.com/LexPredict/lexpredict-legal-dictionary). Black's 1910, US Code, CFR, US Courts, Federal Acts, state codes, etc. CSV files under `en/`.
- **Open Legal Dictionary** (MIT) — [GitHub](https://github.com/digitallawyer/openlegaldictionary). Black's Law Dictionary 2nd Ed, US Courts Glossary. JSON files in `_data/` (bld.json, usc.json).
- **Wikipedia — List of Latin legal terms** — Fetched at build time from [en.wikipedia.org/wiki/List_of_Latin_legal_terms](https://en.wikipedia.org/wiki/List_of_Latin_legal_terms). The build script requests the page HTML via the Wikipedia REST API, parses the terms table, and tokenizes phrases into words. If the fetch fails (e.g. no network), the script logs a warning and continues with LexPredict and Open Legal Dictionary only.

## Regenerating data/legal_words.txt

1. Optionally clone or place the source repos under `data/legal_sources/`:
   - `data/legal_sources/lexpredict-legal-dictionary/` (LexPredict repo)
   - `data/legal_sources/openlegaldictionary/` (Open Legal Dictionary repo)
2. Run:

   ```bash
   just legal-dict
   ```

   Or: `python -m scripts.build_legal_dict`

3. Output is written to `data/legal_words.txt` (one word per line, lowercase, deduplicated).

Wikipedia is fetched every run. If the source directories are missing, the script still runs (Wikipedia words are still included when fetch succeeds); the cascade then uses whatever words were written.

## Cascade order

1. Enchant en_US (aspell, hunspell, nuspell if plugin present)
2. Enchant la (Latin dictionary, if installed — e.g. `hunspell-la` on Arch; not in Debian main, so optional)
3. NLTK WordNet
4. Legal dict (`data/legal_words.txt` when present)

To accept more Latin legal terms via the spell checker itself, install a system Latin dictionary that enchant can use. If none is installed, Latin words still come from the legal dict (Wikipedia + LexPredict + Open Legal Dictionary).

**Optional: install Latin hunspell for enchant**

- **Debian/Ubuntu** (no `hunspell-la` package in main repos): download [hunspell-la.zip](https://latin-dict.github.io/docs/hunspell-la.zip), extract `la_LA.aff` and `la_LA.dic`, then copy them to `/usr/share/hunspell/` (e.g. `sudo cp la_LA.aff la_LA.dic /usr/share/hunspell/`). Enchant will expose them as tag `la`.
- **Arch**: `yay -S hunspell-la` (or from [AUR](https://aur.archlinux.org/packages/hunspell-la)).
- The test `test_cascade_accepts_latin_via_enchant_when_la_dict_installed` verifies the cascade uses the Latin dict when it is installed; it is skipped when no `la` dictionary is available.
