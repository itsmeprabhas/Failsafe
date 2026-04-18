from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, DataBatch, StudentRecord, PredictionLog
from ..schemas import BatchPredictionResponse, PredictionResult, AutoInterventionResponse
from ..auth import require_role
from ..ml.explainer import get_explainer
from ..ml.intervention_generator import get_intervention_generator
from datetime import datetime
import json

router = APIRouter(prefix="/predictions", tags=["Predictions"])

@router.post("/run/{batch_id}", response_model=BatchPredictionResponse)
def run_predictions(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    # Get batch
    batch = db.query(DataBatch).filter(DataBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get student records
    records = db.query(StudentRecord).filter(StudentRecord.batch_id == batch_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="No student records found in batch")
    
    # Initialize ML components
    explainer = get_explainer()
    generator = get_intervention_generator()
    
    predictions = []
    risk_distribution = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    at_risk_count = 0
    
    for record in records:
        # Prepare student data for prediction
        student_data = {
            'student_id': record.student_id,
            'student_name': record.student_name,
            'attendance_percentage': record.attendance_percentage,
            'assignment_avg': record.assignment_avg,
            'midterm_score': record.midterm_score or 50.0,
            'quiz_avg': record.quiz_avg or 50.0,
            'lab_score': record.lab_score or 50.0,
            'previous_gpa': record.previous_gpa or 2.5,
            'study_hours_per_week': record.study_hours_per_week or 10.0,
            'extracurricular_activities': record.extracurricular_activities,
            'socioeconomic_status': record.socioeconomic_status or 'Medium',
            'parent_education': record.parent_education or 'Bachelor',
            'internet_access': record.internet_access
        }
        
        try:
            # Get explanation
            explanation = explainer.explain_prediction(student_data)
            
            # Update record
            record.failure_risk_score = explanation['risk_score']
            record.risk_level = explanation['risk_level']
            record.shap_values = explanation['shap_values']
            record.top_risk_factors = explanation['top_risk_factors']
            
            # Track distribution
            risk_distribution[explanation['risk_level']] += 1
            if explanation['risk_level'] in ['High', 'Critical']:
                at_risk_count += 1
            
            predictions.append(PredictionResult(
                student_id=record.student_id,
                student_name=record.student_name,
                failure_risk_score=explanation['risk_score'],
                risk_level=explanation['risk_level'],
                top_risk_factors=explanation['top_risk_factors'],
                shap_contribution=explanation['shap_values']
            ))
            
        except Exception as e:
            predictions.append(PredictionResult(
                student_id=record.student_id,
                student_name=record.student_name,
                failure_risk_score=0,
                risk_level="Error",
                top_risk_factors=[{"description": f"Prediction error: {str(e)}"}],
                shap_contribution={}
            ))
    
    # Update batch
    batch.processed = True
    batch.at_risk_count = at_risk_count
    
    # Create prediction log
    log = PredictionLog(
        batch_id=batch_id,
        model_version="1.0.0",
        total_predictions=len(records),
        high_risk_count=risk_distribution['High'] + risk_distribution['Critical'],
        medium_risk_count=risk_distribution['Medium'],
        low_risk_count=risk_distribution['Low']
    )
    db.add(log)
    db.commit()
    
    return BatchPredictionResponse(
        batch_id=batch_id,
        total_students=len(records),
        at_risk_count=at_risk_count,
        risk_distribution=risk_distribution,
        predictions=predictions
    )

@router.get("/interventions/{batch_id}")
def get_auto_interventions(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Get auto-generated interventions for at-risk students in a batch"""
    records = db.query(StudentRecord).filter(
        StudentRecord.batch_id == batch_id,
        StudentRecord.risk_level.in_(['High', 'Critical'])
    ).all()
    
    generator = get_intervention_generator()
    interventions = []
    
    for record in records:
        student_data = {
            'attendance_percentage': record.attendance_percentage,
            'assignment_avg': record.assignment_avg,
            'midterm_score': record.midterm_score,
            'quiz_avg': record.quiz_avg,
            'study_hours_per_week': record.study_hours_per_week,
            'internet_access': record.internet_access
        }
        
        recommended = generator.generate_interventions(
            student_data,
            record.risk_level,
            record.top_risk_factors or []
        )
        
        interventions.append(AutoInterventionResponse(
            student_id=record.student_id,
            student_name=record.student_name,
            risk_level=record.risk_level,
            recommended_interventions=recommended
        ))
    
    return interventions

@router.get("/student/{student_record_id}")
def get_student_prediction(
    student_record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Get detailed prediction for a single student"""
    record = db.query(StudentRecord).filter(StudentRecord.id == student_record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Student record not found")
    
    return {
        "student_id": record.student_id,
        "student_name": record.student_name,
        "failure_risk_score": record.failure_risk_score,
        "risk_level": record.risk_level,
        "shap_values": record.shap_values,
        "top_risk_factors": record.top_risk_factors,
        "features": {
            "attendance_percentage": record.attendance_percentage,
            "assignment_avg": record.assignment_avg,
            "midterm_score": record.midterm_score,
            "quiz_avg": record.quiz_avg,
            "lab_score": record.lab_score,
            "previous_gpa": record.previous_gpa,
            "study_hours_per_week": record.study_hours_per_week,
            "extracurricular_activities": record.extracurricular_activities,
            "socioeconomic_status": record.socioeconomic_status,
            "parent_education": record.parent_education,
            "internet_access": record.internet_access
        }
    }
