from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str
    role: str  # 'faculty', 'hod', 'admin'
    department: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: str
    department: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None

# Student Data Schemas
class StudentDataInput(BaseModel):
    student_id: str
    student_name: str
    attendance_percentage: float
    assignment_avg: float
    midterm_score: Optional[float] = None
    quiz_avg: Optional[float] = None
    lab_score: Optional[float] = None
    previous_gpa: Optional[float] = None
    study_hours_per_week: Optional[float] = None
    extracurricular_activities: Optional[int] = 0
    socioeconomic_status: Optional[str] = None
    parent_education: Optional[str] = None
    internet_access: Optional[int] = 1

class StudentDataBatch(BaseModel):
    batch_name: str
    semester: str
    academic_year: str
    subject: str
    students: List[StudentDataInput]

# Prediction Schemas
class PredictionResult(BaseModel):
    student_id: str
    student_name: str
    failure_risk_score: float
    risk_level: str
    top_risk_factors: List[Dict[str, Any]]
    shap_contribution: Dict[str, float]

class BatchPredictionResponse(BaseModel):
    batch_id: int
    total_students: int
    at_risk_count: int
    risk_distribution: Dict[str, int]
    predictions: List[PredictionResult]

# Intervention Schemas
class InterventionCreate(BaseModel):
    student_record_id: int
    intervention_type: str
    title: str
    description: Optional[str] = None
    action_items: Optional[List[str]] = None
    priority: str = "Medium"
    scheduled_date: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None

class InterventionUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None
    completed_date: Optional[datetime] = None

class InterventionResponse(BaseModel):
    id: int
    student_record_id: int
    assigned_by: int
    intervention_type: str
    title: str
    description: Optional[str]
    action_items: Optional[List[str]]
    priority: str
    status: str
    scheduled_date: Optional[datetime]
    completed_date: Optional[datetime]
    follow_up_date: Optional[datetime]
    notes: Optional[str]
    outcome: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AutoInterventionResponse(BaseModel):
    student_id: str
    student_name: str
    risk_level: str
    recommended_interventions: List[Dict[str, Any]]

# Dashboard Schemas
class DashboardOverview(BaseModel):
    total_students: int
    at_risk_students: int
    at_risk_percentage: float
    risk_distribution: Dict[str, int]
    intervention_stats: Dict[str, Any]
    recent_predictions: List[Dict[str, Any]]

class RiskTrend(BaseModel):
    dates: List[str]
    values: List[int]
