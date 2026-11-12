from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr


class Experience(BaseModel):
    role: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None


class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None


class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: list[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    email: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    total_experience_years: Optional[float] = Field(default=None, ge=0, le=60)


class JobRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_title: str = Field(min_length=1, max_length=120)
    required_skills: list[str] = Field(default_factory=list, max_length=100)
    preferred_skills: list[str] = Field(default_factory=list, max_length=100)
    minimum_experience_years: Optional[float] = Field(default=None, ge=0, le=60)
    education_requirement: Optional[str] = Field(default=None, max_length=200)


class CandidateComparisonRequest(BaseModel):
    candidates: list[CandidateProfile] = Field(min_length=1, max_length=100)
    job: JobRequirements
