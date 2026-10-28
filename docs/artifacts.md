# Artifact contract (Track A writes, Track B reads)

All offsets are character offsets into the ORIGINAL document text (`Document.text`),
end-exclusive. `doc_id` is the path relative to `corpus/`, e.g. `cuad/ABILITYINC_...txt`.
Files live in `data/cache/`. Change a column only after both members agree; update this file
in the same commit.

## sections.parquet (Phase 1, Track A)
| column | type | meaning |
|---|---|---|
| doc_id | str | document id |
| subset | str | contractnli / cuad / maud / privacy_qa |
| section_id | str | `{doc_id}#{n}`, n = pre-order index in the section tree |
| parent_id | str or null | section_id of parent node (null for top level) |
| start | int | char offset (inclusive) |
| end | int | char offset (exclusive) |
| level | int | depth in tree, 0 = top level |
| heading | str | heading text ("" if none) |
| breadcrumb | str | headings from root to this node joined by " > " |
| is_leaf | bool | true for retrieval units |
| used_fallback | bool | true if document had no headings and was split on paragraphs |
| minhash | bytes | 128 uint64 hash values (`np.uint64` array `.tobytes()`); leaves only |

## families.parquet (Phase 2, Track A)
| column | type | meaning |
|---|---|---|
| doc_id | str | document id |
| subset | str | subset |
| type_family | int | type-level family id (unique within subset) |
| variant_family | int | variant-level family id (unique within subset) |
| boundary_families | list[int] | other type families within δ (soft assignment), may be empty |

## slots.parquet (Phase 2, Track A)
| column | type | meaning |
|---|---|---|
| slot_id | str | `{subset}/{type_family}/{n}` |
| subset | str | subset |
| type_family | int | family id |
| support | float | share of family documents containing the slot |
| is_template | bool | support >= 0.5 |
| canonical_section_id | str | medoid section |
| member_section_ids | list[str] | all member sections |

## residual_spans.parquet (Phase 3, Track A)
| column | type | meaning |
|---|---|---|
| doc_id | str | document id |
| span_id | str | `{doc_id}#d{n}` |
| section_id | str | section the span belongs to |
| slot_id | str or null | matched slot (null = novel section) |
| kind | str | `replace` / `insert` / `novel` |
| start | int | char offset in the document |
| end | int | char offset in the document |
| canonical_text | str | slot text replaced ("" for insert/novel) |
| doc_text | str | document text at [start, end) |
| norm_tokens | list[str] | normalised tokens (MONEY:..., DUR:..., NEG:not, ...) |
