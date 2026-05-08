# 🛡️ FAILSAFE — Student Risk Prediction System

FAILSAFE is an AI-powered Early Warning System designed to identify at-risk students before they fail. It uses Machine Learning to predict failure risks and provides clear, interpretable explanations for non-technical faculty members.

## 🌟 Key Features
* **AI Predictions:** Uses XGBoost to accurately predict student failure risks based on academic and behavioral data.
* **Explainable AI (XAI):** Integrates SHAP (SHapley Additive exPlanations) to explain exactly *why* a student was flagged, making the AI transparent.
* **Batch Processing:** Upload CSV files containing student data to instantly process hundreds of records.
* **Role-Based Access:** Different dashboards for System Admins, HODs, and Faculty.
* **Intervention Tracking:** Built-in tools to assign and track interventions (counseling, tutoring) for at-risk students.

## 🛠️ Tech Stack
* **Frontend:** React, Vite, TailwindCSS, Recharts
* **Backend:** FastAPI (Python), PostgreSQL, SQLAlchemy
* **Machine Learning:** Scikit-learn, XGBoost, SHAP

## 🚀 Quick Start

### 1. Start the Database
Ensure PostgreSQL is running on port 5432 and create a database named `failsafe_db` with user `failsafe_admin`.

### 2. Start the Backend & Frontend
You can use the provided shell script to start both servers simultaneously:
```bash
./run.sh
```
Or start them manually:
```bash
# Backend (Port 8000)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend (Port 5173)
cd frontend
npm run dev
```

### 3. Demo Credentials
* Admin: `admin / admin123`
* Faculty: `faculty1 / faculty123`
* HOD: `hod1 / hod123`
