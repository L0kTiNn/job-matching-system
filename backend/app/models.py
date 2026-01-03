"""Pydantic модели для API"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ResumeCreate(BaseModel):
    """Модель для создания резюме"""
    user_id: int
    title: str = Field(..., min_length=1, max_length=255)
    summary: Optional[str] = None
    skills: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    desired_position: Optional[str] = None
    desired_salary: Optional[int] = None
    location: Optional[str] = None


class VacancyCreate(BaseModel):
    """Модель для создания вакансии"""
    employer_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: str
    requirements: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Модель ответа с рекомендацией"""
    id: int
    title: str
    description: Optional[str] = None
    similarity: float
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None


class ResumeResponse(BaseModel):
    """Модель ответа с резюме"""
    id: int
    title: str
    summary: Optional[str] = None
    skills: Optional[str] = None
    desired_salary: Optional[int] = None
    location: Optional[str] = None

class ResumeUpdate(BaseModel):
    """Модель для обновления резюме"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    summary: Optional[str] = None
    skills: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    desired_position: Optional[str] = None
    desired_salary: Optional[int] = None
    location: Optional[str] = None


class ResumeDetailResponse(BaseModel):
    """Полная модель резюме для просмотра"""
    id: int
    user_id: int
    title: str
    summary: Optional[str] = None
    skills: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    desired_position: Optional[str] = None
    desired_salary: Optional[int] = None
    location: Optional[str] = None
    created_at: Optional[str] = None

class VacancyUpdate(BaseModel):
    """Модель для обновления вакансии"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None


class VacancyDetailResponse(BaseModel):
    """Полная модель вакансии для просмотра"""
    id: int
    employer_id: int
    title: str
    description: str
    requirements: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None
    created_at: Optional[str] = None
