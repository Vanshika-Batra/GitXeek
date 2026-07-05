import json
import logging
from typing import Any

from app.core.config import get_settings
from app.processing.schemas import LLMEnrichment, MergedKnowledgeObject, NormalizedArtifact

logger = logging.getLogger(__name__)

LLM_ENRICHMENT_PROMPT = """You are GitXeek's enrichment engine analyzing a normalized repository artifact.

The input is deterministic metadata extracted from GitHub — no intelligence yet.
Infer what GitHub never stated explicitly:

- intent (why this change happened)
- architectural_impact / architectural_change
- possible_risks
- possible_effect (for performance/optimization changes)
- technologies involved
- concepts (Authentication, Caching, Database Optimization, etc.)
- breaking_change (true/false)
- affected_domain / domain (Security, Backend, Performance, etc.)
- keywords for retrieval
- dependencies introduced or required
- business_impact

If the change is trivial (formatting, lint, readme-only, whitespace), set skip=true.
Return structured JSON only."""

GRAPH_EXTRACTION_PROMPT = """You are GitXeek's knowledge graph builder.

The input is a merged knowledge object combining deterministic GitHub facts and LLM enrichment.
Extract and connect:

ENTITIES: developers, commits, PRs, issues, modules, files, technologies, concepts, domains
FACTS: who authored what, what replaced what, what files/modules were affected, breaking changes
RELATIONS: AUTHORED, MODIFIES, AFFECTS, USES, REPLACES, INTRODUCED_BY, MERGED_BY, HAS_RISK,
           CHANGED_FILE, PART_OF, EVOLVED_FROM, DEPENDS_ON
TIMELINE: connect this event to prior related changes when timestamps/intent/concepts overlap

Build a rich, traversable graph for questions like:
"Why did we migrate to OAuth?", "Who implemented authentication?", "How did caching evolve?"
"""

GITXEEK_ANSWER_PROMPT = """You are GitXeek — a witty, sharp repository analyst.
Answer using ONLY the retrieved knowledge graph context.
Be precise about who changed what, when, and why. Short, catchy, 2-4 sentences.
Use bullets only for 3+ items. Never invent facts not in context."""


class CogneeClient:
    """Cognee integration — LLM enrichment, graph indexing, and query answering."""

    def __init__(self) -> None:
        print("in cognee client")
        self._settings = get_settings()
        self._cognee = None
        try:
            import cognee
            self._cognee = cognee
            print("connected to cognee client successfully")
        except ImportError:
            self._cognee = None
    
    async def initialize(self):
        await self._cognee.serve(
            url=self._settings.COGNEE_SERVICE_URL,
            api_key=self._settings.COGNEE_API_KEY,
        )

    @property
    def enabled(self) -> bool:
        return self._cognee is not None

    def dataset_name(self, repository_id: int) -> str:
        return f"gitxeek_repo_{repository_id}"

    def session_id(self, repository_id: int, user_id: int) -> str:
        return f"gitxeek_repo_{repository_id}_user_{user_id}"

    async def enrich_with_llm(self, normalized: NormalizedArtifact) -> LLMEnrichment:
        """Step 3 — structured LLM enrichment via Cognee's LLMGateway."""
        if not self.enabled:
            return _fallback_enrichment(normalized)

        try:
            from cognee.infrastructure.llm.LLMGateway import LLMGateway

            payload = json.dumps(
                normalized.model_dump(mode="json", by_alias=True),
                indent=2,
            )
            result = await LLMGateway.acreate_structured_output(
                payload,
                LLM_ENRICHMENT_PROMPT,
                LLMEnrichment,
            )
            return result
        except Exception:
            logger.exception("Cognee LLM enrichment failed for %s", normalized.source_id)
            return _fallback_enrichment(normalized)

    async def index_merged_knowledge(
        self,
        repository_id: int,
        merged: MergedKnowledgeObject,
        *,
        node_set: list[str] | None = None,
    ) -> None:
        """Step 5 — send merged object to Cognee for graph/timeline/semantic memory extraction."""
        if not self.enabled:
            logger.warning("Cognee not installed — merged knowledge not indexed")
            return

        document = json.dumps(merged.model_dump(mode="json"), indent=2)
        kwargs: dict[str, Any] = {
            "dataset_name": self.dataset_name(repository_id),
            "custom_prompt": GRAPH_EXTRACTION_PROMPT,
            "node_set": node_set or [merged.type, merged.module or "general"],
        }
        await self._cognee.remember(document, **kwargs)

    async def recall_context(
        self, repository_id: int, query: str, *, top_k: int = 8
    ) -> list[str]:
        if not self.enabled:
            return []
        results = await self._cognee.recall(
            query,
            datasets=[self.dataset_name(repository_id)],
            top_k=top_k,
            only_context=True,
        )
        return _extract_texts(results)

    async def answer(
        self,
        repository_id: int,
        user_id: int,
        query: str,
        *,
        repo_name: str,
        understanding_pct: int,
    ) -> str:
        """User query → Cognee graph retrieval → Cognee LLM answer."""
        if not self.enabled:
            return ""

        session = self.session_id(repository_id, user_id)
        await self._cognee.remember(query, session_id=session)

        system_prompt = (
            f"{GITXEEK_ANSWER_PROMPT}\n\n"
            f"Repository: {repo_name}\n"
            f"Understanding level: {understanding_pct}%"
        )
        results = await self._cognee.recall(
            query,
            datasets=[self.dataset_name(repository_id)],
            session_id=session,
            system_prompt=system_prompt,
            top_k=10,
        )
        texts = _extract_texts(results)
        return texts[0] if texts else ""


def _fallback_enrichment(normalized: NormalizedArtifact) -> LLMEnrichment:
    """Minimal enrichment when Cognee LLM is unavailable."""
    return LLMEnrichment(
        intent=normalized.summary,
        affected_domain=normalized.module,
        domain=normalized.module,
        concepts=[normalized.module] if normalized.module else [],
        keywords=[normalized.change_type.lower()] if normalized.change_type else [],
        technologies=normalized.languages,
    )


def _extract_texts(results: Any) -> list[str]:
    texts: list[str] = []
    for result in results or []:
        if isinstance(result, str):
            texts.append(result)
            continue
        text = getattr(result, "text", None) or getattr(result, "answer", None)
        if text:
            texts.append(str(text))
            continue
        if isinstance(result, dict):
            for key in ("text", "answer", "content"):
                if result.get(key):
                    texts.append(str(result[key]))
                    break
    return texts


async def search_stored_artifacts(artifacts: list[Any], query: str, limit: int = 8) -> list[str]:
    terms = [t for t in query.lower().split() if len(t) > 2]
    scored: list[tuple[int, str]] = []
    for artifact in artifacts:
        payload = json.dumps(
            {
                "normalized": artifact.normalized_data,
                "llm_enrichment": artifact.enriched_data,
                "merged": getattr(artifact, "merged_data", None),
            },
            default=str,
        ).lower()
        score = sum(payload.count(term) for term in terms)
        if score > 0:
            scored.append((score, payload[:4000]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in scored[:limit]]

cognee_client = CogneeClient()