# Editorial Rules for Best Spanish Wording in Near-Duplicate Definition Clusters

## Purpose

Use these rules when several records define the same standardized Nahuatl lemma with near-duplicate Spanish glosses. The goal is to choose a clear user-facing Spanish wording without erasing what each source actually says.

These rules are for proposals and reviews. They do not imply automatic edits to `data/data.jsonl.gz`.

## Motivating Case: `ceyotl`

The `ceyotl` cluster shows why a single "best" wording can be too blunt:

- Molina 1: `meollo o tuetano de huesos.`
- Molina 2: `tuetano de hueso.`
- 1780 BNF: `Meollo, o tuetano de huesos`
- 17?? BNF: `Medulla o tutanos de huesos`
- V94: `Tuétano, grasa.`
- Wimmer/Launey: `Cualquier sustancia de apariencia gelatinosa, incluida la médula ósea.`

Best row-level treatment for the old-dictionary core sense:

`meollo (arcaico: médula) o tuétano de huesos`

For rows with `Medulla`:

`Medulla (arcaico: médula) o tuétanos de huesos`

Why:

- `tuétano` is the plain modern Spanish continuation of the old `tuetano/tutanos`.
- `meollo` is a source word and should be preserved with `arcaico: médula` help in this marrow sense.
- `Medulla` is likewise a source word and should be preserved with `arcaico: médula` help, not silently replaced.
- V94 and Wimmer should remain untouched in this pass.

## Rule 1: Keep Source Rows Source-Specific

Do not collapse all near-duplicate rows into one global definition if the source wording differs in meaningful ways.

Prefer a row-specific proposed wording when:

- one source gives a narrow anatomical gloss and another gives a broader semantic category;
- one source includes a second sense not present elsewhere;
- one row is a cross-reference, citation, or source note rather than a definition;
- the source family is modern descriptive work such as V94 or Wimmer rather than an old dictionary.

For `ceyotl`, old Molina/BNF rows should preserve `meollo` or `Medulla` with `arcaico:` help and modernize only `tuetano/tutanos` spelling. V94 should retain `Tuétano, grasa`, and Wimmer should retain its broader definition.

## Rule 2: Modernize Old Spellings, Not Old Meanings

Modernize spelling when the change is orthographic and the meaning is unchanged.

Safe examples:

- `tuetano` -> `tuétano`
- `tutanos` -> `tuétanos`
- `Medulla` -> `Medulla (arcaico: médula)` in this source-gloss context
- `Baptismo` -> `Bautismo`

Do not use spelling modernization to silently change the lexical choice.

For `ceyotl`, `tuetano de hueso` becomes `tuétano de hueso`. Rows with `meollo` become `meollo (arcaico: médula) ...`; rows with `Medulla` become `Medulla (arcaico: médula) ...`.

## Rule 3: Preserve Source-First Terms When They Carry Historical Value

If an old Spanish term is meaningful but may be opaque to users, keep it and add parenthetical help.

Use:

`oldword (arcaico: modern help)`

Use this pattern when:

- the old term is not merely a spelling variant;
- the old term is useful for source fidelity;
- replacing it would hide a historical lexical choice;
- the modern help is a gloss, not a new sense.

Examples:

- `baldonar (arcaico: injuriar o afrentar)`
- `abundoso (arcaico: abundante)`
- `abrimiento (arcaico: abertura o apertura)`

For `ceyotl`, preserve `meollo` as `meollo (arcaico: médula)` in the old-source rows because it is the source lexical choice. Preserve `Medulla` the same way.

## Rule 4: Prefer the Narrow Old-Dictionary Sense for Old-Dictionary Rows

When Molina, BNF, and similar old dictionary rows agree on a narrow gloss, prefer that narrow sense over a broader modern definition.

For `ceyotl`:

- Old-dictionary core: `meollo (arcaico: médula) o tuétano de huesos`, or `Medulla (arcaico: médula) o tuétanos de huesos`
- Broader Wimmer/Launey context: `sustancia de apariencia gelatinosa, incluida la médula ósea`
- V94 modern field gloss: `Tuétano, grasa`

Do not replace Molina's `meollo` rows or BNF's `Medulla` rows with Wimmer's broad gelatinous definition. That broad definition may be useful in a merged display, note, or semantic summary, but it is not the wording for a source-faithful old-dictionary row.

## Rule 5: Keep Multiple Senses When the Cluster Actually Has Multiple Senses

Keep multiple senses when they are semantically distinct, not just differently worded.

Keep both senses if:

- different source families independently support them;
- one sense is anatomical and another is material, botanical, ritual, grammatical, or metaphorical;
- the later source adds a real living or regional usage;
- the row itself lists both senses.

For `ceyotl`, keep `grasa` when reviewing the V94 row because V94 explicitly says `Tuétano, grasa.` Do not force it into the old Molina/BNF rows unless those rows themselves support it.

Do not keep multiple senses if they are only spelling or register variants:

- `tuetano`, `tutanos`, and `tuétano` are not separate senses.
- `meollo de huesos`, `médula de huesos`, and `médula ósea` are near-duplicate anatomical wording, not separate senses in this cluster.

## Rule 6: Prefer Modern User-Facing Glosses When They Improve Comprehension

Prefer the clearest modern Spanish wording when:

- the old wording is purely orthographic or register-bound;
- no source-specific sense is lost;
- the modern term is standard and precise;
- the result is shorter or less ambiguous.

For `ceyotl`, prefer row-specific modernization:

`meollo (arcaico: médula) o tuétano de huesos`

or:

`Medulla (arcaico: médula) o tuétanos de huesos`

over:

- replacing `meollo` with only `médula ósea`
- replacing `Medulla` with only `médula`
- importing Wimmer's `cualquier sustancia de apariencia gelatinosa...` into old-source rows

The chosen wording remains source-faithful because it preserves the old lexical forms while making the sense readable to modern users.

## Rule 7: Treat V94 and Wimmer as Broader Evidence, Not Automatic Overrides

Modern sources can clarify the semantic range, but they should not overwrite old dictionary definitions by default.

Use V94/Wimmer to:

- confirm that a modern gloss is plausible;
- identify a broader or living sense;
- choose a precise modern term when old sources are vague;
- add a separate broader-sense proposal when a row actually supports it.

Do not use V94/Wimmer to:

- replace a narrow old source gloss with an encyclopedic definition;
- add a modern sense to a Molina/BNF row that does not contain it;
- erase historical terms that should be preserved with parenthetical help.

For `ceyotl`, Wimmer's broad definition and V94's `grasa` sense should remain in those rows. Neither should replace the old-source wording.

## Rule 8: Resolve Archaic vs Modern by Function

Classify each candidate before proposing wording:

- Orthographic variant: modernize directly.
- Old lexeme with same sense: preserve with `(arcaico: ...)`.
- True alternate sense: keep as a separate sense.
- Modern broader definition: keep in modern-source row or note, not in old-source row.
- Source note or cross-reference: do not rewrite as a definition.

For `ceyotl`:

- `tuetano/tutanos` are orthographic variants.
- `meollo` is source-first; preserve it with `arcaico: médula`.
- `Medulla` is source-first; preserve it with `arcaico: médula`.
- `grasa` is a true additional sense in V94.
- `sustancia gelatinosa` is broader modern analysis.

## Rule 9: Use Evidence Before Wording

Before proposing best wording, gather:

- all rows with the same `Texto estandarizado`;
- close variants such as possessed, compounded, or prefixed forms;
- source family and date;
- old and modern spellings already present in the data;
- whether the row is a direct definition, a cross-reference, or commentary.

For `ceyotl`, also inspect `ceceyotl` and `omiceceyotl`, because they reinforce the anatomical `tuétano/médula ósea` sense without necessarily proving every broader `ceyotl` sense.

## Rule 10: Proposal Format

When proposing a row-level wording, include:

- `record_id`
- `source`
- `lemma`
- `old_translation`
- `proposed_translation`
- confidence
- rationale
- local evidence record IDs

Keep rationales explicit:

- say whether the change is spelling modernization, oldword help, sense separation, or source-family selection;
- identify which sources support the chosen wording;
- state when a broader modern definition was deliberately not used.

## Recommended `ceyotl` Outcomes

For old dictionary rows:

- `meollo o tuetano de huesos.` -> `meollo (arcaico: médula) o tuétano de huesos.`
- `tuetano de hueso.` -> `tuétano de hueso.`
- `Medulla o tutanos de huesos` -> `Medulla (arcaico: médula) o tuétanos de huesos`

For V94:

- keep `Tuétano, grasa.`
- optionally add no parenthetical help; both words are already modern enough.

For Wimmer:

- keep the broader definition as broader semantic context.
- do not use it to overwrite old dictionary rows unless building a separate merged/summary definition.

## Practical Default

When in doubt:

1. Keep the source row's sense.
2. Modernize only spelling and accents.
3. Add parenthetical help for opaque old lexemes.
4. Keep distinct senses separate.
5. Use V94/Wimmer as context, not as an automatic replacement for Molina/BNF wording.
