from pydantic import BaseModel


class FileInfoModel(BaseModel):
    uid: str
    description: str | None = None
