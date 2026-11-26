# veracium (renamed)

Veracium is now published as **`veracium-memory`**. This final release of `veracium` contains no code: it installs
`veracium-memory` 0.34.0. Install the new name directly:

```
pip install "veracium-memory[anthropic]"
```

`import veracium` and the `veracium` and `veracium-mcp` commands are unchanged.

**Upgrading an install made before 0.34.0:** if `import veracium` fails after `pip install -U veracium`, run
`pip install --force-reinstall veracium-memory`. pip installs the new package and then removes the old one's files
from the same paths.
