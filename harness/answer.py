"""
Answering model integration.

The answering model sees ONLY the retrieved excerpts — never the gold answer or
category. It produces a free-text answer that is then graded by the judge pipeline.

This module implements the answer prompt template and the model call.
"""

from harness.transport import TransportFactory, LLMResponse
from harness.telemetry import TelemetryCollector


ANSWER_SYSTEM_PROMPT = """You are a helpful assistant answering questions based ONLY on the provided context excerpts. You do NOT have access to any external knowledge or the full conversation history.

Rules:
1. Answer using ONLY the information in the provided excerpts.
2. If the excerpts do not contain enough information to answer, say "I don't know" or "I don't have enough information to answer that."
3. Be concise. Give a direct answer if possible.
4. Do not make up information that is not in the excerpts.
"""


def answer_question(
    question: str,
    excerpts: list[str],
    model: str,
    track: str,
    telemetry: TelemetryCollector,
) -> str:
    """
    Call the answering model with the retrieved excerpts.

    Args:
        question: The question to answer.
        excerpts: Retrieved context excerpts from the memory tool.
        model: Model string (e.g., "anthropic/claude-sonnet-4.6" or "deepseek-v4-pro").
        track: "main" or "open".
        telemetry: Telemetry collector to instrument the call.

    Returns:
        The model's answer text.
    """
    context_text = "\n\n".join(
        f"Excerpt {i+1}:\n{excerpt}"
        for i, excerpt in enumerate(excerpts)
    ) if excerpts else "No relevant excerpts were found."

    messages = [
        {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
        {"role": "user", "content": f"Context excerpts:\n\n{context_text}\n\nQuestion: {question}\n\nAnswer based ONLY on the excerpts above."},
    ]

    transport = TransportFactory.for_track(track)

    with telemetry.record_call(method="answer", tool=None, model=model) as ctx:
        resp = transport.chat(messages, model=model, temperature=0.0, max_tokens=512)
        if resp.error:
            raise RuntimeError(f"Answer model failed: {resp.error}")
        ctx.set_tokens(resp.tokens_prompt, resp.tokens_completion)

    return resp.text
