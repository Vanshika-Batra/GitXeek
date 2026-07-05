import asyncio
import logging
from dataclasses import dataclass, field
from itertools import count

from app.db.session import async_session_factory
from app.processing.constants import TASK_BASE_PRIORITY, TaskType
from app.processing.pipeline import ProcessingPipeline
from app.processing.relevance import detect_query_categories

logger = logging.getLogger(__name__)


@dataclass(order=True)
class QueueItem:
    priority: int
    seq: int
    repository_id: int = field(compare=False)
    task_type: TaskType = field(compare=False)


class PriorityScheduler:
    """Global async priority queue — supports multiple repos and users concurrently."""

    _instance: "PriorityScheduler | None" = None

    def __init__(self) -> None:
        self._queue: asyncio.PriorityQueue[QueueItem] = asyncio.PriorityQueue()
        self._counter = count()
        self._worker_task: asyncio.Task | None = None
        self._pipeline = ProcessingPipeline()
        self._boosts: dict[tuple[int, TaskType], int] = {}

    @classmethod
    def get(cls) -> "PriorityScheduler":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self) -> None:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("Processing scheduler started")

    async def stop(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

    async def enqueue_repository(self, repository_id: int) -> None:
        for task_type in TaskType:
            if task_type == TaskType.QUERY_BOOST:
                continue
            await self.enqueue(repository_id, task_type)

    async def enqueue(self, repository_id: int, task_type: TaskType, boost: int = 0) -> None:
        priority = TASK_BASE_PRIORITY[task_type] - boost
        item = QueueItem(priority=priority, seq=next(self._counter), repository_id=repository_id, task_type=task_type)
        await self._queue.put(item)

    async def boost_for_query(self, repository_id: int, query: str) -> list[str]:
        categories = detect_query_categories(query)
        category_to_tasks = {
            "readme": [TaskType.README],
            "repo_structure": [TaskType.REPO_STRUCTURE, TaskType.TECH_STACK, TaskType.RELEASES, TaskType.DEFAULT_BRANCH],
            "prs": [TaskType.RECENT_MERGED_PRS, TaskType.LATEST_PRS, TaskType.OLDER_PRS],
            "issues": [TaskType.LATEST_ISSUES],
            "commits": [TaskType.RECENT_COMMITS, TaskType.OLDER_COMMITS],
        }
        boosted_labels: list[str] = []
        for category in categories:
            for task_type in category_to_tasks.get(category, []):
                await self.enqueue(repository_id, task_type, boost=900)
                boosted_labels.append(self._task_label(task_type))
        return boosted_labels

    async def _worker_loop(self) -> None:
        while True:
            item = await self._queue.get()
            try:
                async with async_session_factory() as db:
                    await self._pipeline.run_task(db, item.repository_id, item.task_type)
            except Exception:
                logger.exception(
                    "Processing failed for repo=%s task=%s", item.repository_id, item.task_type
                )
            finally:
                self._queue.task_done()

    def _task_label(self, task_type: TaskType) -> str:
        labels = {
            TaskType.RECENT_MERGED_PRS: "Recent merged PRs",
            TaskType.LATEST_PRS: "PRs",
            TaskType.OLDER_PRS: "Older PRs",
            TaskType.RECENT_COMMITS: "Commits",
            TaskType.OLDER_COMMITS: "Older commits",
            TaskType.LATEST_ISSUES: "Related issues",
            TaskType.README: "README",
            TaskType.REPO_STRUCTURE: "Repository structure",
            TaskType.TECH_STACK: "Tech stack",
            TaskType.RELEASES: "Releases",
            TaskType.DEFAULT_BRANCH: "Default branch",
        }
        return labels.get(task_type, task_type.value)
