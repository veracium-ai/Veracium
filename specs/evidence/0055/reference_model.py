"""Reference model of the credential-shape filter (research prototype for the draft spec).

Deterministic: regular expressions over a normalised view of the text, no model, no network.
Two kinds of class:
  structural - the token's own shape names it (a vendor prefix, a PEM armour line, a JWT's three parts,
               a URL with a password in its userinfo);
  labelled   - a credential-naming label ("password", "api key", ...) followed by a value that passes a
               value test (not a stop word, not already masked).
No unlabelled-entropy class: see the spec's §1 (rejected alternatives).

scan(text)  -> list of Finding(cls, start, end) in ORIGINAL offsets, merged, non-overlapping.
mask(text)  -> (masked_text, report) where report = {cls: count}; never the value, its length, a prefix,
               a suffix or a digest.

No structural test token appears literally: those are assembled at run time (see vectors.py), so that this file
and the spec do not themselves trip a secret scanner on a push. The labelled rows use well-known dummy values, literally.
"""
from __future__ import annotations

import bisect
import re
import unicodedata
from dataclasses import dataclass

PLACEHOLDER = "[credential withheld: {cls}]"

# Characters removed before scanning: zero-width and format characters, soft hyphen.
_INVISIBLE = {"\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad", "\u180e"}

B62 = r"A-Za-z0-9"
STRUCTURAL: list[tuple[str, str]] = [
    ("aws_access_key_id",      r"(?<![A-Za-z0-9])(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}(?![A-Za-z0-9])"),
    ("github_token",           r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{36,255}(?![A-Za-z0-9])"),
    ("github_token",           r"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{22,255}(?![A-Za-z0-9])"),
    ("gitlab_token",           r"(?<![A-Za-z0-9])glpat-[A-Za-z0-9_\-]{20,}"),
    ("slack_token",            r"(?<![A-Za-z0-9])xox[abposr]-[A-Za-z0-9-]{10,}"),
    ("slack_webhook",          r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+"),
    ("stripe_key",             r"(?<![A-Za-z0-9])(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}"),
    ("anthropic_key",          r"(?<![A-Za-z0-9])sk-ant-[A-Za-z0-9_\-]{20,}"),
    ("openai_key",             r"(?<![A-Za-z0-9])sk-(?!ant-)(?:proj-|svcacct-|admin-)?[A-Za-z0-9_\-]{20,}"),
    ("google_api_key",         r"(?<![A-Za-z0-9])AIza[0-9A-Za-z_\-]{35}"),
    ("google_oauth_secret",    r"(?<![A-Za-z0-9])GOCSPX-[A-Za-z0-9_\-]{28}"),
    ("huggingface_token",      r"(?<![A-Za-z0-9])hf_[A-Za-z0-9]{34,}"),
    ("npm_token",              r"(?<![A-Za-z0-9])npm_[A-Za-z0-9]{36}(?![A-Za-z0-9])"),
    ("pypi_token",             r"(?<![A-Za-z0-9])pypi-AgEIcHlwaS5vcmc[A-Za-z0-9_\-]{50,}"),
    ("sendgrid_key",           r"(?<![A-Za-z0-9])SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}"),
    ("digitalocean_token",     r"(?<![A-Za-z0-9])do[por]_v1_[a-f0-9]{64}(?![A-Za-z0-9])"),
    ("azure_storage_key",      r"AccountKey=[A-Za-z0-9+/=]{86,88}"),
    ("jwt",                    r"(?<![A-Za-z0-9])eyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),
    ("private_key_block",      r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----"
                               r"(?:[\s\S]*?-----END (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----|[\s\S]*\Z)"),
    ("url_userinfo_password",  r"(?<![A-Za-z0-9])[a-zA-Z][a-zA-Z0-9+.\-]{0,31}://[^\s:/@]{1,256}:[^\s@/]{1,256}@[^\s/]+"),
    ("auth_header",            r"(?i)(?<![A-Za-z0-9])authorization\s*:\s*(?:basic|bearer|token)\s+[A-Za-z0-9._~+/\-]{16,}=*"),
    ("bearer_token",           r"(?i)(?<![A-Za-z0-9])bearer\s+[A-Za-z0-9._~+/\-]{20,}=*"),
    # Veracium's own bearer: forget_everything_preview's token authorises a whole-user erase (0031 §4f)
    ("veracium_preview_token", r"(?<![A-Za-z0-9])tt1\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{20,}"),
]

# Labels: a credential-naming word or phrase. STRONG labels take any non-stop-word value; WEAK labels
# (words with ordinary senses: secret, token, key, pin) take only a value that looks generated.
STRONG = (r"pass(?:word|wd|phrase|code)|pwd|api[\s_\-]?key|access[\s_\-]?key(?:[\s_\-]?id)?|secret[\s_\-]?key|"
          r"client[\s_\-]?secret|access[\s_\-]?token|auth[\s_\-]?token|refresh[\s_\-]?token|private[\s_\-]?key|"
          r"aws[\s_\-]?secret[\s_\-]?access[\s_\-]?key|contrase[ñn]a|mot de passe|passwort|senha|パスワード|密码")
# "pin" is not a weak label (v0.4.1): in this project it names a commit, and `"pin": "<40-hex sha>"` read as a generated
# value withheld a commit sha (the round-2 package's own self-scan). Numeric PINs have their own rule, PIN, below.
WEAK = r"secret|token"
SEP = r"\s*(?:is(?:\s+now)?|was|=|:|：|->|=>)\s*"
VALUE = r"""(?:["“](?P<qval>[^"”\n]{4,200})["”]|'(?P<sval>[^'\n]{4,200})'|[`‘]?(?P<val>[^\s"'`”’,;]{4,}))"""
# v0.4 (round 1's answer to Q2): structured configuration. A label may close its own quote (`{"password": "…"}`), may
# follow `_` or `-` (`DB_PASSWORD=…`, where \b fails because `_` is a word character) but not `/`, `.` or `\` (a
# path such as /etc/passwd is not a label: the corpus run found one), and an XML element's `>` may
# follow it directly (`<password>…`). The label must not be followed by more of a word (`password_policy`).
LABELLED = re.compile(rf"(?i)(?<![A-Za-z0-9/.\\])(?:(?P<strong>{STRONG})|(?P<weak>{WEAK}))(?![A-Za-z0-9])(?:[\"'](?={SEP}))?(?:{SEP}|>)(?!/){VALUE}")
# PIN: upper-case "PIN" anywhere, or lower/mixed-case "pin" only after an owner word. A bare lower-case "pin"
# is this project's own word for a commit ("capture at the pin: 7351 passed" - 52 hits in specs/, found by the
# corpus run before this rule was narrowed).
_OWNER = r"(?:my|our|your|his|her|their|card|bank|debit|atm|phone|sim|door|alarm|safe|voicemail)"
PIN = re.compile(rf"(?:\bPIN|(?i:\b{_OWNER}\s+pin))(?i:[\s_\-]?(?:code|number))?(?i:{SEP})(?P<pin>\d{{4,8}})\b")

STOP = {
    "the", "a", "an", "my", "our", "your", "their", "his", "her", "its", "in", "on", "at", "to", "for", "of",
    "not", "no", "none", "null", "empty", "blank", "unset", "set", "reset", "changed", "rotated", "revoked",
    "expired", "wrong", "incorrect", "correct", "valid", "invalid", "required", "missing", "stored", "saved",
    "same", "different", "secure", "insecure", "weak", "strong", "long", "short", "case-sensitive",
    "redacted", "hidden", "withheld", "masked", "removed", "unknown", "forgotten", "lost", "shared",
    "configured", "needed", "optional", "mandatory", "there", "here", "below", "above", "attached",
    "in 1password", "somewhere", "elsewhere", "this", "that", "it", "what", "which", "too", "very",
    "something", "nothing", "fine", "good", "bad", "great", "important",
    "true", "false", "yes", "no", "null", "enabled", "disabled", "on", "off",
}
_CODE_EXPR = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\s*[(\[]")
_MASKED_VALUE = re.compile(r"^(?:[*•x#]+|<[^>]*>|\[[^\]]*\]|\{\{[^}]*\}\}|\$\{[^}]*\}|\$[A-Z_][A-Z0-9_]*|%[A-Z_]+%)$", re.I)


def _looks_generated(v: str) -> bool:
    """A weak label's value must look generated: >= 8 chars and at least two of
    {upper, lower, digit, symbol}, or >= 16 chars of [A-Za-z0-9] with a digit."""
    if len(v) < 8:
        return False
    kinds = sum(bool(re.search(p, v)) for p in (r"[A-Z]", r"[a-z]", r"[0-9]", r"[^A-Za-z0-9]"))
    return kinds >= 3 or (kinds >= 2 and len(v) >= 12 and bool(re.search(r"[0-9]", v)))


def _value_ok(v: str, strong: bool) -> bool:
    w = v.strip().rstrip(".!?)").lower()
    if not w or w in STOP or _MASKED_VALUE.match(v.rstrip(".!?)")):
        return False
    if v.startswith(("[", "<", "{", "$", "%", "*")):   # a placeholder, template or masked value (and our own
        return False                                    # placeholder: the filter must be inert on its output)
    if _CODE_EXPR.match(v):                             # `token = m.group(0)`: an expression, not a value
        return False
    if strong:
        return len(w) >= 4
    if any(ch.isspace() for ch in v):                   # a weak label's quoted value must be one token
        return False
    return _looks_generated(v.rstrip(".!?)"))


def _normalise(text: str) -> tuple[str, list[int]]:
    """NFKC per character, invisible characters dropped. Returns the view and, for each view index, the
    original index it came from (so a finding maps back to original offsets)."""
    out, idx = [], []
    for i, ch in enumerate(text):
        if ch in _INVISIBLE or unicodedata.category(ch) == "Cf":
            continue
        n = unicodedata.normalize("NFKC", ch)
        for c in n:
            out.append(c)
            idx.append(i)
    return "".join(out), idx


@dataclass(frozen=True)
class Finding:
    cls: str
    start: int
    end: int


_STRUCT = [(c, re.compile(p)) for c, p in STRUCTURAL]
# one class per finding: the first structural class in list order, then the labelled ones
_RANK = {c: i for i, c in enumerate(dict.fromkeys([c for c, _ in STRUCTURAL] + ["labelled_password", "labelled_pin", "labelled_secret"]))}


def scan(text: str) -> list[Finding]:
    view, idx = _normalise(text)
    raw: list[tuple[int, int, str]] = []
    bounded: set[tuple[int, int]] = set()   # spans already bounded by their own quotes: never widened
    for cls, rx in _STRUCT:
        for m in rx.finditer(view):
            raw.append((m.start(), m.end(), cls))
    for m in LABELLED.finditer(view):
        strong = m.group("strong") is not None
        g = "qval" if m.group("qval") is not None else "sval" if m.group("sval") is not None else "val"
        v = m.group(g)
        if _value_ok(v, strong):
            if g == "val":
                raw.append((m.start(g), m.end(g), "labelled_password" if strong else "labelled_secret"))
            else:
                # a quoted value is withheld quote to quote, inclusive, and not widened: its quotes bound it, and
                # widening to the whitespace token took a JSON object's closing brace with it (v0.4)
                span = (m.start(g) - 1, m.end(g) + 1)
                bounded.add(span)
                raw.append((*span, "labelled_password" if strong else "labelled_secret"))
    for m in PIN.finditer(view):
        raw.append((m.start("pin"), m.end("pin"), "labelled_pin"))
    if not raw:
        return []
    # widen each span to the whitespace-delimited token it sits in (a partial match must not leave a tail)
    # token boundaries computed once (O(n)); widening per finding by bisection, never by walking the run again
    # (walking was quadratic: many findings inside one whitespace-free run, found by redos.py)
    runs = [(m.start(), m.end()) for m in re.finditer(r"\S+", view)]
    starts = [r[0] for r in runs]
    widened = []
    for s, e, c in raw:
        if c != "private_key_block" and (s, e) not in bounded:
            i = bisect.bisect_right(starts, s) - 1
            if i >= 0 and runs[i][0] <= s < runs[i][1]:
                s = runs[i][0]
            j = bisect.bisect_right(starts, max(e - 1, s)) - 1
            if j >= 0 and runs[j][0] <= e - 1 < runs[j][1]:
                e = runs[j][1]
        widened.append((s, e, c))
    widened.sort()
    merged: list[list] = []
    for s, e, c in widened:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
            if c not in merged[-1][2]:
                merged[-1][2].append(c)
        else:
            merged.append([s, e, [c]])
    res = []
    for s, e, cs in merged:
        os_ = idx[s]
        oe = idx[e - 1] + 1
        res.append(Finding(min(cs, key=_RANK.__getitem__), os_, oe))
    return res


# The completed output must be inert (I3): scan(mask(t)[0]) == []. One pass is not enough, because withholding a span
# can SHORTEN an enclosing quoted value back under the labelled rule's 200-character bound, so the next scan finds the
# enclosing label (round 1's R1-04: 'password: "' + "a " * 79 + a GitHub token + ' end"'). mask() therefore repeats.
#
# v0.5 (round 2's R2-01): the bound is a CONSTRUCTION, not an argument about the grammar. mask() runs at most
# MAX_PASSES passes; if the text is still not inert, the WHOLE value is withheld as one placeholder of class
# FALLBACK_CLASS. So mask() always returns, always returns inert text (the placeholder is inert, asserted below), never
# raises, and does at most MAX_PASSES + 1 scans: each scan's result is used twice, as the check that the previous pass
# left the text inert and as the findings the next pass withholds (v0.5.2, round 3's A1: v0.5.1 scanned once inside
# each pass and again before it, two scans per pass and eight at the bound; scan_count.py asserts the count). v0.4's argument ("double-quoted values cannot nest") was false, and
# no argument about the quote grammar can replace it: a pass withholds a quoted value QUOTE TO QUOTE, so the value one
# layer out no longer contains the inner quotes, and every quote class nests to any depth by containment, one layer
# per pass (depth_family.py: the reviewer's curly family, every opener/closer pairing and alternating classes; tried
# and measured, excluding U+201C from the double-quoted body did not remove the nesting, so the grammar is unchanged).
# On ordinary text the repetition needs at most 3 passes (compose_fuzz.py, the table, the corpora); a labelled value
# nested four or more deep is withheld whole.
MAX_PASSES = 4
FALLBACK_CLASS = "unmaskable_text"


def _mask_once(text: str, ours: list = (), found: list | None = None) -> tuple[str, list]:
    """One pass. `ours` is the (start, end, cls) spans of the placeholders earlier passes wrote into `text`; a finding
    that overlaps one swallows it. `found` is scan(text) when the caller already holds it (mask() always does); only
    the evidence's raw-pass counters omit it. Returns the new text and the placeholders it now holds, in order."""
    out, pos, delta, held, k = [], 0, 0, [], 0
    for f in (scan(text) if found is None else found):
        while k < len(ours) and ours[k][1] <= f.start:          # earlier placeholders untouched by this finding
            s, e, cl = ours[k]
            held.append((s + delta, e + delta, cl))
            k += 1
        while k < len(ours) and ours[k][0] < f.end:             # overlapped: swallowed by this finding
            k += 1
        out.append(text[pos:f.start])
        ph = PLACEHOLDER.format(cls=f.cls)
        new_start = f.start + delta
        out.append(ph)
        held.append((new_start, new_start + len(ph), f.cls))
        delta += len(ph) - (f.end - f.start)
        pos = f.end
    for s, e, cl in ours[k:]:
        held.append((s + delta, e + delta, cl))
    out.append(text[pos:])
    return "".join(out), held


def _report(held: list) -> dict:
    """The report counts the placeholders mask() wrote that are in its FINAL output, by class (R2-03's count
    semantics): a span swallowed by a later pass, or merged into another span, is not counted again. A placeholder
    already present in the input is not one mask() wrote and is never counted."""
    rep: dict[str, int] = {}
    for _, _, cl in held:
        rep[cl] = rep.get(cl, 0) + 1
    return rep


def _run(text: str) -> tuple[str, list, int, bool]:
    """The one loop mask() and passes_needed() share. Returns (text, placeholders held, passes, fell back). Scans: one,
    then one after each pass, so a completed mask does passes + 1 scans and a fallback MAX_PASSES + 1."""
    out, held, passes = text, [], 0
    found = scan(out)
    while found:
        if passes >= MAX_PASSES:
            return out, held, passes, True
        out, held = _mask_once(out, held, found)
        passes += 1
        found = scan(out)
    return out, held, passes, False


def mask(text: str) -> tuple[str, dict]:
    out, held, _, fell_back = _run(text)
    if fell_back:
        whole = PLACEHOLDER.format(cls=FALLBACK_CLASS)
        return whole, {FALLBACK_CLASS: 1}
    return out, _report(held)


assert not scan(PLACEHOLDER.format(cls=FALLBACK_CLASS)), "the fallback placeholder must be inert"


def passes_needed(text: str) -> int:
    """How many passes mask() takes: 1..MAX_PASSES when it completes, MAX_PASSES + 1 when it falls back. For the
    evidence. Text with no shape counts as one pass, as before v0.5.2 (that pass now costs only its scan)."""
    _, _, passes, fell_back = _run(text)
    return MAX_PASSES + 1 if fell_back else max(passes, 1)
