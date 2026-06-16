"""
Judge pipeline: deterministic grader + frozen LLM judge.

The judge was frozen before any tool ran. It consists of two stages:
1. Deterministic rules (exact-match types, adversarial abstention checks)
2. LLM judge (frozen prompts, frozen model) for free-form answers

Every verdict includes a confidence score. Confidence < 0.7 triggers a
second independent pass. Raw per-question records are published.

Failure-mode taxonomy:
- missing_recall: answerer says "I don't know" because retrieval was empty
- wrong_fact: answerer gave a specific answer that is factually incorrect
- wrong_abstention: answerer abstained when it should have answered
- partial: answerer gave a partially correct answer
- hallucination: answerer invented information not in the source
- cross_project_leak: retrieved data from a different project (PlatformOps-Mem only)
- none: answerer gave the correct answer (no failure)
"""

from dataclasses import dataclass
from typing import Optional
import json
import re
import hashlib


# Frozen judge prompts — SHA-256 stamped at methodology lock.
# These prompts are never edited mid-series.
JUDGE_PROMPT_SYSTEM = """You are a strict grading assistant for a memory-system benchmark.
Your job is to compare a model's answer against the ground-truth answer and decide if the model's answer is correct.

Rules:
1. The model is given ONLY excerpts from a memory system — it does NOT have access to the full conversation.
2. If the model says "I don't know" or gives a vague non-answer, grade it as INCORRECT (the memory system failed to retrieve the needed context).
3. If the model gives a specific answer that contradicts the ground truth, grade it as INCORRECT.
4. If the model gives a specific answer that matches the ground truth in substance, grade it as CORRECT. Minor wording differences are fine.
5. For adversarial questions (where the correct answer is to abstain), the model should say "I don't know" or similar. If it fabricates an answer, grade it as INCORRECT.

Output format (JSON):
{
  "correct": true | false,
  "confidence": 0.0 to 1.0,
  "failure_mode": "missing_recall" | "wrong_fact" | "wrong_abstention" | "partial" | "hallucination" | "cross_project_leak" | "none",
  "reason": "brief explanation"
}
"""

JUDGE_PROMPT_USER_TEMPLATE = """Question: {question}
Ground-truth answer: {gold_answer}
Model's answer: {model_answer}
Category: {category}

Grade the model's answer."""


@dataclass
class GradeResult:
    correct: bool
    confidence: float
    failure_mode: str
    reason: str
    graded_by: str  # "deterministic" | "llm_judge" | "llm_judge_second_pass"
    pass_number: int = 1


class DeterministicGrader:
    """First-pass deterministic grading for exact-match and abstention cases."""

    # Normalized forms of "I don't know"
    ABSTENTION_PATTERNS = [
        r"i don't know",
        r"i do not know",
        r"i'm not sure",
        r"i am not sure",
        r"not enough information",
        r"insufficient information",
        r"cannot determine",
        r"no information",
        r"unable to answer",
    ]

    @classmethod
    def is_abstention(cls, answer: str) -> bool:
        lower = answer.lower().strip()
        for pat in cls.ABSTENTION_PATTERNS:
            if re.search(pat, lower):
                return True
        return False

    @classmethod
    def grade(cls, question: str, gold_answer: str, model_answer: str,
              category: int) -> Optional[GradeResult]:
        """
        Returns a GradeResult if deterministic grading applies, else None.
        """
        gold_lower = gold_answer.lower().strip()
        model_lower = model_answer.lower().strip()

        # Category 5: adversarial — correct answer is abstention
        if category == 5:
            if cls.is_abstention(model_answer):
                return GradeResult(
                    correct=True,
                    confidence=1.0,
                    failure_mode="none",
                    reason="Correct abstention on adversarial question",
                    graded_by="deterministic"
                )
            else:
                return GradeResult(
                    correct=False,
                    confidence=1.0,
                    failure_mode="wrong_abstention",
                    reason="Should have abstained but gave an answer",
                    graded_by="deterministic"
                )

        # Empty retrieval → abstention is missing_recall, not wrong_abstention
        if cls.is_abstention(model_answer):
            return GradeResult(
                correct=False,
                confidence=1.0,
                failure_mode="missing_recall",
                reason="Model abstained — memory system failed to retrieve context",
                graded_by="deterministic"
            )

        # Exact match (case-insensitive, after stripping)
        if model_lower == gold_lower:
            return GradeResult(
                correct=True,
                confidence=1.0,
                failure_mode="none",
                reason="Exact match",
                graded_by="deterministic"
            )

        # Simple substring containment (for short factual answers)
        if len(gold_answer) < 50 and gold_lower in model_lower:
            return GradeResult(
                correct=True,
                confidence=0.95,
                failure_mode="none",
                reason="Ground truth is substring of model answer",
                graded_by="deterministic"
            )

        return None  # Fall through to LLM judge


class LLMJudge:
    """Second-pass LLM judge for free-form answers."""

    def __init__(self, model: str, transport: str):
        self.model = model
        self.transport = transport
        self.prompt_hash = self._hash_prompt(JUDGE_PROMPT_SYSTEM)

    def _hash_prompt(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    def grade(self, question: str, gold_answer: str, model_answer: str,
              category: int, pass_number: int = 1) -> GradeResult:
        """
        Call the LLM judge via the configured transport.
        
        Parses the model's JSON response into a GradeResult.
        On transport or parsing failure, returns a conservative incorrect verdict.
        """
        from harness.transport import TransportFactory

        try:
            transport = TransportFactory.for_track(self.transport)
            messages = self.build_prompt(question, gold_answer, model_answer, category)
            resp = transport.chat(messages, model=self.model, temperature=0.0, max_tokens=512)

            if resp.error:
                return GradeResult(
                    correct=False,
                    confidence=0.0,
                    failure_mode="missing_recall",
                    reason=f"LLM judge transport error: {resp.error}",
                    graded_by="llm_judge" if pass_number == 1 else "llm_judge_second_pass",
                    pass_number=pass_number
                )

            # Parse JSON from the response text
            parsed = self._parse_judge_output(resp.text)
            return GradeResult(
                correct=parsed.get("correct", False),
                confidence=parsed.get("confidence", 0.0),
                failure_mode=parsed.get("failure_mode", "missing_recall"),
                reason=parsed.get("reason", "No reason provided"),
                graded_by="llm_judge" if pass_number == 1 else "llm_judge_second_pass",
                pass_number=pass_number
            )

        except Exception as e:
            return GradeResult(
                correct=False,
                confidence=0.0,
                failure_mode="missing_recall",
                reason=f"LLM judge exception: {str(e)}",
                graded_by="llm_judge" if pass_number == 1 else "llm_judge_second_pass",
                pass_number=pass_number
            )

    def _parse_judge_output(self, text: str) -> dict:
        """
        Extract and parse JSON from the judge's response text.
        
        Handles:
        - Clean JSON output
        - JSON embedded in markdown code blocks
        - JSON with trailing text
        - Malformed JSON (returns conservative defaults)
        """
        # Try to extract JSON from markdown code block
        code_block = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if code_block:
            text = code_block.group(1)
        else:
            # Try to find the first JSON object
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)

        try:
            parsed = json.loads(text)
            # Validate required fields
            if "correct" not in parsed:
                parsed["correct"] = False
            if "confidence" not in parsed:
                parsed["confidence"] = 0.0
            if "failure_mode" not in parsed:
                parsed["failure_mode"] = "missing_recall"
            if "reason" not in parsed:
                parsed["reason"] = "No reason provided"
            return parsed
        except json.JSONDecodeError:
            # Conservative fallback
            return {
                "correct": False,
                "confidence": 0.0,
                "failure_mode": "missing_recall",
                "reason": f"Failed to parse judge JSON: {text[:200]}"
            }

    def build_prompt(self, question: str, gold_answer: str, model_answer: str,
                     category: int) -> list[dict]:
        return [
            {"role": "system", "content": JUDGE_PROMPT_SYSTEM},
            {"role": "user", "content": JUDGE_PROMPT_USER_TEMPLATE.format(
                question=question,
                gold_answer=gold_answer,
                model_answer=model_answer,
                category=category
            )}
        ]


class JudgePipeline:
    """Full pipeline: deterministic → LLM judge → second pass if confidence < 0.7."""

    def __init__(self, llm_model: str, transport: str):
        self.deterministic = DeterministicGrader()
        self.llm = LLMJudge(llm_model, transport)

    def grade(self, question: str, gold_answer: str, model_answer: str,
              category: int) -> GradeResult:
        # Stage 1: deterministic
        result = self.deterministic.grade(question, gold_answer, model_answer, category)
        if result:
            return result

        # Stage 2: LLM judge
        result = self.llm.grade(question, gold_answer, model_answer, category, pass_number=1)

        # Stage 3: second pass if confidence < 0.7
        if result.confidence < 0.7:
            result2 = self.llm.grade(question, gold_answer, model_answer, category, pass_number=2)
            # Take the more conservative grade (lower confidence, or false if split)
            if result2.correct != result.correct:
                result = GradeResult(
                    correct=False,
                    confidence=min(result.confidence, result2.confidence),
                    failure_mode=result.failure_mode,
                    reason=f"Split verdict (pass 1: {result.correct}, pass 2: {result2.correct}) — conservative fallback to incorrect",
                    graded_by="llm_judge_second_pass",
                    pass_number=2
                )
            else:
                result.confidence = max(result.confidence, result2.confidence)

        return result

    def grade_batch(self, items: list[dict]) -> list[GradeResult]:
        """Grade a batch of questions. Each item is a dict with keys:
        question, gold_answer, model_answer, category."""
        return [self.grade(**item) for item in items]
