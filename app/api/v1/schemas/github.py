from pydantic import BaseModel


class GitHubConnectResponse(BaseModel):
    authorize_url: str
