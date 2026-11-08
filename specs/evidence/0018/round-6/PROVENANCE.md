# 0018 adjacent rungs: the terminal record of the accepted round-6 package

The implementation was ACCEPTED at external round 6 (2026-11-08): specs/0018 v9.1.2, the verdict banked verbatim in the coordination
repository as `outbox/archive/0018-adjacent-rungs-round6-verdict-verbatim.md` (file sha16 150e54293d6de53e, body sha16 56d91e1fd53b8a43).
The accepted artifact is the package `0018-adjacent-rungs-round6-implementation-review-package.tar.gz`, sha256 `f8007ac553705d56cf4227ab0daad6dcca8ea71b357c27b89b2c6124db0693ab`, pin
`91838da576b567ce35c93ab6cee875230e093b12`.

The files beside this one are BYTE COPIES of the sealed package's own members, unmodified, each equal to its line in the package's
SHA256SUMS. They are kept so the named limits stay beside the green matrices, and because the verdict's rule forward asks for them:
"Keep the publication-state matrix, raw invocation witness and source/test-bound backward captures with later changes to these seams."

| file here | member of the package | sha256 (equals the package's SHA256SUMS line) |
|---|---|---|
| `README-0018-adjacent-rungs-round6-bundle.md` | `README-0018-adjacent-rungs-round6-bundle.md` | `22f8768b1a439728d4890025502383fdda8f0c680fd45f94d7de47c3410425a8` |
| `PIN.txt` | `PIN.txt` | `acfa8c38943cf4caed8dbd38f7e04882baa4daa5ea167b8705e7ac261f43bc89` |
| `backward-control.txt` | `collected/backward-control.txt` | `8385f1480e39c2955e9ded372bbd0502e18a46ebeedde518526d48c84ce7dc85` |
| `backward-control-results.xml` | `collected/backward-control-results.xml` | `de711af46cba0845074b175db7338969626d3e6b871a9a87723431b552c7ad32` |
| `backward-twin-results.xml` | `collected/backward-twin-results.xml` | `7d1ac3b57ed68621c92802521231b6d1f066e4e87fb8198feefbe37360b987a5` |
| `obligation-map.md` | `collected/obligation-map.md` | `33b2b98503b946908def8e61675f203f8515fb54b1cdc7ffea13d7beed82c89a` |
| `cell-results.md` | `collected/cell-results.md` | `aa68ba29571b676a35e34c4ccf14a2b138152c5d39fe678fc9dec3c15a89048b` |

What the rule names, and where each is:

- **The source/test-bound backward captures**: `backward-control.txt` (it names round 5's `src/` by git tree and the closure file by git
  blob), `backward-control-results.xml` and `backward-twin-results.xml`, the raw junit.
- **The publication-state matrix**: `tests/test_0018_r5_closures.py`, a module of this tree (blob `94a6cbac9036a5018267d87361c6ff80efe28d6f`
  at the pin). Its results at the pin are in the package's `collected/suite-results.xml` (sha256 `186ab7a68c27ed98a4ee986079595ace20cbaa4e92a85d84781b34810412fe55`),
  which is not copied here; `cell-results.md` is the package's per-cell summary of the 856 closure cells.
- **The raw invocation witness**: `_Trace` in `tests/test_0018_rungs_t5.py`, also a module of this tree (blob
  `620c40d3f05eddd3daadd2016642853178412a6a` at the pin). The package ships no separate witness artifact.

Both modules carry a FROZEN-at-round-6 marker quoting the rule, as does `specs/evidence/0018/rungs/implementation_mutants.py`. The
markers are comments added at the acceptance fold, after the pin, so the modules' blobs here differ from the pin's by those lines only.
