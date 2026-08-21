<!-- GENERATED:lessons-summary -->

# What the external review of 0022 and 0023 actually found

Spec-Status: n/a — this is a process record, not a spec

**The design stopped moving early; the packaging did not.** Since the last
change to either specification, every finding has been in the EVIDENCE
MACHINERY — the checks, the carriers, and the way the package is built. That
is worth stating plainly, because the natural reading of a long series of
returned rounds is that the design is troubled. The generated table below
says when the last specification change was, and how many rounds have passed
since; this prose is no longer permitted to say it.

The findings are not a pile of unrelated defects. Classified by FAILURE
MECHANISM rather than by symptom, they collapse into a small number of classes
— and most of those classes were RE-FOUND after their first instance was
fixed. That is the actual problem: not that the reviewer keeps finding things,
but that I kept fixing the named cell and shipping.

**This document has been the defect it describes, repeatedly.** Its first
version was hand-written, with class counts that did not match the findings
they counted and a restated duration no carrier agreed with. Its replacement
generated the table and then left a free-text round count in this opening
summary — outside the block, ungated, and wrong; the reviewer flipped it to an
absurd value and every check still passed.

So: no quantity appears above the table, and a gate enforces that rather than
trusting me. Everything countable is generated from
`specs/review_lessons.py`, where every finding carries its own classification
and the whole set is checked TOTAL against the closure ledger — an
unclassified finding fails the build, so does a classification naming a
finding that does not exist, and so does a class with nothing in it.

---

## The classes

**90 external findings, raised across 20 rounds, and 11 found internally — every one classified below, exactly once.** Counts are DERIVED from `MECHANISM` in `specs/review_lessons.py`, which is checked total against the closure ledger: a finding that is not classified fails the build, and so does a class with nothing in it. Nothing in this section is a hand-kept number — R15-2 was exactly that.

| # | class | external | self-found | rounds it was raised in | recurred |
|---|---|---|---|---|---|
| 1 | **self-assertion** — A claim not produced by the thing it describes | 14 | 1 | 1, 2, 4, 5, 6, 8, 9, 12, 16 | **yes** |
| 2 | **proxy** — The check binds a stand-in, not the property | 14 | 0 | 1, 3, 5, 7, 10, 11, 18, 19, 20 | **yes** |
| 3 | **second-copy** — The same fact stated twice | 30 | 0 | 1, 2, 3, 4, 5, 6, 7, 10, 13, 15, 16, 17 | **yes** |
| 4 | **domain** — The rule's reach is not its domain | 27 | 6 | 1, 2, 3, 4, 5, 6, 15, 17, 18, 19 | **yes** |
| 5 | **self-reference** — The check reads what its own run produces | 0 | 3 | — | — |
| 6 | **coercion** — A silent cast or default admits what the check meant to reject | 3 | 0 | 8, 13, 14 | **yes** |
| 7 | **env-leak** — The producing environment leaked into the artifact | 2 | 0 | 10, 11 | **yes** |
| 8 | **disclosure** — Behaviour that is correct but never stated to whoever must act on it | 0 | 1 | — | — |

**The last finding that required a change to either specification was raised in round 6.** The 15 rounds that returned a verdict since (7–21) raised packaging and process findings only — 60 of the 101 findings here are spec-scoped, and every one of them is at or before round 6. Derived from the `scope` field on each classification; nothing in this paragraph is typed.

**6 of 8 classes recurred** — they were raised in more than one round, which means the first instance was fixed and the mechanism shipped again in another costume: `self-assertion`, `proxy`, `second-copy`, `domain`, `coercion`, `env-leak`. That is the finding this document exists for. It is derived from the rounds column, not asserted.

**`self-reference`, `disclosure` were never raised by the reviewer** — they are the classes I found myself, while fixing something else. The previous hand-written version of this table attributed external finding ids to `self-reference`, which is how a document about second copies acquired one.

<!-- /GENERATED:lessons-summary -->
Each class, its rule, and what now catches it — the per-finding assignments
and the reason each one was filed where it was are in
`specs/review_lessons.py`:

### 1. self-assertion — a claim not produced by the thing it describes
`ran` trusted rather than derived from the records (R12-2). A transcript whose
deletion left every check green (R12-1). Four hand-maintained package claims
beside the executables that contradicted them (R8-2). A launcher that invented
its own qualification rule and certified against it (R6-4).

And the package's own IDENTITY: an archive named v16 shipped two carriers
saying v15, because the requested version reached the builder and controlled
only the filename (R16-1). The commit had been cross-checked between those two
carriers since round 4; nothing checked which package they claimed to be.

**Rule:** a number, status or NAME in a carrier must be PRODUCED by the thing
it describes, in the same run that ships it — and where a fact has several
carriers, verification must refuse any disagreement between them.
**Mechanized:** the sealer substitutes measured values (`__MEASURED__`,
`__HARNESSES__`, `__EVIDENCE__`, `__LAUNCHER__`, `__CONTEXT__`) and refuses
unsubstituted tokens. The transcript is read, not counted.

### 2. proxy — the check binds a stand-in, not the property
Set-equality of ids instead of per-finding validation (R7-1). Substring
inspection of a command's source, defeated by a comment (R11-1). Labels
instead of argv (R10-2). A BUSY test measuring SQLite's internal wait instead
of the branch it was named for (R5-2). And in the spec itself: a host-supplied
clock standing in for the order decisions were made in (F2).

**Rule:** ask what the check would accept that is wrong. If a rename, a
comment or a cast defeats it, it binds a proxy.
**Mechanized:** argv pinned exactly with `-c` forbidden; every `-k` atom must
select a test; the extraction registry binds behaviour, not labels.

### 3. second-copy — the same fact stated twice
A hand-maintained closure ledger beside the generated one (R6-3, both specs).
"The SAME six checks" over seven (R13-2). The reviewer guide's workflow
contradicting COLLECTED for ten rounds (R10-1). A section header contradicting
a row of its own table (R4-2). This document's own counts (R15-2).

**And a form of it I had not seen until round 16:** `review_lessons.py`
located its generated block with `split(BEGIN, 1)` and never required exactly
one marker pair, so an appended second block claiming different numbers passed
every check (R16-2). The strict rule already existed twelve metres away in
`skip_inventory.verify_collected`, written for 0014's identical finding — so
this was a second, weaker *implementation* of a rule, and it carried the very
bug the original had been written to fix.

**Rule:** if a fact appears twice, one copy is already wrong or will be.
Delete or generate — never sync. **A COUNT IS A SECOND COPY OF A LIST — and AN
IMPLEMENTATION IS A SECOND COPY OF A RULE.** Before writing a checker, grep for
one: this project had already solved marker-block verification, strictly, for
this same reviewer.
**Mechanized:** generated blocks with `--check` gates, including the table
above; the withdrawn-claim sweep reads the BUILT artifact and the reviewer
guide.

### 4. domain — the rule's reach is not its domain
The skip-site regex matched `pytest.mark.skipif` and not `pytest.mark.skip(`,
so four unconditional skips were invisible to the completeness gate (R3-5).
`render()`'s hard-coded category list silently dropped a category (R4-4). The
withdrawn-phrase pattern matched one phrasing of the retracted rule (R3-2).
Failure outcomes that were not total (R5-1), a rollback boundary catching
`Exception` inside an operation catching `BaseException` (R6-1), a closed
schema closed at one level and not the one above it (R15-1). **And the mirror,
which is the same defect:** a lifecycle predicate applied too WIDELY, dropping
episodes in stores with zero revocations (0023 R3-3).

**Rule:** enumerate the domain and prove the enumeration, or make the checker
RAISE on anything it does not recognise. Then check the reach is not too wide
either — over-reach and under-reach are one mechanism.
**Mechanized:** `render()` raises on an unknown category; every `-k` atom must
select a test; the transcript schema is closed at every level, with a mutation
matrix DERIVED from the schema so a field or level added later cannot be
untested.

### 5. self-reference — the check reads what its own run produces
Evidence commands that validated the transcript the runner was writing, and a
command selecting the evidence RUNNER, whose nested child skips on the
recursion marker — so half of it exercised nothing while exiting 0. A test
that spawned the suite that runs it, turning 39s into 23 minutes.

**And the same mechanism between TESTS:** the transcript validator was a
separate test reading the file the runner writes, while `pytest-randomly`
shuffles test order every run — so CI failed on the seeds that put the reader
first, intermittently, from the round-12 seal onward. Four seals went out with
the suite red on GitHub because I pushed and did not look. The ledger already
carried the rule, in two places, and it had been applied to evidence
*commands* only.

**Rule:** nothing may read an artifact whose production it takes part in —
evidence commands and tests alike. Where possible, remove the ordering rather
than fix it: the validation now runs inside the producer.
**Mechanized:** the closure-evidence gate rejects any command that reads an
artifact the runner writes, and is itself proven against synthetic positive and
negative fixtures. *This class was never externally raised — both instances are
mine, and the second was caught by a CI signal I was not reading.*

### 6. coercion — a silent cast or default admits what the check meant to reject
`exit: false` passed `!= 0` because `bool` subclasses `int`. A 64-digit
integer survived `str()` before a hex regex. A duplicated entry vanished into
a set. `raised` read with `.get(..., [])`, so an OMITTED field was
indistinguishable from a declared absence — a default that fabricated the fact
being checked (R8-1, R13-1, R14-1).

**Rule:** `type(x) is T`, never `isinstance`, in any integrity check — and
never a default that fabricates the fact.
**Mechanized:** the closed, exactly-typed transcript schema; `raised` required
explicitly.

### 7. env-leak — the producing environment leaked into the artifact
The sealing user's uid/gid rode into the archive, so a plain `tar -xzf` exited
2 for the recipient (R10-3). Sealing inherited the whole environment, so a
recursion marker turned the evidence runner into a skip while the sealer still
generated an all-commands-ran claim (R11-2).

**Rule:** an artifact must be built and verified as the RECIPIENT will open
it, not as its producer happens to hold it.
**Mechanized:** normalized ownership on every member, a plain `tar -xzf` gate,
and an allowlisted sealing environment.

### 8. disclosure — correct behaviour never stated to whoever must act on it
`complete=False` is the expected steady state on any consolidation-bearing
store, and operators had not been told (M4, internal).

**Rule:** if the steady state surprises an operator, the surprise is the
defect.
**Not mechanized** — prose review only, and it is the one class here with no
gate behind it.

---

## The two rules under all of them

**A check that cannot fail is not a check.** Every class above passes while
examining nothing. So: for every gate, write the mutation that must fail it,
run it, and keep it — *and* keep a clean control, because a check that rejects
everything passes all its rejection tests.

**Fix the class, not the cell.** Most of these classes were re-found after the
first instance was fixed, and the table above derives which ones from the
rounds they appeared in. When a finding lands, ask where else that mechanism
lives before fixing the site named. R15-1 is the sharpest example: the round-14
fix established "closed" for command objects, wrote six mutations for command
objects, and never asked whether the object holding them was closed too.

## Honest limits

- Classes 1 and 3 are only partly mechanized: the sealer substitutes what it
  knows to substitute, and a NEW hand-written claim in a carrier is still
  possible. The withdrawn-claim list is the backstop and it is hand-extended.
- Class 8 has no gate at all.
- The evidence machinery costs real time, and it grows with the ledger: every
  closure row adds a command, and several commands are themselves suite runs.
  No duration is quoted here on purpose — R15-2 was partly a stale one, and the
  same suite measured 16:45, 15:06 and 1:33 in one package depending on the
  host and the environment. The current figures are in `COLLECTED.txt`, which
  is generated by the run that produces them.
