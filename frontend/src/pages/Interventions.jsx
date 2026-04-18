import { useState, useEffect } from 'react';
import { interventionAPI, predictionAPI } from '../services/api';
import {
  ClipboardList, CheckCircle, Clock, AlertCircle,
  Filter, Plus, X, Save, Calendar, User
} from 'lucide-react';

const STATUS_COLORS = {
  'Pending': 'bg-yellow-100 text-yellow-800',
  'In Progress': 'bg-blue-100 text-blue-800',
  'Completed': 'bg-green-100 text-green-800',
  'Cancelled': 'bg-gray-100 text-gray-800',
};

const PRIORITY_COLORS = {
  'Urgent': 'bg-red-100 text-red-800',
  'High': 'bg-orange-100 text-orange-800',
  'Medium': 'bg-yellow-100 text-yellow-800',
  'Low': 'bg-green-100 text-green-800',
};

const TYPE_ICONS = {
  'counseling': '🧠',
  'extra_class': '📚',
  'study_plan': '📋',
  'peer_mentoring': '🤝',
  'parent_meeting': '👨‍👩‍👧',
  'monitoring': '👁️',
};

export default function Interventions() {
  const [interventions, setInterventions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedIntervention, setSelectedIntervention] = useState(null);
  const [updateNotes, setUpdateNotes] = useState('');
  const [updateStatus, setUpdateStatus] = useState('');

  useEffect(() => {
    fetchInterventions();
    fetchStats();
  }, [statusFilter]);

  const fetchInterventions = async () => {
    setLoading(true);
    try {
      const response = await interventionAPI.getAll(statusFilter !== 'all' ? statusFilter : null);
      setInterventions(response.data);
    } catch (error) {
      console.error('Failed to fetch interventions:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await interventionAPI.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleUpdateIntervention = async (id) => {
    try {
      const updateData = {};
      if (updateStatus) updateData.status = updateStatus;
      if (updateNotes) updateData.notes = updateNotes;
      if (updateStatus === 'Completed') {
        updateData.completed_date = new Date().toISOString();
      }

      await interventionAPI.update(id, updateData);
      setSelectedIntervention(null);
      setUpdateNotes('');
      setUpdateStatus('');
      fetchInterventions();
      fetchStats();
    } catch (error) {
      console.error('Failed to update intervention:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Interventions</h1>
          <p className="text-gray-500 mt-1">Track and manage student intervention plans</p>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-center gap-2 mb-1">
              <ClipboardList className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-blue-700">Total</span>
            </div>
            <p className="text-2xl font-bold text-blue-900">{stats.total}</p>
          </div>
          <div className="card bg-yellow-50 border-yellow-200">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-yellow-600" />
              <span className="text-sm text-yellow-700">Pending</span>
            </div>
            <p className="text-2xl font-bold text-yellow-900">{stats.pending}</p>
          </div>
          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-blue-700">In Progress</span>
            </div>
            <p className="text-2xl font-bold text-blue-900">{stats.in_progress}</p>
          </div>
          <div className="card bg-green-50 border-green-200">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-700">Completed</span>
            </div>
            <p className="text-2xl font-bold text-green-900">{stats.completed}</p>
            <p className="text-xs text-green-600">{stats.completion_rate}% rate</p>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="w-4 h-4 text-gray-400" />
        {['all', 'Pending', 'In Progress', 'Completed', 'Cancelled'].map(status => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === status
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {status === 'all' ? 'All' : status}
          </button>
        ))}
      </div>

      {/* Interventions List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : interventions.length > 0 ? (
        <div className="space-y-3">
          {interventions.map(intervention => (
            <div key={intervention.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="text-2xl mt-1">
                    {TYPE_ICONS[intervention.intervention_type] || '📝'}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-medium text-gray-900">{intervention.title}</h3>
                      <span className={`badge ${STATUS_COLORS[intervention.status]}`}>
                        {intervention.status}
                      </span>
                      <span className={`badge ${PRIORITY_COLORS[intervention.priority]}`}>
                        {intervention.priority}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {intervention.intervention_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </p>
                    {intervention.description && (
                      <p className="text-sm text-gray-600 mt-2">{intervention.description}</p>
                    )}
                    
                    {/* Action Items */}
                    {intervention.action_items && intervention.action_items.length > 0 && (
                      <div className="mt-3 space-y-1">
                        {intervention.action_items.map((item, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-sm">
                            <span className="text-gray-400 mt-0.5">•</span>
                            <span className="text-gray-600">{item}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Meta Info */}
                    <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {intervention.scheduled_date 
                          ? new Date(intervention.scheduled_date).toLocaleDateString() 
                          : 'Not scheduled'}
                      </span>
                      {intervention.follow_up_date && (
                        <span>
                          Follow-up: {new Date(intervention.follow_up_date).toLocaleDateString()}
                        </span>
                      )}
                      <span>
                        Created: {new Date(intervention.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    {/* Notes */}
                    {intervention.notes && (
                      <div className="mt-3 p-2 bg-gray-50 rounded text-sm text-gray-600">
                        <span className="font-medium">Notes:</span> {intervention.notes}
                      </div>
                    )}

                    {/* Outcome */}
                    {intervention.outcome && (
                      <div className="mt-2 p-2 bg-green-50 rounded text-sm text-green-700">
                        <span className="font-medium">Outcome:</span> {intervention.outcome}
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 ml-4">
                  {intervention.status !== 'Completed' && intervention.status !== 'Cancelled' && (
                    <button
                      onClick={() => setSelectedIntervention(intervention)}
                      className="p-2 hover:bg-gray-100 rounded-lg text-gray-500"
                      title="Update"
                    >
                      <Save className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <ClipboardList className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">
            {statusFilter === 'all' 
              ? 'No interventions yet. Run predictions to see recommendations.' 
              : `No ${statusFilter.toLowerCase()} interventions.`}
          </p>
        </div>
      )}

      {/* Update Modal */}
      {selectedIntervention && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Update Intervention</h3>
              <button
                onClick={() => {
                  setSelectedIntervention(null);
                  setUpdateNotes('');
                  setUpdateStatus('');
                }}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-sm text-gray-600 mb-4">{selectedIntervention.title}</p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={updateStatus}
                  onChange={(e) => setUpdateStatus(e.target.value)}
                  className="input-field"
                >
                  <option value="">Select status...</option>
                  <option value="Pending">Pending</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Completed">Completed</option>
                  <option value="Cancelled">Cancelled</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={updateNotes}
                  onChange={(e) => setUpdateNotes(e.target.value)}
                  className="input-field h-24 resize-none"
                  placeholder="Add notes about the intervention..."
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    setSelectedIntervention(null);
                    setUpdateNotes('');
                    setUpdateStatus('');
                  }}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleUpdateIntervention(selectedIntervention.id)}
                  className="btn-primary flex-1"
                >
                  Save Update
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
