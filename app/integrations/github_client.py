from typing import Any
from urllib.parse import urlencode
import httpx
from app.core.config import get_settings


class GitHubClient:
    BASE_URL = "https://api.github.com"
    OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"

    def __init__(self, access_token: str | None = None) -> None:
        self._access_token = access_token
        self._settings = get_settings()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    def get_authorize_url(self, state: str) -> str:
        params = {
            "client_id": self._settings.GITHUB_CLIENT_ID,
            "redirect_uri": self._settings.GITHUB_REDIRECT_URI,
            "scope": self._settings.GITHUB_OAUTH_SCOPES,
            "state": state,
        }
        return f"{self.OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                headers={"Accept": "application/json"},
                json={
                    "client_id": self._settings.GITHUB_CLIENT_ID,
                    "client_secret": self._settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": self._settings.GITHUB_REDIRECT_URI,
                },
            )
            response.raise_for_status()
            data = response.json()
            access_token = data.get("access_token")
            if not access_token:
                raise ValueError(data.get("error_description", "Failed to obtain GitHub token"))
            return access_token

    async def get_authenticated_user(self) -> dict[str, Any]:
        return await self._get("/user")

    async def list_repositories(self, page: int = 1, per_page: int = 100) -> list[dict[str, Any]]:
        return await self._get(
            "/user/repos",
            params={
                "page": page,
                "per_page": per_page,
                "sort": "updated",
                "affiliation": "owner,collaborator,organization_member",
            },
        )

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        return await self._get(f"/repos/{owner}/{repo}")

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self.BASE_URL, timeout=30.0) as client:
            response = await client.get(path, headers=self._headers(), params=params)
            response.raise_for_status()
            return response.json()
