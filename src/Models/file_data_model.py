from pydantic import BaseModel


class FileDataModel(BaseModel):
    uid: str
    url: str
    data: bytes
    description: str | None
    parsing_uid: str
