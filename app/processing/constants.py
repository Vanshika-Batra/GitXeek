from enum import Enum

class ArtifactCategory(str, Enum):
    README = "readme"
    REPO_STRUCTURE = "repo_structure"
    PRS = "prs"
    ISSUES = "issues"
    COMMITS = "commits"
    RELEASE = "release"


class TaskType(str, Enum):
    README = "readme"
    REPO_STRUCTURE = "repo_structure"
    TECH_STACK = "tech_stack"
    DEFAULT_BRANCH = "default_branch"
    RECENT_MERGED_PRS = "recent_merged_prs"
    LATEST_PRS = "latest_prs"
    LATEST_ISSUES = "latest_issues"
    RECENT_COMMITS = "recent_commits"
    RELEASES = "releases"
    OLDER_PRS = "older_prs"
    OLDER_COMMITS = "older_commits"
    QUERY_BOOST = "query_boost"


# Lower number = higher priority (processed first)
TASK_BASE_PRIORITY: dict[TaskType, int] = {
    TaskType.README: 0,
    TaskType.REPO_STRUCTURE: 10,
    TaskType.RECENT_MERGED_PRS: 20,
    TaskType.LATEST_PRS: 30,
    TaskType.LATEST_ISSUES: 40,
    TaskType.TECH_STACK: 50,
    TaskType.RECENT_COMMITS: 60,
    TaskType.RELEASES: 70,
    TaskType.DEFAULT_BRANCH: 80,
    TaskType.OLDER_PRS: 90,
    TaskType.OLDER_COMMITS: 100,
    TaskType.QUERY_BOOST: -1000,
}

QUERY_KEYWORDS: dict[ArtifactCategory, tuple[str, ...]] = {
    ArtifactCategory.PRS: ("pr", "pull request", "merge", "merged", "review"),
    ArtifactCategory.COMMITS: ("commit", "change", "changed", "patch", "diff"),
    ArtifactCategory.ISSUES: ("issue", "bug", "ticket", "fix"),
    ArtifactCategory.README: ("readme", "documentation", "docs", "document"),
    ArtifactCategory.REPO_STRUCTURE: (
        "structure",
        "architecture",
        "folder",
        "directory",
        "layout",
        "tech stack",
        "stack",
    ),
}
