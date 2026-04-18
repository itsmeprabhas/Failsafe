import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { adminAPI } from '../services/api';
import {
  Shield, Key, User, Bell, Database,
  AlertTriangle, Trash2, RefreshCw, CheckCircle, XCircle, Loader2
} from 'lucide-react';

// ── Confirmation Modal ────────────────────────────────────────────────────────
function ConfirmModal({ action, onConfirm, onCancel }) {
  const [typed, setTyped] = useState('');
  const needsConfirm = action.confirmWord;
  const ready = !needsConfirm || typed === needsConfirm;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-red-50 border-b border-red-100 px-6 py-5 flex items-start gap-3">
          <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0 mt-0.5">
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <h3 className="font-bold text-gray-900 text-lg">{action.title}</h3>
            <p className="text-sm text-gray-500 mt-0.5">{action.subtitle}</p>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          <p className="text-sm text-gray-700">{action.description}</p>

          {/* Consequences list */}
          <ul className="space-y-1.5">
            {action.consequences.map((c, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-red-700">
                <XCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-500" />
                {c}
              </li>
            ))}
          </ul>

          {/* Type-to-confirm */}
          {needsConfirm && (
            <div className="pt-2 space-y-2">
              <p className="text-sm font-medium text-gray-700">
                Type <span className="font-mono bg-red-50 text-red-600 px-1.5 py-0.5 rounded border border-red-200">{action.confirmWord}</span> to confirm:
              </p>
              <input
                type="text"
                value={typed}
                onChange={e => setTyped(e.target.value)}
                placeholder={action.confirmWord}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-red-400"
                autoFocus
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={!ready}
            className="px-4 py-2 text-sm font-semibold text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            {action.buttonLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Toast Notification ────────────────────────────────────────────────────────
function Toast({ toast }) {
  if (!toast) return null;
  const isSuccess = toast.type === 'success';
  return (
    <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-4 rounded-xl shadow-xl text-sm font-medium transition-all
      ${isSuccess ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
      {isSuccess
        ? <CheckCircle className="w-5 h-5 flex-shrink-0" />
        : <XCircle className="w-5 h-5 flex-shrink-0" />}
      {toast.message}
    </div>
  );
}

// ── Danger Zone Card ──────────────────────────────────────────────────────────
function DangerCard({ title, description, badge, buttonLabel, icon: Icon, onAction, loading }) {
  return (
    <div className="flex items-start justify-between gap-4 p-5 border border-red-100 bg-red-50/40 rounded-xl">
      <div className="flex items-start gap-3 min-w-0">
        <div className="w-9 h-9 rounded-lg bg-red-100 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Icon className="w-4 h-4 text-red-600" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-semibold text-gray-900 text-sm">{title}</p>
            {badge && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium border border-red-200">
                {badge}
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1 leading-relaxed">{description}</p>
        </div>
      </div>
      <button
        onClick={onAction}
        disabled={loading}
        className="flex-shrink-0 flex items-center gap-2 px-4 py-2 text-sm font-semibold text-red-600 border border-red-300 bg-white rounded-lg hover:bg-red-600 hover:text-white hover:border-red-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
        {buttonLabel}
      </button>
    </div>
  );
}

// ── Main Settings Component ───────────────────────────────────────────────────
export default function Settings() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [pendingAction, setPendingAction] = useState(null);
  const [loadingAction, setLoadingAction] = useState(null);
  const [toast, setToast] = useState(null);

  const tabs = [
    { id: 'profile',       label: 'Profile',       icon: User },
    { id: 'security',      label: 'Security',       icon: Key },
    { id: 'notifications', label: 'Notifications',  icon: Bell },
    { id: 'system',        label: 'System Info',    icon: Database },
    ...(user?.role === 'admin' ? [{ id: 'danger', label: 'Danger Zone', icon: AlertTriangle }] : []),
  ];

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const RESET_ACTIONS = [
    {
      id: 'resetPredictions',
      title: 'Clear Prediction Results',
      subtitle: 'Keeps student records and batches',
      description: 'Clears all AI-generated risk scores and SHAP explanations. Student records and batch metadata are kept — you can re-run predictions at any time.',
      consequences: [
        'All risk scores (Low/Medium/High/Critical) will be erased',
        'All SHAP explanation values will be removed',
        'Batches will be marked as unprocessed',
        'Student names, IDs, and academic data are preserved',
      ],
      badge: 'Reversible',
      buttonLabel: 'Clear Predictions',
      icon: RefreshCw,
      apiFn: () => adminAPI.resetPredictions(),
      confirmWord: null,
    },
    {
      id: 'resetInterventions',
      title: 'Delete All Interventions',
      subtitle: 'Permanently removes all intervention records',
      description: 'Deletes every intervention plan assigned to at-risk students. This cannot be undone.',
      consequences: [
        'All counseling, tutoring, and mentoring plans deleted',
        'Intervention status history removed',
        'Student predictions are NOT affected',
      ],
      badge: 'Irreversible',
      buttonLabel: 'Delete Interventions',
      icon: Trash2,
      apiFn: () => adminAPI.resetInterventions(),
      confirmWord: null,
    },
    {
      id: 'resetStudentData',
      title: 'Reset All Student Data',
      subtitle: 'Deletes batches, records, predictions & interventions',
      description: 'Removes all uploaded student data, all batches, all predictions, and all interventions. User accounts are preserved. Type RESET to proceed.',
      consequences: [
        'All data batches permanently deleted',
        'All student records permanently deleted',
        'All risk predictions removed',
        'All interventions removed',
        'Dashboard will be reset to zero',
      ],
      badge: 'Destructive',
      buttonLabel: 'Reset Student Data',
      icon: Database,
      apiFn: () => adminAPI.resetStudentData(),
      confirmWord: 'RESET',
    },
    {
      id: 'resetAll',
      title: 'Full System Reset',
      subtitle: 'Wipes everything — all data and all users',
      description: 'Nuclear option. Removes all student data AND all user accounts except yours. The system will be as if newly installed. Type WIPE ALL to proceed.',
      consequences: [
        'All student data, batches, predictions, interventions — permanently gone',
        'All user accounts deleted (except your admin account)',
        'System returns to fresh-install state',
        'This action CANNOT be undone',
      ],
      badge: 'Nuclear',
      buttonLabel: 'Full Reset',
      icon: AlertTriangle,
      apiFn: () => adminAPI.resetAll(),
      confirmWord: 'WIPE ALL',
    },
  ];

  const handleActionClick = (action) => setPendingAction(action);

  const handleConfirm = async () => {
    if (!pendingAction) return;
    const action = pendingAction;
    setPendingAction(null);
    setLoadingAction(action.id);
    try {
      const res = await action.apiFn();
      showToast(res.data.message || 'Reset successful.', 'success');
    } catch (err) {
      const detail = err.response?.data?.detail || 'Operation failed.';
      showToast(detail, 'error');
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Manage your account and system preferences</p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar tabs */}
        <div className="w-48 space-y-1 flex-shrink-0">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm transition-colors ${
                activeTab === tab.id
                  ? tab.id === 'danger'
                    ? 'bg-red-50 text-red-700 font-medium'
                    : 'bg-primary-50 text-primary-700 font-medium'
                  : tab.id === 'danger'
                    ? 'text-red-500 hover:bg-red-50'
                    : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content area */}
        <div className="flex-1 min-w-0">

          {/* ── Profile ── */}
          {activeTab === 'profile' && (
            <div className="card space-y-4">
              <h3 className="text-lg font-semibold">Profile Information</h3>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold text-primary-700">
                    {user?.full_name?.charAt(0)}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">{user?.full_name}</p>
                  <p className="text-sm text-gray-500 capitalize">{user?.role} • {user?.department}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <input type="text" defaultValue={user?.full_name} className="input-field" disabled />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input type="email" defaultValue={user?.email} className="input-field" disabled />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                  <input type="text" defaultValue={user?.username} className="input-field" disabled />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                  <input type="text" defaultValue={user?.department || 'N/A'} className="input-field" disabled />
                </div>
              </div>
              <p className="text-xs text-gray-400">Contact administrator to update profile information.</p>
            </div>
          )}

          {/* ── Security ── */}
          {activeTab === 'security' && (
            <div className="card space-y-4">
              <h3 className="text-lg font-semibold">Security Settings</h3>
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-700">
                  Password changes require administrator approval for security reasons.
                </p>
              </div>
              <div className="space-y-3">
                {[
                  { label: 'Two-Factor Authentication', desc: 'Add an extra layer of security' },
                  { label: 'Session Management', desc: 'View and manage active sessions' },
                ].map(item => (
                  <div key={item.label} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-sm">{item.label}</p>
                      <p className="text-xs text-gray-500">{item.desc}</p>
                    </div>
                    <span className="badge badge-medium">Coming Soon</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Notifications ── */}
          {activeTab === 'notifications' && (
            <div className="card space-y-4">
              <h3 className="text-lg font-semibold">Notification Preferences</h3>
              {[
                { label: 'Critical risk alerts', desc: 'Get notified when a student is flagged as Critical risk' },
                { label: 'Intervention reminders', desc: 'Reminders for upcoming intervention schedules' },
                { label: 'Weekly summary', desc: 'Weekly digest of risk trends and intervention progress' },
                { label: 'System updates', desc: 'Notifications about model updates and system maintenance' },
              ].map(item => (
                <div key={item.label} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{item.label}</p>
                    <p className="text-xs text-gray-500">{item.desc}</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>
              ))}
            </div>
          )}

          {/* ── System Info ── */}
          {activeTab === 'system' && (
            <div className="card space-y-4">
              <h3 className="text-lg font-semibold">System Information</h3>
              <div className="space-y-3">
                {[
                  { label: 'Model Version', value: 'XGBoost 2.0.3' },
                  { label: 'Explainability', value: 'SHAP 0.44.1' },
                  { label: 'Backend', value: 'FastAPI 0.109.2' },
                  { label: 'Database', value: 'PostgreSQL 15' },
                  { label: 'Authentication', value: 'JWT (HS256)' },
                  { label: 'Features Used', value: '11 student performance indicators' },
                  { label: 'Target Variable', value: 'At-Risk (Binary Classification)' },
                ].map(item => (
                  <div key={item.label} className="flex justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">{item.label}</span>
                    <span className="text-sm font-medium text-gray-900">{item.value}</span>
                  </div>
                ))}
              </div>
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-700">
                  <strong>Model Training:</strong> The model was trained on student performance data using
                  XGBoost with optimized hyperparameters. SHAP values provide local explanations for each
                  prediction, making the system transparent and trustworthy for non-technical faculty.
                </p>
              </div>
            </div>
          )}

          {/* ── Danger Zone ── */}
          {activeTab === 'danger' && (
            <div className="space-y-5">
              {/* Header banner */}
              <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl">
                <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-red-800 text-sm">Danger Zone — Admin Only</p>
                  <p className="text-xs text-red-600 mt-0.5">
                    Actions here are permanent and may be irreversible. Proceed with extreme caution.
                    Only the System Administrator can access these controls.
                  </p>
                </div>
              </div>

              {/* Action cards */}
              <div className="space-y-3">
                {RESET_ACTIONS.map(action => (
                  <DangerCard
                    key={action.id}
                    title={action.title}
                    description={action.description}
                    badge={action.badge}
                    buttonLabel={action.buttonLabel}
                    icon={action.icon}
                    loading={loadingAction === action.id}
                    onAction={() => handleActionClick(action)}
                  />
                ))}
              </div>

              {/* Footer note */}
              <p className="text-xs text-gray-400 text-center pt-2">
                All reset actions are logged. Contact your database administrator to restore from backups.
              </p>
            </div>
          )}

        </div>
      </div>

      {/* Confirmation Modal */}
      {pendingAction && (
        <ConfirmModal
          action={pendingAction}
          onConfirm={handleConfirm}
          onCancel={() => setPendingAction(null)}
        />
      )}

      {/* Toast */}
      <Toast toast={toast} />
    </div>
  );
}
