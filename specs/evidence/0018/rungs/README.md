# 0018 adjacent rungs: I33 (ii)'s release-authored fixtures

`fixtures.tar.xz` holds one store per (origin release, accepted shape at a released base): 141 stores over the 40 shapes, so a
store upgraded from v0.4.8 is here beside one written at its own base. `manifest.json` names each with its base, digest, origin,
route, rows and sha256, and records the coverage measured on them. `test_every_rung_from_every_base` (T5) reads them.

**How a fixture is made.** Each row's newest release writes through its own store API (`populate_release.py`), under that
release's own source. Then every later release's own `migrate_store` carries the store (`walk.py`, research's walk from
stores with rows in them), and each shape is kept once per origin. No store is edited by hand. One input is hand-made: the refusal
row comes from a `SupersessionPlan` built here and passed to the release's `apply_supersession_plan`, not from its planner. The
data steps read only that row's `refusal_id` and `user_id`, so its other values enter no step.

**The recipe**, from a clone with the release tags:

    for t in v0.4.8 v0.5.0 v0.6.0 v0.9.0 v0.10.0 v0.12.0 v0.13.0 v0.15.0 v0.17.0 v0.19.0 v0.25.0 v0.26.1; do
      mkdir -p $W/$t && git archive $t src | tar -x -C $W/$t; done
    python walk.py $W <head src> <python>
    python coverage.py <python> <head src> <this directory> $W > coverage.out
    python package.py $W coverage.out <this directory>

**The coverage rule.** Each write a data step makes sees a row on at least one fixture, or is listed by name with its reason.
`manifest.json` records both. "Saw a row" means the statement changed one, not that each branch of its values ran. Reads are not
counted here: they are measured per entry once T1 names the entries, and nine `before` captures see no row, because each reads a
table its own step creates. One write is listed: `UPDATE redactions`, because no released base holds `redactions`.
So `v16-notice-state` and the `redactions` ALTERs stay on PA1's synthetic row, and "release-authored" stops there.

**What was compared.** Each store then goes to head by the direct route, and head's tables are compared row by row, per origin,
across the routes the walk kept. It keeps one route per (origin, shape), so this is not every route. The results:
- `arity_era`, `edge_event`, `request_registry`, `store_epoch` and `store_identity` differ only in clock columns and in the `origin`
  uuid a migration mints, with equal row counts.
- `episodes` differs from origin v0.4.8 alone: its outcome episode's stored provenance has four byte forms, by route, and one
  meaning: all four load identically under head's `Episode`.
- Every other table agrees byte for byte.

**Limits.** A `kind='outcome'` episode is written only at v0.4.8: later releases refuse it through `add_episode`, and their
`record_outcome` and `append_outcome_if_head` routes were not tried. No data step past base 1 reads `episodes`, and stores from
origin v0.4.8 carry the row to every later shape. One SQLite and one
interpreter wrote all of them (recorded in `manifest.json`), so this does not measure a store written by an older SQLite.

**The vector file.** `digest_vectors.json` issues the rungs' preimages for the first time. 0013 v40's fourth edit changed the `read` field of the preimage §5g.1 calls frozen, before any vector existed, so no issued digest moved: a `read` entry now carries one field per check in its `feeds`. `direct` pins three whole plans for their order only; it is a cell, and no part of the frozen preimages.

**One input the fixtures cannot give.** The v2→v3 `observed_at` fill is reached by no release-authored store: every outcome episode a release wrote already carries `observed_at`. So `test_the_v3_observed_at_fill_is_rung_three_s_read` and `test_a_data_entry_issues_zero_or_more_writes_on_a_v2_fixture` use a hand-made legacy row, and the manifest's `not_release_authored` says so.
