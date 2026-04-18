from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import User, DataBatch, StudentRecord, Intervention
from ..auth import require_role
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    # Total students processed
    total_students = db.query(func.count(StudentRecord.id)).scalar() or 0
    
    # At-risk students (High + Critical)
    at_risk = db.query(func.count(StudentRecord.id)).filter(
        StudentRecord.risk_level.in_(['High', 'Critical'])
    ).scalar() or 0
    
    # Risk distribution
    risk_dist = db.query(
        StudentRecord.risk_level, func.count(StudentRecord.id)
    ).group_by(StudentRecord.risk_level).all()
    
    risk_distribution = {level: count for level, count in risk_dist}
    
    # Batches processed
    batches_processed = db.query(func.count(DataBatch.id)).filter(
        DataBatch.processed == True
    ).scalar() or 0
    
    # Recent predictions (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_predictions = db.query(func.count(StudentRecord.id)).join(
        DataBatch
    ).filter(
        DataBatch.processed == True,
        DataBatch.created_at >= seven_days_ago
    ).scalar() or 0
    
    # Intervention stats
    total_interventions = db.query(func.count(Intervention.id)).scalar() or 0
    completed_interventions = db.query(func.count(Intervention.id)).filter(
        Intervention.status == "Completed"
    ).scalar() or 0
    
    return {
        "total_students": total_students,
        "at_risk_students": at_risk,
        "at_risk_percentage": round((at_risk / total_students * 100), 1) if total_students > 0 else 0,
        "risk_distribution": risk_distribution,
        "batches_processed": batches_processed,
        "recent_predictions": recent_predictions,
        "intervention_stats": {
            "total": total_interventions,
            "completed": completed_interventions,
            "completion_rate": round((completed_interventions / total_interventions * 100), 1) if total_interventions > 0 else 0
        }
    }

@router.get("/risk-trends")
def get_risk_trends(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Get risk level trends over time"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get daily counts of at-risk students from processed batches
    trends = db.query(
        func.date(DataBatch.created_at).label('date'),
        func.sum(DataBatch.at_risk_count).label('at_risk'),
        func.sum(DataBatch.total_students).label('total')
    ).filter(
        DataBatch.processed == True,
        DataBatch.created_at >= start_date
    ).group_by(
        func.date(DataBatch.created_at)
    ).order_by(
        func.date(DataBatch.created_at)
    ).all()
    
    return {
        "dates": [str(t.date) for t in trends],
        "at_risk_counts": [t.at_risk or 0 for t in trends],
        "total_counts": [t.total or 0 for t in trends]
    }

@router.get("/department-analysis")
def get_department_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("hod", "admin"))
):
    """HOD-only: Analysis by department via user's batches"""
    if current_user.role not in ['hod', 'admin']:
        return {"error": "Access denied"}
    
    # Get batches and their risk stats
    batch_stats = db.query(
        DataBatch.subject,
        func.sum(DataBatch.total_students).label('total'),
        func.sum(DataBatch.at_risk_count).label('at_risk')
    ).filter(
        DataBatch.processed == True
    ).group_by(
        DataBatch.subject
    ).all()
    
    return [
        {
            "subject": stat.subject,
            "total_students": stat.total or 0,
            "at_risk_students": stat.at_risk or 0,
            "risk_percentage": round((stat.at_risk / stat.total * 100), 1) if stat.total else 0
        }
        for stat in batch_stats
    ]

@router.get("/top-risk-students")
def get_top_risk_students(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Get students with highest risk scores"""
    students = db.query(StudentRecord).filter(
        StudentRecord.risk_level.in_(['High', 'Critical'])
    ).order_by(
        StudentRecord.failure_risk_score.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": s.id,
            "student_id": s.student_id,
            "student_name": s.student_name,
            "risk_score": s.failure_risk_score,
            "risk_level": s.risk_level,
            "top_factors": [f['description'] for f in (s.top_risk_factors or [])[:3]],
            "batch_id": s.batch_id
        }
        for s in students
    ]
