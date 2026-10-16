from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    posted_date: datetime
    experience_level: Optional[str]
    employment_type: Optional[str]
    skills: List[str] = Field(default_factory=list)

class JobResponse(BaseModel):
    jobs: List[Job]
    total: int
    page: int
    per_page: int