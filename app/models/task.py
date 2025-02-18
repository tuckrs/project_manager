from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class DependencyType(enum.Enum):
    FINISH_TO_START = "FS"
    START_TO_START = "SS"
    FINISH_TO_FINISH = "FF"
    START_TO_FINISH = "SF"

class TaskStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    role = Column(String)
    cost_per_hour = Column(Float, default=0)
    
    # Assignments
    task_assignments = relationship("TaskResourceAssignment", back_populates="resource")

class TaskResourceAssignment(Base):
    __tablename__ = "task_resource_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
    assigned_hours = Column(Float, nullable=False)  # Hours assigned to this resource
    
    task = relationship("Task", back_populates="resource_assignments")
    resource = relationship("Resource", back_populates="task_assignments")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    
    # Scheduling fields
    earliest_start_date = Column(DateTime)
    latest_start_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    duration = Column(Float)  # in days
    work_hours = Column(Float, nullable=False, default=0)  # Total work hours required
    progress = Column(Float, default=0)  # Percentage complete (0-100)
    status = Column(Enum(TaskStatus), default=TaskStatus.NOT_STARTED)
    
    is_milestone = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    
    # Hierarchy
    parent_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)
    children = relationship("Task", backref="parent", remote_side=[id])
    
    # Project association
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    project = relationship("Project", back_populates="tasks")
    
    # Resource assignments
    resource_assignments = relationship("TaskResourceAssignment", back_populates="task")
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    def __repr__(self):
        return f"<Task {self.unique_id}: {self.title}>"

class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    predecessor_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    successor_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    dependency_type = Column(Enum(DependencyType), default=DependencyType.FINISH_TO_START)
    lag_time = Column(Float, default=0)  # in days (can be negative for lead time)
    
    predecessor = relationship("Task", foreign_keys=[predecessor_id])
    successor = relationship("Task", foreign_keys=[successor_id])

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    tasks = relationship("Task", back_populates="project")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)  # Admin, Editor, Viewer
