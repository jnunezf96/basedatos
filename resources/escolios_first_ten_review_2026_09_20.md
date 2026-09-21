# First bounded Escolios repeated-reference review — 2026-09-20

The Chef selected the first ten record IDs, in ascending order, from the intersection of the prior repeated-reference review inventory and records still carrying both a current review flag and an invalidated alignment span. This intersection contained 19 records. Record `1565-sahagun-escolios:000774`, already corrected, was excluded. The initial broader proposal based on 658 flags was not used.

The owner and independent reviewer compared each displayed passage and its neighboring numbered glosses with the internally preserved transcription. This was not a new manuscript-facsimile verification or a general review of the remaining corpus. Five records had confirmed numbering-cycle mismatches; five received no change. “No change” means no demonstrated cycle error in this bounded review, not certification of every word or historical metadata field.

| Record suffix (all `1565-sahagun-escolios:`) | Disposition | Source-based reason |
|---|---|---|
| `000130` | Unchanged | The displayed first-cycle `totonillotl (94)` passage is paired with the heat gloss. The later repeated 94 refers to a different passage and gloss. |
| `000158` | Unchanged | The first-cycle clothing/adornment passage and its 77 gloss agree; the adjacent source forms are supported by the same gloss. |
| `000162` | Unchanged | The first-cycle head-binding passage includes `contzonilpique`, with the corresponding 81 head-binding gloss. |
| `000318` | Corrected | The display attached “estar esperando” to first-cycle `quitocayotia (50)`. The later `mochixcaonoque (50)` passage and contiguous gloss block 49–55 provide the matching witness. |
| `000321` | Corrected | The first-cycle fire passage was attached to “sentarse a esperar.” The later passage contains `quichixtimotecaque`, with the corresponding second-cycle 47–48 gloss block. The preserved source's marker placement was retained, not relocated. |
| `000411` | Corrected | The target passage was already from the third cycle, but neighboring gloss 2 came from the first cycle. The third-cycle 2–3 block concerns swollen eyes and eyelids. |
| `000490` | Corrected | The target passage was from the second cycle, but neighboring glosses 13 and 15 came from the first. The second-cycle 13–15 block matches the quoted passage. |
| `000491` | Unchanged; separate uncertainty | The first-cycle coming-here passage and gloss numbering agree. Displayed “queen” versus preserved `q?en` is an uncertain editorial expansion; no replacement was inferred in this cycle-repair batch. |
| `000501` | Corrected | The first-cycle target 100 was paired with unrelated glosses for its following second-cycle 1–7 passage. The exact contiguous source block 94–100 followed by 1–7 now supplies all shown glosses. The existing standalone normalized definition “recular o volver atrás” was preserved. |
| `000537` | Unchanged | The displayed “por tanto” packet and 27–31 glosses agree. Earlier repeated numbers belong to separate packets. |

Each corrected quotation and contiguous glossary block was verified as an exact unique substring of the row's preserved raw transcription before application. The `000501` occurrence uses the unique anchor `valtziniloth: ye no ceppa`, since the shorter form also occurs in a glossary. No fuzzy spelling match licensed a correction.

Independent full-corpus comparison confirmed changes only to the five approved records. All raw witnesses, lexical fields, record identities, order, and the five unchanged review entries remain intact. Current commentary copies and structured display/witness consumers agree; recorded occurrence and gloss offsets match the preserved source exactly. Standalone visible definitions were preserved; the previously stale structured definition for `000501` was synchronized to its unchanged visible definition.

Repair provenance is recorded in `resources/sahagun_five_cycles_2026_09_20_change.json`, with complete originals in `resources/sahagun_five_cycles_2026_09_20_originals.jsonl.gz`. Independent derived-data checks confirmed that all 51 changed assets have row/posting deltas confined to the five approved IDs and their metadata positions; row/index values match the corrected corpus. SQLite changed only those same five records. The earlier 320 repeated-reference candidates and 99 review-marked candidates were triage counts, not counts of confirmed errors; this ten-record review does not classify all remaining candidates.

The preceding, separately authorized Spanish-only markup batch repaired nine Wimmer records and twelve strings: four closing-tag completions and eight orphan terminal-markup removals. It did not reconstruct missing prose. See `resources/wimmer_spanish_nine_2026_09_20_change.json` for its independent change inventory and preserved originals.
