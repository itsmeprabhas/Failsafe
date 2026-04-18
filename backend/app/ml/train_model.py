"""
ML Model Training Script for FAILSAFE
Uses UCI Student Performance Dataset (processed)
Trains XGBoost classifier with SHAP explainability
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import xgboost as xgb
import shap
import joblib
import json
import os

class StudentRiskModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = [
            'attendance_percentage', 'assignment_avg', 'midterm_score',
            'quiz_avg', 'lab_score', 'previous_gpa', 'study_hours_per_week',
            'extracurricular_activities', 'socioeconomic_status', 
            'parent_education', 'internet_access'
        ]
        self.model_path = os.path.join(os.path.dirname(__file__), 'risk_model.joblib')
        self.scaler_path = os.path.join(os.path.dirname(__file__), 'scaler.joblib')
        self.encoders_path = os.path.join(os.path.dirname(__file__), 'encoders.joblib')
        self.explainer_path = os.path.join(os.path.dirname(__file__), 'shap_explainer.joblib')
        
    def generate_sample_data(self, n_samples=500):
        """Generate synthetic student data for training"""
        np.random.seed(42)
        
        data = {
            'attendance_percentage': np.random.uniform(40, 100, n_samples),
            'assignment_avg': np.random.uniform(20, 100, n_samples),
            'midterm_score': np.random.uniform(15, 100, n_samples),
            'quiz_avg': np.random.uniform(10, 100, n_samples),
            'lab_score': np.random.uniform(0, 100, n_samples),
            'previous_gpa': np.random.uniform(1.0, 4.0, n_samples),
            'study_hours_per_week': np.random.uniform(0, 30, n_samples),
            'extracurricular_activities': np.random.randint(0, 3, n_samples),
            'socioeconomic_status': np.random.choice(['Low', 'Medium', 'High'], n_samples),
            'parent_education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], n_samples),
            'internet_access': np.random.choice([0, 1], n_samples, p=[0.15, 0.85])
        }
        
        df = pd.DataFrame(data)
        
        # Create target variable based on realistic patterns
        # Students fail if: low attendance + low scores + low study hours
        risk_score = (
            (df['attendance_percentage'] < 60) * 3 +
            (df['assignment_avg'] < 40) * 2 +
            (df['midterm_score'] < 35) * 2.5 +
            (df['quiz_avg'] < 30) * 1.5 +
            (df['study_hours_per_week'] < 5) * 2 +
            (df['previous_gpa'] < 2.0) * 1.5 +
            (df['internet_access'] == 0) * 1 +
            (df['socioeconomic_status'] == 'Low') * 0.5
        )
        
        # Add some noise
        noise = np.random.normal(0, 1.5, n_samples)
        risk_score = risk_score + noise
        
        # Convert to binary: 1 = at risk, 0 = not at risk
        df['at_risk'] = (risk_score > 6).astype(int)
        
        return df
    
    def load_and_prepare_data(self, filepath=None):
        """Load data from CSV or generate synthetic data"""
        if filepath and os.path.exists(filepath):
            df = pd.read_csv(filepath)
            print(f"Loaded {len(df)} records from {filepath}")
        else:
            df = self.generate_sample_data(500)
            print(f"Generated {len(df)} synthetic records")
        
        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].fillna(df[col].median())
        
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            df[col] = df[col].fillna('Unknown')
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col])
            else:
                # Handle unseen labels
                le = self.label_encoders[col]
                df[col] = df[col].apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
        
        # Ensure 'at_risk' column exists
        if 'at_risk' not in df.columns:
            raise ValueError("Dataset must contain 'at_risk' target column")
        
        return df
    
    def train(self, filepath=None):
        """Train the XGBoost model"""
        print("=" * 50)
        print("TRAINING STUDENT RISK PREDICTION MODEL")
        print("=" * 50)
        
        # Load and prepare data
        df = self.load_and_prepare_data(filepath)
        
        # Separate features and target
        available_features = [f for f in self.feature_columns if f in df.columns]
        X = df[available_features]
        y = df['at_risk']
        
        print(f"\nFeatures used: {available_features}")
        print(f"Target distribution: {dict(y.value_counts())}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            eval_metric='logloss',
            use_label_encoder=False
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_prob = self.model.predict_proba(X_test_scaled)[:, 1]
        
        print("\n" + "=" * 50)
        print("MODEL EVALUATION")
        print("=" * 50)
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        print(f"\nROC-AUC Score: {roc_auc_score(y_test, y_prob):.4f}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring='roc_auc')
        print(f"5-Fold CV ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
        
        # Feature importance
        print("\n" + "=" * 50)
        print("FEATURE IMPORTANCE (Gain)")
        print("=" * 50)
        importance = self.model.feature_importances_
        for feat, imp in sorted(zip(available_features, importance), key=lambda x: x[1], reverse=True):
            print(f"{feat}: {imp:.4f}")
        
        # Save model and artifacts
        self.save_model()
        
        print("\n" + "=" * 50)
        print("MODEL TRAINING COMPLETE")
        print("=" * 50)
        
        return {
            'accuracy': (y_pred == y_test).mean(),
            'roc_auc': roc_auc_score(y_test, y_prob),
            'cv_scores': cv_scores.tolist()
        }
    
    def save_model(self):
        """Save model and all artifacts"""
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        joblib.dump(self.label_encoders, self.encoders_path)
        
        # Save SHAP explainer
        explainer = shap.TreeExplainer(self.model)
        joblib.dump(explainer, self.explainer_path)
        
        print(f"\nModel saved to: {self.model_path}")
        print(f"Scaler saved to: {self.scaler_path}")
        print(f"Encoders saved to: {self.encoders_path}")
        print(f"SHAP Explainer saved to: {self.explainer_path}")
    
    def load_model(self):
        """Load trained model and artifacts"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError("Model not found. Please train the model first.")
        
        self.model = joblib.load(self.model_path)
        self.scaler = joblib.load(self.scaler_path)
        self.label_encoders = joblib.load(self.encoders_path)
        
        if os.path.exists(self.explainer_path):
            return joblib.load(self.explainer_path)
        else:
            return shap.TreeExplainer(self.model)


if __name__ == "__main__":
    # Train the model
    trainer = StudentRiskModel()
    
    # Try to load from data folder if exists
    data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'student_data.csv')
    if os.path.exists(data_path):
        results = trainer.train(data_path)
    else:
        print("No data file found. Using synthetic data for training.")
        results = trainer.train()
    
    print("\nTraining Results:", results)
