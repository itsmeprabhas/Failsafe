from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, DataBatch, StudentRecord
from ..schemas import StudentDataBatch
from ..auth import get_current_active_user, require_role
import pandas as pd
import io
import os
from datetime import datetime

router = APIRouter(prefix="/upload", tags=["Data Upload"])

@router.post("/csv")
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    batch_name: str = "Untitled Batch",
    semester: str = "Fall 2024",
    academic_year: str = "2024-2025",
    subject: str = "General",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV or Excel files allowed")
    
    try:
        # Read file
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns
        required_cols = ['student_id', 'student_name', 'attendance_percentage', 'assignment_avg']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_cols}"
            )
        
        # Create batch record
        batch = DataBatch(
            batch_name=batch_name,
            semester=semester,
            academic_year=academic_year,
            subject=subject,
            uploaded_by=current_user.id,
            file_path=f"uploads/{file.filename}",
            total_students=len(df)
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        
        # Create student records
        optional_cols = [
            'midterm_score', 'quiz_avg', 'lab_score', 'previous_gpa',
            'study_hours_per_week', 'extracurricular_activities',
            'socioeconomic_status', 'parent_education', 'internet_access'
        ]
        
        for _, row in df.iterrows():
            record = StudentRecord(
                batch_id=batch.id,
                student_id=str(row['student_id']),
                student_name=str(row['student_name']),
                attendance_percentage=float(row['attendance_percentage']),
                assignment_avg=float(row['assignment_avg']),
                midterm_score=float(row['midterm_score']) if 'midterm_score' in row and pd.notna(row['midterm_score']) else None,
                quiz_avg=float(row['quiz_avg']) if 'quiz_avg' in row and pd.notna(row['quiz_avg']) else None,
                lab_score=float(row['lab_score']) if 'lab_score' in row and pd.notna(row['lab_score']) else None,
                previous_gpa=float(row['previous_gpa']) if 'previous_gpa' in row and pd.notna(row['previous_gpa']) else None,
                study_hours_per_week=float(row['study_hours_per_week']) if 'study_hours_per_week' in row and pd.notna(row['study_hours_per_week']) else None,
                extracurricular_activities=int(row['extracurricular_activities']) if 'extracurricular_activities' in row and pd.notna(row['extracurricular_activities']) else 0,
                socioeconomic_status=str(row['socioeconomic_status']) if 'socioeconomic_status' in row and pd.notna(row['socioeconomic_status']) else 'Medium',
                parent_education=str(row['parent_education']) if 'parent_education' in row and pd.notna(row['parent_education']) else 'Bachelor',
                internet_access=int(row['internet_access']) if 'internet_access' in row and pd.notna(row['internet_access']) else 1
            )
            db.add(record)
        
        db.commit()
        
        return {
            "batch_id": batch.id,
            "batch_name": batch_name,
            "total_students": len(df),
            "message": "Data uploaded successfully. Run predictions to analyze risk."
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/manual")
async def upload_manual(
    data: StudentDataBatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    # Create batch
    batch = DataBatch(
        batch_name=data.batch_name,
        semester=data.semester,
        academic_year=data.academic_year,
        subject=data.subject,
        uploaded_by=current_user.id,
        file_path="manual_entry",
        total_students=len(data.students)
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    
    # Create student records
    for student in data.students:
        record = StudentRecord(
            batch_id=batch.id,
            student_id=student.student_id,
            student_name=student.student_name,
            attendance_percentage=student.attendance_percentage,
            assignment_avg=student.assignment_avg,
            midterm_score=student.midterm_score,
            quiz_avg=student.quiz_avg,
            lab_score=student.lab_score,
            previous_gpa=student.previous_gpa,
            study_hours_per_week=student.study_hours_per_week,
            extracurricular_activities=student.extracurricular_activities,
            socioeconomic_status=student.socioeconomic_status,
            parent_education=student.parent_education,
            internet_access=student.internet_access
        )
        db.add(record)
    
    db.commit()
    
    return {
        "batch_id": batch.id,
        "batch_name": data.batch_name,
        "total_students": len(data.students),
        "message": "Manual data entry successful."
    }

@router.get("/batches")
def get_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("faculty", "hod", "admin"))
):
    batches = db.query(DataBatch).order_by(DataBatch.created_at.desc()).all()
    return batches
