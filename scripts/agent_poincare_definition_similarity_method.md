# Definition Similarity Cluster Method

Goal: find reviewable clusters of highly similar Spanish definitions across records, without changing `data/data.jsonl.gz`. The target pattern is like `ceyotl`, where several sources have near-equivalent definitions:

- `Meollo, o tuetano de huesos`
- `Medulla o tutanos de huesos`
- `meollo o tuetano de huesos`
- `tuetano de hueso`

The method below is intended to be implementable with Python stdlib: `gzip`, `json`, `re`, `unicodedata`, `html`, `difflib`, `collections`, and `itertools`.

## Scope

Use record fields:

- `record_id`
- `Fuente`
- `Texto estandarizado`
- `Escritura original`
- `Traducción`
- `Traducción (es)`
- `Comentario`
- `Comentario (es)`
- `eid`
- `prio`

For the first pass, compare only short definition fields:

- Use `Traducción` for non-Wimmer Spanish sources.
- Use `Traducción (es)` for `2021 Wimmer` when it is non-empty.
- Do not use long `Comentario` fields for clustering in the first pass. Comments contain citations, examples, HTML, and multilingual material that increase false positives.

Skip obvious non-definition values:

- empty text
- index-only values like `X-98 129(2)`
- strings over a conservative limit, e.g. 240 characters, unless a later pass explicitly handles long comments
- source-marker-only values like `Cf. ...`

## Normalization

Keep both raw display text and normalized text. Never overwrite raw text during clustering.

### Text Cleanup

1. Decode HTML entities with `html.unescape`.
2. Strip simple tags with `re.sub(r"<[^>]+>", " ", text)`.
3. Normalize Unicode with `unicodedata.normalize("NFC", text)`.
4. Lowercase.
5. Replace separators with spaces or split points:
   - `;`, `/`, newline: strong split points.
   - period followed by whitespace: split point only if both sides are definition-like.
   - comma: weak split point, not used before connector phrases such as `, o ...`.
6. Normalize punctuation to spaces:
   - quotes, parentheses, brackets, colon, question marks, etc.
7. Collapse whitespace.

### Accent and Orthography Folding

Create two normalized forms:

- `norm_light`: lowercase, punctuation-normalized, accents preserved except for comparison aliases.
- `norm_folded`: accentless, old-spelling-normalized, tokenized.

Useful stdlib accent fold:

```python
def strip_accents(value):
    nfd = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
```

Recommended orthography replacements, applied after accent folding:

- `huesso`, `huessos`, `huesos` -> `hueso`
- `tutano`, `tutanos`, `tuetano`, `tuetanos` -> `tuetano`
- `medulla`, `medula` -> `medula`
- `rinon`, `rinones`, `rinonada` normalized for accent only, not collapsed together
- `celebro` -> `cerebro`
- `cabeca`, `cabeça` -> `cabeza`
- `assi` -> `asi`
- `ç` -> `z` before accent folding if it appears
- duplicate Latin/old consonants only for known cases, e.g. `medulla` -> `medula`; do not globally collapse `ll`

Avoid broad `b/v`, `u/v`, or `x/j` folding in the similarity pass unless the candidate pair is already in a tight block. These folds create many Spanish false positives.

### Tokenization

Tokenize with a Spanish-letter regex:

```python
TOKEN_RE = re.compile(r"[a-záéíóúüñç]+", re.I)
```

For each definition unit, store:

- `tokens_all`: all normalized tokens.
- `tokens_content`: remove low-information function words.
- `tokens_ordered`: content tokens in original order.
- `tokens_sorted_key`: sorted unique content tokens, joined with spaces.

Suggested stopwords for content metrics:

```text
a, al, de, del, el, la, las, le, lo, los, o, u, y, en, por, para, con,
sin, se, su, sus, un, una, unos, unas, que, como, cosa, tal, asi
```

Keep stopwords in `norm_string` for `SequenceMatcher`; remove them only for token-set metrics.

### Light Singularization

Use a conservative token normalizer:

- `huesos` -> `hueso`
- `tuetanos` -> `tuetano`
- `tutanos` -> `tuetano`
- For other tokens:
  - if token length >= 6 and ends with `es`, remove `es`
  - else if token length >= 5 and ends with `s`, remove `s`

Do not singularize short tokens. Keep both original and singularized tokens if a token becomes ambiguous.

### Concept Alias Layer

Keep the base token layer intact, but add a separate `concept_tokens` layer for targeted synonym boosts. This helps `Medulla o tutanos de huesos` cluster with `meollo o tuetano de huesos`.

Start with a tiny, auditable alias table:

```python
CONCEPT_ALIASES = {
    "medula": "marrow",
    "medulla": "marrow",
    "meollo": "marrow",
    "tuetano": "marrow",
    "tutano": "marrow",
    "hueso": "bone",
    "huesos": "bone",
    "cerebro": "brain",
    "celebro": "brain",
    "seso": "brain",
    "sesos": "brain",
}
```

Use concept aliases only as a boost, not as the only reason to cluster. Require same lemma, same `prio`, or strong token/character similarity unless manually reviewing cross-lemma clusters.

## Definition Units

Each record should produce one whole-definition unit and optional atom units.

Whole unit:

- the full normalized short definition
- best for preserving the source wording

Atom units:

- split on semicolon, slash, and clear sentence boundaries
- split comma-separated lists only when each segment has at least one content token and is not just a connector continuation
- keep the parent `record_id` and `unit_index`

Example:

`Meollo, o tuetano de huesos, caña, riñonada, o sebo de animal`

Whole unit:

- `meollo o tuetano de huesos caña riñonada o sebo de animal`

Atom units:

- `meollo o tuetano de huesos`
- `caña`
- `riñonada`
- `sebo de animal`

For the first implementation, use whole units for cluster reporting and atom units only to compute subset/containment evidence.

## Grouping Keys

Use blocking keys to avoid all-pairs comparison.

### Primary Blocks

1. `lemma_key`: normalized `Texto estandarizado`.
   - This catches `ceyotl` source variants.
2. `prio_key`: non-empty `prio`.
   - This catches source variants where orthographic forms differ but the data already groups them.
3. `(lemma_key, prio_key)` when both exist.
   - This is the safest high-confidence block.

### Secondary Blocks

4. `content_fingerprint`: sorted unique content tokens, after light normalization.
   - Useful for exact normalized duplicates.
5. `rare_token_key`: one or two rare content tokens in the definition.
   - Build document frequency for content tokens.
   - Use the rarest two content tokens as an inverted-index key.
6. `concept_key`: sorted concept aliases plus remaining strong content tokens.
   - Useful for `medulla/tutano/meollo/tuetano` clusters.

### Cross-Lemma Blocks

Allow cross-lemma candidate generation only when one of these is true:

- same non-empty `prio`
- exact `content_fingerprint`
- same `concept_key` with at least two concepts or one concept plus one rare content token

Flag these clusters as `cross_lemma=true` for review.

## Similarity Metrics

Compute several cheap metrics and keep them in the output.

### Character Sequence Ratio

Use `difflib.SequenceMatcher`:

```python
seq_ratio = SequenceMatcher(None, norm_a, norm_b).ratio()
```

Good for near-identical strings:

- `meollo o tuetano de huesos`
- `meollo o tuetano de hueso`

Weak for synonym variants:

- `medulla o tutanos de huesos`
- `meollo o tuetano de huesos`

### Token Jaccard

```python
jaccard = len(A & B) / len(A | B)
```

Use sets of `tokens_content`.

### Token Dice

```python
dice = 2 * len(A & B) / (len(A) + len(B))
```

Usually better than Jaccard for short definition strings.

### Token Containment

```python
containment = len(A & B) / min(len(A), len(B))
```

This catches subset definitions:

- `tuetano de hueso`
- `meollo o tuetano de huesos`

### Character N-Gram Dice

Use character trigrams from `norm_folded` without spaces collapsed too aggressively.

```python
def trigrams(s):
    s = f"  {s}  "
    return {s[i:i+3] for i in range(len(s)-2)}
```

Then use Dice over trigram sets. This helps with small spelling differences.

### Concept Jaccard

Use `concept_tokens`, but only as a boost:

```python
concept_jaccard = len(CA & CB) / len(CA | CB)
```

For the `ceyotl` example, concept tokens turn both definitions into roughly:

- `marrow bone`

### Composite Score

A practical score:

```text
base_score =
  0.30 * seq_ratio +
  0.25 * token_dice +
  0.20 * ngram_dice +
  0.15 * containment +
  0.10 * concept_jaccard
```

Add bounded bonuses:

- `+0.05` same `Texto estandarizado`
- `+0.05` same non-empty `prio`
- `+0.03` exact same `content_fingerprint`
- `+0.03` same `concept_key` and at least one ordinary content token also overlaps

Cap at `1.0`.

Keep raw metric values in review output. Do not rely only on the composite.

## Edge Thresholds

Create graph edges between units that pass conservative thresholds. Then connected components become candidate clusters.

### Very High Confidence

Use when any of these is true:

- `norm_folded` strings are identical.
- same `(lemma_key, prio_key)` and `base_score >= 0.88`.
- same `(lemma_key, prio_key)`, `containment >= 0.95`, and the smaller side has at least 2 content tokens.
- same `(lemma_key, prio_key)`, `concept_jaccard >= 0.80`, and at least one non-concept content token overlaps, e.g. `hueso`.

### High Confidence

Use when:

- same `lemma_key` and `base_score >= 0.84`
- same non-empty `prio_key` and `base_score >= 0.84`
- exact `content_fingerprint` across different lemmas
- same `concept_key`, `concept_jaccard >= 0.80`, and `seq_ratio >= 0.55`

### Review Only

Use when:

- same `lemma_key` and `base_score` is `0.74` to `0.84`
- cross-lemma and `base_score >= 0.80`
- containment is high but the longer definition has extra content tokens that may represent a real extra sense

### Reject Pair

Reject or mark low priority when:

- fewer than 2 content tokens on both sides
- only stopwords overlap
- only concept alias overlaps and there is no same lemma/prio
- either side is a citation/source note rather than a definition
- either side contains negation or contrast markers: `no`, `sin`, `excepto`, `sino`, `pero`

## Cluster Construction

1. Build candidate units from all eligible records.
2. Build blocks using the grouping keys above.
3. Within each block, compute pairwise metrics.
4. Add graph edges for pairs passing threshold.
5. Build connected components.
6. For each component, compute:
   - `min_pair_score`
   - `median_pair_score`
   - `max_pair_score`
   - `best_pair_score`
   - `all_same_lemma`
   - `all_same_prio`
   - `source_count`
   - `raw_variant_count`
7. Split a component if it was created only by a chain:
   - If `min_pair_score < 0.70`, keep the strongest seed and reassign weaker edges.
   - Require each member to match the cluster centroid/canonical above the same threshold used to enter the cluster.

### Canonical Display Choice

For review, pick a canonical display only as a suggestion:

1. Prefer a modernized Spanish field (`Traducción (es)`) when source policy allows it.
2. Otherwise prefer the shortest complete definition with the highest average similarity to others.
3. Avoid choosing a strict subset if the cluster has longer definitions with extra senses.
4. Preserve accents from the best display form when available.

Example for `ceyotl`:

- canonical review string might be `meollo o tuétano de huesos`
- but `tuétano de hueso` should be marked `subset_of_canonical=true`
- `Medulla o tutanos de huesos` should be marked `orthography_or_latin_variant=true`

## Expected `ceyotl` Behavior

Records:

- `1571-molina-1:007501`: `meollo o tuetano de huesos.`
- `1571-molina-2:005286`: `tuetano de hueso.`
- `1780-bnf-361:006570`: `Meollo, o tuetano de huesos`
- `17-bnf-362:001240`: `Medulla o tutanos de huesos`

After normalization:

- `meollo o tuetano de hueso`
- `tuetano de hueso`
- `meollo o tuetano de hueso`
- `medula o tuetano de hueso`

Likely metrics:

- exact or near-exact between Molina 1 and BNF 361
- high containment between `tuetano de hueso` and the longer definitions
- high concept similarity between `medula...` and `meollo...`

Cluster result:

- one high-confidence cluster under `(lemma_key=ceyotl, prio_key=12903)`
- no automatic edit
- review suggestion that these are equivalent marrow/bone definitions with spelling/source variants

## False Positives

Watch these explicitly in the report.

### Short Definitions

One-word definitions such as `agua`, `piedra`, `árbol`, `sebo` can match many unrelated rows. Require same lemma/prio or exact content fingerprint.

### Multi-Sense Lists

`sebo de animal, riñonada, tuetano. o caña de vaca` partly overlaps with a marrow cluster but includes extra senses. Mark as `partial_overlap`, not equivalent.

### Generic Formulae

Definitions ending in `así`, `tal`, `cosa`, `persona`, `instrumento para` may have high structure similarity but different meanings. Downweight stopwords and generic tokens.

### Same Source Formula, Different Meaning

Many Molina entries use formulaic wording. Do not cluster on `de esta manera`, `el que`, `la que`, `acto de` without content-word overlap.

### Orthography Folds That Are Too Broad

Global `b/v`, `u/v`, `x/j`, or dropped initial `h` can merge unrelated words. Use only targeted replacements unless the pair is already in same lemma/prio.

### Synonym Alias Overreach

Concept aliases are dangerous across lemmas. `meollo`, `médula`, and `tuétano` can be equivalent in bone contexts, but not every `meollo` means bone marrow. Require a supporting content token like `hueso`.

### Long Comments and Examples

Long `Comentario` fields contain examples, citations, source-language forms, and multiple languages. Do not include them in the first pass.

### Proper Names and Taxonomy

Latin names, toponyms, and personal names can look similar after accent folding. Use source and capitalization flags to avoid treating them as definition clusters.

## Output Fields for Review

Produce JSONL or TSV. JSONL is better because clusters contain lists.

Recommended cluster-level fields:

- `cluster_id`: stable deterministic ID, e.g. hash of sorted record IDs plus unit indexes
- `group_keys`: object containing `lemma_key`, `prio_key`, `content_fingerprint`, `concept_key`
- `cluster_grade`: `very_high`, `high`, `review`
- `member_count`
- `record_count`
- `source_count`
- `sources`
- `lemmas`
- `all_same_lemma`
- `all_same_prio`
- `cross_lemma`
- `canonical_display_suggestion`
- `canonical_norm`
- `raw_variant_count`
- `normalized_variant_count`
- `min_pair_score`
- `median_pair_score`
- `max_pair_score`
- `mean_pair_score`
- `strongest_pair`
- `weakest_pair`
- `flags`
- `review_recommendation`

Recommended member-level fields inside `members`:

- `record_id`
- `unit_id`: `record_id#whole` or `record_id#atom2`
- `source`
- `eid`
- `prio`
- `lemma`
- `original_script`
- `field_used`: `Traducción` or `Traducción (es)`
- `raw_text`
- `unit_text`
- `norm_light`
- `norm_folded`
- `tokens_content`
- `concept_tokens`
- `is_subset_of_canonical`
- `extra_content_tokens`
- `missing_canonical_tokens`
- `source_order`

Recommended pair-level fields for top evidence:

- `left_unit_id`
- `right_unit_id`
- `seq_ratio`
- `token_jaccard`
- `token_dice`
- `containment`
- `ngram_dice`
- `concept_jaccard`
- `base_score`
- `same_lemma`
- `same_prio`
- `edge_reason`

Suggested `flags`:

- `exact_normalized_duplicate`
- `orthography_variant`
- `accent_variant`
- `latin_or_old_spanish_variant`
- `subset_definition`
- `partial_overlap_extra_senses`
- `cross_lemma`
- `short_definition`
- `long_definition_skipped`
- `formulaic_definition`
- `needs_human_review`

## Review Recommendations

Use conservative labels:

- `equivalent_definitions`: same concept with only spelling/source variation.
- `subset_of_longer_definition`: shorter member is contained in longer member.
- `partial_overlap`: shared core but extra senses exist.
- `orthography_only`: same definition after spelling/diacritic normalization.
- `do_not_merge`: high score likely caused by formulaic wording or generic tokens.

The output should never directly prescribe an edit to `data/data.jsonl.gz`. It should identify clusters, scores, and review notes so a separate pass can decide whether to normalize display text, add modern help, or leave source wording intact.

