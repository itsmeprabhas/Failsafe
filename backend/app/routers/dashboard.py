from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from ..database import get_db
from ..models import User, DataBatch, StudentRecord, Intervention, StudentProgress
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

@router.get("/semester-comparison")
def get_semester_comparison(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Compare risk metrics across semesters for trend monitoring"""
    # Group by semester and academic year
    semester_stats = db.query(
        DataBatch.semester,
        DataBatch.academic_year,
        func.sum(DataBatch.total_students).label('total'),
        func.sum(DataBatch.at_risk_count).label('at_risk')
    ).filter(
        DataBatch.processed == True
    ).group_by(
        DataBatch.semester, DataBatch.academic_year
    ).order_by(
        DataBatch.academic_year, DataBatch.semester
    ).all()
    
    results = []
    for stat in semester_stats:
        total = stat.total or 0
        at_risk = stat.at_risk or 0
        
        # Calculate average risk score for this semester
        avg_risk = db.query(func.avg(StudentRecord.failure_risk_score)).join(
            DataBatch
        ).filter(
            DataBatch.semester == stat.semester,
            DataBatch.academic_year == stat.academic_year,
            DataBatch.processed == True,
            StudentRecord.failure_risk_score.isnot(None)
        ).scalar() or 0
        
        # Calculate improvement rate (students whose risk decreased)
        improved = db.query(func.count(StudentProgress.id)).filter(
            StudentProgress.semester == stat.semester,
            StudentProgress.academic_year == stat.academic_year,
            StudentProgress.risk_change < 0  # negative = improved
        ).scalar() or 0
        
        total_with_progress = db.query(func.count(StudentProgress.id)).filter(
            StudentProgress.semester == stat.semester,
            StudentProgress.academic_year == stat.academic_year,
            StudentProgress.risk_change.isnot(None)
        ).scalar() or 0
        
        results.append({
            "semester": stat.semester,
            "academic_year": stat.academic_year,
            "total_students": total,
            "at_risk_students": at_risk,
            "at_risk_percentage": round((at_risk / total * 100), 1) if total > 0 else 0,
            "avg_risk_score": round(float(avg_risk), 4),
            "improvement_rate": round((improved / total_with_progress * 100), 1) if total_with_progress > 0 else 0
        })
    
    return results

@router.get("/improvement-metrics")
def get_improvement_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Get overall improvement metrics — how effective are interventions?"""
    # Students who have completed interventions
    students_with_completed = db.query(StudentRecord.id).join(
        Intervention
    ).filter(
        Intervention.status == "Completed"
    ).distinct().all()
    
    student_ids = [s[0] for s in students_with_completed]
    total_with_interventions = len(student_ids)
    
    if total_with_interventions == 0:
        return {
            "total_with_interventions": 0,
            "improved_count": 0,
            "improvement_rate": 0,
            "avg_risk_reduction": 0,
            "intervention_effectiveness": {}
        }
    
    # Check progress snapshots for improvement
    improved_count = 0
    total_risk_change = 0
    
    for sid in student_ids:
        # Get latest progress snapshot
        latest = db.query(StudentProgress).filter(
            StudentProgress.student_record_id == sid,
            StudentProgress.risk_change.isnot(None)
        ).order_by(StudentProgress.snapshot_date.desc()).first()
        
        if latest and latest.risk_change is not None:
            if latest.risk_change < 0:
                improved_count += 1
            total_risk_change += latest.risk_change
    
    # Effectiveness by intervention type
    intervention_types = db.query(
        Intervention.intervention_type,
        func.count(Intervention.id).label('total'),
        func.count(case(
            (Intervention.status == 'Completed', 1),
        )).label('completed')
    ).group_by(Intervention.intervention_type).all()
    
    effectiveness = {}
    for it in intervention_types:
        rate = round((it.completed / it.total * 100), 1) if it.total > 0 else 0
        effectiveness[it.intervention_type] = rate
    
    return {
        "total_with_interventions": total_with_interventions,
        "improved_count": improved_count,
        "improvement_rate": round((improved_count / total_with_interventions * 100), 1) if total_with_interventions > 0 else 0,
        "avg_risk_reduction": round(total_risk_change / total_with_interventions, 4) if total_with_interventions > 0 else 0,
        "intervention_effectiveness": effectiveness
    }
