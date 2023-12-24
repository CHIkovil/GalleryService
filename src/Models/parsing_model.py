from pydantic import BaseModel
from enum import Enum


class ExtendedEnum(Enum):
    @classmethod
    def set(cls):
        return set(map(lambda c: c.value, cls))


class ParsingType(str, ExtendedEnum):
    images = "images"


class ParsingModel(BaseModel):
    url: str
    type: ParsingType
