"""Veracium as the long-term memory layer of a LangChain chat app.

Mirrors the standard LangChain memory pattern — `RunnableWithMessageHistory`
over a session-keyed chat history — and upgrades its "hybrid memory" slot:
recent turns stay in LangChain's in-memory buffer (short-term coherence), and
the durable layer is Veracium instead of an LLM summary or a replayed message
log. What that buys over the usual approaches:

- **Distilled facts, not transcript replay** — supersession keeps one current
  value per fact with history retained, instead of a growing JSON log.
- **A trust model** — content the user pastes in from elsewhere can be
  ingested as `THIRD_PARTY`: its claims are quarantined and the recalled
  context flags them "never assert as fact" instead of feeding them to the
  model as truth.
- **Per-user isolation** — LangChain's `session_id` maps 1:1 onto Veracium's
  `user_id`; memory is isolated structurally, not by dict key.

Needs: `pip install "veracium[anthropic]" langchain-core` plus any LangChain
chat model (the demo uses `langchain-anthropic`; swap in yours).

One model serves both sides: `LangChainComplete` adapts your existing
LangChain chat model into Veracium's `Complete` contract, so Veracium's
extraction/curation runs on the model you already configured.
"""

from __future__ import annotations

from typing import Optional

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from veracium import EvidenceAuthor, Memory, MemoryConfig


class LangChainComplete:
    """Adapt any LangChain chat model into a Veracium `Complete` callable.

    Honest `json_schema` handling: we don't force structured output — Veracium's
    tolerant parser copes with prose-wrapped JSON, which is exactly why the
    interface allows ignoring the schema.
    """

    def __init__(self, model: BaseChatModel):
        self._model = model

    def __call__(self, prompt: str, *, system: Optional[str] = None,
                 role: str = "compile", json_schema: Optional[dict] = None) -> str:
        messages = ([("system", system)] if system else []) + [("human", prompt)]
        return self._model.invoke(messages).text


class VeraciumLangChainMemory:
    """The hybrid: a per-session LangChain buffer for recent turns + Veracium
    for durable memory. Wire `get_session_history` into
    `RunnableWithMessageHistory` exactly as in any LangChain memory tutorial;
    call `context(...)` for the prompt's long-term slot and `observe(...)`
    after each user turn."""

    def __init__(self, llm, db_path: str = "langchain-veracium.db",
                 recent_window: int = 6):
        self.mem = Memory(llm=llm, config=MemoryConfig(db_path=db_path))
        self.recent_window = recent_window
        self._buffers: dict[str, InMemoryChatMessageHistory] = {}

    # -- the LangChain side: short-term buffer, session-keyed ---------------
    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self._buffers:
            self._buffers[session_id] = InMemoryChatMessageHistory()
        hist = self._buffers[session_id]
        hist.messages = hist.messages[-self.recent_window:]   # window, not log
        return hist

    # -- the Veracium side: durable, distilled, provenance-aware ------------
    def observe(self, session_id: str, user_text: str, *,
                third_party: bool = False) -> None:
        """Remember a turn. Set third_party=True for content the user pasted
        from elsewhere (a received email, a web page) — its claims are
        quarantined rather than stored as user facts."""
        self.mem.remember(session_id, user_text,
                          author=EvidenceAuthor.THIRD_PARTY if third_party
                          else EvidenceAuthor.USER,
                          event_type="paste" if third_party else "chat")

    def context(self, session_id: str, query: str, *, token_budget: int = 600) -> str:
        """Grounded long-term context for the prompt: verified facts stated
        plainly, unverified third-party claims fenced under a never-assert
        marker, trimmed to the budget."""
        return self.mem.recall(session_id, query, token_budget=token_budget).context


def build_chain(model: BaseChatModel, memory: VeraciumLangChainMemory):
    """The tutorial-standard wiring (`RunnableWithMessageHistory` — deprecated
    upstream in favor of LangGraph persistence, but still what most memory
    tutorials teach), plus one extra prompt slot for Veracium. On LangGraph,
    skip this wrapper and call `memory.observe()` / `memory.context()` from
    your graph nodes the same way."""
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a helpful assistant with long-term memory.\n"
         "LONG-TERM MEMORY (verified facts are stated plainly; anything under "
         "an UNVERIFIED marker must never be asserted as fact):\n{longterm}"),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])
    return RunnableWithMessageHistory(
        prompt | model,
        memory.get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )


def chat_with_persistent_memory(user_id: str, model: BaseChatModel) -> None:
    """A persistent multi-user chatbot, tutorial-style: quit with 'quit'.
    Unlike a JSON message log, restarting doesn't replay a transcript — it
    recalls distilled facts with provenance."""
    memory = VeraciumLangChainMemory(LangChainComplete(model))
    chain = build_chain(model, memory)
    print(f"[memory loaded for {user_id!r} — Veracium recalls facts, not transcripts]")
    while True:
        text = input("> ").strip()
        if text.lower() in ("quit", "exit"):
            break
        memory.observe(user_id, text)
        reply = chain.invoke(
            {"input": text,
             "longterm": memory.context(user_id, text)},
            config={"configurable": {"session_id": user_id}})
        print(reply.text)
    memory.mem.close()


if __name__ == "__main__":
    # Any LangChain chat model works; this uses Anthropic:
    #   pip install langchain-anthropic  (and set ANTHROPIC_API_KEY)
    from langchain_anthropic import ChatAnthropic
    chat_with_persistent_memory("alice", ChatAnthropic(model="claude-haiku-4-5"))
