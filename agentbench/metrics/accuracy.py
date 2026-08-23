"""Accuracy scorers.

Three implementations of the :class:`Scorer` protocol:

* :class:`ExactMatchScorer` — string equality after light normalization.
* :class:`SemanticSimilarityScorer` — cosine similarity of sentence-transformers
  embeddings (lazy-loaded so importing the package doesn't pay the model cost).
* :class:`LLMJudgeScorer` — an LLM grades the prediction against the reference
  and returns a 0-1 score with reasoning, via LiteLLM.
"""

from __future__ import annotations

import json
import re
from typing import Any, Protocol, runtime_checkable

from agentbench.exceptions import ScorerError


@runtime_checkable
class Scorer(Protocol):
    """Anything that maps (prediction, reference) -> [0, 1]."""

    def score(self, prediction: str, reference: str) -> float: ...


_NUMERIC_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _extract_last_number(text: str) -> str | None:
    matches = _NUMERIC_RE.findall(text)
    if not matches:
        return None
    return matches[-1].rstrip(".")


class ExactMatchScorer:
    """Exact-match scorer with normalization.

    For numeric references the scorer also tries to extract the last number from
    the prediction (a common pattern with chain-of-thought outputs that end with
    "The answer is 42.").
    """

    def __init__(self, *, numeric_fallback: bool = True) -> None:
        self.numeric_fallback = numeric_fallback

    def score(self, prediction: str, reference: str) -> float:
        p = _normalize(prediction)
        r = _normalize(reference)
        if not r:
            return 0.0
        if p == r or r in p:
            return 1.0
        if self.numeric_fallback and _NUMERIC_RE.fullmatch(r.replace(",", "")):
            extracted = _extract_last_number(prediction.replace(",", ""))
            if extracted is not None:
                try:
                    if abs(float(extracted) - float(r.replace(",", ""))) < 1e-6:
                        return 1.0
                except ValueError:
                    pass
        return 0.0


class SemanticSimilarityScorer:
    """Cosine similarity between sentence embeddings.

    Uses ``sentence-transformers/all-MiniLM-L6-v2`` by default. The model is
    loaded lazily on first call and cached on the instance.
    """

    _DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, *, model_name: str | None = None, threshold: float = 0.0) -> None:
        self.model_name = model_name or self._DEFAULT_MODEL
        self.threshold = threshold
        self._model: Any | None = None

    def _ensure_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover
                raise ScorerError(
                    "sentence-transformers not installed; install with `pip install agentbench`."
                ) from exc
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def score(self, prediction: str, reference: str) -> float:
        if not prediction or not reference:
            return 0.0
        model = self._ensure_model()
        try:
            from sentence_transformers import util

            embeddings = model.encode([prediction, reference], convert_to_tensor=True)
            sim = float(util.cos_sim(embeddings[0], embeddings[1]).item())
        except Exception as exc:  # pragma: no cover - defensive
            raise ScorerError(f"Embedding similarity failed: {exc}") from exc
        # Clamp to [0, 1]; cosine ranges [-1, 1] but for sentence-transformers,
        # negative similarities are vanishingly rare and not meaningful here.
        return max(0.0, min(1.0, sim))


_JUDGE_PROMPT = """You are a strict but fair grader.

Compare the candidate answer to the reference answer for the given question. \
Return JSON with two fields:
  - "score": a number in [0, 1] where 1 means equivalent, 0 means unrelated/wrong.
  - "reasoning": one sentence explaining the score.

Question (may be empty):
{question}

Reference answer:
{reference}

Candidate answer:
{prediction}

Respond with JSON only.
"""


class LLMJudgeScorer:
    """LLM-as-judge scorer.

    Calls a configurable model via LiteLLM, parses a JSON ``{"score": ..., "reasoning": ...}``
    response, and returns the score. On parse failure the scorer returns 0.0 and
    stores the raw response on the last_response attribute for debugging.
    """

    def __init__(
        self,
        *,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 256,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.last_response: str | None = None
        self.last_reasoning: str | None = None

    def score(self, prediction: str, reference: str, *, question: str = "") -> float:
        try:
            from litellm import completion
        except ImportError as exc:  # pragma: no cover
            raise ScorerError("litellm not installed") from exc

        prompt = _JUDGE_PROMPT.format(
            question=question, reference=reference, prediction=prediction
        )
        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as exc:  # pragma: no cover - network path
            raise ScorerError(f"Judge model call failed: {exc}") from exc

        content = self._extract_content(response)
        self.last_response = content
        score, reasoning = self._parse(content)
        self.last_reasoning = reasoning
        return score

    @staticmethod
    def _extract_content(response: Any) -> str:
        try:
            return str(response["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError):
            try:
                return str(response.choices[0].message.content)
            except AttributeError:
                return ""

    @staticmethod
    def _parse(content: str) -> tuple[float, str | None]:
        if not content:
            return 0.0, None
        # Try direct JSON, then a regex fallback for ```json fences.
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{[^{}]*\"score\"[^{}]*\}", content, re.DOTALL)
            if not match:
                return 0.0, content[:200]
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return 0.0, content[:200]
        try:
            score = float(data.get("score", 0.0))
        except (TypeError, ValueError):
            return 0.0, str(data)[:200]
        reasoning = data.get("reasoning")
        return max(0.0, min(1.0, score)), str(reasoning) if reasoning is not None else None
