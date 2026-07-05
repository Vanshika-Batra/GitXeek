import re

from app.processing.constants import QUERY_KEYWORDS

IRRELEVANT_TITLE_PATTERNS = re.compile(
    r"\b(format|formatting|lint|prettier|eslint|style|indent|whitespace|"
    r"readme|typo|spelling|chore|bump version|merge branch|merge main|"
    r"update dependencies|dependabot|ci:|cd:)\b",
    re.IGNORECASE,
)

IRRELEVANT_COMMIT_PATTERNS = re.compile(
    r"^(style|chore|docs|ci|build)(\(.+\))?!?:|\b(format|lint|readme|typo|whitespace)\b",
    re.IGNORECASE,
)

MIN_MEANINGFUL_FILES = 1
DOC_ONLY_EXTENSIONS = {".md", ".txt", ".rst", ".json", ".yaml", ".yml", ".toml", ".lock"}


def is_irrelevant_pr(title: str, body: str | None = None, files: list[str] | None = None) -> bool:
    if IRRELEVANT_TITLE_PATTERNS.search(title):
        return True
    if files and _only_doc_files(files):
        return True
    if body and len(body.strip()) < 20 and (not files or len(files) <= 2):
        return True
    return False


def is_irrelevant_commit(message: str, files: list[str] | None = None) -> bool:
    first_line = message.splitlines()[0] if message else ""
    if IRRELEVANT_COMMIT_PATTERNS.search(first_line):
        return True
    if files and _only_doc_files(files):
        return True
    return False


def is_irrelevant_issue(title: str, labels: list[str] | None = None) -> bool:
    if IRRELEVANT_TITLE_PATTERNS.search(title):
        return True
    if labels and any(label.lower() in {"duplicate", "wontfix", "invalid"} for label in labels):
        return True
    return False


def _only_doc_files(files: list[str]) -> bool:
    if not files:
        return False
    return all(any(path.endswith(ext) for ext in DOC_ONLY_EXTENSIONS) for path in files)


def detect_query_categories(query: str) -> set[str]:
    lowered = query.lower()
    categories: set[str] = set()
    for category, keywords in QUERY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            categories.add(category.value)
    if not categories:
        categories = {"prs", "commits", "issues", "readme", "repo_structure"}
    return categories
