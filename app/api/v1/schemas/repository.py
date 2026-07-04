from datetime import datetime

from pydantic import BaseModel, Field

from app.models.repository import Status, Visibility


class GitHubRepoResponse(BaseModel):
    github_repo_id: str
    name: str
    full_name: str
    url: str
    clone_url: str
    default_branch: str | None
    visibility: Visibility
    is_owner: bool


class RepositoryCreateRequest(BaseModel):
    full_name: str = Field(..., description="GitHub repository in owner/repo format")


class RepositoryResponse(BaseModel):
    id: int
    name: str
    full_name: str
    github_repo_id: str
    url: str
    status: Status
    visibility: Visibility
    default_branch: str | None
    current_branch: str | None
    is_owner: bool
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
