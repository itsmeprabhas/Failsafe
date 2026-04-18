"""
Train FAILSAFE model with UCI Student Performance Dataset
Download from: https://www.kaggle.com/datasets/uciml/student-alcohol-consumption
or: https://archive.ics.uci.edu/ml/datasets/student+performance

This script processes the raw UCI data into FAILSAFE-compatible format.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score
import xgboost as xgb
import shap
import joblib
import os

class UCIDataProcessor:
    """Process UCI Student Performance Data for FAILSAFE"""
    
    def __init__(self):
        self.base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        os.makedirs(self.base_path, exist_ok=True)
    
    def loaduci_data(self, filepath=None):
        """Load UCI student performance CSV (semicolon separated)"""
        if filepath and os.path.exists(filepath):
            # UCI data uses semicolon separator
            df = pd.read_csv(filepath, sep=';')
            return df
        else:
            print("UCI file not found. Using enhanced synthetic data.")
            return None
    
    def transform_to_failsafe_format(self, df):
        """Transform UCI columns to FAILSAFE feature schema"""
        # Map UCI features to FAILSAFE features
        transformed = pd.DataFrame()
        
        # Attendance: UCI has 'absences', convert to percentage (assume 200 class days)
        if 'absences' in df.columns:
            transformed['attendance_percentage'] = ((200 - df['absences']) / 200 * 100).clip(0, 100)
        
        # Assignment scores: Map from UCI grading
        # UCI has G1 (first period grade), G2 (second period grade)
        if 'G1' in df.columns:
            transformed['midterm_score'] = (df['G1'] / 20 * 100).clip(0, 100)
        if 'G2' in df.columns:
            transformed['quiz_avg'] = (df['G2'] / 20 * 100).clip(0, 100)
        
        # Final grade as assignment average proxy
        if 'G3' in df.columns:
            transformed['assignment_avg'] = (df['G3'] / 20 * 100).clip(0, 100)
        
        # Lab score: Use 'schoolsup' and 'higher' as proxies
        if 'schoolsup' in df.columns:
            transformed['lab_score'] = np.where(df['schoolsup'] == 'yes', 75, 50)
            transformed['lab_score'] += np.where(df['higher'] == 'yes', 15, 0)
        
        # Study time: UCI has 'studytime' (1-4 scale)
        if 'studytime' in df.columns:
            # Map: 1=<2hr, 2=2-5hr, 3=5-10hr, 4=>10hr
            study_map = {1: 1.5, 2: 3.5, 3: 7.5, 4: 15}
            transformed['study_hours_per_week'] = df['studytime'].map(study_map)
        
        # Previous GPA proxy: Use 'Medu' (mother education) + 'Fedu' (father education)
        if 'Medu' in df.columns and 'Fedu' in df.columns:
            edu_avg = (df['Medu'] + df['Fedu']) / 2
            # Map 0-4 scale to 1.0-4.0 GPA
            transformed['previous_gpa'] = (edu_avg / 4 * 3.0 + 1.0).clip(1.0, 4.0)
        
        # Extracurricular activities
        if 'activities' in df.columns:
            transformed['extracurricular_activities'] = np.where(df['activities'] == 'yes', 1, 0)
        
        # Internet access
        if 'internet' in df.columns:
            transformed['internet_access'] = np.where(df['internet'] == 'yes', 1, 0)
        
        # Socioeconomic status: Use 'famsize', 'Pstatus', 'Fjob', 'Mjob'
        if 'Fjob' in df.columns:
            job_map = {'teacher': 'High', 'health': 'High', 'services': 'Medium', 
                       'at_home': 'Low', 'other': 'Medium'}
            transformed['socioeconomic_status'] = df['Fjob'].map(job_map).fillna('Medium')
        
        # Parent education
        if 'Medu' in df.columns:
            edu_map = {0: 'High School', 1: 'High School', 2: 'Bachelor', 
                       3: 'Master', 4: 'PhD'}
            transformed['parent_education'] = df['Medu'].map(edu_map).fillna('Bachelor')
        
        # Create target: at_risk = G3 < 10 (out of 20, which is passing)
        if 'G3' in df.columns:
            transformed['at_risk'] = (df['G3'] < 10).astype(int)
        
        # Add some noise for realism
        np.random.seed(42)
        for col in ['attendance_percentage', 'assignment_avg', 'midterm_score', 'quiz_avg', 'lab_score']:
            if col in transformed.columns:
                noise = np.random.normal(0, 3, len(transformed))
                transformed[col] = (transformed[col] + noise).clip(0, 100)
        
        return transformed


def train_with_uci():
    """Main training function"""
    processor = UCIDataProcessor()
    
    # Try to load UCI data
    uci_path = os.path.join(processor.base_path, 'student-mat.csv')
    df = processor.loaduci_data(uci_path)
    
    if df is not None:
        print(f"Loaded UCI dataset: {len(df)} records")
        transformed_df = processor.transform_to_failsafe_format(df)
        print(f"Transformed to FAILSAFE format: {len(transformed_df)} records")
        print(f"Target distribution: {dict(transformed_df['at_risk'].value_counts())}")
        
        # Save transformed data
        output_path = os.path.join(processor.base_path, 'uci_transformed.csv')
        transformed_df.to_csv(output_path, index=False)
        print(f"Saved transformed data to {output_path}")
    else:
        transformed_df = None
    
    # Now train using the existing train_model.py logic
    from train_model import StudentRiskModel
    
    trainer = StudentRiskModel()
    
    if transformed_df is not None:
        # Save as the expected format and train
        train_path = os.path.join(processor.base_path, 'training_data.csv')
        transformed_df.to_csv(train_path, index=False)
        results = trainer.train(train_path)
    else:
        print("\nFalling back to synthetic data training...")
        results = trainer.train()
    
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("FAILSAFE - Training with UCI Student Performance Dataset")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Download 'student-mat.csv' from:")
    print("   https://www.kaggle.com/datasets/uciml/student-alcohol-consumption")
    print("2. Place it in the /data folder")
    print("3. Run this script again\n")
    
    results = train_with_uci()
    print("\nTraining complete!", results)
