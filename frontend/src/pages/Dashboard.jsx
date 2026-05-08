import { useState, useEffect } from 'react';
import { dashboardAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { 
  Users, AlertTriangle, TrendingUp, TrendingDown, CheckCircle, 
  BarChart3, ArrowUpRight, ArrowDownRight, Activity, Zap
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend,
  RadialBarChart, RadialBar
} from 'recharts';

const RISK_COLORS = {
  Low: '#22c55e',
  Medium: '#f59e0b',
  High: '#f97316',
  Critical: '#ef4444',
};

export default function Dashboard() {
  const { user } = useAuth();
  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState(null);
  const [topStudents, setTopStudents] = useState([]);
  const [semesterData, setSemesterData] = useState([]);
  const [improvement, setImprovement] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [overviewRes, trendsRes, studentsRes, semesterRes, improvementRes] = await Promise.all([
        dashboardAPI.getOverview(),
        dashboardAPI.getRiskTrends(30),
        dashboardAPI.getTopRiskStudents(10),
        dashboardAPI.getSemesterComparison(),
        dashboardAPI.getImprovementMetrics(),
      ]);
      setOverview(overviewRes.data);
      setTrends(trendsRes.data);
      setTopStudents(studentsRes.data);
      setSemesterData(semesterRes.data);
      setImprovement(improvementRes.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !overview) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const pieData = Object.entries(overview.risk_distribution || {}).map(
    ([name, value]) => ({ name, value })
  );

  const trendChartData = trends?.dates?.map((date, index) => ({
    date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    at_risk: trends.at_risk_counts[index],
    total: trends.total_counts[index],
  })) || [];

  const semesterChartData = semesterData.map(s => ({
    name: `${s.semester} ${s.academic_year}`,
    at_risk_pct: s.at_risk_percentage,
    avg_risk: Math.round(s.avg_risk_score * 100),
    improvement: s.improvement_rate,
    total: s.total_students,
  }));

  const stats = [
    {
      title: 'Total Students',
      value: overview.total_students,
      icon: Users,
      color: 'bg-blue-500',
      change: null,
    },
    {
      title: 'At-Risk Students',
      value: overview.at_risk_students,
      icon: AlertTriangle,
      color: 'bg-red-500',
      change: `${overview.at_risk_percentage}%`,
    },
    {
      title: 'Batches Processed',
      value: overview.batches_processed,
      icon: BarChart3,
      color: 'bg-purple-500',
      change: null,
    },
    {
      title: 'Interventions Done',
      value: overview.intervention_stats.completed,
      icon: CheckCircle,
      color: 'bg-green-500',
      change: `${overview.intervention_stats.completion_rate}%`,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500">Welcome back, {user?.full_name}</p>
        </div>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.title} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{stat.title}</p>
                <p className="text-2xl font-bold mt-1">{stat.value}</p>
                {stat.change && (
                  <p className="text-xs text-gray-500 mt-1">
                    {stat.change} of total
                  </p>
                )}
              </div>
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Improvement Metrics Banner */}
      {improvement && improvement.total_with_interventions > 0 && (
        <div className="card bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200">
          <div className="flex items-center gap-6 flex-wrap">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                <TrendingDown className="w-6 h-6 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-emerald-700 font-medium">Intervention Effectiveness</p>
                <p className="text-2xl font-bold text-emerald-900">{improvement.improvement_rate}%</p>
              </div>
            </div>
            <div className="h-12 w-px bg-emerald-200 hidden md:block" />
            <div>
              <p className="text-sm text-emerald-700">{improvement.improved_count} of {improvement.total_with_interventions} students improved</p>
              <p className="text-xs text-emerald-600">Avg. risk reduction: {Math.abs(improvement.avg_risk_reduction * 100).toFixed(1)}%</p>
            </div>
            {Object.keys(improvement.intervention_effectiveness || {}).length > 0 && (
              <>
                <div className="h-12 w-px bg-emerald-200 hidden md:block" />
                <div className="flex flex-wrap gap-2">
                  {Object.entries(improvement.intervention_effectiveness).map(([type, rate]) => (
                    <span key={type} className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-lg">
                      {type.replace('_', ' ')}: {rate}%
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Pie Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Risk Distribution</h3>
          {pieData.length > 0 ? (
            <div className="flex items-center">
              <ResponsiveContainer width="60%" height={250}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry) => (
                      <Cell 
                        key={entry.name} 
                        fill={RISK_COLORS[entry.name] || '#94a3b8'} 
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 ml-4">
                {pieData.map((item) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: RISK_COLORS[item.name] }}
                    />
                    <span className="text-sm text-gray-600">
                      {item.name}: {item.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available</p>
          )}
        </div>

        {/* Risk Trends Line Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Risk Trends (30 Days)</h3>
          {trendChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="at_risk" 
                  stroke="#ef4444" 
                  strokeWidth={2}
                  name="At-Risk"
                />
                <Line 
                  type="monotone" 
                  dataKey="total" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  name="Total"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No trend data available</p>
          )}
        </div>
      </div>

      {/* Semester Comparison */}
      {semesterChartData.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold">Semester-over-Semester Comparison</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={semesterChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="at_risk_pct" fill="#f97316" name="At-Risk %" radius={[4, 4, 0, 0]} />
              <Bar dataKey="avg_risk" fill="#ef4444" name="Avg Risk Score" radius={[4, 4, 0, 0]} />
              <Bar dataKey="improvement" fill="#22c55e" name="Improvement %" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top Risk Students Table */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Highest Risk Students</h3>
          <span className="text-sm text-gray-500">Top {topStudents.length}</span>
        </div>
        {topStudents.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Student</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Risk Score</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Risk Level</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Top Factors</th>
                </tr>
              </thead>
              <tbody>
                {topStudents.map((student) => (
                  <tr key={student.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div>
                        <p className="font-medium text-gray-900">{student.student_name}</p>
                        <p className="text-xs text-gray-500">{student.student_id}</p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-mono font-medium">
                        {(student.risk_score * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`badge badge-${student.risk_level.toLowerCase()}`}>
                        {student.risk_level}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {student.top_factors.map((factor, idx) => (
                          <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                            {factor}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">
            No at-risk students identified yet. Upload data and run predictions.
          </p>
        )}
      </div>
    </div>
  );
}
