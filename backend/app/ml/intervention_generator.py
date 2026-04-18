"""
Auto-Generate Personalized Intervention Plans
Based on risk factors and SHAP explanations
"""
from typing import Dict, List, Any
from datetime import datetime, timedelta

class InterventionGenerator:
    def __init__(self):
        self.intervention_templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load intervention templates for different risk factors"""
        return {
            'attendance_percentage': {
                'Low': [
                    {
                        'type': 'counseling',
                        'title': 'Attendance Recovery Meeting',
                        'description': 'One-on-one session to understand attendance barriers and create recovery plan.',
                        'action_items': [
                            'Identify root cause of absences (health, transport, motivation)',
                            'Set attendance improvement targets (weekly milestones)',
                            'Explore make-up class options',
                            'Assign peer buddy for class notes'
                        ],
                        'priority': 'High'
                    },
                    {
                        'type': 'parent_meeting',
                        'title': 'Parent/Guardian Consultation on Attendance',
                        'description': 'Involve family in addressing chronic attendance issues.',
                        'action_items': [
                            'Discuss attendance pattern with family',
                            'Identify home-related barriers',
                            'Create home support plan',
                            'Schedule follow-up check-in in 2 weeks'
                        ],
                        'priority': 'High'
                    }
                ],
                'Critical': [
                    {
                        'type': 'counseling',
                        'title': 'Urgent Attendance Intervention',
                        'description': 'Immediate meeting required - attendance at critical level affecting academic survival.',
                        'action_items': [
                            'Same-day meeting with student',
                            'Contact guardian within 24 hours',
                            'Consider academic probation warning',
                            'Explore alternative learning arrangements',
                            'Daily attendance monitoring for 2 weeks'
                        ],
                        'priority': 'Urgent'
                    }
                ]
            },
            'assignment_avg': {
                'Low': [
                    {
                        'type': 'extra_class',
                        'title': 'Assignment Skills Workshop',
                        'description': 'Small group session focusing on assignment completion strategies.',
                        'action_items': [
                            'Review assignment requirements and rubric',
                            'Teach time management for assignments',
                            'Practice with sample problems',
                            'Set up weekly check-in for upcoming assignments'
                        ],
                        'priority': 'Medium'
                    }
                ],
                'Critical': [
                    {
                        'type': 'study_plan',
                        'title': 'Comprehensive Study Plan Restructure',
                        'description': 'Complete overhaul of study approach with intensive support.',
                        'action_items': [
                            'Assess learning style and gaps',
                            'Create detailed weekly study schedule',
                            'Pair with high-performing peer tutor',
                            'Weekly progress meetings with faculty',
                            'Break down remaining assignments into micro-tasks'
                        ],
                        'priority': 'High'
                    }
                ]
            },
            'midterm_score': {
                'Low': [
                    {
                        'type': 'extra_class',
                        'title': 'Midterm Review and Recovery Sessions',
                        'description': 'Targeted sessions to address midterm performance gaps.',
                        'action_items': [
                            'Analyze midterm mistakes by topic',
                            'Create topic-wise remediation plan',
                            'Provide additional practice materials',
                            'Schedule makeup assessment opportunity'
                        ],
                        'priority': 'High'
                    }
                ],
                'Critical': [
                    {
                        'type': 'study_plan',
                        'title': 'Academic Recovery Program',
                        'description': 'Intensive program to recover from severely low midterm performance.',
                        'action_items': [
                            'Complete diagnostic assessment',
                            'Daily supervised study hours (minimum 2)',
                            'Weekly quizzes to track improvement',
                            'Consider course withdrawal vs. recovery timeline',
                            'Mentor assignment for continuous support'
                        ],
                        'priority': 'Urgent'
                    }
                ]
            },
            'study_hours_per_week': {
                'Low': [
                    {
                        'type': 'counseling',
                        'title': 'Study Habits Counseling',
                        'description': 'Session to assess and improve study habits and time allocation.',
                        'action_items': [
                            'Conduct study habits assessment',
                            'Identify time-wasting activities',
                            'Teach effective study techniques (Pomodoro, active recall)',
                            'Help create realistic study schedule',
                            'Recommend study environment improvements'
                        ],
                        'priority': 'Medium'
                    }
                ],
                'Critical': [
                    {
                        'type': 'peer_mentoring',
                        'title': 'Study Buddy Assignment',
                        'description': 'Pair with dedicated peer to model and reinforce study habits.',
                        'action_items': [
                            'Match with compatible high-performing student',
                            'Set joint study session schedule (3x/week)',
                            'Peer to share notes and study strategies',
                            'Faculty check-in with pair bi-weekly'
                        ],
                        'priority': 'High'
                    }
                ]
            },
            'previous_gpa': {
                'Low': [
                    {
                        'type': 'counseling',
                        'title': 'Academic History Review',
                        'description': 'Deep dive into academic history to identify patterns and solutions.',
                        'action_items': [
                            'Review transcript and identify problem courses',
                            'Assess for possible learning disabilities',
                            'Discuss long-term academic goals',
                            'Connect with academic advisor for degree planning',
                            'Consider reduced course load'
                        ],
                        'priority': 'Medium'
                    }
                ],
                'Critical': [
                    {
                        'type': 'counseling',
                        'title': 'Academic Probation Prevention',
                        'description': 'Comprehensive support to prevent academic probation.',
                        'action_items': [
                            'Immediate meeting with academic advisor',
                            'Assessment for learning support services',
                            'Consider incompletes vs. withdrawals',
                            'Create survival plan for current semester',
                            'Weekly mandatory check-ins'
                        ],
                        'priority': 'Urgent'
                    }
                ]
            },
            'internet_access': {
                'Low': [
                    {
                        'type': 'counseling',
                        'title': 'Technology Access Support',
                        'description': 'Help student overcome technology barriers.',
                        'action_items': [
                            'Identify campus computer lab availability',
                            'Explore loaner laptop programs',
                            'Provide offline resource alternatives',
                            'Contact student services for technology assistance',
                            'Adjust assignment deadlines if needed'
                        ],
                        'priority': 'Medium'
                    }
                ]
            },
            'quiz_avg': {
                'Low': [
                    {
                        'type': 'extra_class',
                        'title': 'Quiz Preparation Strategies',
                        'description': 'Teach effective quiz preparation and test-taking strategies.',
                        'action_items': [
                            'Analyze quiz performance patterns',
                            'Teach active recall and spaced repetition',
                            'Provide practice quizzes',
                            'Review common quiz question types'
                        ],
                        'priority': 'Medium'
                    }
                ]
            }
        }
    
    def generate_interventions(
        self, 
        student_data: Dict, 
        risk_level: str, 
        top_risk_factors: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized intervention plan based on risk factors
        
        Args:
            student_data: Student's raw data
            risk_level: 'Low', 'Medium', 'High', or 'Critical'
            top_risk_factors: List of risk factors from SHAP explanation
            
        Returns:
            List of recommended interventions with details
        """
        interventions = []
        
        if risk_level == 'Low':
            return [{
                'type': 'monitoring',
                'title': 'Standard Monitoring',
                'description': 'Continue regular monitoring. No immediate intervention required.',
                'action_items': ['Continue tracking performance metrics'],
                'priority': 'Low',
                'scheduled_date': (datetime.now() + timedelta(days=14)).isoformat()
            }]
        
        for factor in top_risk_factors:
            feature = factor['feature']
            severity = factor['severity']
            
            templates = self.intervention_templates.get(feature, {})
            
            # Try to get severity-specific template, fallback to 'Low'
            if severity in templates:
                selected = templates[severity]
            elif 'Low' in templates:
                selected = templates['Low']
            else:
                continue
            
            for template in selected:
                intervention = template.copy()
                intervention['risk_factor'] = feature
                intervention['risk_contribution'] = factor['shap_contribution']
                
                # Add scheduling
                if intervention['priority'] == 'Urgent':
                    intervention['scheduled_date'] = (datetime.now() + timedelta(days=1)).isoformat()
                    intervention['follow_up_date'] = (datetime.now() + timedelta(days=3)).isoformat()
                elif intervention['priority'] == 'High':
                    intervention['scheduled_date'] = (datetime.now() + timedelta(days=3)).isoformat()
                    intervention['follow_up_date'] = (datetime.now() + timedelta(days=7)).isoformat()
                else:
                    intervention['scheduled_date'] = (datetime.now() + timedelta(days=5)).isoformat()
                    intervention['follow_up_date'] = (datetime.now() + timedelta(days=14)).isoformat()
                
                interventions.append(intervention)
        
        # Add general support for High/Critical risk
        if risk_level in ['High', 'Critical']:
            interventions.append({
                'type': 'counseling',
                'title': 'Overall Academic Wellness Check',
                'description': 'Holistic assessment of student wellbeing affecting academics.',
                'action_items': [
                    'Assess stress levels and mental health',
                    'Review sleep and nutrition habits',
                    'Discuss personal challenges',
                    'Refer to counseling services if needed'
                ],
                'priority': 'High' if risk_level == 'High' else 'Urgent',
                'scheduled_date': (datetime.now() + timedelta(days=2)).isoformat(),
                'follow_up_date': (datetime.now() + timedelta(days=7)).isoformat()
            })
        
        # Remove duplicates and sort by priority
        seen = set()
        unique_interventions = []
        for i in interventions:
            key = i['title']
            if key not in seen:
                seen.add(key)
                unique_interventions.append(i)
        
        priority_order = {'Urgent': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        unique_interventions.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return unique_interventions
    
    def format_intervention_message(
        self, 
        student_name: str, 
        risk_level: str, 
        interventions: List[Dict]
    ) -> str:
        """Format interventions into a readable message for faculty"""
        if risk_level == 'Low':
            return f"✅ {student_name}: No intervention needed. Continue standard monitoring."
        
        lines = [f"⚠️ INTERVENTION PLAN for {student_name}"]
        lines.append(f"Risk Level: {risk_level}")
        lines.append("=" * 50)
        
        for i, intervention in enumerate(interventions, 1):
            lines.append(f"\n{i}. [{intervention['priority']}] {intervention['title']}")
            lines.append(f"   Type: {intervention['type'].replace('_', ' ').title()}")
            lines.append(f"   Schedule: {intervention['scheduled_date'][:10]}")
            lines.append(f"   Description: {intervention['description']}")
            lines.append("   Actions:")
            for action in intervention['action_items']:
                lines.append(f"   • {action}")
        
        return "\n".join(lines)


# Singleton instance
generator_instance = None

def get_intervention_generator() -> InterventionGenerator:
    global generator_instance
    if generator_instance is None:
        generator_instance = InterventionGenerator()
    return generator_instance
