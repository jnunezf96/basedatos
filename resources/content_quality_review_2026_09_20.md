# Corpus content review — 2026-09-20

## Scope and method

The Chef reviewed displayed excerpts from a deterministic first/middle/last sample of each of the 27 raw source labels: 81 records. Long comments were truncated in the review output; this is not a line-by-line review of every long comment or a statistically representative sample. An independent worker profiled the core text fields of all 275,734 records for extraction debris, incomplete HTML endings, technical placeholders, encoding patterns, blank fields, and exact four-field duplicates.

This is a content review. Previously completed identity, bootstrap, and U+0012 work is not counted as evidence that all lexical content is correct. Historical spelling, diacritics, editorial layers, and legitimate source-dependent omissions are preserved.

## Findings and disposition

1. **Confirmed source-backed alignment error — one record corrected and independently verified:** `1565-sahagun-escolios:000774` (`momati`, “pensar”). Its displayed example highlighted `tlalpilli (65)` from the first numbering cycle. The preserved raw witness also contains a later `momatque (65)` passage, with a separate “pensar” gloss. Sibling `1565-sahagun-escolios:001473` links the first `tlalpilli` occurrence to “cosa atada.” The narrow correction selects the later occurrence and its corresponding gloss context; raw witnesses and lexical fields must remain unchanged. Repair evidence is recorded in `resources/sahagun_000774_alignment_2026_09_20.json`. Independent acceptance confirmed that only this record changed across the corpus, all raw and lexical fields remained unchanged, the later witness and gloss offsets match the preserved transcription exactly, current display consumers agree, and all 27 changed derived assets have record/posting changes confined to this target. The corresponding SQLite update was also confined to this record. This finding is supported by the internally preserved transcription and sibling records; no new manuscript facsimile verification was performed. The owner’s reference-number profile flags 320 of 1,547 Escolios records with repeated references, including 99 carrying review or invalidation markers. These are review candidates, not 320 or 99 confirmed errors.

2. **Closing-tag repair completed — 139 Wimmer records:** the original inventory below had `Comentario` values terminating in incomplete `</`. Independent strict parsing found exactly one unmatched `<b>` and no earlier tag mismatch in all 529 affected fields: 272 current commentary fields and 257 raw counterparts. With explicit user authorization, each string received only `b>`, completing `</b>`; no prose was added or removed. The original 139 complete records remain in `resources/wimmer_terminal_html_2026_09_20_originals.jsonl.gz`, and the complete corpus before-image is backed up. Independent full-corpus comparison confirmed exactly those 529 suffix changes, preserved all other values and ordering, and verified affected rows, indexes, Pair projection, and SQLite consistency. Native browser checks on three representative comments confirmed removal of the visible terminal markup artifact while preserving prose. Details: `resources/wimmer_terminal_html_2026_09_20_change.json`. Whether any source continuation was lost before import remains unknown; closing the tag does not certify that the whole commentary is complete.

3. **Literal-markup candidates — two Máynez records:** `1580-sahagun-maynez:001480` and `1580-sahagun-maynez:001723`. The former contains escaped `<b>: </b>` in an editorial note. Source-aware review is needed before deciding how to render or correct it. The Wimmer `&amp;c;` matches are historical abbreviation markup, not evidence of an encoding defect.

4. **Duplicate content requiring provenance review — 132 extra records:** exact same-source tuples of Original, Editado, Traducción, and Comentario, including 73 extras in Olmos_V. Distinct record identifiers and other provenance may reflect legitimate source entries. No deduplication is authorized by this heuristic alone.

5. **Not classified as errors:** CF Index translations often contain reference locators, consistent with its index role. Blank editions, translations, or comments are source-dependent and not automatically missing data. No technical-placeholder or robust mojibake pattern matched the scanned core fields in this pass. This is a bounded pattern result, not a guarantee of error-free text.

## Per-source inventory and sample IDs

Counts in the duplicate column are extra records after the first matching four-field tuple. Blank counts are observations, not confirmed defects.

| Raw source | Rows | Blank edition with original | Blank translation | Duplicate extras | First / middle / last sample IDs |
|---|---:|---:|---:|---:|---|
| 153? Trilingüe | 12165 | 55 | 0 | 0 | `153-trilingue:000001`; `153-trilingue:006083`; `153-trilingue:012165` |
| 1547 Olmos_G | 868 | 0 | 0 | 2 | `1547-olmos-g:000001`; `1547-olmos-g:000435`; `1547-olmos-g:000868` |
| 1547 Olmos_V ? | 2008 | 4 | 3 | 73 | `1547-olmos-v:000001`; `1547-olmos-v:001005`; `1547-olmos-v:002008` |
| 1551-95 Documentos nahuas de la Ciudad de México | 3144 | 49 | 0 | 0 | `1551-95-documentos-nahuas-de-la-ciudad-de-mexico:000001`; `1551-95-documentos-nahuas-de-la-ciudad-de-mexico:001573`; `1551-95-documentos-nahuas-de-la-ciudad-de-mexico:003144` |
| 1565 Sahagún Escolios | 1547 | 0 | 0 | 0 | `1565-sahagun-escolios:000001`; `1565-sahagun-escolios:000774`; `1565-sahagun-escolios:001547` |
| 1571 Molina 1 | 36248 | 0 | 0 | 35 | `1571-molina-1:000001`; `1571-molina-1:018125`; `1571-molina-1:036248` |
| 1571 Molina 2 | 24188 | 5 | 6 | 2 | `1571-molina-2:000001`; `1571-molina-2:012095`; `1571-molina-2:024188` |
| 1579 Durán | 413 | 0 | 0 | 0 | `1579-duran:000001`; `1579-duran:000207`; `1579-duran:000413` |
| 1580 CF Index | 53619 | 1 | 0 | 0 | `1580-cf-index:000001`; `1580-cf-index:026810`; `1580-cf-index:053619` |
| 1580 Sahagún/Máynez | 2207 | 2 | 2 | 0 | `1580-sahagun-maynez:000001`; `1580-sahagun-maynez:001104`; `1580-sahagun-maynez:002207` |
| 1595 Rincón | 705 | 1 | 0 | 0 | `1595-rincon:000001`; `1595-rincon:000353`; `1595-rincon:000705` |
| 1598 Tezozomoc | 1887 | 0 | 0 | 0 | `1598-tezozomoc:000001`; `1598-tezozomoc:000944`; `1598-tezozomoc:001887` |
| 1611 Arenas | 2165 | 30 | 0 | 0 | `1611-arenas:000001`; `1611-arenas:001083`; `1611-arenas:002165` |
| 1629 Alarcón | 1566 | 16 | 1 | 0 | `1629-alarcon:000001`; `1629-alarcon:000784`; `1629-alarcon:001566` |
| 1645 Carochi | 2728 | 12 | 0 | 0 | `1645-carochi:000001`; `1645-carochi:001365`; `1645-carochi:002728` |
| 1692 Guerra | 919 | 0 | 0 | 0 | `1692-guerra:000001`; `1692-guerra:000460`; `1692-guerra:000919` |
| 1759 Paredes | 2023 | 0 | 0 | 0 | `1759-paredes:000001`; `1759-paredes:001012`; `1759-paredes:002023` |
| 1765 Cortés y Zedeño | 4724 | 0 | 0 | 6 | `1765-cortes-y-zedeno:000001`; `1765-cortes-y-zedeno:002363`; `1765-cortes-y-zedeno:004724` |
| 1780 ? Bnf_361 | 28260 | 31 | 14 | 8 | `1780-bnf-361:000001`; `1780-bnf-361:014131`; `1780-bnf-361:028260` |
| 1780 Clavijero | 3303 | 39 | 41 | 0 | `1780-clavijero:000001`; `1780-clavijero:001652`; `1780-clavijero:003303` |
| 17?? Bnf_362 | 5136 | 2 | 0 | 2 | `17-bnf-362:000001`; `17-bnf-362:002569`; `17-bnf-362:005136` |
| 17?? Bnf_362bis | 920 | 18 | 4 | 1 | `17-bnf-362bis:000001`; `17-bnf-362bis:000461`; `17-bnf-362bis:000920` |
| 1984 Tzinacapan | 2940 | 1 | 0 | 0 | `1984-tzinacapan:000001`; `1984-tzinacapan:001471`; `1984-tzinacapan:002940` |
| 1992 Karttunen | 6407 | 0 | 1 | 0 | `1992-karttunen:000001`; `1992-karttunen:003204`; `1992-karttunen:006407` |
| 2002 Mecayapan | 3183 | 7 | 0 | 0 | `2002-mecayapan:000001`; `2002-mecayapan:001592`; `2002-mecayapan:003183` |
| 2021 Wimmer | 42464 | 0 | 0 | 3 | `2021-wimmer:000001`; `2021-wimmer:021233`; `2021-wimmer:042464` |
| V94 Diccionario Global SNP | 29997 | 0 | 0 | 0 | `v94-diccionario-global-snp:000001`; `v94-diccionario-global-snp:014999`; `v94-diccionario-global-snp:029997` |

## Wimmer incomplete-ending record inventory

`2021-wimmer:001073`, `2021-wimmer:002889`, `2021-wimmer:003105`, `2021-wimmer:003390`, `2021-wimmer:003441`, `2021-wimmer:003626`, `2021-wimmer:004278`, `2021-wimmer:004315`, `2021-wimmer:004486`, `2021-wimmer:004546`, `2021-wimmer:004601`, `2021-wimmer:004798`, `2021-wimmer:005006`, `2021-wimmer:005062`, `2021-wimmer:005140`, `2021-wimmer:005319`, `2021-wimmer:005730`, `2021-wimmer:005746`, `2021-wimmer:005838`, `2021-wimmer:006028`, `2021-wimmer:006053`, `2021-wimmer:006072`, `2021-wimmer:006397`, `2021-wimmer:006531`, `2021-wimmer:006834`, `2021-wimmer:007090`, `2021-wimmer:007225`, `2021-wimmer:008724`, `2021-wimmer:009372`, `2021-wimmer:009526`, `2021-wimmer:009594`, `2021-wimmer:009598`, `2021-wimmer:010069`, `2021-wimmer:010136`, `2021-wimmer:010293`, `2021-wimmer:010363`, `2021-wimmer:010423`, `2021-wimmer:010454`, `2021-wimmer:010517`, `2021-wimmer:010803`, `2021-wimmer:010824`, `2021-wimmer:011367`, `2021-wimmer:011376`, `2021-wimmer:011438`, `2021-wimmer:011461`, `2021-wimmer:011481`, `2021-wimmer:011897`, `2021-wimmer:012205`, `2021-wimmer:012379`, `2021-wimmer:012513`, `2021-wimmer:012846`, `2021-wimmer:013136`, `2021-wimmer:013336`, `2021-wimmer:013431`, `2021-wimmer:013635`, `2021-wimmer:013643`, `2021-wimmer:014086`, `2021-wimmer:014152`, `2021-wimmer:014878`, `2021-wimmer:014995`, `2021-wimmer:015393`, `2021-wimmer:015837`, `2021-wimmer:015859`, `2021-wimmer:016039`, `2021-wimmer:016363`, `2021-wimmer:016377`, `2021-wimmer:016582`, `2021-wimmer:017227`, `2021-wimmer:017241`, `2021-wimmer:017433`, `2021-wimmer:017812`, `2021-wimmer:018065`, `2021-wimmer:018303`, `2021-wimmer:018982`, `2021-wimmer:019055`, `2021-wimmer:019131`, `2021-wimmer:020410`, `2021-wimmer:020425`, `2021-wimmer:020583`, `2021-wimmer:020589`, `2021-wimmer:021127`, `2021-wimmer:021485`, `2021-wimmer:022147`, `2021-wimmer:022309`, `2021-wimmer:022652`, `2021-wimmer:023377`, `2021-wimmer:024565`, `2021-wimmer:024588`, `2021-wimmer:026232`, `2021-wimmer:026427`, `2021-wimmer:026999`, `2021-wimmer:027028`, `2021-wimmer:027089`, `2021-wimmer:027107`, `2021-wimmer:027214`, `2021-wimmer:027231`, `2021-wimmer:027533`, `2021-wimmer:027826`, `2021-wimmer:028103`, `2021-wimmer:028118`, `2021-wimmer:028179`, `2021-wimmer:028274`, `2021-wimmer:028454`, `2021-wimmer:028740`, `2021-wimmer:029025`, `2021-wimmer:029244`, `2021-wimmer:030087`, `2021-wimmer:030089`, `2021-wimmer:030098`, `2021-wimmer:030183`, `2021-wimmer:030187`, `2021-wimmer:030497`, `2021-wimmer:030810`, `2021-wimmer:031449`, `2021-wimmer:031532`, `2021-wimmer:031865`, `2021-wimmer:032385`, `2021-wimmer:032957`, `2021-wimmer:033318`, `2021-wimmer:033451`, `2021-wimmer:033609`, `2021-wimmer:033646`, `2021-wimmer:033699`, `2021-wimmer:033886`, `2021-wimmer:034104`, `2021-wimmer:035277`, `2021-wimmer:035504`, `2021-wimmer:035598`, `2021-wimmer:035932`, `2021-wimmer:036163`, `2021-wimmer:037211`, `2021-wimmer:037523`, `2021-wimmer:037833`, `2021-wimmer:037970`, `2021-wimmer:038532`, `2021-wimmer:039385`, `2021-wimmer:039439`, `2021-wimmer:041566`, `2021-wimmer:041650`

## Review evidence

Local review artifacts: `/tmp/nahuatl-chef-corpus-content/stratified-81-sample.json` (Chef sample), `/tmp/corpus-content-profile/profile.json` (counts/examples), and `/tmp/corpus-content-profile/wimmer-truncated-candidates.json` (139 original candidate records). These are local evidence paths, not deployed dependencies. The durable source counts, sample IDs, dispositions, and malformed-ending IDs are reproduced above.

## Subsequent bounded corrections

The nine remaining Spanish-only Wimmer markup cases were separately reviewed and repaired without reconstructing prose: four closing-tag completions and eight orphan-marker removals across nine records. See `resources/wimmer_spanish_nine_2026_09_20_change.json`.

A subsequent deterministic ten-record Escolios review confirmed and corrected five numbering-cycle mismatches, leaving five records unchanged. See `resources/escolios_first_ten_review_2026_09_20.md` for the exact selection, per-record disposition, and uncertainty limits, and `resources/sahagun_five_cycles_2026_09_20_change.json` for the correction ledger. The initial candidate counts above remain historical triage counts, not claims that every remaining candidate is incorrect.
