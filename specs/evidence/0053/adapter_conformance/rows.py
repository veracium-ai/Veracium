"""specs/0053 §5: each adapter's row. The framework and its pinned version, the decoder declared, each provider path
with its description limit and the limit's source, and the mutants its row runs (mutants.MUTANTS, by adapter).

A row is read against the running environment by `tests/test_0053_adapter_conformance.py`: a framework version other
than the pinned one fails by name, since a framework update can change serialisation (§5)."""

ROWS = {
    "core": {
        "module": "veracium.adapters._surface",
        "framework": None,
        "decoder": "identity: the core returns the library's value; a raise is the reference form ('error', message)",
        "providers": [],
    },
    "langchain": {
        "module": "veracium.adapters.langchain",
        "framework": ("langchain-core", "1.7.6"),
        "decoder": "ToolMessage -> ('error', content) on status 'error'; otherwise the content, or the dict the "
                   "framework serialised to JSON text (json.loads). Round-tripped over every reference value of the "
                   "run through the framework's own ToolMessage path (checks.check_decoder)",
        "providers": [
            {"path": "OpenAI function form (langchain_core.utils.function_calling.convert_to_openai_tool)",
             "limit": "no cap in the conversion",
             "source": "measured offline through the framework's conversion: every served description carried in full "
                       "(K2, view 'converted'); the provider's own request-time limit was not read (§6)"},
        ],
    },
}
