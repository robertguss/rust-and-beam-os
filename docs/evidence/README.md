# Evidence model

Evidence is durable, machine-validated, and repository-relative. Prose explains
a result; it never replaces the files and hashes that support it.

## Layout

- `schema/evidence-v1.schema.json` documents one execution receipt.
- `schema/source-claims-v1.schema.json` documents the primary-source ledger.
- `index.json` maps completed task claims to evidence records.
- `sources.json` maps technical claims to immutable primary sources and known
  limitations.
- `fixtures/` is a stable validator canary.
- `phase-N/RB-T-*/` stores task records and their retained artifacts.

Run `just evidence-check`. Validation rejects unknown/missing fields, unsafe or
missing paths, digest drift, malformed IDs/timestamps/build IDs, unindexed task
records, and inconsistent source-lock/bootstrap metadata.

## Evidence receipt

An execution receipt names:

- owning task and one precise claim;
- classification (`scaffold`, `host`, `smoke`, or `target`);
- build ID, full Git revision, dirty state, and target;
- exact argv/cwd and terminal result;
- host identity and relevant tool versions;
- at least one immutable input and artifact, each with `sha256:<hex>`.

`scaffold`, `host`, and `smoke` evidence cannot be cited as target proof. A
dirty build cannot be cited as a reproducible release. The validator proves
integrity and schema compliance, not the truth or sufficiency of a claim.

## Source/claim ledger

Each source entry records a title, immutable locator/reference where available,
retrieval date, local digest where practical, classification, exact supported
claims, consumers, and limitations/disagreements. Gate packets must not rely on
empty entries, search snippets, or model recollection.
