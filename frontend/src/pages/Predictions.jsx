import { useState, useEffect } from 'react';
import { uploadAPI, predictionAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { 
  AlertTriangle, ChevronDown, ChevronUp, Eye, 
  Target, BarChart3, User, ArrowRight
} from 'lucide-react';

export default function Predictions() {
  const navigate = useNavigate();
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [batchPredictions, setBatchPredictions] = useState(null);
  const [interventions, setInterventions] = useState(null);
  const [expandedStudent, setExpandedStudent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchBatches();
  }, []);

  const fetchBatches = async () => {
    try {
      const response = await uploadAPI.getBatches();
      setBatches(response.data.filter(b => b.processed));
    } catch (error) {
      console.error('Failed to fetch batches:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPredictions = async (batchId) => {
    setSelectedBatch(batchId);
    setLoading(true);
    try {
      // Fetch batch-level predictions
      const batch = batches.find(b => b.id === batchId);
      
      // Fetch auto interventions which contain student details
      const response = await predictionAPI.getAutoInterventions(batchId);
      setInterventions(response.data);
      setBatchPredictions({
        total_students: batch?.total_students || 0,
        at_risk_count: batch?.at_risk_count || 0,
        risk_distribution: { High: response.data.filter(s => s.risk_level === 'High').length, Critical: response.data.filter(s => s.risk_level === 'Critical').length, Medium: response.data.filter(s => s.risk_level === 'Medium').length, Low: response.data.filter(s => s.risk_level === 'Low').length }
      });
    } catch (error) {
      console.error('Failed to fetch predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredPredictions = interventions?.filter(p => {
    if (filter === 'all') return true;
    return p.risk_level === filter;
  });

  const getRiskBadgeClass = (level) => {
    const classes = {
      Low: 'badge-low',
      Medium: 'badge-medium',
      High: 'badge-high',
      Critical: 'badge-critical',
    };
    return classes[level] || '';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Predictions & Explanations</h1>
          <p className="text-gray-500 mt-1">View AI-generated risk predictions with SHAP explanations</p>
        </div>
      </div>

      {/* Batch Selection */}
      <div className="card">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Select Batch</h3>
        <div className="flex flex-wrap gap-2">
          {batches.map(batch => (
            <button
              key={batch.id}
              onClick={() => fetchPredictions(batch.id)}
              className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                selectedBatch === batch.id
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {batch.batch_name} ({batch.at_risk_count}/{batch.total_students} at-risk)
            </button>
          ))}
          {batches.length === 0 && (
            <p className="text-gray-500">No processed batches found. Upload data first.</p>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      {batchPredictions && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card text-center">
            <p className="text-2xl font-bold text-gray-900">{batchPredictions.total_students}</p>
            <p className="text-xs text-gray-500">Total Students</p>
          </div>
          <div className="card text-center border-red-200 bg-red-50">
            <p className="text-2xl font-bold text-red-600">{batchPredictions.at_risk_count}</p>
            <p className="text-xs text-red-500">At-Risk</p>
          </div>
          <div className="card text-center border-orange-200 bg-orange-50">
            <p className="text-2xl font-bold text-orange-600">{batchPredictions.risk_distribution?.High || 0}</p>
            <p className="text-xs text-orange-500">High Risk</p>
          </div>
          <div className="card text-center border-red-200 bg-red-50">
            <p className="text-2xl font-bold text-red-700">{batchPredictions.risk_distribution?.Critical || 0}</p>
            <p className="text-xs text-red-500">Critical</p>
          </div>
        </div>
      )}

      {/* Filter */}
      {interventions && interventions.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-gray-500">Filter:</span>
          {['all', 'Critical', 'High', 'Medium', 'Low'].map(level => (
            <button
              key={level}
              onClick={() => setFilter(level)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                filter === level
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {level === 'all' ? `All (${interventions.length})` : `${level} (${interventions.filter(s => s.risk_level === level).length})`}
            </button>
          ))}
        </div>
      )}

      {/* Predictions List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : filteredPredictions?.length > 0 ? (
        <div className="space-y-3">
          {filteredPredictions.map((student, idx) => (
            <div key={idx} className="card hover:shadow-md transition-shadow">
              {/* Student Header */}
              <div className="flex items-center justify-between">
                <div 
                  className="flex items-center gap-4 flex-1 cursor-pointer"
                  onClick={() => setExpandedStudent(expandedStudent === idx ? null : idx)}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    student.risk_level === 'Critical' ? 'bg-red-100 text-red-600' :
                    student.risk_level === 'High' ? 'bg-orange-100 text-orange-600' :
                    student.risk_level === 'Medium' ? 'bg-yellow-100 text-yellow-600' :
                    'bg-green-100 text-green-600'
                  }`}>
                    {student.risk_level === 'Critical' || student.risk_level === 'High' ? (
                      <AlertTriangle className="w-5 h-5" />
                    ) : (
                      <User className="w-5 h-5" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{student.student_name}</p>
                    <p className="text-sm text-gray-500">{student.student_id}</p>
                  </div>
                  <span className={`badge ${getRiskBadgeClass(student.risk_level)}`}>
                    {student.risk_level}
                  </span>
                  {expandedStudent === idx ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </div>

                {/* View Detail Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    // Navigate to student detail if we have the record id
                    navigate(`/predictions/student/${idx}`);
                  }}
                  className="ml-4 flex items-center gap-1 px-3 py-1.5 text-sm text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                >
                  <Eye className="w-4 h-4" />
                  Detail
                </button>
              </div>

              {/* Expanded Content */}
              {expandedStudent === idx && (
                <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
                  {/* Risk Factors */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                      <Target className="w-4 h-4" />
                      Why This Student is Flagged
                    </h4>
                    <div className="space-y-2">
                      {student.recommended_interventions?.slice(0, 3).map((intervention, i) => (
                        <div key={i} className="bg-gray-50 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-sm text-gray-700">
                              {intervention.title}
                            </span>
                            <span className={`badge ${
                              intervention.priority === 'Urgent' ? 'badge-critical' :
                              intervention.priority === 'High' ? 'badge-high' :
                              'badge-medium'
                            }`}>
                              {intervention.priority}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{intervention.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Recommended Interventions */}
                  {student.recommended_interventions && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        Recommended Interventions
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {student.recommended_interventions.map((intervention, i) => (
                          <div key={i} className="border border-gray-200 rounded-lg p-3">
                            <p className="font-medium text-sm">{intervention.title}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {intervention.intervention_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </p>
                            <p className="text-xs text-gray-400">
                              Schedule: {new Date(intervention.scheduled_date).toLocaleDateString()}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Action Items */}
                  {student.recommended_interventions?.[0]?.action_items && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Action Items</h4>
                      <div className="space-y-1">
                        {student.recommended_interventions[0].action_items.map((item, i) => (
                          <div key={i} className="flex items-start gap-2 text-sm text-gray-600">
                            <span className="text-gray-400">•</span>
                            {item}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : selectedBatch ? (
        <div className="card text-center py-12">
          <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No predictions match the current filter.</p>
        </div>
      ) : (
        <div className="card text-center py-12">
          <Eye className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Select a batch to view predictions</p>
        </div>
      )}
    </div>
  );
}
