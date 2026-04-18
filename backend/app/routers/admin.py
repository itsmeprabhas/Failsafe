from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..models import User, DataBatch, StudentRecord, Intervention, PredictionLog, DashboardMetrics
from ..auth import require_role

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.delete("/reset/predictions")
def reset_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Clear all prediction results (risk scores, SHAP values) — keeps student records & batches."""
    try:
        updated = db.query(StudentRecord).update({
            "failure_risk_score": None,
            "risk_level": None,
            "shap_values": None,
            "top_risk_factors": None,
        })
        db.query(DataBatch).update({"processed": False, "at_risk_count": 0})
        db.query(PredictionLog).delete()
        db.commit()
        return {"message": f"Cleared predictions for {updated} student records.", "affected": updated}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reset/interventions")
def reset_interventions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Delete all intervention records."""
    try:
        count = db.query(Intervention).count()
        db.query(Intervention).delete()
        db.commit()
        return {"message": f"Deleted {count} intervention records.", "affected": count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reset/student-data")
def reset_student_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Delete all student records, batches, predictions, and interventions. Keeps users."""
    try:
        interventions = db.query(Intervention).count()
        students = db.query(StudentRecord).count()
        batches = db.query(DataBatch).count()

        db.query(Intervention).delete()
        db.query(PredictionLog).delete()
        db.query(StudentRecord).delete()
        db.query(DataBatch).delete()
        db.query(DashboardMetrics).delete()
        db.commit()

        return {
            "message": f"Cleared all student data: {batches} batches, {students} records, {interventions} interventions.",
            "affected": {"batches": batches, "students": students, "interventions": interventions}
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reset/all")
def reset_everything(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Nuclear reset: delete all data AND all non-system users. Re-seeds default accounts on next startup."""
    try:
        db.query(Intervention).delete()
        db.query(PredictionLog).delete()
        db.query(StudentRecord).delete()
        db.query(DataBatch).delete()
        db.query(DashboardMetrics).delete()
        # Delete all non-system users (keep the current admin)
        db.query(User).filter(User.id != current_user.id).delete()
        db.commit()
        return {"message": "Full system reset complete. All data cleared. Only your admin account remains."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
