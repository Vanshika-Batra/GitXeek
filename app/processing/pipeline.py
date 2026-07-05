import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.cognee_client import cognee_client
from app.integrations.github_client import GitHubClient
from app.models.artifact import ArtifactStatus, RepositoryArtifact
from app.models.repository import ProcessingStatus, Repository
from app.models.user import User
from app.processing.constants import ArtifactCategory, TaskType
from app.processing.enricher import ArtifactEnricher
from app.processing.normalizer import (
    detect_tech_stack,
    normalize_commit,
    normalize_issue,
    normalize_pull_request,
    normalize_readme,
    normalize_release,
    normalize_repo_structure,
    read_local_readme,
    walk_local_tree,
)
from app.processing.progress import (
    calculate_understanding_percentage,
    increment_artifact_count,
    init_progress,
    mark_task_complete,
)
from app.processing.schemas import NormalizedArtifact

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    def __init__(self) -> None:
        self._enricher = ArtifactEnricher()
        self._cognee = cognee_client

    async def run_task(self, db: AsyncSession, repository_id: int, task_type: TaskType) -> None:
        print("in run task....")
        print("repoj id: ", repository_id)
        print("task type: ", task_type)
        repo = await db.get(Repository, repository_id)
        print("repo fetched from db: ", repo)
        if not repo or not repo.clone_path:
            return

        progress = dict(repo.processing_progress)
        print("progress: ", progress)
        print(repo.processing_progress)
        print(progress["completed_tasks"])
        if task_type.value in progress.get("completed_tasks", []):
            return

        user = await db.get(User, repo.user_id)
        if not user or not user.github_token:
            return

        repo.processing_status = ProcessingStatus.PROCESSING
        repo.processing_progress = progress
        if not repo.cognee_dataset_name:
            repo.cognee_dataset_name = self._cognee.dataset_name(repository_id)
        await db.commit()
        print("dataset name: ", repo.cognee_dataset_name)

        owner, name = repo.full_name.split("/", 1)
        client = GitHubClient(access_token=user.github_token)
        clone_path = Path(repo.clone_path)

        try:
            print("ABOUT TO PROCESS EVERYTHINGGGGGGGGG......")
            handlers = {
                TaskType.README: lambda: self._process_readme(db, repo, clone_path),
                TaskType.REPO_STRUCTURE: lambda: self._process_repo_structure(db, repo, clone_path),
                TaskType.TECH_STACK: lambda: self._process_tech_stack(db, repo, clone_path),
                TaskType.DEFAULT_BRANCH: lambda: self._process_default_branch(db, repo, client, owner, name),
                TaskType.RECENT_MERGED_PRS: lambda: self._process_prs(
                    db, repo, client, owner, name, merged_only=True, limit=20
                ),
                TaskType.LATEST_PRS: lambda: self._process_prs(
                    db, repo, client, owner, name, merged_only=False, limit=20
                ),
                TaskType.OLDER_PRS: lambda: self._process_prs(
                    db, repo, client, owner, name, merged_only=False, limit=50, page=2
                ),
                TaskType.LATEST_ISSUES: lambda: self._process_issues(db, repo, client, owner, name, limit=20),
                TaskType.RECENT_COMMITS: lambda: self._process_commits(
                    db, repo, client, owner, name, limit=50, page=1
                ),
                TaskType.OLDER_COMMITS: lambda: self._process_commits(
                    db, repo, client, owner, name, limit=50, page=2
                ),
                TaskType.RELEASES: lambda: self._process_releases(db, repo, client, owner, name),
            }
            handler = handlers.get(task_type)
            if handler:
                await handler()

            await db.refresh(repo)
            progress = dict(repo.processing_progress)
            progress = mark_task_complete(progress, task_type)
            repo.processing_progress = progress
            print("repo.processing progres..: ", repo.processing_progress)
            repo.understanding_percentage = calculate_understanding_percentage(repo.processing_progress)
            if repo.understanding_percentage >= 100:
                repo.processing_status = ProcessingStatus.READY
            await db.commit()
        except Exception:
            logger.exception("Task failed repo=%s task=%s", repository_id, task_type)
            repo.processing_status = ProcessingStatus.FAILED
            await db.commit()
            raise

    async def _process_readme(self, db: AsyncSession, repo: Repository, clone_path: Path) -> None:
        print("in process readme")
        content = read_local_readme(clone_path)
        if content:
            await self._process_single(db, repo, normalize_readme(content, repo.full_name))

    async def _process_repo_structure(self, db: AsyncSession, repo: Repository, clone_path: Path) -> None:
        tree = walk_local_tree(clone_path)
        tech = detect_tech_stack(clone_path)
        await self._process_single(db, repo, normalize_repo_structure(tree, repo.full_name, tech))

    async def _process_tech_stack(self, db: AsyncSession, repo: Repository, clone_path: Path) -> None:
        tech = detect_tech_stack(clone_path)
        normalized = NormalizedArtifact(
            artifact_type="tech_stack",
            source_id="tech_stack",
            category=ArtifactCategory.REPO_STRUCTURE.value,
            repo=repo.full_name,
            title="Tech stack",
            summary=", ".join(tech) if tech else "Unknown stack",
            body=", ".join(tech),
            languages=tech,
            module="Architecture",
            change_type="Structure",
            metadata={"stack": tech},
        )
        await self._process_single(db, repo, normalized)

    async def _process_default_branch(
        self, db: AsyncSession, repo: Repository, client: GitHubClient, owner: str, name: str
    ) -> None:
        gh_repo = await client.get_repository(owner, name)
        normalized = NormalizedArtifact(
            artifact_type="default_branch",
            source_id=gh_repo.get("default_branch") or "main",
            category=ArtifactCategory.REPO_STRUCTURE.value,
            repo=repo.full_name,
            title=f"Default branch: {gh_repo.get('default_branch')}",
            summary=f"Default branch is {gh_repo.get('default_branch')}",
            branch=gh_repo.get("default_branch"),
            languages=[gh_repo.get("language")] if gh_repo.get("language") else [],
            module="Configuration",
            change_type="Structure",
            metadata={"default_branch": gh_repo.get("default_branch"), "language": gh_repo.get("language")},
        )
        await self._process_single(db, repo, normalized)

    async def _process_prs(
        self,
        db: AsyncSession,
        repo: Repository,
        client: GitHubClient,
        owner: str,
        name: str,
        *,
        merged_only: bool,
        limit: int,
        page: int = 1,
    ) -> None:
        prs = await client.list_pull_requests(owner, name, state="all" if not merged_only else "closed", page=page)
        if merged_only:
            prs = [pr for pr in prs if pr.get("merged_at")][:limit]
        else:
            prs = prs[:limit]
        for pr in prs:
            await self._process_single(db, repo, normalize_pull_request(pr, repo.full_name))

    async def _process_issues(
        self, db: AsyncSession, repo: Repository, client: GitHubClient, owner: str, name: str, *, limit: int
    ) -> None:
        issues = (await client.list_issues(owner, name))[:limit]
        for issue in issues:
            await self._process_single(db, repo, normalize_issue(issue, repo.full_name))

    async def _process_commits(
        self,
        db: AsyncSession,
        repo: Repository,
        client: GitHubClient,
        owner: str,
        name: str,
        *,
        limit: int,
        page: int,
    ) -> None:
        commits = (await client.list_commits(owner, name, branch=repo.default_branch, page=page))[:limit]
        for commit in commits:
            detailed = await client.get_commit(owner, name, commit["sha"])
            await self._process_single(
                db, repo, normalize_commit(detailed, repo.full_name, repo.default_branch)
            )

    async def _process_releases(
        self, db: AsyncSession, repo: Repository, client: GitHubClient, owner: str, name: str
    ) -> None:
        releases = await client.list_releases(owner, name)
        for release in releases:
            await self._process_single(db, repo, normalize_release(release, repo.full_name))

    async def _process_single(
        self, db: AsyncSession, repo: Repository, normalized: NormalizedArtifact
    ) -> None:
        print("processing single artifact.......")
        existing = await db.execute(
            select(RepositoryArtifact).where(
                RepositoryArtifact.repository_id == repo.id,
                RepositoryArtifact.artifact_type == normalized.artifact_type,
                RepositoryArtifact.source_id == normalized.source_id,
            )
        )
        if existing.scalar_one_or_none():
            return

        processed = await self._enricher.process(normalized)
        artifact = RepositoryArtifact(
            repository_id=repo.id,
            artifact_type=normalized.artifact_type,
            source_id=normalized.source_id,
            category=normalized.category,
            status=ArtifactStatus.SKIPPED if processed.skipped else ArtifactStatus.INDEXED,
            normalized_data=processed.normalized.model_dump(mode="json", by_alias=True),
            enriched_data=(
                processed.llm_enrichment.model_dump(mode="json") if processed.llm_enrichment else None
            ),
            merged_data=processed.merged.model_dump(mode="json") if processed.merged else None,
            skip_reason=processed.skip_reason,
        )
        db.add(artifact)

        await db.refresh(repo)

        progress = dict(repo.processing_progress)

        progress = increment_artifact_count(
            progress,
            skipped=processed.skipped,
        )

        repo.processing_progress = progress

        if not processed.skipped and processed.merged:
            print("sending to cognee for merging.......")
            await self._cognee.index_merged_knowledge(
                repo.id,
                processed.merged,
                node_set=[normalized.category, normalized.artifact_type, normalized.module or "general"],
            )
        await db.commit()
