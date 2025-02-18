import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from .models.task import Task, TaskDependency, Project, User, Resource, TaskResourceAssignment
from .services.scheduler import ProjectScheduler
from .database import SessionLocal, engine, Base
from . import schemas

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Project Management API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Resource endpoints
@app.post("/resources/", response_model=schemas.Resource)
def create_resource(resource: schemas.ResourceCreate, db: Session = Depends(get_db)):
    db_resource = Resource(**resource.dict())
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource

@app.get("/resources/", response_model=List[schemas.Resource])
def list_resources(db: Session = Depends(get_db)):
    return db.query(Resource).all()

@app.get("/resources/{resource_id}", response_model=schemas.Resource)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource

# Project endpoints
@app.post("/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[schemas.Project])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()

@app.get("/projects/{project_id}", response_model=schemas.Project)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# Task endpoints
@app.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    # Extract resource assignments
    resource_assignments = task.resource_assignments
    task_dict = task.dict(exclude={'resource_assignments'})
    
    # Create task
    db_task = Task(**task_dict)
    db.add(db_task)
    db.flush()  # Get task ID without committing
    
    # Create resource assignments
    if resource_assignments:
        for assignment in resource_assignments:
            db_assignment = TaskResourceAssignment(
                task_id=db_task.id,
                **assignment.dict()
            )
            db.add(db_assignment)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(
    task_id: int,
    task_update: schemas.TaskCreate,
    db: Session = Depends(get_db)
):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update task fields
    for key, value in task_update.dict(exclude={'resource_assignments'}).items():
        setattr(db_task, key, value)
    
    # Update resource assignments
    if task_update.resource_assignments is not None:
        # Remove existing assignments
        db.query(TaskResourceAssignment).filter(
            TaskResourceAssignment.task_id == task_id
        ).delete()
        
        # Create new assignments
        for assignment in task_update.resource_assignments:
            db_assignment = TaskResourceAssignment(
                task_id=task_id,
                **assignment.dict()
            )
            db.add(db_assignment)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@app.post("/tasks/{task_id}/dependencies/")
def create_dependency(
    task_id: int,
    dependency: schemas.DependencyCreate,
    db: Session = Depends(get_db)
):
    # Verify tasks exist
    if not db.query(Task).filter(Task.id == task_id).first():
        raise HTTPException(status_code=404, detail="Task not found")
    if not db.query(Task).filter(Task.id == dependency.predecessor_id).first():
        raise HTTPException(status_code=404, detail="Predecessor task not found")
    
    db_dependency = TaskDependency(
        successor_id=task_id,
        **dependency.dict()
    )
    db.add(db_dependency)
    
    # Check for circular dependencies
    scheduler = ProjectScheduler()
    tasks = db.query(Task).all()
    dependencies = db.query(TaskDependency).all()
    scheduler.build_dependency_graph(tasks, dependencies)
    
    if scheduler.detect_cycles():
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="This dependency would create a circular reference"
        )
    
    db.commit()
    return {"status": "success"}

@app.post("/projects/{project_id}/schedule")
def calculate_project_schedule(project_id: int, db: Session = Depends(get_db)):
    # Get project tasks and dependencies
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="Project not found or has no tasks")
    
    dependencies = (
        db.query(TaskDependency)
        .filter(TaskDependency.successor_id.in_([t.id for t in tasks]))
        .all()
    )
    
    # Calculate schedule
    scheduler = ProjectScheduler()
    scheduler.build_dependency_graph(tasks, dependencies)
    
    try:
        schedule = scheduler.calculate_critical_path()
        return {
            "project_id": project_id,
            "critical_path": schedule["critical_path"],
            "project_duration": schedule["project_duration"],
            "task_schedules": schedule["schedule"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_id}/gantt")
def get_gantt_data(project_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="Project not found or has no tasks")
    
    return [{
        "id": task.id,
        "title": task.title,
        "start_date": task.actual_start_date or task.earliest_start_date,
        "end_date": task.actual_end_date,
        "duration": task.duration,
        "progress": task.progress,
        "parent": task.parent_id,
        "work_hours": task.work_hours,
        "assigned_resources": [
            assignment.resource.name
            for assignment in task.resource_assignments
        ],
        "dependencies": [
            dep.predecessor_id
            for dep in db.query(TaskDependency)
            .filter(TaskDependency.successor_id == task.id)
            .all()
        ]
    } for task in tasks]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
