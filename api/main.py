from fastapi import FastAPI, HTTPException
from api.schemas import TaskInput, TaskResponse
from logging_config import setup_logger

logger = setup_logger()

app = FastAPI(
    title="Task Management API",
    description="FastAPI project with Git, logging, and validation",
    version="1.0.0"
)

tasks = []


@app.get("/")
def home():
    logger.info("Home endpoint accessed")
    return {"message": "Task Management API is running"}


@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: TaskInput):
    logger.info("Creating a new task")

    new_task = {
        "id": len(tasks) + 1,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": "pending"
    }

    tasks.append(new_task)

    logger.info("Task created successfully | id=%s", new_task["id"])

    return new_task


@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks():
    logger.info("Retrieving all tasks")
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    logger.info("Retrieving task | id=%s", task_id)

    for task in tasks:
        if task["id"] == task_id:
            return task

    logger.warning("Task not found | id=%s", task_id)

    raise HTTPException(
        status_code=404,
        detail="Task not found"
    )