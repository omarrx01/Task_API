
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from api.schemas import TaskInput, TaskResponse
from api.database import get_db
from api.models import Task
from logging_config import setup_logger

logger = setup_logger()

app = FastAPI(
    title="Task Management API",
    description="FastAPI project with PostgreSQL, Docker, logging, and validation",
    version="1.0.0"
)


@app.get("/")
def home():
    logger.info("Home endpoint accessed")
    return {"message": "Task Management API is running"}


@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: TaskInput, db: Session = Depends(get_db)):
    logger.info("Creating a new task")

    new_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        status="pending"
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    logger.info("Task created successfully | id=%s", new_task.id)

    return new_task


@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    logger.info("Retrieving all tasks")

    return db.query(Task).order_by(Task.id).all()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    logger.info("Retrieving task | id=%s", task_id)

    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        logger.warning("Task not found | id=%s", task_id)
        raise HTTPException(status_code=404, detail="Task not found")

    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    updated_task: TaskInput,
    db: Session = Depends(get_db)
):
    logger.info("Updating task | id=%s", task_id)

    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        logger.warning("Task not found | id=%s", task_id)
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = updated_task.title
    task.description = updated_task.description
    task.priority = updated_task.priority

    db.commit()
    db.refresh(task)

    logger.info("Task updated successfully | id=%s", task_id)

    return task
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    logger.info("Deleting task | id=%s", task_id)

    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        logger.warning("Task not found | id=%s", task_id)
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    logger.info("Task deleted successfully | id=%s", task_id)