from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .models import User
from .schemas import UserCreate
from .auth import get_password_hash, require_role
from .routers import auth, upload, predictions, interventions, dashboard, reports, admin
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FAILSAFE - Student Risk Prediction System",
    description="Early warning system for at-risk students using XGBoost and SHAP explainability",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(predictions.router)
app.include_router(interventions.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(admin.router)

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

@app.on_event("startup")
def startup_event():
    """Initialize default admin user if none exists"""
    db = next(get_db())
    try:
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            admin_user = User(
                email="admin@failsafe.edu",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="System Administrator",
                role="admin",
                department="Administration"
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created: admin / admin123")
        
        faculty = db.query(User).filter(User.username == "faculty1").first()
        if not faculty:
            faculty_user = User(
                email="faculty@failsafe.edu",
                username="faculty1",
                hashed_password=get_password_hash("faculty123"),
                full_name="Dr. Sarah Johnson",
                role="faculty",
                department="Computer Science"
            )
            db.add(faculty_user)
            db.commit()
            print("Sample faculty user created: faculty1 / faculty123")

        hod = db.query(User).filter(User.username == "hod1").first()
        if not hod:
            hod_user = User(
                email="hod@failsafe.edu",
                username="hod1",
                hashed_password=get_password_hash("hod123"),
                full_name="Prof. Michael Chen",
                role="hod",
                department="Computer Science"
            )
            db.add(hod_user)
            db.commit()
            print("Sample HOD user created: hod1 / hod123")
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "message": "FAILSAFE API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
