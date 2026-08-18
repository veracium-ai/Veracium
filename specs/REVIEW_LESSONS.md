# What fifteen external rounds actually found

Spec-Status: n/a — this is a process record, not a spec

**Both specs have been semantically clear since round 7.** Every finding
since has been in the EVIDENCE MACHINERY: the checks, the carriers and the
packaging. That is worth stating plainly, because the natural reading of
"fifteen rounds" is that the design is troubled, and the design has not moved
in eight rounds.

The findings are not fifteen unrelated defects. Classified by FAILURE
MECHANISM rather than by symptom, 39 external findings collapse into six
classes, and **I re-found five of them after fixing the first instance.** That
is the actual problem: not that the reviewer keeps finding things, but that I
kept fixing the named cell and shipping.

---

## The six classes, with what now catches them

### 1. Self-assertion — a claim read from the thing it describes (9 findings)
The count came from the ledger's length, not from execution (R11-2). `ran`
was trusted rather than derived from the records (R12-2). The manifest said
"26 findings" beside 31 rows (R7-1). COLLECTED claimed packaged-state
execution the sealer's own order contradicts (R8-2).

**Rule:** a number or status in a carrier must be PRODUCED by the thing it
describes, in the same run that ships it.
**Mechanized:** the sealer substitutes measured values (`__MEASURED__`,
`__HARNESSES__`, `__EVIDENCE__`, `__LAUNCHER__`, `__CONTEXT__`) and refuses
unsubstituted tokens. The transcript is read, not counted.

### 2. Proxy-not-property — the check inspects a stand-in (6 findings)
Set-equality of ids instead of per-finding validation (R7-1). Substring
inspection of a command's source, defeated by a comment (R11-1). Labels
instead of argv (R10-2). Presence and length instead of values (R13-1).

**Rule:** ask what the check would accept that is wrong. If a rename, a
comment or a cast defeats it, it binds a proxy.
**Mechanized:** argv pinned exactly with `-c` forbidden; the closed schema;
adversarial mutations for each.

### 3. Second copy — the same fact stated twice (6 findings)
Two closure ledgers (R5-3). A hand-written verifier list beside the generated
one (round 12, self-found). "The SAME six checks" over seven (R13-2). The
reviewer guide's workflow contradicting COLLECTED for ten rounds (R10-1).

**Rule:** if a fact appears twice, one copy is already wrong or will be.
Delete or generate — never sync. **A COUNT IS A SECOND COPY OF A LIST.**
**Mechanized:** generated blocks with `--check` gates; the withdrawn-claim
sweep reads the BUILT artifact and the reviewer guide.

### 4. Domain-too-narrow — the checker cannot see part of its own domain (4)
The skip-site regex matched `pytest.mark.skipif` and not `pytest.mark.skip(`,
so four unconditional skips were invisible to a test named `..._is_complete`
(R4-4). `render()`'s hard-coded category list silently dropped a category. The
withdrawn-phrase pattern matched one phrasing of the retracted rule (R3-2).

**Rule:** enumerate the domain and prove the enumeration, or make the checker
RAISE on anything it does not recognise.
**Mechanized:** `render()` raises on an unknown category; every `-k` atom must
select a test; the closed schema refuses undeclared fields.

### 5. Self-reference — the check reads what it is producing (3 findings)
Evidence commands validated the transcript the runner was writing (R12-1/2),
**and I reintroduced it at R13-3 while repointing a stale selector.** A test
spawned the suite that runs it, turning 39s into 23 minutes.

**Rule:** an evidence command must never read an artifact whose production it
is part of. Validate finished artifacts in the extraction.
**Mechanized below** — this class had no gate until now.

### 6. Silent coercion — the language accepts what the check meant to reject (2)
`exit: false` passed `!= 0` because `bool` subclasses `int`. A 64-digit
integer survived `str()` before a hex regex. A duplicated entry vanished into
a set (R13-1, R14-1).

**Rule:** `type(x) is T`, never `isinstance`, in any integrity check.
**Mechanized:** the closed, exactly-typed transcript schema.

---

## The two rules under all six

**A check that cannot fail is not a check.** Every class above passes while
examining nothing. So: for every gate, write the mutation that must fail it,
run it, and keep it — *and* keep a clean control, because a check that rejects
everything passes all its rejection tests.

**Fix the class, not the cell.** Five of six classes were re-found after I
fixed the first instance. When a finding lands, ask where else that mechanism
lives before fixing the site named.

## Honest limits

- Classes 1 and 3 are only partly mechanized: the sealer substitutes what it
  knows to substitute, and a NEW hand-written claim in a carrier is still
  possible. The withdrawn-claim list is the backstop and it is hand-extended.
- The suite grew from 39s to ~5min as the evidence runner grew with the
  ledger. That is a real cost, accepted deliberately, and it will keep growing
  linearly with findings.
