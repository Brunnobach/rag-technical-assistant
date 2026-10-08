"""Answer generation layer.

Generates a grounded answer using a simple local-LM or template-based fallback.
No OpenAI API key is required; the fallback assembles the answer directly from
retrieved context and includes the cited sources.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFacePipeline, LlamaCpp

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """Generates an answer from retrieved chunks and formats citations."""

    def __init__(self, use_local_llm: bool = False, model_path: str | None = None):
        self.use_local_llm = use_local_llm
        self.model_path = model_path
        self._llm = None

        if self.use_local_llm:
            self._llm = self._load_local_llm()

    def _load_local_llm(self):
        """Load a small local language model for answer generation."""
        if self.model_path and self.model_path.endswith(".gguf"):
            return LlamaCpp(model_path=self.model_path, verbose=False, n_ctx=2048)

        # Default to a small HuggingFace text-generation model
        logger.info("Loading local HuggingFace text-generation pipeline (this may take a moment)")
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        model_name = "HuggingFaceTB/SmolLM2-135M-Instruct"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=256,
            do_sample=False,
        )
        return HuggingFacePipeline(pipeline=pipe)

    def generate(self, question: str, results: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        """Return an answer and the list of sources used.

        When no local LLM is configured, a deterministic template answer is built
        from the retrieved chunks. This keeps the project fully self-contained.
        """
        sources = self._build_sources(results)
        context = self._build_context(sources)

        if self._llm is not None:
            prompt = PromptTemplate(
                input_variables=["context", "question"],
                template=(
                    "You are a technical assistant. Use only the provided context to answer the question.\n\n"
                    "Context:\n{context}\n\n"
                    "Question: {question}\n\n"
                    "Answer concisely and cite the relevant documents by name."
                ),
            )
            chain = LLMChain(llm=self._llm, prompt=prompt)
            answer = chain.predict(context=context, question=question).strip()
        else:
            answer = self._template_answer(question, context)

        return answer, sources

    def _build_context(self, sources: list[dict[str, Any]]) -> str:
        """Join sources into a single context block for the prompt."""
        blocks = []
        for idx, source in enumerate(sources, start=1):
            blocks.append(f"[{idx}] {source['document']} (chunk {source['chunk_index']}):\n{source['text']}")
        return "\n\n".join(blocks)

    def _build_sources(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert retrieval results into a clean source list."""
        sources = []
        for r in results:
            meta = r.get("metadata", {})
            sources.append(
                {
                    "document": meta.get("document", "unknown"),
                    "chunk_index": meta.get("chunk_index", -1),
                    "page": meta.get("page"),
                    "text": r.get("text", ""),
                    "score": r.get("score", 0.0),
                }
            )
        return sources

    def _template_answer(self, question: str, context: str) -> str:
        """Build a simple deterministic answer when no LLM is configured."""
        return (
            "Based on the retrieved technical documents, here is the information related to your question:\n\n"
            f"{context}\n\n"
            "Answer the question using the passages above. If the context does not contain enough information, "
            "say that you cannot answer confidently."
        )
