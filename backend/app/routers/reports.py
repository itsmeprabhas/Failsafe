from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, DataBatch, StudentRecord, Intervention
from ..auth import require_role
from datetime import datetime
import csv
import io

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/batch/{batch_id}/csv")
def export_batch_report(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Export batch predictions as CSV"""
    batch = db.query(DataBatch).filter(DataBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    records = db.query(StudentRecord).filter(StudentRecord.batch_id == batch_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Student ID', 'Student Name', 'Attendance %', 'Assignment Avg',
        'Midterm Score', 'Quiz Avg', 'Lab Score', 'Previous GPA',
        'Study Hours/Week', 'Risk Score', 'Risk Level',
        'Top Risk Factor 1', 'Top Risk Factor 2', 'Top Risk Factor 3'
    ])
    
    for record in records:
        top_factors = record.top_risk_factors or []
        factor_descs = [f.get('description', '') for f in top_factors[:3]]
        while len(factor_descs) < 3:
            factor_descs.append('')
        
        writer.writerow([
            record.student_id,
            record.student_name,
            record.attendance_percentage,
            record.assignment_avg,
            record.midterm_score or '',
            record.quiz_avg or '',
            record.lab_score or '',
            record.previous_gpa or '',
            record.study_hours_per_week or '',
            record.failure_risk_score or '',
            record.risk_level or '',
            factor_descs[0],
            factor_descs[1],
            factor_descs[2]
        ])
    
    output.seek(0)
    
    filename = f"failsafe_report_{batch.batch_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/interventions/csv")
def export_interventions_report(
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Export interventions as CSV"""
    query = db.query(Intervention).join(StudentRecord)
    if status:
        query = query.filter(Intervention.status == status)
    
    interventions = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Student ID', 'Student Name', 'Intervention Type', 'Title',
        'Priority', 'Status', 'Scheduled Date', 'Completed Date',
        'Description', 'Notes', 'Outcome'
    ])
    
    for inv in interventions:
        writer.writerow([
            inv.student.student_id if inv.student else '',
            inv.student.student_name if inv.student else '',
            inv.intervention_type,
            inv.title,
            inv.priority,
            inv.status,
            inv.scheduled_date.strftime('%Y-%m-%d') if inv.scheduled_date else '',
            inv.completed_date.strftime('%Y-%m-%d') if inv.completed_date else '',
            inv.description or '',
            inv.notes or '',
            inv.outcome or ''
        ])
    
    output.seek(0)
    
    filename = f"interventions_report_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/summary/text")
def get_text_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    """Generate text summary for email/report"""
    total = db.query(StudentRecord).count()
    at_risk = db.query(StudentRecord).filter(
        StudentRecord.risk_level.in_(['High', 'Critical'])
    ).count()
    
    critical = db.query(StudentRecord).filter(
        StudentRecord.risk_level == 'Critical'
    ).count()
    
    pending_interventions = db.query(Intervention).filter(
        Intervention.status == 'Pending'
    ).count()
    
    completed_interventions = db.query(Intervention).filter(
        Intervention.status == 'Completed'
    ).count()
    
    summary = f"""
FAILSAFE - Student Risk Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

OVERVIEW
--------
Total Students Analyzed: {total}
At-Risk Students: {at_risk} ({at_risk/total*100:.1f}% if total > 0 else 0)
Critical Risk: {critical}
High Risk: {at_risk - critical}

INTERVENTIONS
-------------
Pending: {pending_interventions}
Completed: {completed_interventions}
Completion Rate: {completed_interventions/(pending_interventions+completed_interventions)*100:.1f}% if (pending_interventions+completed_interventions) > 0 else 0

RECOMMENDATIONS
---------------
1. {'URGENT: ' if critical > 0 else ''}Schedule immediate counseling for {critical} critical-risk students
2. Follow up on {pending_interventions} pending interventions
3. Review intervention outcomes for completed cases
4. Upload new data for students not yet analyzed

---
Generated by FAILSAFE Student Risk Prediction System
    """.strip()
    
    return {"summary": summary}
