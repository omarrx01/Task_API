
import json

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from redis.exceptions import RedisError

from api.schemas import TaskInput, TaskResponse
from api.database import get_db
from api.models import Task
from api.redis_client import redis_client
from logging_config import setup_logger


logger = setup_logger()

app = FastAPI(
    title="Task Management API",
    description="FastAPI project with PostgreSQL, Redis, Docker, logging, and validation",
    version="1.0.0"
)


# ----------------------------------------
# Redis cache helper
# ----------------------------------------

def clear_tasks_cache():
    try:
        redis_client.delete("tasks:all")
        logger.info("Redis cache invalidated")
    except RedisError as error:
        logger.warning("Redis cache invalidation failed: %s", error)


# ----------------------------------------
# Home
# ----------------------------------------

@app.get("/")
def home():
    logger.info("Home endpoint accessed")
    return {"message": "Task Management API is running"}


# ----------------------------------------
# CREATE TASK
# ----------------------------------------

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

    clear_tasks_cache()

    logger.info("Task created successfully | id=%s", new_task.id)

    return new_task


# ----------------------------------------
# READ ALL TASKS (REDIS CACHE)
# ----------------------------------------

@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    logger.info("Retrieving all tasks")

    cache_key = "tasks:all"

    # Step 1: Check Redis
    try:
        cached_tasks = redis_client.get(cache_key)

        if cached_tasks is not None:
            logger.info("CACHE HIT: Returning tasks from Redis")
            return json.loads(cached_tasks)

    except (RedisError, ValueError) as error:
        logger.warning("Redis cache read failed: %s", error)

    # Step 2: Retrieve tasks from PostgreSQL
    logger.info("CACHE MISS: Retrieving tasks from PostgreSQL")

    tasks = db.query(Task).order_by(Task.id).all()

    task_data = [
        TaskResponse.model_validate(
            task,
            from_attributes=True
        ).model_dump()
        for task in tasks
    ]

    # Step 3: Store results in Redis for 60 seconds
    try:
        redis_client.setex(
            cache_key,
            60,
            json.dumps(task_data)
        )
        logger.info("Tasks cached in Redis for 60 seconds")

    except RedisError as error:
        logger.warning("Redis cache write failed: %s", error)

    return task_data


# ----------------------------------------
# READ SINGLE TASK
# ----------------------------------------

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    logger.info("Retrieving task | id=%s", task_id)

    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        logger.warning("Task not found | id=%s", task_id)
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


# ----------------------------------------
# UPDATE TASK
# ----------------------------------------

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
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    task.title = updated_task.title
    task.description = updated_task.description
    task.priority = updated_task.priority

    db.commit()
    db.refresh(task)

    clear_tasks_cache()

    logger.info("Task updated successfully | id=%s", task_id)

    return task


# ----------------------------------------
# DELETE TASK
# ----------------------------------------

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    logger.info("Deleting task | id=%s", task_id)

    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        logger.warning("Task not found | id=%s", task_id)
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    db.delete(task)
    db.commit()

    clear_tasks_cache()

    logger.info("Task deleted successfully | id=%s", task_id)
