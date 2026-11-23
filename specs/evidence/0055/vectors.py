"""Adversarial table for the credential-shape filter. Every STRUCTURAL token (vendor key, PEM block, JWT, URL with a
password, preview token) is ASSEMBLED at run time from parts, so none appears literally in this file, the spec, or a
commit (a push must not trip a secret scanner, and a real-looking token in our own repo would be the defect this spec
exists to prevent). The LABELLED rows are literal on purpose: well-known dummy values (hunter2, swordfish, made-up
PINs) that the table needs as written. Corrected 2026-11-22 (v0.3.2): this docstring said no literal credential
appeared at all; dev's pre-seal scan with credential_shapes.scan found the labelled rows, which is what it should find.

Each row: (id, group, text, expect) where expect is a set of classes that MUST be reported, or set() for a
near-miss that MUST be stored unchanged. Group "limit" rows are evasions the filter does NOT catch by design;
their expect is set() and the table records that as a stated limit, not a pass.
"""
import hashlib
import random
import uuid

_r = random.Random(20261122)


def rnd(n, alphabet):
    return "".join(_r.choice(alphabet) for _ in range(n))


UP = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LO = "abcdefghijklmnopqrstuvwxyz"
DI = "0123456789"
B62 = UP + LO + DI
HEX = "0123456789abcdef"

AWS_ID = "AK" + "IA" + "IOSFODNN7" + "EXAMPLE"            # AWS's documented example key id
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/" + "bPxRfiCYEXAMPLEKEY"  # AWS's documented example secret
GH = "gh" + "p_" + rnd(36, B62)
GH_FINE = "github" + "_pat_" + rnd(22, B62) + "_" + rnd(59, B62)
GL = "gl" + "pat-" + rnd(20, B62)
SLACK = "xo" + "xb-" + rnd(12, DI) + "-" + rnd(13, DI) + "-" + rnd(24, B62)
SLACK_HOOK = "https://hooks.slack.com/services/" + "T" + rnd(10, UP + DI) + "/B" + rnd(10, UP + DI) + "/" + rnd(24, B62)
STRIPE = "sk" + "_live_" + rnd(24, B62)
ANTH = "sk-" + "ant-api03-" + rnd(80, B62 + "_-")
OPENAI = "sk-" + "proj-" + rnd(48, B62 + "_-")
GOOG = "AI" + "za" + rnd(35, B62 + "_-")
HF = "hf" + "_" + rnd(34, B62)
NPM = "np" + "m_" + rnd(36, B62)
SG = "S" + "G." + rnd(22, B62) + "." + rnd(43, B62)
JWT = "ey" + "J" + rnd(20, B62) + ".ey" + "J" + rnd(40, B62) + "." + rnd(43, B62 + "_-")
PEM = ("-----BEGIN " + "RSA PRIVATE" + " KEY-----\n" + "\n".join(rnd(64, B62 + "+/") for _ in range(3))
       + "\n-----END " + "RSA PRIVATE" + " KEY-----")
PEM_OPENSSH = ("-----BEGIN " + "OPENSSH PRIVATE" + " KEY-----\n" + rnd(70, B62 + "+/") + "\n-----END " + "OPENSSH PRIVATE" + " KEY-----")
PEM_TRUNC = "-----BEGIN " + "PRIVATE" + " KEY-----\n" + rnd(64, B62 + "+/")
PW = "Tr0ub4dor&3-" + "probe"
DBURL = "postgres://" + "app" + ":" + "s3cr3t" + "Pw" + "@db.internal:5432/prod"

SHA1 = hashlib.sha1(b"a").hexdigest()
SHA256 = hashlib.sha256(b"a").hexdigest()
SHA16 = SHA256[:16]
UUID4 = str(uuid.UUID(int=_r.getrandbits(128), version=4))
B64_DIGEST = __import__("base64").b64encode(hashlib.sha256(b"a").digest()).decode()

ZW = "​"

def _curly(depth):
    """Round 2's R2-01 construction (the reviewer's probe): nested labelled values in curly double quotes. No token."""
    s = "password: \u201c" + "z " * 85 + "end\u201d"
    for _ in range(depth):
        s = "password: \u201c" + "a " * 35 + s + " tail\u201d"
    return s


ROWS = [
    # --- the witness: research's adoption probe 1, one message, three credentials and one ordinary fact
    ("W1", "witness", f"My AWS key is {AWS_ID}, the staging database password is {PW}, and my GitHub token is {GH}. I deploy every Friday.",
     {"aws_access_key_id", "labelled_password", "github_token"}),
    # --- structural
    ("S1", "structural", f"aws_access_key_id = {AWS_ID}", {"aws_access_key_id"}),
    ("S2", "structural", f"export AWS_SECRET_ACCESS_KEY={AWS_SECRET}", {"labelled_password"}),
    ("S3", "structural", f"use {GH} for the CI bot", {"github_token"}),
    ("S4", "structural", f"fine-grained: {GH_FINE}", {"github_token"}),
    ("S5", "structural", f"gitlab {GL}", {"gitlab_token"}),
    ("S6", "structural", f"bot token {SLACK}", {"slack_token"}),
    ("S7", "structural", f"post alerts to {SLACK_HOOK}", {"slack_webhook"}),
    ("S8", "structural", f"stripe {STRIPE}", {"stripe_key"}),
    ("S9", "structural", f"claude key {ANTH}", {"anthropic_key"}),
    ("S10", "structural", f"openai {OPENAI}", {"openai_key"}),
    ("S11", "structural", f"maps key {GOOG}", {"google_api_key"}),
    ("S12", "structural", f"hf {HF}", {"huggingface_token"}),
    ("S13", "structural", f"npm {NPM}", {"npm_token"}),
    ("S14", "structural", f"sendgrid {SG}", {"sendgrid_key"}),
    ("S15", "structural", f"session cookie {JWT}", {"jwt"}),
    ("S16", "structural", f"deploy key:\n{PEM}\nthanks", {"private_key_block"}),
    ("S17", "structural", f"{PEM_OPENSSH}", {"private_key_block"}),
    ("S18", "structural", f"pasted half a key: {PEM_TRUNC}", {"private_key_block"}),
    ("S19", "structural", f"the app connects with {DBURL}", {"url_userinfo_password"}),
    ("S20", "structural", f"curl -H 'Authorization: Bearer {rnd(32, B62)}' https://api.example.com", {"auth_header"}),
    # --- labelled
    ("L1", "labelled", "my password is hunter2", {"labelled_password"}),
    ("L2", "labelled", "My password is swordfish.", {"labelled_password"}),
    ("L3", "labelled", 'wifi password: "correcthorsebatterystaple"', {"labelled_password"}),
    ("L4", "labelled", "passphrase = 'blue-otter-lamp-91'", {"labelled_password"}),
    ("L5", "labelled", "API key: 3f9Kq7LmZp2Xv8RtYb4N", {"labelled_password"}),
    ("L6", "labelled", "client_secret=Zq8-rT2_mK9vL4xP", {"labelled_password"}),
    ("L7", "labelled", "PIN: 4821", {"labelled_pin"}),
    ("L8", "labelled", "the token is Ab3dEf9hJk2L", {"labelled_secret"}),
    ("L9", "labelled", "contraseña: Gato!2024", {"labelled_password"}),
    ("L10", "labelled", "mot de passe : Soleil2024", {"labelled_password"}),
    ("L11", "labelled", "Passwort: Sommer2024", {"labelled_password"}),
    ("L12", "labelled", "password：Tr0ub4dor9", {"labelled_password"}),  # fullwidth colon
    ("L13", "labelled", "PASSWORD=Hunter2Hunter2", {"labelled_password"}),
    # --- normalisation adversaries
    ("N1", "normalisation", f"key {AWS_ID[:6]}{ZW}{AWS_ID[6:]}", {"aws_access_key_id"}),
    ("N2", "normalisation", "pass" + ZW + "word is Hunter22", {"labelled_password"}),
    ("N3", "normalisation", "ＡＫＩＡ" + AWS_ID[4:], {"aws_access_key_id"}),  # fullwidth AKIA
    ("N4", "normalisation", f"({GH})", {"github_token"}),
    ("N5", "normalisation", f"`{STRIPE}`", {"stripe_key"}),
    # --- near-misses that MUST be stored unchanged
    ("K1", "near-miss", f"fixed in commit {SHA1}", set()),
    ("K2", "near-miss", f"the digest is sha256:{SHA256}", set()),
    ("K3", "near-miss", f"sha16 {SHA16} matched", set()),
    ("K4", "near-miss", f"request id {UUID4}", set()),
    ("K5", "near-miss", f"base64 digest {B64_DIGEST}", set()),
    ("K6", "near-miss", "my password is expired", set()),
    ("K7", "near-miss", "the password is in 1Password", set()),
    ("K8", "near-miss", "I reset my password on Tuesday", set()),
    ("K9", "near-miss", "the secret is to use butter", set()),
    ("K10", "near-miss", "the secret is cumin", set()),
    ("K11", "near-miss", "the key is practice", set()),
    ("K12", "near-miss", "boarding pass: AB12CD", set()),
    ("K13", "near-miss", "export AWS_SECRET_ACCESS_KEY=$AWS_SECRET", set()),
    ("K14", "near-miss", "password: ********", set()),
    ("K15", "near-miss", "password=<redacted>", set()),
    ("K16", "near-miss", "clone https://github.com/org/repo.git", set()),
    ("K17", "near-miss", "ssh git@github.com:org/repo.git", set()),
    ("K18", "near-miss", "-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQ\n-----END PUBLIC KEY-----", set()),
    ("K19", "near-miss", "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB9x user@host", set()),
    ("K20", "near-miss", "arn:aws:iam::123456789012:user/deploy", set()),
    ("K21", "near-miss", "I use scikit-learn and sk-image", set()),
    ("K22", "near-miss", "the token is valid until Friday", set()),
    ("K23", "near-miss", "My PIN is the same as before", set()),
    ("K24", "near-miss", "http://localhost:8080/health", set()),
    ("K25", "near-miss", "email me at ana@example.com", set()),
    ("K26", "near-miss", "version 0.18.1, build 20261122", set()),
    ("K27", "near-miss", "The password policy requires 12 characters", set()),
    ("K28", "near-miss", "AKIA is the prefix AWS uses for access key ids", set()),
    ("K29", "near-miss", "edge e-f10b9ffaccd2 came from episode ep-38b383a2afdd", set()),
    ("K30", "near-miss", "evidence ev-5f7fd238ff9a, store 2d692894-7ee1-47ea-86a9-d708ea4705e0", set()),
    ("K31", "near-miss", "uuid hex 06dd6c7f815f475aa7e83bcc26262aa0", set()),
    ("K32", "near-miss", "source digest 2a50546560b1d8fcf4b495bf71084bb32d8c3dd876c5e18681c8cbc69c3d3f5e", set()),
    ("K33", "near-miss", "the token is valid for 7 days", set()),
    ("K34", "near-miss", "secret: none", set()),
    ("S21", "structural", "confirm with tt1." + "eyJ" + rnd(60, B62) + "." + rnd(43, B62 + "_-"), {"veracium_preview_token"}),
    ("L14", "labelled", "my bank pin is 7351", {"labelled_pin"}),
    ("L15", "labelled", "card PIN code: 0042", {"labelled_pin"}),
    ("K35", "near-miss", "fresh-clone capture at the pin: 7351 passed, 12 skipped", set()),
    ("L16", "labelled", 'the wifi password is "correct horse battery staple" for guests', {"labelled_password"}),
    ("L17", "labelled", "passphrase: 'violet lamp otter 7' (case matters)", {"labelled_password"}),
    ("L18", "labelled", "db password: Kx9f;Qz7!mR2 (rotate monthly)", {"labelled_password"}),
    ("K36", "near-miss", "    token = m.group(0).lower()", set()),
    ("K37", "near-miss", "    password = get_password(user)", set()),
    ("K38", "near-miss", 'SECRET = "Mo flies a Beechcraft Baron"', set()),
    # --- composition (round 1's R1-04): masking a structural token shortens an enclosing quoted value; around the
    # 200-character bound the enclosing label must then be withheld too, and the completed output must be inert
    ("C1", "composition", 'password: "' + "a " * 75 + GH + ' end"', {"github_token"}),
    ("C2", "composition", 'password: "' + "a " * 76 + GH + ' end"', {"github_token"}),
    ("C3", "composition", 'password: "' + "a " * 77 + GH + ' end"', {"github_token"}),
    ("C4", "composition", 'password: "' + "a " * 78 + GH + ' end"', {"github_token"}),
    ("C5", "composition", 'password: "' + "a " * 79 + GH + ' end"', {"labelled_password"}),   # two passes: the token's placeholder is swallowed by the enclosing value's (v0.5 count semantics, below)
    ("C6", "composition", 'password: "' + "a " * 80 + GH + ' end"', {"labelled_password"}),   # two passes: the token's placeholder is swallowed by the enclosing value's (v0.5 count semantics, below)
    ("C7", "composition", 'password: "' + "a " * 81 + GH + ' end"', {"github_token"}),
    ("C8", "composition", 'password: "' + "a " * 82 + GH + ' end"', {"github_token"}),
    ("C9", "composition", 'password: "' + "a " * 83 + GH + ' end"', {"github_token"}),
    ("C10", "composition", 'password: "' + "a " * 84 + GH + ' end"', {"github_token"}),
    ("C11", "composition", 'password: "' + "a " * 85 + GH + ' end"', {"github_token"}),
    ("C12", "composition", "token: " + GH, {"github_token"}),
    ("C13", "composition", 'api key: "' + AWS_ID + '"', {"aws_access_key_id"}),
    ("C14", "composition", 'password: "' + "b " * 70 + "secret: 'Ab3dEf9hJk2L' " + "c " * 20 + '"', {"labelled_secret"}),   # the placeholder (38) is LONGER than the value (14): the outer value grows, stays over the bound, and only the inner secret is withheld
    ("C15", "composition", "PIN: 4821 and token: " + STRIPE + " and password is " + PW, {"labelled_pin", "stripe_key", "labelled_password"}),
    # --- v0.5 (round 2's R2-01, R2-03): multi-span and multi-pass controls with EXACT expected counts (EXPECTED_REPORT),
    # and the reviewer's curly-quote depth family: depth 3 completes in four passes; depth 4 falls back, the whole value
    # withheld as one placeholder
    ("C16", "composition", 'password: "' + "a " * 79 + GH + ' end" and token: ' + STRIPE, {"labelled_password", "stripe_key"}),
    ("C17", "composition", "token: " + GH + " then token: " + GH_FINE + " then PIN: 4821", {"github_token", "labelled_pin"}),   # two github_token spans: a count of 2
    ("D3", "composition", _curly(3), {"labelled_password"}),
    ("D4", "composition", _curly(4), {"unmaskable_text"}),
    # --- structured configuration (v0.4, round 1's answer to Q2): JSON and dict keys, prefixed env vars, XML
    ("L19", "labelled", '{"password": "Tr0ub4dor9x", "user": "app"}', {"labelled_password"}),
    ("L20", "labelled", "{'api_key': 'Zq8rT2mK9vL4xP7q'}", {"labelled_password"}),
    ("L21", "labelled", "DB_PASSWORD=Tr0ub4dor9x", {"labelled_password"}),
    ("L22", "labelled", "<password>Tr0ub4dor9x</password>", {"labelled_password"}),
    ("L23", "labelled", '{"token": "Ab3dEf9hJk2L"}', {"labelled_secret"}),
    ("K39", "near-miss", "reset_password: true", set()),
    ("K40", "near-miss", '{"password_policy": "strict"}', set()),
    ("K41", "near-miss", "my_password_hint: blue", set()),
    ("K42", "near-miss", "password > twelve chars", set()),
    ("K44", "near-miss", "read ('/etc/passwd' IS '/etc/passwd') before the copy", set()),
    ("K45", "near-miss", '{"pin": "2040a7893658fbc8069e99f1f9dda9d10e225532"}', set()),
    ("K46", "near-miss", "Source pin: `2040a7893658fbc8069e99f1f9dda9d10e225532`.", set()),
    ("K47", "near-miss", '"source_pin": "2040a7893658fbc8069e99f1f9dda9d10e225532",', set()),
    ("K43", "near-miss", '{"password": null, "token": false}', set()),
    # --- stated limits: NOT caught, by design (expect set(), recorded as limits)
    ("X1", "limit", "my password is the name of my first dog", set()),
    ("X2", "limit", "A K I A I O S F O D N N 7 E X A M P L E", set()),
    ("X3", "limit", "key (base64): " + __import__("base64").b64encode(AWS_ID.encode()).decode(), set()),
    ("X4", "limit", "the password is hunter2 spelled backwards: 2retnuh".replace("hunter2 ", "the word "), set()),
    ("X6", "limit", "my password is correct horse battery staple", set()),
    ("X5", "limit", "use " + rnd(40, B62) + " for the staging box", set()),  # unlabelled, unprefixed random secret
]

# Every secret value the positive rows carry; the runner asserts none survives masking (substring, after
# removing invisible characters), which is the property, not merely that a class was reported.
SECRET_VALUES = [AWS_ID, AWS_SECRET, GH, GH_FINE, GL, SLACK, SLACK_HOOK, STRIPE, ANTH, OPENAI, GOOG, HF, NPM, SG, JWT,
                 PW, "s3cr3tPw", "hunter2", "swordfish", "correcthorsebatterystaple", "blue-otter-lamp-91",
                 "3f9Kq7LmZp2Xv8RtYb4N", "Zq8-rT2_mK9vL4xP", "4821", "Ab3dEf9hJk2L", "Gato!2024", "Soleil2024",
                 "Sommer2024", "Tr0ub4dor9", "Hunter2Hunter2", "Hunter22", "7351", "0042", "correct horse battery staple", "violet lamp otter 7", "Qz7!mR2", "Tr0ub4dor9x", "Zq8rT2mK9vL4xP7q"] + PEM.split("\n")[1:-1] + PEM_TRUNC.split("\n")[1:]

# v0.5 (round 2's R2-03): the EXACT report each row must produce, written from the row's text, not from the
# implementation. The count semantics: a report counts the placeholders mask() wrote that are in its FINAL output, by
# class. A span swallowed by a later pass is not counted (C5, C6, C16, D3), spans merged into one are one placeholder
# under the merged span's class, and a fallback is {"unmaskable_text": 1}. Every positive row not listed here holds
# exactly one withheld span, so its exact report is {its one class: 1}; every near-miss and limit row's is {}.
EXPECTED_REPORT = {
    "W1": {"aws_access_key_id": 1, "labelled_password": 1, "github_token": 1},
    "C15": {"labelled_pin": 1, "stripe_key": 1, "labelled_password": 1},
    "C16": {"labelled_password": 1, "stripe_key": 1},
    "C17": {"github_token": 2, "labelled_pin": 1},
}


def expected_report(rid, expect):
    if rid in EXPECTED_REPORT:
        return EXPECTED_REPORT[rid]
    if not expect:
        return {}
    assert len(expect) == 1, f"{rid}: a multi-class row needs an EXPECTED_REPORT entry"
    return {next(iter(expect)): 1}
