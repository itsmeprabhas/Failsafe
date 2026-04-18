from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, StudentRecord, Intervention
from ..schemas import InterventionCreate, InterventionUpdate, InterventionResponse
from ..auth import require_role
from datetime import datetime

router = APIRouter(prefix="/interventions", tags=["Interventions"])

@router.post("/", response_model=InterventionResponse)
def create_intervention(
    intervention: InterventionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    # Verify student record exists
    student = db.query(StudentRecord).filter(
        StudentRecord.id == intervention.student_record_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")
    
    db_intervention = Intervention(
        student_record_id=intervention.student_record_id,
        assigned_by=current_user.id,
        intervention_type=intervention.intervention_type,
        title=intervention.title,
        description=intervention.description,
        action_items=intervention.action_items,
        priority=intervention.priority,
        scheduled_date=intervention.scheduled_date,
        follow_up_date=intervention.follow_up_date
    )
    db.add(db_intervention)
    db.commit()
    db.refresh(db_intervention)
    return db_intervention

@router.get("/student/{student_record_id}")
def get_student_interventions(
    student_record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    interventions = db.query(Intervention).filter(
        Intervention.student_record_id == student_record_id
    ).order_by(Intervention.created_at.desc()).all()
    return interventions

@router.put("/{intervention_id}", response_model=InterventionResponse)
def update_intervention(
    intervention_id: int,
    update: InterventionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    
    if update.status:
        intervention.status = update.status
    if update.notes:
        intervention.notes = update.notes
    if update.outcome:
        intervention.outcome = update.outcome
    if update.completed_date:
        intervention.completed_date = update.completed_date
    
    intervention.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(intervention)
    return intervention

@router.get("/")
def get_all_interventions(
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    query = db.query(Intervention)
    if status:
        query = query.filter(Intervention.status == status)
    return query.order_by(Intervention.created_at.desc()).all()

@router.get("/stats")
def get_intervention_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    total = db.query(Intervention).count()
    pending = db.query(Intervention).filter(Intervention.status == "Pending").count()
    in_progress = db.query(Intervention).filter(Intervention.status == "In Progress").count()
    completed = db.query(Intervention).filter(Intervention.status == "Completed").count()
    
    # By type
    types = db.query(Intervention.intervention_type).all()
    type_counts = {}
    for (t,) in types:
        type_counts[t] = type_counts.get(t, 0) + 1
    
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "completion_rate": (completed / total * 100) if total > 0 else 0,
        "by_type": type_counts
    }
