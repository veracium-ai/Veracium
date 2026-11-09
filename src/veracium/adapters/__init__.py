"""Framework adapters: veracium's served tools, handed to an agent framework.

An adapter adds no trust logic. It carries the library's (specs/0053, the adapter conformance suite):

- the tools, their parameters and their descriptions are the SERVED MCP surface's, read from `build_server`'s own
  registration, never restated;
- each call is validated by the served tool's own argument model and answered by the `*_impl` function the MCP tool
  calls, under the host's bindings (user, capability, source, principal), all fixed when the adapter is built;
- a refusal reaches the model as the library's data, and a raise as the framework's tool-error result carrying the
  library's message.

Each framework is an optional extra, imported only by its own module:

    pip install "veracium[langchain]"       # veracium.adapters.langchain.as_tools

The served surface is read from the MCP server's registration, so every adapter also needs the `mcp` extra; each
framework extra installs it.
"""
