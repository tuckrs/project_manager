from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from .models.task import TaskPriority, DependencyType, TaskStatus

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    earliest_start_date: Optional[datetime] = None
    latest_start_date: Optional[datetime] = None
    duration: Optional[float] = None
    work_hours: float = Field(default=0, ge=0)  # Must be non-negative
    is_milestone: bool = False
    is_locked: bool = False
    parent_id: Optional[int] = None
    project_id: int
    status: TaskStatus = TaskStatus.NOT_STARTED
    progress: float = Field(default=0, ge=0, le=100)  # Between 0 and 100

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    unique_id: str
    actual_start_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    class Config:
        orm_mode = True

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    tasks: List[Task] = []

    class Config:
        orm_mode = True

class DependencyBase(BaseModel):
    predecessor_id: int
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag_time: float = 0

class DependencyCreate(DependencyBase):
    pass

class Dependency(DependencyBase):
    id: int
    successor_id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: str = "Viewer"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class ResourceBase(BaseModel):
    name: str
    email: str
    role: Optional[str] = None
    cost_per_hour: float = 0

class ResourceCreate(ResourceBase):
    pass

class Resource(ResourceBase):
    id: int

    class Config:
        orm_mode = True

class TaskResourceAssignmentBase(BaseModel):
    resource_id: int
    assigned_hours: float

class TaskResourceAssignmentCreate(TaskResourceAssignmentBase):
    pass

class TaskResourceAssignment(TaskResourceAssignmentBase):
    id: int
    task_id: int

    class Config:
        orm_mode = True

# Response schemas for specific operations
class ScheduleResponse(BaseModel):
    project_id: int
    critical_path: List[int]
    project_duration: float
    task_schedules: dict

class GanttTaskResponse(BaseModel):
    id: int
    title: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    duration: Optional[float]
    progress: float
    parent: Optional[int]
    dependencies: List[int]
    work_hours: float
    assigned_resources: List[str]  # Resource names
