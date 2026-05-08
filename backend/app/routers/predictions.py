from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, DataBatch, StudentRecord, PredictionLog, Intervention, StudentProgress
from ..schemas import BatchPredictionResponse, PredictionResult, AutoInterventionResponse, ApplyInterventionsRequest
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
            
            # Store previous risk score for progress tracking
            previous_risk = record.failure_risk_score
            
            # Update record
            record.failure_risk_score = explanation['risk_score']
            record.risk_level = explanation['risk_level']
            record.shap_values = explanation['shap_values']
            record.top_risk_factors = explanation['top_risk_factors']
            
            # Create progress snapshot
            active_interventions = db.query(Intervention).filter(
                Intervention.student_record_id == record.id,
                Intervention.status.in_(['Pending', 'In Progress'])
            ).count()
            completed_interventions = db.query(Intervention).filter(
                Intervention.student_record_id == record.id,
                Intervention.status == 'Completed'
            ).count()
            
            progress = StudentProgress(
                student_record_id=record.id,
                batch_id=batch_id,
                risk_score=explanation['risk_score'],
                risk_level=explanation['risk_level'],
                previous_risk_score=previous_risk,
                risk_change=(explanation['risk_score'] - previous_risk) if previous_risk is not None else None,
                semester=batch.semester,
                academic_year=batch.academic_year,
                active_interventions_count=active_interventions,
                completed_interventions_count=completed_interventions,
            )
            db.add(progress)
            
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

@router.get("/student/{student_record_id}/shap-plot")
def get_student_shap_plot(
    student_record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Generate SHAP waterfall plot for a single student (base64 PNG)"""
    record = db.query(StudentRecord).filter(StudentRecord.id == student_record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Student record not found")
    
    student_data = {
        'student_id': record.student_id,
        'student_name': record.student_name,
        'attendance_percentage': record.attendance_percentage or 50.0,
        'assignment_avg': record.assignment_avg or 50.0,
        'midterm_score': record.midterm_score or 50.0,
        'quiz_avg': record.quiz_avg or 50.0,
        'lab_score': record.lab_score or 50.0,
        'previous_gpa': record.previous_gpa or 2.5,
        'study_hours_per_week': record.study_hours_per_week or 10.0,
        'extracurricular_activities': record.extracurricular_activities or 0,
        'socioeconomic_status': record.socioeconomic_status or 'Medium',
        'parent_education': record.parent_education or 'Bachelor',
        'internet_access': record.internet_access if record.internet_access is not None else 1
    }
    
    explainer = get_explainer()
    plot_base64 = explainer.generate_shap_plot(student_data)
    
    return {"plot": plot_base64, "student_name": record.student_name}

@router.get("/batch/{batch_id}/shap-summary")
def get_batch_shap_summary(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Generate SHAP summary plot for an entire batch (base64 PNG)"""
    records = db.query(StudentRecord).filter(StudentRecord.batch_id == batch_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="No student records found in batch")
    
    students_data = []
    for record in records:
        students_data.append({
            'attendance_percentage': record.attendance_percentage or 50.0,
            'assignment_avg': record.assignment_avg or 50.0,
            'midterm_score': record.midterm_score or 50.0,
            'quiz_avg': record.quiz_avg or 50.0,
            'lab_score': record.lab_score or 50.0,
            'previous_gpa': record.previous_gpa or 2.5,
            'study_hours_per_week': record.study_hours_per_week or 10.0,
            'extracurricular_activities': record.extracurricular_activities or 0,
            'socioeconomic_status': record.socioeconomic_status or 'Medium',
            'parent_education': record.parent_education or 'Bachelor',
            'internet_access': record.internet_access if record.internet_access is not None else 1
        })
    
    explainer = get_explainer()
    plot_base64 = explainer.generate_batch_summary_plot(students_data)
    
    return {"plot": plot_base64, "total_students": len(records)}

@router.post("/apply-interventions")
def apply_recommended_interventions(
    request: ApplyInterventionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Apply auto-generated interventions for a student (one-click apply)"""
    # Verify student exists
    student = db.query(StudentRecord).filter(
        StudentRecord.id == request.student_record_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")
    
    created = []
    for inv_data in request.interventions:
        intervention = Intervention(
            student_record_id=request.student_record_id,
            assigned_by=current_user.id,
            intervention_type=inv_data.get('type', 'counseling'),
            title=inv_data.get('title', 'Auto-generated intervention'),
            description=inv_data.get('description', ''),
            action_items=inv_data.get('action_items', []),
            priority=inv_data.get('priority', 'Medium'),
            scheduled_date=datetime.fromisoformat(inv_data['scheduled_date']) if inv_data.get('scheduled_date') else None,
            follow_up_date=datetime.fromisoformat(inv_data['follow_up_date']) if inv_data.get('follow_up_date') else None,
        )
        db.add(intervention)
        created.append(intervention)
    
    db.commit()
    
    return {
        "message": f"Applied {len(created)} interventions for {student.student_name}",
        "count": len(created),
        "student_id": student.student_id,
        "student_name": student.student_name
    }

@router.get("/student/{student_record_id}/progress")
def get_student_progress(
    student_record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Get risk score history for a student over time"""
    progress = db.query(StudentProgress).filter(
        StudentProgress.student_record_id == student_record_id
    ).order_by(StudentProgress.snapshot_date.asc()).all()
    
    return [
        {
            "id": p.id,
            "risk_score": p.risk_score,
            "risk_level": p.risk_level,
            "previous_risk_score": p.previous_risk_score,
            "risk_change": p.risk_change,
            "semester": p.semester,
            "academic_year": p.academic_year,
            "active_interventions": p.active_interventions_count,
            "completed_interventions": p.completed_interventions_count,
            "date": p.snapshot_date.isoformat() if p.snapshot_date else None
        }
        for p in progress
    ]
