import json
import logging
import re
from pathlib import Path
from typing import Any

from app.processing.constants import ArtifactCategory
from app.processing.schemas import NormalizedArtifact

MODULE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"auth|login|oauth|jwt|session", re.I), "Authentication"),
    (re.compile(r"cache|redis|memcache", re.I), "Caching"),
    (re.compile(r"db|database|sql|migration|model", re.I), "Database"),
    (re.compile(r"api|route|endpoint|middleware", re.I), "API"),
    (re.compile(r"test|spec", re.I), "Testing"),
    (re.compile(r"config|settings|env", re.I), "Configuration"),
    (re.compile(r"docker|deploy|ci|cd|pipeline", re.I), "Infrastructure"),
    (re.compile(r"ui|frontend|component|page", re.I), "Frontend"),
]


def normalize_readme(content: str, repo_full_name: str) -> NormalizedArtifact:
    print("in normalize readme")
    return NormalizedArtifact(
        artifact_type="readme",
        source_id="readme",
        category=ArtifactCategory.README.value,
        repo=repo_full_name,
        title="README",
        summary="Repository documentation",
        body=content[:50000],
        module="Documentation",
        change_type="Documentation",
    )


def normalize_repo_structure(
    tree: list[dict[str, Any]], repo_full_name: str, tech_stack: list[str] | None = None
) -> NormalizedArtifact:
    print("normalize repo structure")
    return NormalizedArtifact(
        artifact_type="repo_structure",
        source_id="repo_structure",
        category=ArtifactCategory.REPO_STRUCTURE.value,
        repo=repo_full_name,
        title="Repository structure",
        summary=f"Repository layout with {len(tree)} entries",
        body=json.dumps({"tree": tree, "tech_stack": tech_stack or []}, indent=2)[:50000],
        languages=tech_stack or [],
        module="Architecture",
        change_type="Structure",
        metadata={"tech_stack": tech_stack or [], "entry_count": len(tree)},
    )


def normalize_pull_request(pr: dict[str, Any], repo_full_name: str) -> NormalizedArtifact:
    print("normalize pr")
    user = pr.get("user") or {}
    labels = [label.get("name", "") for label in pr.get("labels", []) if label.get("name")]
    files = pr.get("changed_files")
    files_list: list[str] = []
    if isinstance(files, int):
        files_list = [f"{files} files changed"]
    reviewers = _extract_reviewers(pr)
    status = "Merged" if pr.get("merged_at") else pr.get("state", "open").title()
    title = pr.get("title") or ""

    return NormalizedArtifact(
        artifact_type="pull_request",
        source_id=str(pr["number"]),
        category=ArtifactCategory.PRS.value,
        repo=repo_full_name,
        title=title,
        summary=title,
        author=user.get("login"),
        timestamp=pr.get("merged_at") or pr.get("created_at"),
        body=(pr.get("body") or "")[:20000],
        pr_number=pr.get("number"),
        status=status,
        labels=labels,
        reviewers=reviewers,
        files_changed=files_list,
        module=_infer_module(title, files_list),
        change_type=_infer_change_type(title),
        github_url=pr.get("html_url"),
        metadata={"merged": bool(pr.get("merged_at")), "url": pr.get("html_url")},
    )


def normalize_issue(issue: dict[str, Any], repo_full_name: str) -> NormalizedArtifact:
    print("normalize issue")
    user = issue.get("user") or {}
    labels = [label.get("name", "") for label in issue.get("labels", []) if label.get("name")]
    title = issue.get("title") or ""

    return NormalizedArtifact(
        artifact_type="issue",
        source_id=str(issue["number"]),
        category=ArtifactCategory.ISSUES.value,
        repo=repo_full_name,
        title=title,
        summary=title,
        author=user.get("login"),
        timestamp=issue.get("created_at"),
        body=(issue.get("body") or "")[:20000],
        status=issue.get("state"),
        labels=labels,
        module=_infer_module(title, []),
        change_type="Bugfix" if any("bug" in label.lower() for label in labels) else "Issue",
        github_url=issue.get("html_url"),
        metadata={"url": issue.get("html_url")},
    )


def normalize_commit(
    commit: dict[str, Any], repo_full_name: str, branch: str | None = None
) -> NormalizedArtifact:
    print("normalize commit")
    commit_data = commit.get("commit") or {}
    author = commit_data.get("author") or {}
    sha = commit.get("sha", "")
    message = commit_data.get("message") or ""
    summary = message.splitlines()[0][:200] if message else sha[:8]
    pr_number = _extract_pr_number(message)
    files = [f.get("filename", "") for f in commit.get("files", []) if f.get("filename")]

    return NormalizedArtifact(
        artifact_type="commit",
        source_id=sha,
        category=ArtifactCategory.COMMITS.value,
        repo=repo_full_name,
        branch=branch,
        title=summary,
        summary=summary,
        author=author.get("name") or (commit.get("author") or {}).get("login"),
        timestamp=author.get("date"),
        body=message[:20000],
        files_changed=files,
        languages=_infer_languages_from_files(files),
        module=_infer_module(summary, files),
        change_type=_infer_change_type(summary),
        github_url=commit.get("html_url"),
        pr_number=pr_number,
        metadata={"url": commit.get("html_url"), "sha": sha},
    )


def normalize_release(release: dict[str, Any], repo_full_name: str) -> NormalizedArtifact:
    print("normalize release")
    title = release.get("name") or release.get("tag_name") or "Release"
    return NormalizedArtifact(
        artifact_type="release",
        source_id=release.get("tag_name") or str(release.get("id")),
        category=ArtifactCategory.RELEASE.value,
        repo=repo_full_name,
        title=title,
        summary=title,
        timestamp=release.get("published_at"),
        body=(release.get("body") or "")[:20000],
        module="Release",
        change_type="Release",
        github_url=release.get("html_url"),
        metadata={"tag": release.get("tag_name"), "url": release.get("html_url")},
    )


def walk_local_tree(clone_path: Path, max_depth: int = 4) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    ignore = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".pytest_cache"}

    def _walk(path: Path, depth: int, prefix: str) -> None:
        if depth > max_depth:
            return
        try:
            children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return
        for child in children:
            if child.name in ignore:
                continue
            rel = f"{prefix}{child.name}"
            entries.append({"path": rel, "type": "dir" if child.is_dir() else "file"})
            if child.is_dir():
                _walk(child, depth + 1, f"{rel}/")

    if clone_path.exists():
        _walk(clone_path, 0, "")
    return entries[:500]


def detect_tech_stack(clone_path: Path) -> list[str]:
    markers = {
        "package.json": "Node.js",
        "pyproject.toml": "Python",
        "requirements.txt": "Python",
        "go.mod": "Go",
        "Cargo.toml": "Rust",
        "pom.xml": "Java",
        "build.gradle": "Java/Kotlin",
        "Dockerfile": "Docker",
        "docker-compose.yml": "Docker Compose",
        "tsconfig.json": "TypeScript",
    }
    return [tech for filename, tech in markers.items() if (clone_path / filename).exists()]


def read_local_readme(clone_path: Path) -> str | None:
    print("normalizer readme")
    for name in ("README.md", "README.MD", "readme.md", "README.rst", "README"):
        path = clone_path / name
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")
    return None


def _extract_pr_number(message: str) -> int | None:
    match = re.search(r"#(\d+)", message)
    return int(match.group(1)) if match else None


def _extract_reviewers(pr: dict[str, Any]) -> list[str]:
    reviewers: list[str] = []
    for review in pr.get("requested_reviewers") or []:
        login = review.get("login")
        if login:
            reviewers.append(login)
    return reviewers


def _infer_module(text: str, files: list[str]) -> str:
    corpus = " ".join([text, *files])
    for pattern, module in MODULE_PATTERNS:
        if pattern.search(corpus):
            return module
    if files:
        top = files[0].split("/")[0]
        return top.replace("_", " ").replace("-", " ").title()
    return "General"


def _infer_change_type(text: str) -> str:
    print("infer change type...")
    lowered = text.lower()
    if any(w in lowered for w in ("fix", "bug", "patch")):
        return "Bugfix"
    if any(w in lowered for w in ("refactor", "replace", "migrate", "restructure")):
        return "Refactor"
    if any(w in lowered for w in ("optimize", "performance", "cache", "latency")):
        return "Performance"
    if any(w in lowered for w in ("feat", "add", "implement", "introduce")):
        return "Feature"
    if any(w in lowered for w in ("doc", "readme")):
        return "Documentation"
    if any(w in lowered for w in ("ci", "docker", "deploy", "infra")):
        return "Infrastructure"
    return "Change"


def _infer_languages_from_files(files: list[str]) -> list[str]:
    ext_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".rb": "Ruby",
        ".php": "PHP",
        ".cs": "C#",
    }
    langs: list[str] = []
    for path in files:
        for ext, lang in ext_map.items():
            if path.endswith(ext) and lang not in langs:
                langs.append(lang)
    return langs
