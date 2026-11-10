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
    "pydantic_ai": {
        "module": "veracium.adapters.pydantic_ai",
        "framework": ("pydantic-ai-slim", "2.66.0"),
        "decoder": "the ToolReturnPart the agent hands the model, read from its text (model_response_str): an outcome of "
                   "'retried' (ModelRetry, the framework's tool-error channel) is {\"error\": message} -> ('error', "
                   "message); otherwise the tool's string, or the dict the framework serialised to JSON text. "
                   "Round-tripped over every reference value through the framework's own agent path (checks.check_decoder)",
        "retry_budget": "the host's: Pydantic AI ends a run with UnexpectedModelBehavior when one tool errors more "
                        "times than its max_retries (default: the agent's retries, 1) without a success of its own in "
                        "between; a call to another tool, raising or not, resets nothing, and at max_retries=0 the "
                        "first error ends the run before the model sees it (research's PA-1). as_tools(max_retries=) "
                        "sets every tool's budget. Measured on 2.66.0, held by "
                        "test_the_pydantic_ai_retry_budget_is_the_hosts",
        "providers": [
            {"path": "the ToolDefinitions an Agent hands any model (FunctionModel's AgentInfo.function_tools)",
             "limit": "no cap in the conversion",
             "source": "measured offline through the framework's own agent: every served description carried in full "
                       "(K2, view 'converted'); each provider model class maps these at request time, past what the "
                       "offline path shows, and no provider's documentation was read (§6)"},
        ],
    },
}
