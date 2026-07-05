from app.processing.constants import TaskType

# Each completed task contributes this many points toward understanding_percentage (sums to 100)
# weighted count is calculated using the below points
TASK_UNDERSTANDING_POINTS: dict[TaskType, int] = {
    TaskType.README: 20,
    TaskType.REPO_STRUCTURE: 5,
    TaskType.RECENT_MERGED_PRS: 8,
    TaskType.LATEST_PRS: 9,
    TaskType.LATEST_ISSUES: 20,
    TaskType.TECH_STACK: 3,
    TaskType.RECENT_COMMITS: 12,
    TaskType.RELEASES: 5,
    TaskType.DEFAULT_BRANCH: 2,
    TaskType.OLDER_PRS: 8,
    TaskType.OLDER_COMMITS: 8,
}


def init_progress() -> dict:
    return {"completed_tasks": [], "skipped_artifacts": 0, "indexed_artifacts": 0}


def calculate_understanding_percentage(progress: dict) -> int:
    print("in calculating understanding percentage.....: ", progress)
    completed = set(progress.get("completed_tasks", []))
    total = sum(
        points for task, points in TASK_UNDERSTANDING_POINTS.items() if task.value in completed
    )
    return min(total, 100)


def mark_task_complete(progress: dict, task_type: TaskType) -> dict:
    print("in mark_task_complete: ;;;;" )
    print("PROGRESS...: ", progress)
    print("TASK TYPE...: ", task_type)
    completed = progress.setdefault("completed_tasks", [])
    if task_type.value not in completed:
        completed.append(task_type.value)
    print("progresssss.....", progress)
    return progress


def increment_artifact_count(progress: dict, *, skipped: bool) -> dict:
    print("incrementing artifact count..........")
    key = "skipped_artifacts" if skipped else "indexed_artifacts"
    progress[key] = progress.get(key, 0) + 1
    print("progress[key]", key, progress[key])
    return progress
