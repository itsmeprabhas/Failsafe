import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Shield, AlertCircle } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    /* Outer Container: Full screen height + extra vertical padding for perfect centering */
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-900 via-primary-800 to-primary-700 px-4 py-16">
      <div className="max-w-md w-full">
        
        {/* Logo / Header Section with generous gap */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-white/10 backdrop-blur-sm rounded-2xl mb-6 shadow-lg border border-white/20">
            <Shield className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-extrabold text-white tracking-tight">FAILSAFE</h1>
          <p className="text-primary-200 mt-3 text-lg font-light tracking-wide">
            Student Risk Prediction System
          </p>
        </div>

        {/* Login Card with shadow and spacing */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 space-y-6 border border-white/10">
          <h2 className="text-xl font-semibold text-gray-800">Sign In</h2>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3 text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-700">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all text-gray-900 placeholder-gray-400"
                placeholder="Enter your username"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-700">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all text-gray-900 placeholder-gray-400"
                placeholder="Enter your password"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3.5 rounded-xl transition-colors duration-200 shadow-md hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-base"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Authenticating...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Demo Credentials Section with added gaps */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-4 text-center">
              Demo Credentials
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 hover:bg-gray-100 transition-colors">
                <p className="font-bold text-gray-800 text-sm">Admin</p>
                <p className="text-gray-500 text-xs mt-1 font-mono">admin / admin123</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 hover:bg-gray-100 transition-colors">
                <p className="font-bold text-gray-800 text-sm">Faculty</p>
                <p className="text-gray-500 text-xs mt-1 font-mono">faculty1 / faculty123</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Footer text */}
        <p className="text-center text-primary-300/60 text-xs mt-8 tracking-wide">
          © 2024 FAILSAFE • Powered by XGBoost & SHAP
        </p>
      </div>
    </div>
  );
}
