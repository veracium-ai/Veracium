"""Credential-shaped text is never stored (specs/0055).

The recogniser (§4a): deterministic regular expressions over a normalised VIEW of the text. No model, no network, no
state. `scan(text)` returns the findings in ORIGINAL offsets; `mask(text)` withholds every finding and returns the
masked text and its report, `{class: count}`. A report never carries the value, its length, its offsets, a prefix, a
suffix or a digest of it (§4g).

Research's reference model (specs/evidence/0055/reference_model.py) is the oracle: the build's tests compare this
module with it row by row and over a seeded fuzz, so a change here that drifts from the accepted rule set goes RED.
This module differs from the reference only in speed: the normalised view of an ASCII text is the text itself, so no
per-character map is built for it (I9 times the build, not the reference, at 256 KiB and 1 MiB).

Two kinds of class:
  structural - the token's own shape names it (a vendor prefix, PEM armour, a JWT's three parts, a URL whose
               userinfo carries a password, our own `tt1` preview token);
  labelled   - a credential-naming label, a separator, then a value that passes the value test.
There is deliberately no unlabelled-entropy class (§1, rejected alternatives).

`mask()` repeats until the output is inert, at most MAX_PASSES passes; if the text is still not inert after them the
WHOLE value is withheld as one `unmaskable_text` placeholder (§4a, round 2's R2-01). It never raises, and it scans
at most MAX_PASSES + 1 times: one scan, then one after each pass, each scan's result used both as the inertness check
and as the next pass's findings (round 3's A1).

Identifier fields are never masked (§4b): an entry point refuses one that carries a shape with `CredentialRefused`,
whose message names the field and the class and never the value.
"""
from __future__ import annotations

import bisect
import contextlib as _contextlib
import contextvars as _contextvars
import re
import unicodedata
from dataclasses import dataclass

#: The rule set's version, recorded in every audit event (§4a "Versioned"). Adding a class, or changing what a class
#: matches, is a spec change. 2 from v0.5.7: the token boundary, where `_` and every non-ASCII character are a boundary.
CREDENTIAL_SHAPES_VERSION = 2

#: The placeholder. NOT 0041's redaction marker (0041 INV-11 forbids ordinary writes from introducing that one).
PLACEHOLDER = "[credential withheld: {cls}]"
PLACEHOLDER_PREFIX = "[credential withheld: "

MAX_PASSES = 4
FALLBACK_CLASS = "unmaskable_text"

#: The refusal's name, shared by the library exception and every served refusal (§4g; the 0037 pattern).
REFUSAL = "credential_refused"

# Zero-width and format characters, and the soft hyphen, are dropped from the view (category Cf covers most).
_INVISIBLE = frozenset({"\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad", "\u180e"})

STRUCTURAL: tuple[tuple[str, str], ...] = (
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
)

# Strong labels take any value that is not a stop word; weak labels (ordinary words with a credential sense) take
# only a value that looks generated. "pin" is not a weak label: in this project it names a commit (§4a, K45-K47).
STRONG = (r"pass(?:word|wd|phrase|code)|pwd|api[\s_\-]?key|access[\s_\-]?key(?:[\s_\-]?id)?|secret[\s_\-]?key|"
          r"client[\s_\-]?secret|access[\s_\-]?token|auth[\s_\-]?token|refresh[\s_\-]?token|private[\s_\-]?key|"
          r"aws[\s_\-]?secret[\s_\-]?access[\s_\-]?key|contrase[ñn]a|mot de passe|passwort|senha|パスワード|密码")
WEAK = r"secret|token"
SEP = r"\s*(?:is(?:\s+now)?|was|=|:|：|->|=>)\s*"
VALUE = r"""(?:["“](?P<qval>[^"”\n]{4,200})["”]|'(?P<sval>[^'\n]{4,200})'|[`‘]?(?P<val>[^\s"'`”’,;]{4,}))"""
# Where a label may stand (v0.4): it may close its own quote (JSON and dict keys), follow `_` or `-` (a prefixed
# environment variable) but not `/`, `.` or `\` (a path), and be followed directly by `>` (an XML element). It may
# not be followed by more of a word (`password_policy`).
LABELLED = re.compile(rf"(?i)(?<![A-Za-z0-9/.\\])(?:(?P<strong>{STRONG})|(?P<weak>{WEAK}))(?![A-Za-z0-9])"
                      rf"(?:[\"'](?={SEP}))?(?:{SEP}|>)(?!/){VALUE}")
# PIN: upper-case "PIN" anywhere, or "pin" only after an owner word; a bare lower-case "pin" names a commit here.
_OWNER = r"(?:my|our|your|his|her|their|card|bank|debit|atm|phone|sim|door|alarm|safe|voicemail)"
PIN = re.compile(rf"(?:\bPIN|(?i:\b{_OWNER}\s+pin))(?i:[\s_\-]?(?:code|number))?(?i:{SEP})(?P<pin>\d{{4,8}})\b")

STOP = frozenset({
    "the", "a", "an", "my", "our", "your", "their", "his", "her", "its", "in", "on", "at", "to", "for", "of",
    "not", "no", "none", "null", "empty", "blank", "unset", "set", "reset", "changed", "rotated", "revoked",
    "expired", "wrong", "incorrect", "correct", "valid", "invalid", "required", "missing", "stored", "saved",
    "same", "different", "secure", "insecure", "weak", "strong", "long", "short", "case-sensitive",
    "redacted", "hidden", "withheld", "masked", "removed", "unknown", "forgotten", "lost", "shared",
    "configured", "needed", "optional", "mandatory", "there", "here", "below", "above", "attached",
    "in 1password", "somewhere", "elsewhere", "this", "that", "it", "what", "which", "too", "very",
    "something", "nothing", "fine", "good", "bad", "great", "important",
    "true", "false", "yes", "no", "null", "enabled", "disabled", "on", "off",
})
_CODE_EXPR = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\s*[(\[]")
_MASKED_VALUE = re.compile(r"^(?:[*•x#]+|<[^>]*>|\[[^\]]*\]|\{\{[^}]*\}\}|\$\{[^}]*\}|\$[A-Z_][A-Z0-9_]*|%[A-Z_]+%)$",
                           re.I)
_UPPER, _LOWER, _DIGIT, _SYMBOL = (re.compile(p) for p in (r"[A-Z]", r"[a-z]", r"[0-9]", r"[^A-Za-z0-9]"))
_RUN = re.compile(r"\S+")


def _looks_generated(v: str) -> bool:
    """A weak label's value must look generated: at least 8 characters and three of {upper, lower, digit, symbol},
    or 12+ characters, two kinds, one of them a digit."""
    if len(v) < 8:
        return False
    kinds = sum(1 for rx in (_UPPER, _LOWER, _DIGIT, _SYMBOL) if rx.search(v))
    return kinds >= 3 or (kinds >= 2 and len(v) >= 12 and _DIGIT.search(v) is not None)


def _value_ok(v: str, strong: bool) -> bool:
    w = v.strip().rstrip(".!?)").lower()
    if not w or w in STOP or _MASKED_VALUE.match(v.rstrip(".!?)")):
        return False
    if v.startswith(("[", "<", "{", "$", "%", "*")):   # a placeholder, template or masked value; our own
        return False                                    # placeholder must stay inert
    if _CODE_EXPR.match(v):                             # `token = m.group(0)`: an expression, not a value
        return False
    if strong:
        return len(w) >= 4
    if any(ch.isspace() for ch in v):                   # a weak label's value must be one token
        return False
    return _looks_generated(v.rstrip(".!?)"))


_NON_ASCII = re.compile(r"[^\x00-\x7f]+")
_NORM_CACHE: dict[str, str] = {}


def _norm_char(ch: str) -> str:
    n = _NORM_CACHE.get(ch)
    if n is None:
        n = "" if (ch in _INVISIBLE or unicodedata.category(ch) == "Cf") else unicodedata.normalize("NFKC", ch)
        if len(_NORM_CACHE) < 65536:
            _NORM_CACHE[ch] = n
    return n


class _Translate(dict):
    """str.translate's table over the normalisation cache."""

    def __missing__(self, cp: int) -> str:
        n = _norm_char(chr(cp))
        if len(self) < 65536:
            self[cp] = n
        return n


_TRANSLATE = _Translate()


class _OffsetMap:
    """Maps a view index back to the original index it came from, as the reference's per-character list does, but
    stored as breakpoints: identity segments (view index v maps to base + (v - start)) and expansion segments (every
    view index maps to one original index). Only a dropped character or a normalisation that changes the length
    starts a segment, so ordinary non-ASCII text (curly quotes, accents, full-width letters) costs no entries."""

    __slots__ = ("starts", "bases", "ident")

    def __init__(self):
        self.starts: list[int] = [0]
        self.bases: list[int] = [0]
        self.ident: list[bool] = [True]

    def mark(self, vpos: int, opos: int, ident: bool) -> None:
        if self.starts[-1] == vpos:                     # a later mark at the same view index replaces it
            self.bases[-1], self.ident[-1] = opos, ident
        else:
            self.starts.append(vpos)
            self.bases.append(opos)
            self.ident.append(ident)

    def __getitem__(self, v: int) -> int:
        k = bisect.bisect_right(self.starts, v) - 1
        return self.bases[k] + (v - self.starts[k]) if self.ident[k] else self.bases[k]


def _normalise(text: str) -> tuple[str, "_OffsetMap | None"]:
    """The view: NFKC per character, invisible characters dropped. Returns the view and the map from a view index to
    the original index it came from; None when the view IS the text (pure ASCII: NFKC is the identity on ASCII and no
    ASCII character is a format character)."""
    if text.isascii():
        return text, None
    out: list[str] = []
    omap = _OffsetMap()
    vpos = 0
    pos = 0
    for m in _NON_ASCII.finditer(text):
        s, e = m.span()
        if s > pos:
            out.append(text[pos:s])
            vpos += s - pos
        run = text[s:e]
        lens = {len(_norm_char(ch)) for ch in set(run)}
        if lens == {1}:                                 # every character one for one: the mapping holds
            out.append(run.translate(_TRANSLATE))
            vpos += e - s
            pos = e
            continue
        if lens == {0}:                                 # every character dropped (a run of invisible characters)
            omap.mark(vpos, e, True)
            pos = e
            continue
        for i in range(s, e):
            n = _norm_char(text[i])
            if len(n) == 1:                             # one for one: the current segment's mapping holds
                out.append(n)
                vpos += 1
                continue
            if n:                                       # an expansion: every view char maps to i
                omap.mark(vpos, i, False)
                out.append(n)
                vpos += len(n)
            omap.mark(vpos, i + 1, True)                # what follows maps one for one from i + 1
        pos = e
    if pos < len(text):
        out.append(text[pos:])
    return "".join(out), omap


@dataclass(frozen=True)
class Finding:
    cls: str
    start: int
    end: int


# Necessary literals: a structural pattern can match only where one of its literals occurs (in the view, or for the
# two case-insensitive patterns in the folded view), so a scan skips a pattern whose literals are all absent. Exact,
# not a heuristic: each literal is a substring every match of its pattern contains (test_0055_recogniser holds this
# by the reference model's differential and by a per-pattern check).
_NECESSARY: dict[str, tuple[tuple[str, ...], bool]] = {
    "aws_access_key_id": (("AKIA", "ASIA", "ABIA", "ACCA"), False),
    "github_token": (("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"), False),
    "gitlab_token": (("glpat-",), False),
    "slack_token": (("xox",), False),
    "slack_webhook": (("https://hooks.slack.com/services/T",), False),
    "stripe_key": (("_live_", "_test_"), False),
    "anthropic_key": (("sk-ant-",), False),
    "openai_key": (("sk-",), False),
    "google_api_key": (("AIza",), False),
    "google_oauth_secret": (("GOCSPX-",), False),
    "huggingface_token": (("hf_",), False),
    "npm_token": (("npm_",), False),
    "pypi_token": (("pypi-AgEIcHlwaS5vcmc",), False),
    "sendgrid_key": (("SG.",), False),
    "digitalocean_token": (("_v1_",), False),
    "azure_storage_key": (("AccountKey=",), False),
    "jwt": (("eyJ",), False),
    "private_key_block": (("-----BEGIN ",), False),
    "url_userinfo_password": (("://",), False),
    "auth_header": (("authorization",), True),
    "bearer_token": (("bearer",), True),
    "veracium_preview_token": (("tt1.eyJ",), False),
}
# Every label alternative of STRONG and WEAK contains one of these stems (case-folded); PIN needs "pin".
_LABEL_STEMS = ("pass", "pwd", "api", "access", "secret", "client", "auth", "refresh", "private", "aws", "contrase",
                "senha", "token", "\u30d1\u30b9\u30ef\u30fc\u30c9", "\u5bc6\u7801")
_STRUCT = tuple((c, re.compile(p), _NECESSARY[c][0], _NECESSARY[c][1]) for c, p in STRUCTURAL)
# One class per finding: the first structural class in list order, then the labelled ones.
_RANK = {c: i for i, c in enumerate(dict.fromkeys(
    [c for c, _ in STRUCTURAL] + ["labelled_password", "labelled_pin", "labelled_secret"]))}

#: Every class a report may name: the structural and labelled classes and the fallback. A report key outside this
#: set is a defect (I8's schema).
CLASSES = frozenset(_RANK) | {FALLBACK_CLASS}


def _fold(view: str) -> str:
    """A case-folded copy for the prefilters only (never for offsets). The regular-expression engine's IGNORECASE
    also equates two non-ASCII letters that NFKC keeps with ASCII ones (U+0130 and U+0131 with "i"; checked over
    every code point by test_0055_recogniser), so they fold to "i" here; dropping U+0307 can only widen the
    prefilter, never narrow it."""
    f = view.lower()
    if not f.isascii():
        f = f.replace("\u0131", "i").replace("\u0307", "")
    return f


def scan(text: str) -> list[Finding]:
    """Every credential-shaped span of `text`, merged and non-overlapping, in original offsets."""
    view, idx = _normalise(text)
    folded = _fold(view)
    raw: list[tuple[int, int, str]] = []
    bounded: set[tuple[int, int]] = set()   # spans bounded by their own quotes: never widened
    for cls, rx, lits, on_folded in _STRUCT:
        hay = folded if on_folded else view
        if not any(lit in hay for lit in lits):
            continue
        for m in rx.finditer(view):
            raw.append((m.start(), m.end(), cls))
    if any(stem in folded for stem in _LABEL_STEMS):
        for m in LABELLED.finditer(view):
            strong = m.group("strong") is not None
            g = "qval" if m.group("qval") is not None else "sval" if m.group("sval") is not None else "val"
            v = m.group(g)
            if _value_ok(v, strong):
                cls = "labelled_password" if strong else "labelled_secret"
                if g == "val":
                    raw.append((m.start(g), m.end(g), cls))
                else:
                    # a quoted value is withheld quote to quote, inclusive, and not widened (v0.4)
                    span = (m.start(g) - 1, m.end(g) + 1)
                    bounded.add(span)
                    raw.append((span[0], span[1], cls))
    if "pin" in folded:
        for m in PIN.finditer(view):
            raw.append((m.start("pin"), m.end("pin"), "labelled_pin"))
    if not raw:
        return []
    # Widen each unquoted span (a PEM block excepted) to the whitespace-delimited token it sits in, so a partial match
    # never leaves a tail (L18). Token boundaries are computed once, and only when some span needs widening;
    # widening is by bisection (walking the run per finding was quadratic, §4a T1).
    runs: list[tuple[int, int]] | None = None
    starts: list[int] = []
    widened = []
    for s, e, c in raw:
        if c != "private_key_block" and (s, e) not in bounded:
            if runs is None:
                runs = [m.span() for m in _RUN.finditer(view)]
                starts = [r[0] for r in runs]
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
        if idx is None:
            os_, oe = s, e
        else:
            os_, oe = idx[s], idx[e - 1] + 1
        res.append(Finding(min(cs, key=_RANK.__getitem__), os_, oe))
    return res


def _mask_once(text: str, ours: list, found: list) -> tuple[str, list]:
    """One pass over `found` (= scan(text)). `ours` holds the (start, end, cls) placeholders earlier passes wrote into
    `text`; a finding that overlaps one swallows it. Returns the new text and the placeholders it now holds."""
    out, pos, delta, held, k = [], 0, 0, [], 0
    for f in found:
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


def _run(text: str) -> tuple[str, list, int, bool]:
    """The one loop: (text, placeholders held, passes, fell back). One scan, then one after each pass."""
    out, held, passes = text, [], 0
    found = scan(out)
    while found:
        if passes >= MAX_PASSES:
            return out, held, passes, True
        out, held = _mask_once(out, held, found)
        passes += 1
        found = scan(out)
    return out, held, passes, False


def mask(text: str) -> tuple[str, dict[str, int]]:
    """Withhold every credential-shaped span. Returns (masked text, {class: count}). The count is of the placeholders
    mask() wrote that are in its FINAL output (§4a "What a report counts"): a span swallowed by a later pass is not
    counted again, merged spans are one, a fallback is {"unmaskable_text": 1}, and a placeholder already in the input
    is never counted. Text with no shape is returned unchanged (the same object) with an empty report."""
    out, held, _, fell_back = _run(text)
    if fell_back:
        return PLACEHOLDER.format(cls=FALLBACK_CLASS), {FALLBACK_CLASS: 1}
    rep: dict[str, int] = {}
    for _, _, cl in held:
        rep[cl] = rep.get(cl, 0) + 1
    return out, rep


assert not scan(PLACEHOLDER.format(cls=FALLBACK_CLASS)), "the fallback placeholder must be inert"

def mask_from(text: str, start: int) -> str:
    """The masked form of `text[start:]`, recognised IN THE CONTEXT of all of `text` (round 5's R5-04). `mask`'s own
    loop, with a cursor: a span that begins before the cursor and ends after it is omitted whole (its beginning is
    not being sent), and the cursor is carried through each pass's placeholders. A fallback is the fallback
    placeholder, as in `mask`."""
    out, held, passes, cur = text, [], 0, start
    found = scan(out)
    while found:
        if passes >= MAX_PASSES:
            return PLACEHOLDER.format(cls=FALLBACK_CLASS)
        for f in found:
            if f.start < cur < f.end:
                cur = f.end
        shift = sum(len(PLACEHOLDER.format(cls=f.cls)) - (f.end - f.start) for f in found if f.end <= cur)
        out, held = _mask_once(out, held, found)
        cur += shift
        passes += 1
        found = scan(out)
    return out[cur:]


#: Round 5's R5-04. The recogniser's multi-line grammars other than the PEM block join their parts by WHITE SPACE only
#: (a label's words `[\s_\-]?`, SEP's `\s*`, auth_header's and bearer_token's `\s+`), so a match that reaches a line
#: from earlier lines carries at least one of its parts on each non-blank line between. The longest chain of parts is
#: 7 (`aws secret access key` + `is now` + the value; PIN: owner, `pin`, `code`, `is now`, digits is 6), so a match
#: ending after the first CHAIN_LINES non-blank lines of a cut text begins inside it. The PEM block's body has no such
#: bound: its state at a cut is read from the text before the cut (`pem_open_before`).
CHAIN_LINES = 8
PEM_MARKER = re.compile(r"-----(BEGIN|END) (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")
PEM_REOPEN = "-----BEGIN PRIVATE KEY-----\n"


def chain_safe_offset(text: str) -> int:
    """The offset in `text` (which begins at a line start) after its first CHAIN_LINES non-blank lines, judged on the
    recogniser's view (an invisible character is not a part). Text before it is screened as context and not sent."""
    seen, pos = 0, 0
    while seen < CHAIN_LINES and pos < len(text):
        nl = text.find("\n", pos)
        end = len(text) if nl < 0 else nl + 1
        if _normalise(text[pos:end])[0].strip():
            seen += 1
        pos = end
    return pos


def pem_open_before(read_back, pos: int, chunk: int = 1 << 20) -> bool:
    """Whether a PEM private-key block is open at byte `pos` of a stream: the LAST BEGIN/END marker before `pos`, found
    by reading backwards (`read_back(lo, hi)` returns the bytes [lo, hi)), is a BEGIN. Exact for the block rule, whose
    match runs from a BEGIN to the first END or to the end of the text. Reads back until a marker or the start.

    Every view the markers are read in ENDS where no marker can be cut: a marker never spans a newline, so a view ends
    at `pos` or at a newline. `pos` must therefore be a LINE START (0, or just after a newline), else ValueError (research's
    stage 2 of round 5, S2-1: a log window starting inside a BEGIN line cut the marker in two, neither half a marker,
    and sent the key body). Going back, each chunk carries the previous view's partial first line with it, so a marker
    of any length that straddles a chunk edge is read whole (a fixed overlap missed a marker longer than itself: the
    marker's `(?:[A-Z0-9]+ )*` is unbounded). The bytes held are bounded by `chunk` plus the longest line read back."""
    if pos < 0 or (pos > 0 and read_back(pos - 1, pos) != b"\n"):
        raise ValueError("pem_open_before: pos must be a line start")
    hi, carry = pos, b""
    while hi > 0:
        lo = max(0, hi - chunk)
        raw = read_back(lo, hi) + carry                   # the bytes [lo, hi + len(carry)): one contiguous range
        view = _normalise(raw.decode("utf-8", "replace"))[0]
        last = None
        for m in PEM_MARKER.finditer(view):
            last = m.group(1)
        if last is not None:
            return last == "BEGIN"
        nl = raw.find(b"\n")
        carry = raw if nl < 0 else raw[:nl]               # the partial first line: a marker straddling `lo` ends in it
        hi = lo
    return False



def exact(value):
    """specs/0055 §4b and round 5's R5-06: the exact built-in `str` of a `str` subclass's data, else `value` unchanged.
    A subclass may format differently from its data (a standard `Enum(type=str)` member formats as its NAME), so the
    screen and every later consumer must use this one representation. `str.__str__` of a subclass instance is a new
    exact `str` holding its data, whatever the subclass's own `__str__`/`__format__` do."""
    return str.__str__(value) if isinstance(value, str) and type(value) is not str else value


def first_class(text: str) -> str | None:
    """The class of the first finding in `text`, or None. For identifier screens, which refuse rather than mask."""
    found = scan(text)
    return found[0].cls if found else None


class CredentialRefused(ValueError):
    """An identifier field carries a credential shape (§4b): the call is refused whole and nothing is written.

    `.reason` is always "credential_refused" (the served refusal's name), `.field` names the argument and `.cls`
    the class. The message names both and NEVER the value (§4g E1)."""

    reason = REFUSAL

    def __init__(self, field: str, cls: str):
        self.field = field
        self.cls = cls
        super().__init__(f"{REFUSAL}: {field} carries a {cls}")

    def as_refusal(self) -> dict:
        return {"ok": False, "refusal": REFUSAL, "field": self.field, "class": self.cls}


def merge_report(into: dict, field: str, report: dict) -> dict:
    """Fold one field's {class: count} into a result's `credentials_withheld` {field: {class: count}}."""
    if report:
        slot = into.setdefault(field, {})
        for cls, n in report.items():
            slot[cls] = slot.get(cls, 0) + n
    return into


# ---- the surface a call arrived through (§4g's audit `surface` field) -----------------------------------------------
_SURFACE: _contextvars.ContextVar[str] = _contextvars.ContextVar("veracium_credential_surface", default="library")


def current_surface() -> str:
    """"library", or the served surface ("mcp", "adapter") a call came through."""
    return _SURFACE.get()


@_contextlib.contextmanager
def on_surface(name: str):
    """Mark the calls made inside this block as arriving through `name` (the MCP tool boundary and the adapters'
    Binding set it); the audit events of §4g carry it."""
    token = _SURFACE.set(name)
    try:
        yield
    finally:
        _SURFACE.reset(token)


def audit_fields(op: str, field: str, *, source: str, classes: dict | None = None, cls: str | None = None) -> dict:
    """The content-free fields of one `credential_withheld` / `credential_refused` AuditLog line (§4g): the surface,
    the operation, the field, the class counts (or the refused class), the source and the rule set's version. Never
    the value, its length, offsets or a digest."""
    out = {"surface": current_surface(), "operation": op, "field": field, "source": source,
           "shapes_version": CREDENTIAL_SHAPES_VERSION}
    if classes is not None:
        out["classes"] = dict(classes)
    if cls is not None:
        out["class"] = cls
    return out


# ---- the read backstop (§4e): stored record text on its way to a model or a tool result ---------------------------
def mask_text(text):
    """mask(text)[0] for a str; anything else unchanged. The read backstop's one call: a stored value is masked
    before it is rendered, so a legacy credential never reaches a model or a tool result (I7)."""
    if isinstance(text, str) and text:
        return mask(text)[0]
    return text


def masked_edge(edge):
    """A copy of a stored edge whose text fields are masked, for rendering only; the edge itself when none carries a
    shape. Applied BEFORE any clamp, so a truncation can never cut a credential into a fragment the recogniser no
    longer names."""
    # a stored Edge (pydantic) carries `original_relation`; the as-of path's `Adapted` record (a frozen dataclass with
    # the same four text fields) does not, and is copied with dataclasses.replace. The copy names its fields literally,
    # so no other field (`confidence` above all, 0048's census) can be written through it.
    from pydantic import BaseModel
    subject, relation, obj, note = (mask_text(edge.subject), mask_text(edge.relation), mask_text(edge.object),
                                    mask_text(edge.note))
    unchanged = subject is edge.subject and relation is edge.relation and obj is edge.object and note is edge.note
    if isinstance(edge, BaseModel):
        original = mask_text(edge.original_relation)
        if unchanged and original is edge.original_relation:
            return edge
        return edge.model_copy(update={"subject": subject, "relation": relation, "object": obj, "note": note,
                                       "original_relation": original})
    if unchanged:
        return edge
    import dataclasses
    return dataclasses.replace(edge, subject=subject, relation=relation, object=obj, note=note)


def mask_deep(value):
    """The read backstop over a structured report (`why`'s biography, a tool result built from stored rows): every
    str leaf masked, and every str dict KEY (round 5, the carrier table: `outcome_counts` is `dict[str, int]`, so a
    legacy key is stored text, and `why` printed it); non-text values unchanged, containers rebuilt only when
    something changed. Two keys that mask alike stay two entries: the later one is numbered (` #2`, ...)."""
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, dict):
        out: dict = {}
        changed = False
        for k, v in value.items():
            nk = mask_text(k) if isinstance(k, str) else k
            if nk != k:
                changed = True
                base, n = nk, 2
                while nk in out or nk in value:
                    nk, n = f"{base} #{n}", n + 1
            nv = mask_deep(v)
            changed = changed or nv is not v
            out[nk] = nv
        return out if changed else value
    if isinstance(value, (list, tuple)):
        items = [mask_deep(v) for v in value]
        if all(a is b for a, b in zip(items, value)):
            return value
        return type(value)(items) if isinstance(value, list) else tuple(items)
    return value


# ---- §4g E1/E2: the outward formatter ------------------------------------------------------------------------------
class ArgumentRefused(ValueError):
    """A caller argument outside its closed vocabulary or contract. The library message (to the host that made the
    call) may name the value; `.field`, `.reason` and `.allowed` let a served boundary say what was wrong WITHOUT it
    (§4g E1: field, reason, and for a closed vocabulary the allowed values)."""

    def __init__(self, message: str, *, field: str, reason: str = "invalid_value", allowed=None):
        super().__init__(message)
        self.field = field
        self.reason = reason
        self.allowed = tuple(allowed) if allowed is not None else None


def _declared_field_names() -> frozenset:
    """Every field name (and alias) of the declared product models (`_declared_model_walk`)."""
    return _declared_model_walk()[1]


def _declared_titles() -> frozenset:
    """Round 6's R6-01: a Pydantic validation error's TITLE is printed by its formatting ("1 validation error for
    <title>"), and a title is whatever the constructor was given. A withheld defect keeps a title only when it is the
    class name of a declared product model (`_declared_model_walk`); any other title prints as `WITHHELD_TITLE`."""
    return frozenset(c.__name__ for c in _declared_model_walk()[0])


def _declared_model_walk() -> tuple:
    """`(models, names)`: every field name (and alias) a product Pydantic model declares: the product's record and receipt models, named
    here, and every model their fields' annotations reach. A validation location segment is printed only when it is
    one of these or a list index (round 4's S3); a model outside them prints every segment as `[key]`, the safe
    direction. tests/test_0055_r4_closure.py holds every product model's fields inside the result (a test may walk
    subclasses; the product reads no registry)."""
    import typing
    from pydantic import BaseModel
    from . import redaction as _redaction_mod
    from . import schema as _schema
    todo = [_schema.AgreementRecord, _schema.Confirmation, _schema.ConsolidationOp, _schema.ConsolidationOutputDraft,
            _schema.ContestedGroup, _schema.ContestedLinkage, _schema.ContributionDraft, _schema.ContributionRecord,
            _schema.CorrectionAuthorisation, _schema.Edge, _schema.Episode, _schema.OutcomeJudgmentDraft,
            _schema.Provenance, _schema.Relation, _schema.Reply, _schema.SupersessionPlan, _schema.SupersessionRefusal,
            _schema.SupersessionRefusalDraft, _schema.SupersessionResult, _redaction_mod.RedactionReceipt]
    names, seen = set(), set()
    while todo:
        cls = todo.pop()
        if cls in seen or cls is BaseModel:
            continue
        seen.add(cls)
        for fname, finfo in (cls.model_fields or {}).items():
            names.add(fname)
            for alias in (finfo.alias, finfo.validation_alias):
                if isinstance(alias, str):
                    names.add(alias)
            stack = [finfo.annotation]
            while stack:
                t = stack.pop()
                if isinstance(t, type) and issubclass(t, BaseModel):
                    todo.append(t)
                stack.extend(typing.get_args(t))
    return frozenset(seen - {BaseModel}), frozenset(names)


_DECLARED_CACHE: list = []


def path_segment(key) -> str:
    """§4g/I8's label rule for a path built from a record (round 5's R5-02): a declared field name or a list index is
    printed, any other key is `[key]` (a key is input: the import file's, or a stored mapping's). The import screen,
    the store guard and every refusal or report label built from a path take their segments from here."""
    if not _DECLARED_CACHE:
        _DECLARED_CACHE.append(_declared_field_names())
    return _loc_segment(key, _DECLARED_CACHE[0])


def _loc_segment(seg, declared) -> str:
    """§4g E1/E2 at a validation error's location (round 4's research S3): a location segment can be a DICT KEY from the
    input (`Edge.outcome_counts` is `dict[str, int]`, so `{"<key>": "x"}` reads `outcome_counts.<key>: int_parsing`).
    Only a list index or a declared field name is printed; any other segment is `[key]`."""
    if isinstance(seg, int) and not isinstance(seg, bool):
        return str(seg)
    if isinstance(seg, str) and seg in declared:
        return seg
    return "[key]"


def _pydantic_errors(exc):
    try:
        from pydantic import ValidationError
    except ImportError:                                  # pragma: no cover - pydantic is a hard dependency
        return None
    if not isinstance(exc, ValidationError):
        return None
    try:
        return exc.errors(include_url=False, include_context=False, include_input=False)
    except Exception:                                    # noqa: BLE001 - a formatter never raises
        return []


#: §4g E1 (round 6's R6-01, research's addition 2): the ONE closed set of refusal reasons an outward formatter prints.
#: An exception's `.reason` outside it prints as nothing (the fixed "refused" text), however it is spelled: a spelling
#: check establishes no membership. tests/test_0055_r6_closure.py censuses every reason the product's exceptions carry
#: (a class attribute, or a constructor's argument at every raise) against this set, both ways.
DECLARED_REASONS = frozenset({
    # ArgumentRefused / ArgumentTypeRefused (the default, and each raise's literal)
    "invalid_value", "future_date", "not_accepted", "not_an_iso_date", "not_a_string",
    # class-level reasons: CredentialRefused, CredentialImportRefused, SourceIdRequired, CorrectionOfUnclassified
    REFUSAL, "source_id_required", "correction_of_unclassified",
    # trust_tools.REFUSALS (TrustRefused refuses any other reason at construction)
    "attempted_elevation", "correction_refused", "erasure_disabled", "invalid_target", "not_found_in_scope",
    "out_of_scope", "preview_expired", "preview_unknown", "principal_scoped", "principal_ungroupable",
    "reason_too_long", "refused", "scope_unconfigured", "source_out_of_scope", "source_unbound", "store_changed",
    # procedures: ProcedureValueError / ProcedureTypeError
    "basis_required", "correction_of_procedure", "relation_not_procedural", "summary_empty", "summary_too_long",
    "when_beyond_skew", "when_naive", "when_not_datetime", "author_not_evidence_author",
    "context_not_evidence_context", "relation_not_str", "summary_not_str", "user_id_invalid", "note_not_str",
    "evidence_ref_not_str", "source_id_not_str",
    # store/base.UNDO_REFUSAL_REASONS (UndoRefused) and REPLY_REFUSAL_REASONS (ReplyRefused): closed at construction
    "no-outcome", "not-restored", "testimony", "not-applicable", "edge-unavailable", "ambiguous-outcome",
    "kind", "actor", "shape", "marker", "unknown-edge", "redacted-edge", "procedural-edge", "resolve-target",
    "resolve-repeat",
    # store/release_migration._MINT_REASONS (MintError): closed at construction
    "source-missing", "source-unaccepted", "source-changed",
    # store/schema_version.REASONS (StoreVersionError): closed at construction
    "invalid-version", "newer", "foreign-shape", "stamped-shape-mismatch", "adoption-refused", "locked",
    "unsupported-sqlite", "migration-required", "unsupported-migration",
})

#: Round 6's R6-01: the content-free stand-ins a withheld display prints in place of a carrier outside its closed set.
WITHHELD_TITLE = "withheld"
WITHHELD_ERROR_TYPE = "invalid"
WITHHELD_ERROR_MESSAGE = "invalid value (its message is withheld: it may carry the input)"
_WITHHELD_SUFFIX = ": its message is withheld from this stream (specs/0055 §4g E1)"
_WITHHELD_MSG = re.compile(r"[A-Za-z_][A-Za-z0-9_]*" + re.escape(_WITHHELD_SUFFIX))
_TYPE_PREFIX = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.(?:<locals>|[A-Za-z_][A-Za-z0-9_]*))*")

#: §4g E1, the display-carrier table (round 6's R6-01, research's addition 1): every place a formatted exception
#: carries text, derived from what RENDERS it, not from the carriers a review found. tests/test_0055_r6_closure.py
#: holds each namespace equal to its renderer's own fields (`traceback.TracebackException`'s, Pydantic's error keys, the
#: built-in types' formatted attributes), so a field the renderer gains fails there until it has a row. Each row says
#: how a withheld CLI defect and `outward_text` treat it.
DISPLAY_CARRIERS = {
    # traceback.TracebackException's fields
    "traceback:_str": "str(exc): the args are replaced by the fixed withheld message; the display must then render as exactly "
            "that one line, else the object is replaced",
    "traceback:__notes__": "dropped on the final object (`_settled`)",
    "traceback:__cause__": "cleared on the final object (`_settled`)",
    "traceback:__context__": "not displayed: clearing the cause on the final object (`_settled`) suppresses it, and the "
                             "root is also raised `from None`",
    "traceback:__suppress_context__": "set by `_settled` (assigning the cause sets it); the final check requires it on "
                                      "a group",
    "traceback:exceptions": "a group's children: rebuilt one by one under this whole rule into a BUILT-IN group (never the "
                  "subclass, its `derive` or its `__str__`), else the group is replaced by a content-free defect",
    "traceback:exc_type_qualname": "the class name: a program identifier, printed (out of scope, as the frames' source lines "
                         "are: an input-derived class name is not a supported carrier)",
    "traceback:exc_type_module": "the class's module: a program identifier, printed (out of scope, as above)",
    "traceback:stack": "the frames: the program's own source lines, outside the contract (round 5's answer 4)",
    "traceback:filename": "a SyntaxError's field: never raised as itself (replaced)",
    "traceback:lineno": "a SyntaxError's field: never raised as itself (replaced)",
    "traceback:end_lineno": "a SyntaxError's field: never raised as itself (replaced)",
    "traceback:offset": "a SyntaxError's field: never raised as itself (replaced)",
    "traceback:end_offset": "a SyntaxError's field: never raised as itself (replaced)",
    "traceback:text": "a SyntaxError's field: never raised as itself (replaced)",
    "traceback:msg": "a SyntaxError's field: never raised as itself (replaced)",
    "traceback:_exc_metadata": "a SyntaxError's field: never raised as itself (replaced)",
    "traceback:_exc_type": "the type object itself: no text of its own",
    "traceback:_have_exc_type": "a flag: no text",
    "traceback:_is_syntax_error": "a flag: no text",
    "traceback:max_group_width": "a renderer setting: no text",
    "traceback:max_group_depth": "a renderer setting: no text",
    # Pydantic ValidationError's rendering
    "pydantic:title": "printed only when it is a declared product model's class name, else `WITHHELD_TITLE`",
    "pydantic.error:type": "an error's type: printed only when it is one of Pydantic's own error types or `WITHHELD_ERROR_TYPE`, "
            "else `WITHHELD_ERROR_TYPE` (outward_text too)",
    "pydantic.error:loc": "an error's location: each segment a declared field name or a list index, else `[key]`",
    "pydantic.error:msg": "an error's message: replaced by `WITHHELD_ERROR_MESSAGE`",
    "pydantic.error:input": "an error's input: hidden (`hide_input=True`), and `None` in the rebuilt error",
    "pydantic.error:ctx": "an error's context: never copied into the rebuilt error",
    "pydantic.error:url": "the documentation URL, which embeds the error type: the rebuilt errors are custom errors, which carry none",
    # a built-in type's own __str__ (they print these fields, not only args)
    "builtin:errno": "OSError: printed by its str() only with strerror; the args are replaced, so the render check decides",
    "builtin:strerror": "OSError: as errno",
    "builtin:filename2": "OSError: as errno",
    "builtin:encoding": "UnicodeError: its str() formats its fields; the render check refuses it and it is replaced",
    "builtin:object": "UnicodeError: as encoding",
    "builtin:start": "UnicodeError: as encoding",
    "builtin:end": "UnicodeError: as encoding",
    "builtin:reason": "UnicodeError: as encoding",
    "builtin:filename": "OSError: as errno",
    "builtin:name": "AttributeError, NameError, ImportError: the renderer's \"Did you mean\" suggestion reads it; the "
                    "render check refuses the extra text and the replacement carries none",
    "builtin:obj": "AttributeError: as name",
    "builtin:msg": "ImportError: its str() prints its `msg` attribute, not its args; the render check refuses it and it "
                   "is replaced",
    "builtin:name_from": "ImportError: as msg",
    "builtin:path": "ImportError: as msg",
    "builtin:key_repr": "KeyError: its str() is its argument's repr, the withheld message's repr",
    # outward_text's own fields
    "outward_text:reason": "any exception's `.reason`: printed only when it is in `DECLARED_REASONS`",
    "outward_text:field": "ArgumentRefused.field: printed only when it is a declared argument or field name, else `[argument]`",
    "outward_text:allowed": "ArgumentRefused.allowed: built only from module constants at every raise (the R6 census)",
    "outward_text:class_name": "type(exc).__name__ at outward_text: a program identifier (out of scope, as above)",
}


def withheld_defect(exc: BaseException) -> BaseException:
    """§4g E1 at the CLI for a DEFECT (round 4's R4-05, research's S3, round 6's R6-01): the exception to raise in place
    of `exc`. It still fails loudly as a crash and is never turned into a clean refusal, but nothing its display shows
    may come from the input; `DISPLAY_CARRIERS` is the table of what a display shows and how each carrier is treated.
      - an exception GROUP is rebuilt as a built-in group of its children, each withheld under this whole rule
        (recursively), else replaced by a content-free `RuntimeError`;
      - an exception whose display, once its message is replaced and its notes, cause and context are cleared, RENDERS
        as exactly one line, its type and that message, is raised AS ITSELF (its type, attributes and traceback);
      - a Pydantic `ValidationError` is REBUILT over closed values only: a declared title, each error's type when it
        is one of Pydantic's own, each location reduced as `outward_text` reduces it, each message withheld, the input
        hidden;
      - any other exception is replaced by a fresh instance of its own class built from the message alone when that
        renders safely, else by a `RuntimeError` naming its class.
    Every result passes `_display_safe` on the FINAL object, after construction. The caller raises it `from None`,
    with the original frames (`with_traceback`)."""
    return _withheld(exc, 0)


_GROUP_DEPTH = 64


def _withheld(exc: BaseException, depth: int) -> BaseException:
    msg = f"{type(exc).__name__}{_WITHHELD_SUFFIX}"
    if isinstance(exc, BaseExceptionGroup):
        try:
            if depth >= _GROUP_DEPTH:
                raise RecursionError("an exception group nested too deep to rebuild")
            children = [_withheld(c, depth + 1) for c in exc.exceptions]
            fresh = _settled(BaseExceptionGroup(msg, children))   # the built-in: never the subclass or its derive
            if _display_safe(fresh):
                return fresh.with_traceback(exc.__traceback__)
        except Exception:                                # noqa: BLE001 - fall through to the content-free defect
            pass
        return _settled(RuntimeError(msg)).with_traceback(exc.__traceback__)
    try:
        exc.args = (msg,)
        _settled(exc)                                    # notes may quote the input (research's S3); so may a cause
        if _formats_as(exc, msg):
            return exc
    except Exception:                                    # noqa: BLE001 - fall through to a replacement
        pass
    errs = _pydantic_errors(exc)
    if errs is not None:
        from pydantic import ValidationError
        from pydantic_core import PydanticCustomError
        declared = _declared_field_names()
        titles, types = _declared_titles(), _declared_error_types()
        try:
            title = exc.title if isinstance(exc.title, str) and exc.title in titles else WITHHELD_TITLE
            fresh = ValidationError.from_exception_data(
                title, [{"type": PydanticCustomError(_closed_type(e.get("type"), types), WITHHELD_ERROR_MESSAGE),
                         "loc": tuple(_loc_segment(x, declared) for x in (e.get("loc") or ())), "input": None}
                        for e in errs] or [{"type": PydanticCustomError(WITHHELD_ERROR_TYPE, WITHHELD_ERROR_MESSAGE),
                                            "loc": (), "input": None}],
                hide_input=True)
            _settled(fresh)
            if _display_safe(fresh):
                return fresh.with_traceback(exc.__traceback__)
        except Exception:                                # noqa: BLE001 - fall through
            pass
    try:
        fresh = _settled(type(exc)(msg))
        if not _display_safe(fresh):
            fresh = _settled(RuntimeError(msg))
    except Exception:                                    # noqa: BLE001 - a class whose constructor wants more
        fresh = _settled(RuntimeError(msg))
    return fresh.with_traceback(exc.__traceback__)


def _settled(exc: BaseException) -> BaseException:
    """Round 5's R5-05: a replacement is constructed, and a constructor can add notes (or set a cause) again, so the
    notes are dropped and the cause cleared on the FINAL object, after construction; `_display_safe` then judges that
    object. Assigning the cause, even `None`, also sets `__suppress_context__` (Python's own rule), so the context is no
    longer displayed either: that holds for a group's children too, which are never raised `from None` (round 6's
    R6-01; the root is also raised `from None`)."""
    try:
        del exc.__notes__
    except AttributeError:
        pass
    exc.__cause__ = None
    return exc


def _formats_as(exc: BaseException, msg: str) -> bool:
    """Whether the traceback module RENDERS `exc` itself as exactly one line, its type and `msg` (or, for a KeyError,
    `msg`'s repr), with nothing else (round 6's R6-01: judged on the rendering, not on `str()` plus notes, so notes,
    a group's children, a cause or context, a syntax error's source fields and a type's own formatted attributes all
    show up as extra or different text and refuse). The frames' source lines are the program's own and outside this
    judgement (round 5's answer 4): the rendering is taken without them."""
    import traceback
    try:
        lines = traceback.format_exception(type(exc), exc, None)
    except Exception:                                    # noqa: BLE001 - an unrenderable exception is not safe
        return False
    if len(lines) != 1:
        return False
    line = lines[0]
    for shown in (msg, repr(msg)):
        tail = f": {shown}\n"
        if line.endswith(tail) and _TYPE_PREFIX.fullmatch(line[: -len(tail)]):
            return True
    return False


def _display_safe(exc: BaseException) -> bool:
    """The FINAL check (round 6's R6-01), on the object a withheld defect returns: every carrier `DISPLAY_CARRIERS`
    lists holds a closed value. A group: a BUILT-IN group whose message is a withheld message, with no notes, cause or
    context, and every child safe under this same check. A validation error: a declared title, closed error types,
    declared locations, withheld messages, no input. Anything else: it renders as its withheld message alone."""
    try:
        if isinstance(exc, BaseExceptionGroup):
            if type(exc) not in (ExceptionGroup, BaseExceptionGroup) or not _WITHHELD_MSG.fullmatch(exc.message):
                return False
            # its context is displayed unless suppressed: `_settled` suppresses it (clearing the cause), and the root is
            # also raised `from None`
            if getattr(exc, "__notes__", None) or exc.__cause__ is not None or not exc.__suppress_context__:
                return False
            n = len(exc.exceptions)
            if str(exc) != f"{exc.message} ({n} sub-exception{'s' if n > 1 else ''})":
                return False
            return all(_display_safe(c) for c in exc.exceptions)
        errs = _pydantic_errors(exc)
        if errs is not None:
            if exc.title not in _declared_titles() and exc.title != WITHHELD_TITLE:
                return False
            types, declared = _declared_error_types(), _declared_field_names()
            full = exc.errors(include_url=True, include_context=True, include_input=True)
            return all(e.get("type") in types and e.get("msg") == WITHHELD_ERROR_MESSAGE and e.get("input") is None
                       and not e.get("ctx") and not e.get("url")
                       and all(isinstance(x, int) or x in declared or x == "[key]" for x in e.get("loc") or ())
                       for e in full) and len(full) == len(errs)
        return (len(exc.args) == 1 and isinstance(exc.args[0], str) and _WITHHELD_MSG.fullmatch(exc.args[0]) is not None
                and _formats_as(exc, exc.args[0]))
    except Exception:                                    # noqa: BLE001 - a check that cannot run is not a pass
        return False


def _declared_error_types() -> frozenset:
    """Pydantic's own closed error vocabulary (`pydantic_core.core_schema.ErrorType`) and `WITHHELD_ERROR_TYPE`. The
    product raises no custom error code of its own (the R6 census); a custom code is input as far as a display can
    tell (round 6's R6-01), and prints as `WITHHELD_ERROR_TYPE`."""
    import typing
    from pydantic_core.core_schema import ErrorType
    return frozenset(typing.get_args(ErrorType)) | {WITHHELD_ERROR_TYPE}


def _closed_type(code, types: frozenset) -> str:
    return code if isinstance(code, str) and code in types else WITHHELD_ERROR_TYPE


#: Round 6's R6-01: the argument names a refusal may name that are not declared model fields. Every `field` the product
#: raises is a literal at its site; tests/test_0055_r6_closure.py censuses each against `_declared_argument_names`.
ARGUMENT_NAMES = frozenset({"corrected_value", "event_text", "event_type"})


def _declared_argument_names() -> frozenset:
    """The names an `ArgumentRefused.field` may print (round 6's R6-01): every declared model field name and
    `ARGUMENT_NAMES`. Any other field prints as `[argument]`."""
    return _declared_field_names() | ARGUMENT_NAMES


def outward_text(exc: BaseException) -> str:
    """§4g E1, ONE outward formatter: the text an error carries when it leaves the library toward a model, a tool
    result, a CLI stream or the diagnostics log. It names the field and the reason, and for a closed vocabulary the
    allowed values; it NEVER names the caller's value, so it is never built from `str(exc)` of an exception that may
    echo one. A pydantic validation error is reduced to its locations and error types (E2)."""
    if isinstance(exc, CredentialRefused):
        return str(exc)                                  # content-free by construction
    errs = _pydantic_errors(exc)
    if errs is not None:
        parts = []
        declared = _declared_field_names()
        types = _declared_error_types()
        for e in errs[:8]:
            loc = ".".join(_loc_segment(x, declared) for x in (e.get("loc") or ())) or "argument"
            parts.append(f"{loc}: {_closed_type(e.get('type'), types)}")   # round 6's R6-01: a custom code is input
        return "invalid arguments (" + "; ".join(parts) + ")" if parts else "invalid arguments"
    name = type(exc).__name__
    field = exc.field if isinstance(exc, ArgumentRefused) else None
    reason = exc.reason if isinstance(exc, ArgumentRefused) else None
    allowed = exc.allowed if isinstance(exc, ArgumentRefused) else None
    if reason is None:
        reason = getattr(exc, "reason", None)
    # round 6's R6-01: a reason prints only as a member of the ONE declared set, a field only as a declared name; a
    # spelling check established no membership
    reason = reason if isinstance(reason, str) and reason in DECLARED_REASONS else None
    if field is not None and not (isinstance(field, str) and field in _declared_argument_names()):
        field = "[argument]"
    out = name
    if field:
        out += f": {field}"
    out += f" ({reason})" if reason else ": refused (its message is withheld from this surface: it may carry the input)"
    if allowed:
        out += f"; allowed: {list(allowed)}"
    return out


class ArgumentTypeRefused(ArgumentRefused, TypeError):
    """§4b's type refusal (round 4's R4-01): a screened argument that is neither `None` nor a `str`. It is an
    `ArgumentRefused` (`.field`, `.reason == "not_a_string"`; a served boundary formats it without the value) AND a
    `TypeError`, so the type contracts that predate the screen hold: 0037's `record_procedure` refuses a non-`str`
    argument with a `TypeError`."""
