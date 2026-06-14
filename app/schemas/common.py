from pydantic import BaseModel


class MessageOut(BaseModel):
    message: str


class DbHealthOut(BaseModel):
    status: str
    database: str
    public_table_count: int
