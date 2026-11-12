# Feature spec 0054: the container image, a published release artifact for hosts without Python 3.14

Spec-Status: accepted

| | |
|---|---|
| **Author / session** | research (veracium-research), draft v0.1. Adopted by dev 2026-11-12 from research `0037512a` (v0.5, sha256 `46fc4d20…`), byte for byte but the status line, this cell, the Version, Internal reviewers and Decision cells, and `## Review closure` |
| **Version** | **ACCEPTED — 2026-11-12, on v0.5: the owner's word, no external round (PROCESS §4a's second path).** He accepted v0.4 ("Accept 0054 v0.4 (Recommended)"), then v0.5's one change, I8(a) narrowed by property after the real build ("Accept v0.5 (Recommended)"), both first-hand in the dev session. The body is v0.5's, unchanged. **v0.5 — 2026-11-12: I8(a) narrowed, by property, to what the real build found.** The owner accepted v0.4 ("Accept 0054 v0.4 (Recommended)", first-hand to dev). Dev's first real build then failed I8(a) on certifi's own `tests` package, installed from the hashed lock. A repository name is now refused unless BOTH hold: it is one of the generic names `tests` or `specs`, and an installed distribution other than veracium lists it in its RECORD. `CLAUDE.md`, `.claude`, `COORDINATION.md` and `.git` are refused wherever they are, whatever any RECORD lists. Nothing under veracium's own distribution is exempt either: a RECORD is the package's own claim, and the 0.1.2–0.15.0 leak was the project's own artifact, which I1 would pass, since I1 proves only identity with what PyPI serves. One RED case is added for that. The narrowing goes to the owner as a change to accepted text. **Prior: v0.4 — 2026-11-12: the owner's two rulings, and dev's read of v0.3 (R1–R4).** As dev relays them, first-hand to dev: Q1 "Accept on your word (Recommended)" and Q2 "On the /data volume (Recommended)" (§10). R1: §4e states what each configuration yields, measured by dev on prototype v4. R2: I8's secrets scan names its instrument and its RED case, both demonstrated by dev. R3: arm64's I1–I8 gate the first push, run on the native runner. R4: the dependency lock is committed with its generator named. Dev's v4 verified C1: I1–I8 pass 8 of 8, and the `VERACIUM_DB` variant fails I4. **Prior: v0.3 — 2026-11-12: §6's RED demonstrations, run by dev on prototype v3 in a scratchpad (`container/checks.py`), and two corrections they found.** The GREEN baseline, v2: I1–I8 pass. Each RED case fails as named. Two exceptions: I5's wrong entry point crashes the handshake rather than listing other names, which is still red; and I4's RED case **as v0.2 wrote it was false**. **C1:** with `WORKDIR /data`, an image setting `VERACIUM_DB` instead of `VERACIUM_DB_PATH` passes I4, since the default relative `veracium.db` lands at `/data/veracium.db` anyway. §4b now sets `WORKDIR /home/veracium`, and I4's RED case names that pairing. **C2:** the build gate tests `runtime_status().status == "attested"`, the value I2 checks, never doctor's prose. N4 is added. **Prior: v0.2 — 2026-11-12: dev's prototype v2 measured what v0.1 left open.** Dev built it to §4b and §4c in a scratchpad; nothing is in the repo. Startup and the handshake need neither the key nor a network (§2c-ii). `/data` after a handshake holds exactly `veracium.db` and `config/veracium/` (§6 I6). arm64's I2 runs on GitHub's native arm64 runner (§5). B1 is settled: dev's handshake passed `VERACIUM_MCP_CAPABILITY=direct`, so §4e's usage stands. B2–B4 are taken as written. **Prior: v0.1 — 2026-11-12: first draft**, from dev's proposed shape (seven points, four questions) and the owner's two rulings as dev relays them: "Container (Recommended)" over lowering the Python floor, and "GitHub Container Registry (Recommended)". Number taken from the registry (`specs/allocation.py --next`, peer tree CHECKED) at 18:50Z. |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line at the top* |
| **Internal reviewers** | research (author) · dev (proposed the shape; prototype v1–v4 in a scratchpad; the implementation, `container/`, with I1–I8 and the RED matrix run on the 0.32.0 wheel) |
| **External review** | none: the owner ruled acceptance on his word (§10 Q1), as for 0053 |
| **Decision + date** | the owner's rulings, 2026-11-12, first-hand in the dev session (as dev relays them): acceptance on his word once research and dev have read the text (Q1); `config/` and `state/` on `/data` (Q2). **ACCEPTED: the owner, first-hand in the dev session, 2026-11-12: "Accept 0054 v0.4 (Recommended)", then, for I8(a)'s narrowing, "Accept v0.5 (Recommended)"** |
| **Path** | `lightweight` by D2: the image adds a Dockerfile, a CI job and documentation and touches no file on the guarded list. Item §10 N1 (serverInfo's version) would touch `src/veracium/mcp_server.py`, which IS guarded, and is therefore kept out of this spec. |

---

## 1. Problem and motivation

Veracium requires Python 3.14 (`requires-python = ">=3.14"` since v0.27.0, `87526b0e`, the owner's floor of 2026-09-27,
which stays). Ubuntu 24.04's system Python is 3.12, and `pip install veracium` there resolves to v0.26.1, the last
release whose `requires-python` admits it (`>=3.10`). Those users get a release about six minor versions old and none of
its fixes.

**The image** gives them the current release with no 3.14 on the host: `ghcr.io/veracium-ai/veracium:<version>`, the
MCP server over stdio, the store on a volume.

**Alternatives rejected:**
- **Lower the floor:** the owner ruled against it.
- **Tell users to install 3.14:** that is the status quo, and it is what leaves them on 0.26.1.
- **A convenience build outside the release:** see §4a. An image under the project's name, once pulled, is mirrored and
  cached like a PyPI upload. The release runbook's opening line, "A release is outward-facing and irreversible",
  applies to it unchanged.

## 2. Field contracts touched

None in the store or the API. The image fixes the values of four environment variables the product already reads, and
sets no others:

| variable | read by | the image's value | why |
|---|---|---|---|
| `VERACIUM_DB_PATH` | `mcp_server.build_memory` | `/data/veracium.db` | the store on the volume (§4c). The name is exact: dev's prototype first used `VERACIUM_DB`, and it worked only because `WORKDIR /data` caught the default `veracium.db` |
| `HOME` | Python's `Path.home()` | `/home/veracium`, outside `/data` | §4c: `/data` holds the store and the two named directories, nothing else |
| `XDG_CONFIG_HOME` | `telemetry.py`, `diagnostics.py` | `/data/config` | consent persists with the store, per volume (§4c) |
| `XDG_STATE_HOME` | `diagnostics.py` | `/data/state` | the local error log persists for `veracium diagnostics report` |

**Never set by the image** (§3): `ANTHROPIC_API_KEY`, `VERACIUM_MCP_CAPABILITY`, `VERACIUM_MCP_SOURCE_ID`,
`VERACIUM_USER`. Each is the host's to supply.

## 2c. Untrusted inputs — REQUIRED, blocking

| input | supplied by | what treats it as data |
|---|---|---|
| MCP messages on stdin | the MCP client and, through it, the model | the server's existing contract (0031, 0037), unchanged: the image adds no tool and no argument |
| the environment at `docker run` | the host | the server's existing validation. `VERACIUM_MCP_CAPABILITY` outside the closed set raises at construction (`_resolve_capability`). The image supplies none of the trust-bearing ones |
| the contents of the mounted `/data` | whoever wrote the volume: another image version, a host tool, an attacker with access to the volume | the store's existing open-time checks (0007, 0013): a store stamped newer than the build refuses (`store.open.newer`), an older one refuses with the migrate remedy, and a manifest that does not validate refuses. The image adds no read path to the volume |
| the build inputs: the base image, the wheel, the dependencies | the registries at build time | pinned and checked (§4b, I1, I2): the base by digest, the wheel by sha256 equal to the PyPI-served file, every dependency by hash |

An input only the image itself supplies (its own `ENV`, its user, its paths) is not an untrusted input. It is listed in
§2 and checked in §6.

### 2c-ii. Assertions about reach — REQUIRED

**What was read, 2026-11-12, at dev `f2b0004c`:**
- **The outbound network calls in `src/veracium`.** `urllib.request.urlopen` appears in exactly two places:
  `telemetry.py:425` and `diagnostics.py:298`. Both post to a configured endpoint, and veracium ships none
  (`telemetry.py:13`, `diagnostics.py:19`). There is no `requests`, `httpx`, `http.client` or socket use. The one
  provider SDK is `anthropic`, imported in `llm/anthropic.py`. The census was a grep over `src/`, excluding
  `store/evidence`.
- **What startup needs.** `veracium-mcp` builds the reference provider at start (`build_memory`:
  `AnthropicComplete()` constructs `anthropic.Anthropic()`) and exits "failed to start" if that raises. Whether the
  handshake needs a key value or a network was left to the prototype. **Dev's prototype v2 measured it: under
  `--network none` and with no `ANTHROPIC_API_KEY`, `initialize` then `tools/list` gives exactly the six names.** The
  same holds with the key, so I5 needs no placeholder.

These are statements about this corpus at this commit. They are not a claim that no future dependency opens a socket;
I5 is the check that keeps that true.

## 3. Trust-class matrix — REQUIRED, blocking

| class | does the image touch it? | how |
|---|---|---|
| **host capability** (`VERACIUM_MCP_CAPABILITY`, 0031 §4a) | **no: never set** | `direct` is the deployment's attestation that every call originates with the authenticated principal: "liability, not clairvoyance". An image default would make that claim for every deployment that pulls it. The absence default, `none`, stays |
| **source identity** (`VERACIUM_MCP_SOURCE_ID`, 0006) | **no: never set** | the host's opaque id for its source. A baked value would give every deployment one shared identity, so one revocation would reach them all |
| **the provider key** (`ANTHROPIC_API_KEY`) | **no: never set, never in a layer** | passed at run time. I8 scans the layers |
| **user identity** (`VERACIUM_USER`) | no | the product's default (`"default"`) stands, and the host process is the identity boundary |
| **evidence author classes** (USER, SYSTEM, ASSISTANT, THIRD_PARTY) | untouched | the server's rules, unchanged |
| **stored records and their provenance** | untouched | the store's rules, unchanged. The image changes where the file lives, not what it holds |

**What follows for the documented usage (BLOCKING on dev's point 3).** With neither `VERACIUM_MCP_CAPABILITY` nor
`VERACIUM_MCP_SOURCE_ID` set, `remember` refuses every event.
- **Why:** under `none` the author baseline is `third_party` (`mcp_server._BASELINE_AUTHOR`).
  `MemoryConfig.require_source_id` defaults to `True` (`config.py:82`). A third-party event with no source id is
  refused (`ingest.py`, `source_id_required`). The server's own help says so: "such a deployment must set this (or
  attest `direct`) before `remember` stores anything".
- **What follows:** dev's usage line, `docker run -i --rm -v veracium-data:/data -e ANTHROPIC_API_KEY …`, starts a
  server that stores nothing. The documented usage must pass `-e VERACIUM_MCP_SOURCE_ID=<the host's id>`, or `-e
  VERACIUM_MCP_CAPABILITY=direct` where the host stands behind that attestation. The image itself sets neither.

## 4. Behaviour

### 4a. The image is a release artifact (dev's question a)

It is gated like the wheel, in the release runbook's order, and adds four steps:
1. **After PyPI's consumer-side check passes:** download the PyPI-served wheel, and check its sha256 equals the
   release's built wheel. The image installs that file, never a source build and never a local rebuild.
2. **Build once, for linux/amd64 and linux/arm64, then gate that build** (§6, I1–I8). The digest that passed is the
   digest pushed. **A release never rebuilds to push**, since a rebuild may resolve different bytes.
3. **Push on the owner's release word**, as `:<version>` and `:latest`. A version tag is pushed once and never moved;
   a botched image is a new version, as a botched wheel is ("Never reuse a version number"). `:latest` moves by design.
4. **Consumer-side check:** pull by tag, compare the digest with the pushed one, then run I2 and I5, and `veracium
   selfcheck` with the key, which spends the same small live budget as the wheel's consumer selfcheck.

The test-harness release gate covers the wheel's code. The image adds an operating-system layer and a different
interpreter build, which I2 and I5 cover. The harness gate is not re-run per image.

### 4b. The build

- **Base:** `python:3.14-slim`, a Debian trixie variant, **pinned by digest**. Dev's prototype base is
  `sha256:9aaa4740…`: Python 3.14.10, SQLite 3.46.1.
- **Install:** the wheel by sha256 (§4a.1), with `veracium[mcp,anthropic]`'s dependencies **pinned by hash**, from a
  lock generated at the release, committed beside the Dockerfile with its generator and version named in the commit
  (for example `uv pip compile --generate-hashes` over the wheel's requirements), and installed with `--require-hashes`. An unpinned dependency would make two builds of
  one version differ.
- **The user:** non-root, uid 10001, a `nologin` shell and no skeleton files. It owns `/home/veracium` and `/data`, both
  mode 700.
- **Working directory:** `WORKDIR /home/veracium`, never `/data`. With `/data` as the working directory, the default
  relative store path lands on the volume whatever the variable is called, and I4 cannot tell a wrong variable name from
  the right one (C1, demonstrated).
- **Entry point and contents:** `ENTRYPOINT ["veracium-mcp"]`, with the CLI by `--entrypoint veracium`. No repository
  file is in any layer (I8): only the wheel's installed contents and the base.
- **The attested gate refuses the build** unless `runtime_status().status == "attested"` inside the built image, per
  platform: the status itself, as I2 reads it, not a match on doctor's prose (C2).

### 4c. Data location and upgrades (dev's question c)

**`/data` holds exactly:**
- `veracium.db` and SQLite's sidecars (`-wal`, `-shm`, `-journal`);
- `config/`: the telemetry and diagnostics choices;
- `state/`: the local diagnostics log.

Nothing else; HOME is elsewhere (dev's point 4). Telemetry and diagnostics consent is therefore recorded **per volume**:
an operator who enables either in one volume has enabled it for every container that mounts that volume, and for no
other (dev's point 5).

**What an upgrade from image N to N+1 does to `/data`**, from the store's open rules at `f2b0004c`
(`store/schema_version.py`, the open branch):
- **Same schema version:** it opens. The schema has been at 16 since at least v0.29.0 and is 16 at 0.32.0.
- **N+1's schema is higher:** the server **refuses to open**, naming the remedy: "opening does not migrate … Migrate
  it offline first: stop every process using the file, back it up, then run `veracium migrate --db ...
  --i-have-quiesced --backup REF`" (0018 §4g). In the image that is: stop every container mounting the volume, copy
  the volume out, then `docker run --rm -v veracium-data:/data --entrypoint veracium ghcr.io/veracium-ai/veracium:<N+1>
  migrate --db /data/veracium.db --i-have-quiesced --backup <REF>`.
- **Back to N after a migration:** refused, `store.open.newer`: "install a build whose SCHEMA_VERSION covers the
  store". The way back is the backup.

**`:latest` crosses a schema boundary unasked**, so the documented client configuration names a version tag, never
`:latest`.

### 4d. Network (dev's question b)

**The promise:** at run time, the only network traffic veracium in the image originates is to the configured LLM
provider (Anthropic's API), when a tool needs the model. Telemetry and diagnostics send nothing unless an operator
configures an endpoint and enables them in that volume (§4c); veracium ships no endpoint.
- **Startup and the MCP handshake need no network.** I5 runs them under `--network none`.
- **The image opens no port.** stdio is the server's only transport.

Build-time traffic (the base registry, PyPI) is not part of this promise. It is pinned by digest and hash (§4b).

### 4e. Usage, as documented

```json
{"mcpServers": {"veracium": {
  "command": "docker",
  "args": ["run", "-i", "--rm", "-v", "veracium-data:/data",
           "-e", "ANTHROPIC_API_KEY", "-e", "VERACIUM_MCP_SOURCE_ID",
           "ghcr.io/veracium-ai/veracium:0.32.0"],
  "env": {"ANTHROPIC_API_KEY": "<key>", "VERACIUM_MCP_SOURCE_ID": "<the host's source id>"}}}}
```

**What each configuration yields** (dev's prototype v4, measured):

| configuration | `remember` | what `recall` shows |
|---|---|---|
| neither variable | refused: `{"ok": false, "refusal": "source_id_required"}` | nothing stored |
| `VERACIUM_MCP_SOURCE_ID` only, as above | stored as **third-party**: "Third party reported that the user has …" | "(no verified facts in this view)"; the content appears under UNVERIFIED THIRD-PARTY CLAIMS, never asserted |
| `VERACIUM_MCP_CAPABILITY=direct`, where the host stands behind it | the user's own statements are the user's | verified facts |

The second row is 0031's `none`, working as designed: with no attestation, nothing a model relays is the user's own word. A
single-user desktop where the person IS the authenticated principal is the case `direct` exists for (0031 §3a: "liability,
not clairvoyance"), and the host makes that attestation, never the image. Which configuration the documentation leads
with is a documentation choice. This spec binds only that each row's consequence is stated beside it.

The `env` block is required. The MCP SDK's stdio launcher passes the child only a minimal environment, and a bare `-e
NAME` forwards nothing that is not there (dev's point 3: the first handshake failed on exactly this).

## 5. Regime analysis — where does this behave differently?

| regime | behaviour | stated where |
|---|---|---|
| a named volume (`-v veracium-data:/data`) | first mount copies `/data`'s ownership from the image; uid 10001 writes | the documented path |
| a bind mount (`-v ./dir:/data`) | the host directory's owner decides; uid 10001 may not write, and the open fails loudly | docs: `--user "$(id -u):$(id -g)"`, or chown the directory |
| Docker Desktop on macOS or Windows, bind mount | file locking through the VM's file sharing is not SQLite's documented-safe case | docs: use a named volume there |
| two containers on one volume | the store's existing concurrency contract (the store-concurrency harness), unchanged | — |
| linux/arm64 | the attested gate decides per platform. The arm64 image is **built and gated natively on GitHub's arm64 runner** (`ubuntu-24.04-arm`), never by emulation; this box has no arm64 emulation, and installing it would be a host change | §6 I2 |
| a future base re-pin whose SQLite is not attested | the build refuses (I2); the image never ships a merely `verified` build | §4b |

## 6. Invariants and executable checks — REQUIRED, blocking

Each check runs in CI on every push (build and test, no push) and again at the release step on the digest to be pushed.
Each must be **demonstrated RED** once, against a deliberately wrong image, before acceptance.

| | invariant | check | RED demonstration |
|---|---|---|---|
| **I1** | the installed veracium is the release's wheel | the build verifies the wheel's sha256 against the PyPI-served file. `importlib.metadata.version("veracium")` in the image equals the tag | a wheel one byte changed: the build refuses |
| **I2** | the store opens as an **attested** build, per platform | `docker run --entrypoint python IMG -c` running `veracium.store.schema_version.runtime_status()` gives `.status == "attested"` (one of `RUNTIME_STATUSES`). `veracium doctor` reads the same, for example "SQLite 3.46.1 on x86_64 Linux glibc is an attested build" in dev's prototype. The build refuses otherwise, and the consumer check repeats it on the pulled digest | a base whose SQLite build key is not in `src/veracium/store/evidence/sqlite_runtimes.json`: the build refuses. Dev's v3: `python:3.14-alpine3.21`, SQLite 3.48.0, musl, x86_64, "runtime status: verified". Its key is absent from all 22 attested keys; the control, the image's own 3.46.1 x86_64 glibc key, is present |
| **I3** | the image sets no trust-bearing variable | `docker image inspect`: `Config.Env` holds none of `ANTHROPIC_API_KEY`, `VERACIUM_MCP_CAPABILITY`, `VERACIUM_MCP_SOURCE_ID`, `VERACIUM_USER` | an image with `ENV VERACIUM_MCP_CAPABILITY=direct`: refused |
| **I4** | non-root, and `/data` is its own | `Config.User` is `10001`. In a fresh named volume, the store file is created at `/data/veracium.db` (the exact path, so a wrong variable name fails, per dev's point 2) and owned by 10001 | an image with no `USER`: refused, `Config.User` unset and the store owned by 0. An image setting `VERACIUM_DB` instead, **with `WORKDIR` not `/data`**: refused, `/data/veracium.db` absent. With `WORKDIR /data` that variant passes, which is why §4b forbids it (C1) |
| **I5** | startup and the handshake need no network, and serve the six tools | under `--network none`: MCP `initialize`, then `tools/list` gives exactly the six served names | an image whose entry point is `veracium`, the CLI: the handshake fails, which is red |
| **I6** | `/data` holds only what §4c names | after I5 and one CLI call, list `/data`: a subset of {`veracium.db`, its sidecars, `config/`, `state/`}. Dev's prototype v2, after the handshake: exactly `veracium.db` and `config/veracium/`; `state/` appears only once a diagnostics log is written | `HOME=/data` (dev's prototype): skeleton dotfiles appear, refused |
| **I7** | a store the build does not cover is refused, never opened | a store stamped above the build's `SCHEMA_VERSION`, on a volume: the server's open refuses (`store.open.newer`, `StoreVersionError`) and writes nothing | a store at the build's own version: opens (the control). Dev's v2: the control opens at 16. Stamped 17, it is refused with the remedy ("newer (found=17, this build=16) … install a build whose SCHEMA_VERSION covers the store"), and the store's bytes are unchanged. The check requires the refusal's own words in stderr, so a handshake that failed for another reason cannot pass it |
| **I8** | no repository file and no secret in any layer | (a) the exported filesystem (`docker export`), outside the base image's own paths, holds no path named `CLAUDE.md`, `.claude`, `COORDINATION.md` or `.git` anywhere, and no path named `specs` or `tests` unless an installed distribution OTHER than veracium lists it in its RECORD (read in the image by `importlib.metadata` over every distribution). Nothing in veracium's own distribution is exempt by its RECORD; (b) no file in it matches the provider-key shape, by `grep -rIlaE 'sk-ant-[A-Za-z0-9_-]{20,}'` over the exported filesystem, and at the release step none holds the exact bytes of the key in use. A match is allowed only by an entry of path and sha256 in a committed allowlist, initially empty (the 0.1.2–0.15.0 sdist lesson). Dev's v4: no match over all 14,503 paths, site-packages included, so the allowlist stays empty | (a) an image with `COPY . /src`: refused, since no distribution owns it. A veracium wheel rebuilt with a `CLAUDE.md` in its package and listed in its own RECORD, installed with I1's check bypassed so as to test I8 alone: refused. A file placed in site-packages outside pip: refused. The control: certifi's `tests` package passes (dev's v3: the copied tree's COORDINATION file, its specs directory and its tests directory, each found); (b) an image with a planted fake key-shaped string in a dotfile under HOME: refused, naming the file (dev, demonstrated) |

**Live checks at the release step only:** `veracium selfcheck` with the key (13/13 at 0.32.0, per dev's prototype),
and dev's prototype's `remember` then `recall` round trip. CI holds no provider key (none of the four workflows reads a
secret), and a per-push live call would spend on every push.

## 7. Failure modes and reversibility

- **A pushed version tag is irreversible in practice.** A pull is a copy. A defect is fixed by a new version, never by
  re-pushing the tag (§4a.3).
- **A failed migration:** the 0018 contract, with the volume backup as the host's `--backup` reference.
- **The attested gate fails on a re-pin:** the build refuses, and nothing is pushed.
- **An image with a trust-bearing default ships:** I3 refuses it at build. If one escaped, every deployment that
  pulled it would carry the attestation. That is why I3 runs on the digest to be pushed, not only per push.

## 8. Claims and limits

**Claim:** for a release with an image, the image runs that release's wheel, opens its store as an attested build on
linux/amd64 and linux/arm64, sets no trust-bearing value, and originates network traffic at run time only to the
configured LLM provider.

**Not claimed:**
- that the image's dependencies are free of defects. They are pinned, not audited;
- Windows images, an HTTP transport, a lower floor, or bundled providers other than Anthropic (dev's point 7);
- that a host's `VERACIUM_MCP_CAPABILITY=direct` is honest. That is the deployment's attestation (0031 §8);
- that the reported `serverInfo.version` is veracium's (§10 N1).

## 9. Brief for the external reviewer

To be written if §10 Q1 rules for review. The questions would be §3's trust defaults, §4a's gating order, and §4c's
upgrade contract.

## 10. Open questions

**For the owner (both RULED, 2026-11-12, first-hand to dev):**
- **Q1, ruled "Accept on your word (Recommended)":** review path. D2 makes this `lightweight`: no guarded file. It is still a new outward-facing artifact.
  External review, or acceptance on the owner's word as for 0053?
- **Q2, ruled "On the /data volume (Recommended)":** `config/` and `state/` on the volume, per §4c's recommendation, or HOME-only and ephemeral? With HOME-only,
  consent and the local error log are lost with `--rm`, and telemetry stays at its default, off.

**BLOCKING on dev's proposed shape (corrected in this draft):**
- **B1:** the usage must pass `VERACIUM_MCP_SOURCE_ID`, or a host-attested `VERACIUM_MCP_CAPABILITY`, or `remember`
  stores nothing (§3). The image sets neither.
- **B2:** the per-push smoke cannot include `selfcheck`, which needs a live key, and CI holds none. Per push: I1–I8;
  live checks at the release step (§6).
- **B3:** push the digest that passed the gates; never rebuild at release. Dependencies are pinned by hash (§4a, §4b).
- **B4:** HOME outside `/data`, and `/data`'s contents named (§4c, I6), per dev's point 4.

**NEXT-ROUND (outside this spec):**
- **N1:** `serverInfo.version` reports the MCP SDK's version ("1.30.0"), not veracium's (dev's point 1). It is a
  `src/veracium/mcp_server.py` change, a guarded file, so it is its own item.
- **N2:** `server.json`, the MCP Registry manifest, names version 0.16.0. The registry's `oci` package type could list
  the image beside the PyPI package once it ships.
- **N4:** `mcp_server.main()` appends "(Is ANTHROPIC_API_KEY set? Run veracium-mcp --help.)" to every start failure,
  the store's schema refusal included. In the image it misleads twice: the refusal is not about the key, and startup
  needs none (measured). `src/veracium/mcp_server.py` is guarded, so this is an item of its own, like N1.
- **N3:** SBOM and build-provenance attestations for the image (GitHub's artifact attestations), if the owner wants
  them.

## Reviewer checklist

- [ ] §3 has a row for every class, the untouched ones included
- [ ] every §6 check was demonstrated RED against its named wrong image
- [ ] I1–I8 on linux/arm64, natively on `ubuntu-24.04-arm`: they can run only in the implementation's first CI run, so **the first push is gated on them**, not a pre-acceptance demonstration
- [ ] the documented usage stores a fact (B1), and §4e states what each configuration yields (R1)
- [ ] the pushed digest is the gated digest (B3)

## Review closure

**Owner-accepted: the owner's word, first-hand in the dev session, 2026-11-12: "Accept 0054 v0.4 (Recommended)", then
"Accept v0.5 (Recommended)" for I8(a)'s narrowing. No external round (PROCESS §4a's second path; §10 Q1).** The reviews
were internal: research's drafts v0.1–v0.5, and dev's prototype and implementation reads. One row per finding, each
closed by a file, a check or a test that fails if it reopens. Test nodes are in `tests/test_0054_container.py`; the
image checks are `container/check_image.py check` (I1–I8) and `container/check_image.py red` (the RED matrix), run by
the `container` workflow. At adoption the RED matrix, run on the 0.32.0 wheel, refused 11 of 11 wrong images, and
the GREEN image passed I1–I8.

| # | finding (source) | closed by |
|---|---|---|
| B1 | the documented usage stored nothing without a source id or a host attestation (research, v0.1) | §4e's usage passes `VERACIUM_MCP_SOURCE_ID`, and its table states what each configuration yields (R1) |
| B2 | the per-push check could not include `selfcheck`, which needs a live key (research, v0.1) | `.github/workflows/container.yml` runs I1–I8 and the RED matrix on every push with no secret; the live checks are the release step's (§6) |
| B3 | the pushed digest must be the gated one, and the dependencies pinned (research, v0.1) | `container/Dockerfile` installs `container/requirements.lock` with `--require-hashes`; `test_every_locked_dependency_is_hashed_and_the_lock_covers_the_install`; §4a.2 for the release step |
| B4 | HOME on the volume put skeleton files and settings into `/data` (dev's point 4) | I6, with the RED case `I6-home-on-the-volume`; `test_non_root_the_working_directory_off_the_volume_and_the_server_as_entrypoint` |
| C1 | with `WORKDIR /data`, a wrong store-variable name passed I4 (dev's v3 RED run) | `WORKDIR /home/veracium` in `container/Dockerfile`; the RED case `I4-wrong-store-variable`; `test_non_root_the_working_directory_off_the_volume_and_the_server_as_entrypoint`; `test_the_store_variable_is_the_one_the_server_reads` |
| C2 | the build gate matched doctor's prose rather than the status (dev's read) | `test_the_attested_gate_reads_the_status_not_doctors_prose`; the RED case `I2-unattested-base` (refused, "runtime status: verified") |
| R1 | §4e did not say what each configuration yields (dev's v4 measurement) | §4e's three-row table |
| R2 | I8's secrets scan named no instrument and had no RED case (dev's read) | I8(b) in `container/check_image.py`; the RED case `I8-planted-key`; `test_the_secret_scan_allowlist_is_well_formed` |
| R3 | arm64 could not be checked on this box (dev, no emulation) | the `image (arm64)` job of `.github/workflows/container.yml`, on `ubuntu-24.04-arm`; the first push is gated on it (checklist) |
| R4 | the lock's generator was unnamed (dev's read) | `container/requirements.lock`, its generator and version named in the adoption commit |
| v0.5 | I8(a) as v0.4 worded it refused certifi's own `tests` package; a narrowing by RECORD alone would have exempted veracium's own wheel (dev's build; research's correction) | the two tiers in `container/check_image.py` (`NEVER`, `UNLESS_OTHERS_OWN`); the RED cases `I8-repository-copied`, `I8-veracium-ships-claude-md` and `I8-unowned-tests-in-site-packages`; `test_every_red_edit_still_applies_and_the_matrix_names_its_invariants`; `test_a_wheel_rebuilt_with_one_more_file_lists_it_in_its_own_record` |
| I7 | a failed handshake could have read as the refusal (dev's own instrument, before any result went out) | I7 in `container/check_image.py` requires the refusal's own words in the server's stderr |
