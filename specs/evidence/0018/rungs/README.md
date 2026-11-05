# 0018 adjacent rungs: I33 (ii)'s release-authored fixtures

`fixtures.tar.xz` holds one store per accepted shape at a released base. `manifest.json` names each with its base, digest, route,
rows and sha256, and records the coverage measured on them. `test_every_rung_from_every_base` (T5) reads them.

**How a fixture is made.** Each row's newest release writes through its own store API (`populate_release.py`), under that
release's own source. Then every later release's own `migrate_store` carries the store (`walk.py`, research's walk from
stores with rows in them), and each shape reached is kept once. Nothing is written by hand.

**The recipe**, from a clone with the release tags:

    for t in v0.4.8 v0.5.0 v0.6.0 v0.9.0 v0.10.0 v0.12.0 v0.13.0 v0.15.0 v0.17.0 v0.19.0 v0.25.0 v0.26.1; do
      mkdir -p $W/$t && git archive $t src | tar -x -C $W/$t; done
    python walk.py $W <head src> <python>
    python coverage.py <python> <head src> <this directory> $W > coverage.out
    python package.py $W coverage.out <this directory>

**The coverage rule.** Each write a data step makes sees a row on at least one fixture, or is listed by name with its reason.
`manifest.json` records both. One is listed: `UPDATE redactions`, because no released base holds `redactions`.
So `v16-notice-state` and the `redactions` ALTERs stay on PA1's synthetic row, and "release-authored" stops there.

**What was compared.** Each shape then goes to head by the direct route. Across every route from one origin, `edges`, `episodes`
and every other table agree except `arity_era`, `edge_event`, `request_registry`, `store_epoch` and `store_identity`, and those
differ only in clock columns and in the `origin` uuid a migration mints, with the same row counts.

**Limits.** A `kind='outcome'` episode is written only at v0.4.8: later releases refuse it through `add_episode`. One SQLite and one
interpreter wrote all of them (recorded in `manifest.json`), so this does not measure a store written by an older SQLite.
