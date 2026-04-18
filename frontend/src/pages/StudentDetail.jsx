import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { predictionAPI, interventionAPI } from '../services/api';
import {
  ArrowLeft, User, AlertTriangle, Target,
  ClipboardList, CheckCircle
} from 'lucide-react';

export default function StudentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [student, setStudent] = useState(null);
  const [interventions, setInterventions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudentData();
  }, [id]);

  const fetchStudentData = async () => {
    setLoading(true);
    try {
      const [studentRes, interventionsRes] = await Promise.all([
        predictionAPI.getStudentPrediction(id),
        interventionAPI.getByStudent(id),
      ]);
      setStudent(studentRes.data);
      setInterventions(interventionsRes.data);
    } catch (error) {
      console.error('Failed to fetch student data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level) => {
    const colors = {
      Low: 'text-green-600 bg-green-50 border-green-200',
      Medium: 'text-yellow-600 bg-yellow-50 border-yellow-200',
      High: 'text-orange-600 bg-orange-50 border-orange-200',
      Critical: 'text-red-600 bg-red-50 border-red-200',
    };
    return colors[level] || colors.Low;
  };

  const getRiskGaugeWidth = (score) => `${Math.min(score * 100, 100)}%`;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!student) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Student not found</p>
        <button onClick={() => navigate(-1)} className="btn-primary mt-4">Go Back</button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-gray-100 rounded-lg"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{student.student_name}</h1>
            <span className={`badge ${getRiskColor(student.risk_level).split(' ')[1]} border`}>
              {student.risk_level} Risk
            </span>
          </div>
          <p className="text-gray-500">{student.student_id}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Score Card */}
        <div className={`card border-2 ${getRiskColor(student.risk_level).split(' ')[2]}`}>
          <h3 className="text-sm font-medium text-gray-500 mb-4">Failure Risk Score</h3>
          <div className="text-center">
            <p className="text-5xl font-bold">{(student.failure_risk_score * 100).toFixed(1)}%</p>
            <div className="mt-4 h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  student.risk_level === 'Critical' ? 'bg-red-500' :
                  student.risk_level === 'High' ? 'bg-orange-500' :
                  student.risk_level === 'Medium' ? 'bg-yellow-500' :
                  'bg-green-500'
                }`}
                style={{ width: getRiskGaugeWidth(student.failure_risk_score) }}
              />
            </div>
            <p className="text-sm text-gray-500 mt-2">
              {student.risk_level === 'Critical' ? 'Immediate action required' :
               student.risk_level === 'High' ? 'Early intervention needed' :
               student.risk_level === 'Medium' ? 'Monitor closely' :
               'On track'}
            </p>
          </div>
        </div>

        {/* Feature Values */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-4">Student Data</h3>
          <div className="space-y-3">
            {Object.entries(student.features).map(([key, value]) => {
              if (value === null || value === undefined) return null;
              const labels = {
                attendance_percentage: 'Attendance',
                assignment_avg: 'Assignments',
                midterm_score: 'Midterm',
                quiz_avg: 'Quizzes',
                lab_score: 'Lab Work',
                previous_gpa: 'Previous GPA',
                study_hours_per_week: 'Study Hours/Week',
                extracurricular_activities: 'Extracurriculars',
                socioeconomic_status: 'Socioeconomic',
                parent_education: "Parent's Education",
                internet_access: 'Internet Access',
              };
              return (
                <div key={key} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{labels[key] || key}</span>
                  <span className="text-sm font-medium text-gray-900">
                    {key === 'internet_access' ? (value ? 'Yes' : 'No') :
                     key === 'extracurricular_activities' ? value :
                     typeof value === 'number' ? value.toFixed(1) : value}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* SHAP Explanation */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-4 flex items-center gap-2">
            <Target className="w-4 h-4" />
            Why Flagged? (SHAP)
          </h3>
          {student.top_risk_factors && student.top_risk_factors.length > 0 ? (
            <div className="space-y-3">
              {student.top_risk_factors.map((factor, idx) => (
                <div key={idx} className="bg-gray-50 rounded-lg p-3">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-sm font-medium text-gray-800">
                      {factor.description}
                    </span>
                    <span className={`badge ${
                      factor.severity === 'Critical' ? 'badge-critical' :
                      factor.severity === 'High' ? 'badge-high' :
                      'badge-medium'
                    }`}>
                      {factor.severity}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600">{factor.explanation}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs text-gray-400">Value:</span>
                    <span className="text-xs font-mono text-gray-700">{factor.actual_value}</span>
                    <span className="text-xs text-gray-400 ml-auto">Impact:</span>
                    <span className="text-xs font-mono text-red-600">+{factor.shap_contribution}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No risk factors identified</p>
          )}
        </div>
      </div>

      {/* SHAP Values Chart */}
      {student.shap_values && (
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-4">Feature Contributions (SHAP Values)</h3>
          <div className="space-y-2">
            {Object.entries(student.shap_values)
              .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
              .map(([feature, value]) => {
                const labels = {
                  attendance_percentage: 'Attendance',
                  assignment_avg: 'Assignments',
                  midterm_score: 'Midterm',
                  quiz_avg: 'Quizzes',
                  lab_score: 'Lab Work',
                  previous_gpa: 'Previous GPA',
                  study_hours_per_week: 'Study Hours',
                  extracurricular_activities: 'Extracurriculars',
                  socioeconomic_status: 'Socioeconomic',
                  parent_education: 'Parent Edu.',
                  internet_access: 'Internet',
                };
                const maxVal = Math.max(...Object.values(student.shap_values).map(Math.abs));
                const barWidth = Math.abs(value) / maxVal * 100;
                const isPositive = value > 0;

                return (
                  <div key={feature} className="flex items-center gap-3">
                    <span className="text-xs text-gray-600 w-28 text-right">{labels[feature] || feature}</span>
                    <div className="flex-1 flex items-center">
                      <div
                        className={`h-4 rounded ${
                          isPositive ? 'bg-red-400' : 'bg-green-400'
                        }`}
                        style={{ width: `${barWidth}%`, marginLeft: isPositive ? 'auto' : '0' }}
                      />
                    </div>
                    <span className={`text-xs font-mono w-12 ${isPositive ? 'text-red-600' : 'text-green-600'}`}>
                      {value > 0 ? '+' : ''}{value.toFixed(3)}
                    </span>
                  </div>
                );
              })}
          </div>
          <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <div className="w-3 h-3 bg-red-400 rounded" /> Increases risk
            </span>
            <span className="flex items-center gap-1">
              <div className="w-3 h-3 bg-green-400 rounded" /> Decreases risk
            </span>
          </div>
        </div>
      )}

      {/* Interventions History */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <ClipboardList className="w-5 h-5" />
            Interventions
          </h3>
        </div>

        {interventions.length > 0 ? (
          <div className="space-y-3">
            {interventions.map(inv => (
              <div key={inv.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">
                      {inv.intervention_type === 'counseling' ? '🧠' :
                       inv.intervention_type === 'extra_class' ? '📚' :
                       inv.intervention_type === 'study_plan' ? '📋' :
                       inv.intervention_type === 'peer_mentoring' ? '🤝' :
                       inv.intervention_type === 'parent_meeting' ? '👨‍👩‍👧' : '📝'}
                    </span>
                    <span className="font-medium">{inv.title}</span>
                  </div>
                  <span className={`badge ${
                    inv.status === 'Completed' ? 'badge-low' :
                    inv.status === 'In Progress' ? 'bg-blue-100 text-blue-800' :
                    inv.status === 'Pending' ? 'badge-medium' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {inv.status}
                  </span>
                </div>
                {inv.description && (
                  <p className="text-sm text-gray-600 mb-2">{inv.description}</p>
                )}
                {inv.action_items && (
                  <div className="space-y-1 mb-2">
                    {inv.action_items.map((item, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-sm">
                        <CheckCircle className="w-3 h-3 text-gray-400 mt-0.5" />
                        <span className="text-gray-600">{item}</span>
                      </div>
                    ))}
                  </div>
                )}
                {inv.notes && (
                  <p className="text-sm text-gray-500 bg-gray-50 p-2 rounded mt-2">
                    <span className="font-medium">Notes:</span> {inv.notes}
                  </p>
                )}
                {inv.outcome && (
                  <p className="text-sm text-green-700 bg-green-50 p-2 rounded mt-2">
                    <span className="font-medium">Outcome:</span> {inv.outcome}
                  </p>
                )}
                <div className="text-xs text-gray-400 mt-2">
                  Scheduled: {inv.scheduled_date ? new Date(inv.scheduled_date).toLocaleDateString() : 'N/A'}
                  {inv.completed_date && ` | Completed: ${new Date(inv.completed_date).toLocaleDateString()}`}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <ClipboardList className="w-10 h-10 text-gray-300 mx-auto mb-2" />
            <p>No interventions recorded for this student yet.</p>
            <p className="text-sm mt-1">Go to Predictions page to see AI recommendations.</p>
          </div>
        )}
      </div>
    </div>
  );
}
