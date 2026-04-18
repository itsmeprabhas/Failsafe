"""
Generate sample student data for testing FAILSAFE
"""
import os  # <-- Added this import
import pandas as pd
import numpy as np

def generate_sample_students(n=50):
    np.random.seed(42)
    
    data = []
    for i in range(1, n + 1):
        # Mix of at-risk and normal students
        is_at_risk = np.random.random() < 0.3  # 30% at-risk
        
        if is_at_risk:
            attendance = np.random.uniform(35, 65)
            assignment = np.random.uniform(20, 50)
            midterm = np.random.uniform(15, 40)
            quiz = np.random.uniform(15, 40)
            study_hours = np.random.uniform(1, 6)
            previous_gpa = np.random.uniform(1.0, 2.2)
        else:
            attendance = np.random.uniform(70, 98)
            assignment = np.random.uniform(55, 95)
            midterm = np.random.uniform(50, 95)
            quiz = np.random.uniform(50, 90)
            study_hours = np.random.uniform(8, 25)
            previous_gpa = np.random.uniform(2.5, 4.0)
        
        student = {
            'student_id': f'STU{i:04d}',
            'student_name': f'Student {i}',
            'attendance_percentage': round(attendance, 1),
            'assignment_avg': round(assignment, 1),
            'midterm_score': round(midterm, 1),
            'quiz_avg': round(quiz, 1),
            'lab_score': round(np.random.uniform(20, 95), 1),
            'previous_gpa': round(previous_gpa, 2),
            'study_hours_per_week': round(study_hours, 1),
            'extracurricular_activities': np.random.randint(0, 3),
            'socioeconomic_status': np.random.choice(['Low', 'Medium', 'High']),
            'parent_education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD']),
            'internet_access': np.random.choice([0, 1], p=[0.1, 0.9])
        }
        data.append(student)
    
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    df = generate_sample_students(50)
    
    # Ensure the 'data' directory exists before saving
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, 'sample_students.csv')
    df.to_csv(output_path, index=False)
    
    print(f"Generated {len(df)} student records to {output_path}")
    print("\nSample data:")
    print(df.head(10))