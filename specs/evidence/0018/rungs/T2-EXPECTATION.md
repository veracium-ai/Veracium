# T2's census expectation, stated before any T2 code

Committed ahead of the code on purpose (plan §C): an expectation written after the code is only a description of it.

Today the repository census reads 8 references to the head in the forward step's reach:

| where | kind |
|---|---|
| `MigrationPostconditionError.__init__` | error-default |
| `_apply_forward`, the base check | guard |
| `_apply_forward`, the unsupported-base raise (2) | error-argument |
| `_apply_forward`, `plan(base, SCHEMA_VERSION)` | other |
| `_apply_forward`, the version-fault raise | error-argument |
| `_check_stamp` (2) | other |

**After T2 the census reads exactly ONE:** the default of `_apply_forward`'s `target` parameter, `target=SCHEMA_VERSION`, kind
`other`, function `_apply_forward`. Every other member becomes `target`:

- the base check is `base >= target`, and its raise's expected version and text carry `target`;
- `plan(base, target)`;
- the version fault's expected version is `target`;
- `_check_stamp` reads `run.target`;
- `MigrationPostconditionError` takes its expected version as an argument with no default, so the constructor names no head.

`_refuse_unless` keeps its three arguments, its first now `run` (research, 74add182): test_0007's patch passes it through unread, so
the error is built once, at the fire, with `run.target`. (This line first said two files patch it; T1 moved test_0013's hook.) If the census reads anything but this one reference, T2 is wrong or this file is, and
this file changes only with a stated reason.
