import json
import logging

from app.integrations.cognee_client import cognee_client
from app.processing.merger import merge_knowledge
from app.processing.relevance import (
    is_irrelevant_commit,
    is_irrelevant_issue,
    is_irrelevant_pr,
)
from app.processing.schemas import (
    LLMEnrichment,
    MergedKnowledgeObject,
    NormalizedArtifact,
    ProcessedArtifact,
)

logger = logging.getLogger(__name__)


class ArtifactEnricher:
    """
    Step 2.5 — relevance filter (rules, no AI)
    Step 3   — LLM enrichment via Cognee's configured LLM
    Step 4   — merge normalized + LLM into MergedKnowledgeObject
    """

    def __init__(self) -> None:
        self._cognee = cognee_client

    async def process(self, normalized: NormalizedArtifact) -> ProcessedArtifact:
        print("in artifact enrichment process.....")
        if self._should_skip(normalized):
            print("normaized: ", normalized)
            print("is being skipped")
            return ProcessedArtifact(
                normalized=normalized,
                skipped=True,
                skip_reason="Filtered as low-signal change",
            )

        print("llm enrichment with llm")
        llm_enrichment = await self._cognee.enrich_with_llm(normalized)
        if llm_enrichment.skip:
            print("llm said to skip")
            return ProcessedArtifact(
                normalized=normalized,
                llm_enrichment=llm_enrichment,
                skipped=True,
                skip_reason="LLM marked as low-signal change",
            )

        print("LLM ENRICHMENT : ", llm_enrichment)
        merged = merge_knowledge(normalized, llm_enrichment)
        print("merged the outputs")
        return ProcessedArtifact(
            normalized=normalized,
            llm_enrichment=llm_enrichment,
            merged=merged,
        )

    def _should_skip(self, normalized: NormalizedArtifact) -> bool:
        if normalized.artifact_type == "pull_request":
            return is_irrelevant_pr(
                normalized.title or "",
                normalized.body,
                normalized.files_changed,
            )
        if normalized.artifact_type == "commit":
            return is_irrelevant_commit(normalized.summary or normalized.body or "", normalized.files_changed)
        if normalized.artifact_type == "issue":
            return is_irrelevant_issue(normalized.title or "", normalized.labels)
        return False
