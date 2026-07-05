from typing import Any

from pydantic import BaseModel, Field


class NormalizedArtifact(BaseModel):
    """Step 2 — deterministic parsing. No AI."""

    artifact_type: str = Field(serialization_alias="type")
    source_id: str
    category: str
    repo: str
    branch: str | None = None
    title: str | None = None
    summary: str | None = None
    author: str | None = None
    timestamp: str | None = None
    body: str | None = None
    files_changed: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    module: str | None = None
    change_type: str | None = None
    github_url: str | None = None
    pr_number: int | None = None
    status: str | None = None
    labels: list[str] = Field(default_factory=list)
    reviewers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class LLMEnrichment(BaseModel):
    """Step 3 — inferred intelligence via Cognee's configured LLM."""

    intent: str | None = None
    architectural_impact: str | None = None
    architectural_change: str | None = None
    possible_risks: list[str] = Field(default_factory=list)
    possible_effect: str | None = None
    technologies: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    breaking_change: bool = False
    affected_domain: str | None = None
    domain: str | None = None
    keywords: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    business_impact: str | None = None
    skip: bool = False


class MergedKnowledgeObject(BaseModel):
    """Step 4 — normalized facts + LLM inference, ready for Cognee graph extraction."""

    type: str
    source_id: str
    repo: str
    author: str | None = None
    timestamp: str | None = None
    title: str | None = None
    summary: str | None = None
    module: str | None = None
    change_type: str | None = None
    files: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    github_url: str | None = None
    status: str | None = None
    labels: list[str] = Field(default_factory=list)
    reviewers: list[str] = Field(default_factory=list)
    pr_number: int | None = None
    intent: str | None = None
    architectural_impact: str | None = None
    architectural_change: str | None = None
    possible_effect: str | None = None
    breaking_change: bool = False
    affected_domain: str | None = None
    concepts: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    business_impact: str | None = None

class CodeKnowledge(BaseModel):
    path: str
    purpose: str | None = None
    summary: str | None = None
    technologies: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    classes: list[str] = Field(default_factory=list)
    functions: list[str] = Field(default_factory=list)
    api_endpoints: list[str] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)
    configuration: dict[str, str] = Field(default_factory=dict)
    environment_variables: list[str] = Field(default_factory=list)
    database_models: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    architectural_role: str | None = None
    security_notes: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    behavior_changes: list[str] = Field(default_factory=list)
    architectural_notes: str | None = None

class RepositoryKnowledgeDocument(BaseModel):
    artifact: MergedKnowledgeObject
    code_changes: list[CodeKnowledge] = Field(default_factory=list)

class ProcessedArtifact(BaseModel):
    normalized: NormalizedArtifact
    llm_enrichment: LLMEnrichment | None = None
    merged: MergedKnowledgeObject | None = None
    skipped: bool = False
    skip_reason: str | None = None

    # Backward-compatible alias used by DB column name
    @property
    def enriched(self) -> LLMEnrichment | None:
        return self.llm_enrichment
