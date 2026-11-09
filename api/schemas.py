from pydantic import BaseModel, Field, ConfigDict


class TaskInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=5, max_length=500)
    priority: int = Field(ge=1, le=5)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: int
    status: str