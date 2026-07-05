from app.processing.schemas import LLMEnrichment, MergedKnowledgeObject, NormalizedArtifact


def merge_knowledge(
    normalized: NormalizedArtifact, enrichment: LLMEnrichment
) -> MergedKnowledgeObject:
    """Step 4 — combine deterministic normalization with LLM enrichment."""
    domain = enrichment.affected_domain or enrichment.domain
    architectural = enrichment.architectural_impact or enrichment.architectural_change

    return MergedKnowledgeObject(
        type=normalized.artifact_type,
        source_id=normalized.source_id,
        repo=normalized.repo,
        author=normalized.author,
        timestamp=normalized.timestamp,
        title=normalized.title,
        summary=normalized.summary or normalized.title,
        module=normalized.module,
        change_type=normalized.change_type,
        files=normalized.files_changed,
        languages=normalized.languages,
        github_url=normalized.github_url,
        status=normalized.status,
        labels=normalized.labels,
        reviewers=normalized.reviewers,
        pr_number=normalized.pr_number,
        intent=enrichment.intent,
        architectural_impact=architectural,
        architectural_change=enrichment.architectural_change,
        possible_effect=enrichment.possible_effect,
        breaking_change=enrichment.breaking_change,
        affected_domain=domain,
        concepts=enrichment.concepts,
        keywords=enrichment.keywords,
        risks=enrichment.possible_risks,
        technologies=enrichment.technologies,
        dependencies=enrichment.dependencies,
        business_impact=enrichment.business_impact,
    )
