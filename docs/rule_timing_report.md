# Rule timing report

All rules in order of total time (scan + normalize, first 100 transcripts).

## Bottlenecks (how to speed up)

- **split_word_merge** (≈40% of total): Consider optimizing scan or normalizer for this rule.

| Rank | Rule | Scan (s) | Normalize (s) | Total (s) | % |
| ---:| --- | ---: | ---: | ---: | ---: |
| 1 | split_word_merge | 5.28 | 0.06 | 5.35 | 39.8 |
| 2 | latin_extended | 0.02 | 2.67 | 2.69 | 20.0 |
| 3 | repeated_word_accept | 1.10 | 0.00 | 1.10 | 8.2 |
| 4 | global_repeated_word_accept | 0.54 | 0.00 | 0.54 | 4.0 |
| 5 | concatenated_word_split | 0.47 | 0.00 | 0.48 | 3.5 |
| 6 | typo_levenshtein | 0.33 | 0.00 | 0.33 | 2.5 |
| 7 | short_mixed_acronym | 0.29 | 0.00 | 0.29 | 2.1 |
| 8 | single_digit_valid_word | 0.28 | 0.00 | 0.28 | 2.1 |
| 9 | digit_letter_mixed | 0.21 | 0.00 | 0.21 | 1.5 |
| 10 | inline_typo | 0.20 | 0.00 | 0.20 | 1.5 |
| 11 | replacement_char_fix | 0.14 | 0.00 | 0.14 | 1.0 |
| 12 | trailing_dash_accept | 0.13 | 0.00 | 0.13 | 0.9 |
| 13 | mixed_case_accept_6plus | 0.11 | 0.00 | 0.11 | 0.8 |
| 14 | half_number | 0.11 | 0.00 | 0.11 | 0.8 |
| 15 | dash | 0.09 | 0.00 | 0.09 | 0.7 |
| 16 | title_abbreviation | 0.07 | 0.00 | 0.07 | 0.5 |
| 17 | fraction | 0.07 | 0.00 | 0.07 | 0.5 |
| 18 | non_speech_brackets | 0.07 | 0.00 | 0.07 | 0.5 |
| 19 | known_mixed_case_entities | 0.07 | 0.00 | 0.07 | 0.5 |
| 20 | known_names | 0.06 | 0.00 | 0.06 | 0.5 |
| 21 | numbered_list_marker | 0.06 | 0.00 | 0.06 | 0.4 |
| 22 | all_caps_accept | 0.05 | 0.00 | 0.05 | 0.4 |
| 23 | pascal_case_accept | 0.05 | 0.00 | 0.05 | 0.4 |
| 24 | letter_dash_sequence | 0.05 | 0.00 | 0.05 | 0.4 |
| 25 | years | 0.05 | 0.00 | 0.05 | 0.4 |
| 26 | leading_decimal | 0.05 | 0.00 | 0.05 | 0.4 |
| 27 | percentages | 0.05 | 0.00 | 0.05 | 0.4 |
| 28 | ordinals | 0.05 | 0.00 | 0.05 | 0.4 |
| 29 | roman_numerals | 0.05 | 0.00 | 0.05 | 0.4 |
| 30 | time_of_day | 0.05 | 0.00 | 0.05 | 0.4 |
| 31 | single_letter_parens | 0.05 | 0.00 | 0.05 | 0.4 |
| 32 | decades | 0.05 | 0.00 | 0.05 | 0.4 |
| 33 | number_parens | 0.05 | 0.00 | 0.05 | 0.4 |
| 34 | vote_tally | 0.05 | 0.00 | 0.05 | 0.4 |
| 35 | double_letter_parens | 0.05 | 0.00 | 0.05 | 0.4 |
| 36 | name_pattern_di | 0.05 | 0.00 | 0.05 | 0.3 |
| 37 | common_acronym | 0.04 | 0.00 | 0.04 | 0.3 |
| 38 | section_header | 0.04 | 0.00 | 0.04 | 0.3 |
| 39 | open_double_quote | 0.04 | 0.00 | 0.04 | 0.3 |
| 40 | close_double_quote | 0.04 | 0.00 | 0.04 | 0.3 |
| 41 | special_currency | 0.02 | 0.00 | 0.02 | 0.2 |
| 42 | bracket_sentence_unwrap | 0.01 | 0.00 | 0.01 | 0.1 |
| 43 | dual_notation | 0.01 | 0.00 | 0.01 | 0.1 |
| 44 | editorial_dollar | 0.01 | 0.00 | 0.01 | 0.1 |
| 45 | bracket_acronym | 0.01 | 0.00 | 0.01 | 0.0 |
| 46 | currency | 0.01 | 0.00 | 0.01 | 0.0 |
| 47 | symbol_section | 0.01 | 0.00 | 0.01 | 0.0 |
| 48 | symbol_section_ref | 0.01 | 0.00 | 0.01 | 0.0 |
| 49 | symbol_copyright | 0.01 | 0.00 | 0.01 | 0.0 |
| 50 | symbol_pound | 0.01 | 0.00 | 0.01 | 0.0 |
| 51 | letter_roman_clause | 0.01 | 0.00 | 0.01 | 0.0 |
| 52 | roman_parens | 0.01 | 0.00 | 0.01 | 0.0 |
| 53 | website_dot | 0.01 | 0.00 | 0.01 | 0.0 |
| 54 | invalid_question_mark_fix | 0.00 | 0.00 | 0.00 | 0.0 |
