from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'faculty', 'hod', 'admin'
    department = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    uploaded_batches = relationship("DataBatch", back_populates="uploaded_by_user")
    interventions = relationship("Intervention", back_populates="assigned_by_user")

class DataBatch(Base):
    __tablename__ = "data_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_name = Column(String, nullable=False)
    semester = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String, nullable=False)
    total_students = Column(Integer, default=0)
    at_risk_count = Column(Integer, default=0)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    uploaded_by_user = relationship("User", back_populates="uploaded_batches")
    student_records = relationship("StudentRecord", back_populates="batch")

class StudentRecord(Base):
    __tablename__ = "student_records"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("data_batches.id"))
    student_id = Column(String, nullable=False, index=True)
    student_name = Column(String, nullable=False)
    
    # Features
    attendance_percentage = Column(Float, nullable=True)
    assignment_avg = Column(Float, nullable=True)
    midterm_score = Column(Float, nullable=True)
    quiz_avg = Column(Float, nullable=True)
    lab_score = Column(Float, nullable=True)
    previous_gpa = Column(Float, nullable=True)
    study_hours_per_week = Column(Float, nullable=True)
    extracurricular_activities = Column(Integer, default=0)
    socioeconomic_status = Column(String, nullable=True)
    parent_education = Column(String, nullable=True)
    internet_access = Column(Integer, default=1)
    
    # Prediction Results
    failure_risk_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)  # 'Low', 'Medium', 'High', 'Critical'
    shap_values = Column(JSON, nullable=True)
    top_risk_factors = Column(JSON, nullable=True)
    
    # Relationships
    batch = relationship("DataBatch", back_populates="student_records")
    interventions = relationship("Intervention", back_populates="student")

class Intervention(Base):
    __tablename__ = "interventions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_record_id = Column(Integer, ForeignKey("student_records.id"))
    assigned_by = Column(Integer, ForeignKey("users.id"))
    
    intervention_type = Column(String, nullable=False)  # 'counseling', 'extra_class', 'study_plan', 'peer_mentoring', 'parent_meeting'
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    action_items = Column(JSON, nullable=True)
    priority = Column(String, default="Medium")  # 'Low', 'Medium', 'High', 'Urgent'
    status = Column(String, default="Pending")  # 'Pending', 'In Progress', 'Completed', 'Cancelled'
    
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    
    notes = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("StudentRecord", back_populates="interventions")
    assigned_by_user = relationship("User", back_populates="interventions")

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("data_batches.id"))
    model_version = Column(String, nullable=True)
    total_predictions = Column(Integer, default=0)
    high_risk_count = Column(Integer, default=0)
    medium_risk_count = Column(Integer, default=0)
    low_risk_count = Column(Integer, default=0)
    model_accuracy = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DashboardMetrics(Base):
    __tablename__ = "dashboard_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    department = Column(String, nullable=True)
    semester = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    
    total_students = Column(Integer, default=0)
    at_risk_students = Column(Integer, default=0)
    intervention_success_rate = Column(Float, default=0)
    avg_improvement_score = Column(Float, default=0)
    
    risk_trend_data = Column(JSON, nullable=True)
    department_risk_data = Column(JSON, nullable=True)
    intervention_type_distribution = Column(JSON, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow)
