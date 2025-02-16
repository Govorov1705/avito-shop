from pydantic import BaseModel


class ErrorResponse(BaseModel):
    errors: str
