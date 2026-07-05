from pathlib import Path
from app.processing.schemas import MergedKnowledgeObject, CodeKnowledge
from app.integrations.cognee_client import cognee_client
from app.core.config import get_settings
settings = get_settings()

ARCHITECTURE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".java",
    ".go",
    ".rs",
    ".kt",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
}

SKIP_NAMES = {
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "pnpm-lock.yaml",
    "uv.lock"
}

class CodeAnalyzer:
    async def analyze(
        self,
        repo_path: Path,
        merged: MergedKnowledgeObject,
    ) -> list[CodeKnowledge]:
        print("in code analyze")
        knowledge = []

        for relative_file in merged.files:
            absolute_path = repo_path / relative_file

            if not absolute_path.exists():
                continue

            if Path(relative_file).name in SKIP_NAMES:
                continue

            suffix = Path(relative_file).suffix.lower()

            if suffix not in ARCHITECTURE_EXTENSIONS:
                continue

            result = await cognee_client.analyze_file_with_llm(
                absolute_path
            )
            knowledge.append(result)
        return knowledge

code_analyzer = CodeAnalyzer()