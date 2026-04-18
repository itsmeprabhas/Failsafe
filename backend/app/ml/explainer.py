"""
SHAP-based Explainability Module for FAILSAFE
Provides human-readable explanations for each prediction
"""
import numpy as np
import pandas as pd
import shap
import joblib
import os
from typing import Dict, List, Any, Tuple

class SHAPExplainer:
    def __init__(self):
        self.explainer = None
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.feature_columns = [
            'attendance_percentage', 'assignment_avg', 'midterm_score',
            'quiz_avg', 'lab_score', 'previous_gpa', 'study_hours_per_week',
            'extracurricular_activities', 'socioeconomic_status', 
            'parent_education', 'internet_access'
        ]
        
        # Human-readable descriptions for features
        self.feature_descriptions = {
            'attendance_percentage': 'Attendance Rate',
            'assignment_avg': 'Assignment Performance',
            'midterm_score': 'Midterm Exam Score',
            'quiz_avg': 'Quiz Performance',
            'lab_score': 'Lab Work Score',
            'previous_gpa': 'Previous Semester GPA',
            'study_hours_per_week': 'Weekly Study Hours',
            'extracurricular_activities': 'Extracurricular Involvement',
            'socioeconomic_status': 'Socioeconomic Background',
            'parent_education': "Parent's Education Level",
            'internet_access': 'Internet Access Availability'
        }
        
        # Thresholds for identifying "problematic" values
        self.risk_thresholds = {
            'attendance_percentage': {'low': 60, 'critical': 45},
            'assignment_avg': {'low': 40, 'critical': 25},
            'midterm_score': {'low': 35, 'critical': 20},
            'quiz_avg': {'low': 30, 'critical': 15},
            'lab_score': {'low': 35, 'critical': 20},
            'previous_gpa': {'low': 2.0, 'critical': 1.5},
            'study_hours_per_week': {'low': 5, 'critical': 2},
            'extracurricular_activities': {'low': 0, 'critical': 0},
            'internet_access': {'low': 0, 'critical': 0}
        }
        
        self._load_artifacts()
    
    def _load_artifacts(self):
        """Load model artifacts"""
        base_path = os.path.dirname(__file__)
        
        model_path = os.path.join(base_path, 'risk_model.joblib')
        scaler_path = os.path.join(base_path, 'scaler.joblib')
        explainer_path = os.path.join(base_path, 'shap_explainer.joblib')
        encoders_path = os.path.join(base_path, 'encoders.joblib')
        
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.label_encoders = joblib.load(encoders_path) if os.path.exists(encoders_path) else {}
            
            if os.path.exists(explainer_path):
                self.explainer = joblib.load(explainer_path)
            else:
                self.explainer = shap.TreeExplainer(self.model)
        else:
            raise FileNotFoundError(
                "Model not found. Run train_model.py first to train the model."
            )
    
    def encode_categorical(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical columns using saved label encoders"""
        df_encoded = df.copy()
        
        for col, encoder in self.label_encoders.items():
            if col in df_encoded.columns:
                df_encoded[col] = df_encoded[col].apply(
                    lambda x: encoder.transform([x])[0] if x in encoder.classes_ else -1
                )
        
        return df_encoded
    
    def explain_prediction(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanation for a single student prediction
        
        Returns:
            {
                'risk_score': float,
                'risk_level': str,
                'top_risk_factors': List[Dict],
                'shap_values': Dict[str, float],
                'summary': str
            }
        """
        # Prepare features
        df = pd.DataFrame([student_data])
        df_encoded = self.encode_categorical(df)
        
        available_features = [f for f in self.feature_columns if f in df_encoded.columns]
        X = df_encoded[available_features].values
        X_scaled = self.scaler.transform(X)
        
        # Get prediction
        risk_score = self.model.predict_proba(X_scaled)[0, 1]
        risk_level = self._get_risk_level(risk_score)
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(X_scaled)[0]
        
        # Create feature-SHAP mapping
        shap_dict = {}
        for feat, val in zip(available_features, shap_values):
            shap_dict[feat] = round(float(val), 4)
        
        # Get top risk factors (positive SHAP = increases risk)
        top_factors = self._get_top_risk_factors(
            student_data, available_features, shap_values
        )
        
        # Generate human-readable summary
        summary = self._generate_summary(student_data, top_factors, risk_level)
        
        return {
            'risk_score': round(risk_score, 4),
            'risk_level': risk_level,
            'top_risk_factors': top_factors,
            'shap_values': shap_dict,
            'summary': summary
        }
    
    def explain_batch(self, students_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate explanations for a batch of students"""
        results = []
        
        for student in students_data:
            try:
                explanation = self.explain_prediction(student)
                explanation['student_id'] = student.get('student_id', 'unknown')
                explanation['student_name'] = student.get('student_name', 'Unknown')
                results.append(explanation)
            except Exception as e:
                results.append({
                    'student_id': student.get('student_id', 'unknown'),
                    'student_name': student.get('student_name', 'Unknown'),
                    'error': str(e)
                })
        
        return results
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to categorical level"""
        if risk_score >= 0.8:
            return 'Critical'
        elif risk_score >= 0.6:
            return 'High'
        elif risk_score >= 0.35:
            return 'Medium'
        else:
            return 'Low'
    
    def _get_top_risk_factors(
        self, 
        student_data: Dict, 
        features: List[str], 
        shap_values: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Extract and format top risk factors"""
        factors = []
        
        # Sort by SHAP value (descending = most risk-increasing)
        sorted_indices = np.argsort(shap_values)[::-1]
        
        for idx in sorted_indices[:5]:  # Top 5 factors
            feature = features[idx]
            shap_val = float(shap_values[idx])
            
            if shap_val <= 0:
                continue  # Skip factors that reduce risk
            
            description = self.feature_descriptions.get(feature, feature)
            actual_value = student_data.get(feature, 'N/A')
            severity = self._get_severity(feature, actual_value)
            
            factors.append({
                'feature': feature,
                'description': description,
                'actual_value': actual_value,
                'shap_contribution': round(shap_val, 4),
                'severity': severity,
                'explanation': self._factor_explanation(feature, actual_value, shap_val)
            })
        
        return factors
    
    def _get_severity(self, feature: str, value: Any) -> str:
        """Determine severity of a risk factor"""
        thresholds = self.risk_thresholds.get(feature, {})
        
        try:
            value = float(value)
            if 'critical' in thresholds and value <= thresholds['critical']:
                return 'Critical'
            elif 'low' in thresholds and value <= thresholds['low']:
                return 'High'
        except (ValueError, TypeError):
            pass
        
        return 'Medium'
    
    def _factor_explanation(self, feature: str, value: Any, shap_val: float) -> str:
        """Generate explanation for a specific risk factor"""
        explanations = {
            'attendance_percentage': f"Attendance is at {value}% (below 60% threshold), directly impacting course engagement and knowledge retention.",
            'assignment_avg': f"Assignment average of {value}% indicates significant difficulty in understanding and applying course concepts.",
            'midterm_score': f"Midterm score of {value}% suggests foundational gaps that will compound in later assessments.",
            'quiz_avg': f"Quiz performance at {value}% shows inconsistent preparation or difficulty with regular assessments.",
            'lab_score': f"Lab score of {value}% indicates practical skill gaps that affect theoretical understanding.",
            'previous_gpa': f"Previous GPA of {value} suggests a pattern of academic struggle that requires systematic intervention.",
            'study_hours_per_week': f"Only {value} hours/week of study is significantly below the recommended 10+ hours for this course.",
            'extracurricular_activities': f"No extracurricular involvement may indicate social isolation or time management issues.",
            'internet_access': f"Lack of reliable internet access creates barriers to online resources and assignment submission."
        }
        
        return explanations.get(feature, f"{feature} contributes to failure risk with a value of {value}.")
    
    def _generate_summary(
        self, 
        student_data: Dict, 
        top_factors: List[Dict], 
        risk_level: str
    ) -> str:
        """Generate a human-readable summary of the prediction"""
        if risk_level == 'Low':
            return "Student is performing within expected parameters. Continue monitoring."
        
        primary_factors = [f['description'].lower() for f in top_factors[:2]]
        primary_str = " and ".join(primary_factors)
        
        if risk_level == 'Critical':
            return f"IMMEDIATE ACTION REQUIRED: Student shows {len(top_factors)} significant risk factors, primarily {primary_str}. High probability of course failure without urgent intervention."
        elif risk_level == 'High':
            return f"Student is at elevated risk due to {primary_str}. Early intervention with targeted support recommended."
        else:
            return f"Student shows some risk indicators, particularly {primary_str}. Proactive monitoring and minor adjustments may prevent escalation."


# Singleton instance
explainer_instance = None

def get_explainer() -> SHAPExplainer:
    global explainer_instance
    if explainer_instance is None:
        explainer_instance = SHAPExplainer()
    return explainer_instance
