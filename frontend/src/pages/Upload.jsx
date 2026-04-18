import { useState, useRef } from 'react';
import { uploadAPI, predictionAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [metadata, setMetadata] = useState({
    batch_name: '',
    semester: 'Fall 2024',
    academic_year: '2024-2025',
    subject: '',
  });
  const [uploading, setUploading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef();
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setError('');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const response = await uploadAPI.uploadCSV(file, metadata);
      setResult(response.data);
      
      // Auto-run predictions
      setPredicting(true);
      try {
        const predResponse = await predictionAPI.runPredictions(response.data.batch_id);
        setResult({ ...response.data, predictions: predResponse.data });
      } catch (predError) {
        console.error('Prediction error:', predError);
      }
      setPredicting(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    const headers = 'student_id,student_name,attendance_percentage,assignment_avg,midterm_score,quiz_avg,lab_score,previous_gpa,study_hours_per_week,extracurricular_activities,socioeconomic_status,parent_education,internet_access';
    const example = 'STU0001,John Doe,75,65,70,60,80,3.2,12,1,Medium,Bachelor,1';
    const csv = headers + '\n' + example;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'student_data_template.csv';
    a.click();
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload Student Data</h1>
        <p className="text-gray-500 mt-1">
          Upload CSV file with student performance data for risk analysis
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {result?.predictions && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2 text-green-700 mb-2">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">Analysis Complete!</span>
          </div>
          <div className="grid grid-cols-3 gap-4 mt-3">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">{result.total_students}</p>
              <p className="text-xs text-gray-500">Total Students</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">{result.predictions.at_risk_count}</p>
              <p className="text-xs text-gray-500">At-Risk Students</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">
                {result.predictions.risk_distribution?.High || 0}
              </p>
              <p className="text-xs text-gray-500">High Risk</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/predictions')}
            className="btn-primary mt-4 w-full"
          >
            View Detailed Predictions
          </button>
        </div>
      )}

      <form onSubmit={handleUpload} className="card space-y-4">
        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Batch Name</label>
            <input
              type="text"
              value={metadata.batch_name}
              onChange={(e) => setMetadata({ ...metadata, batch_name: e.target.value })}
              className="input-field"
              placeholder="e.g., CS101 Section A"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
            <input
              type="text"
              value={metadata.subject}
              onChange={(e) => setMetadata({ ...metadata, subject: e.target.value })}
              className="input-field"
              placeholder="e.g., Data Structures"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Semester</label>
            <select
              value={metadata.semester}
              onChange={(e) => setMetadata({ ...metadata, semester: e.target.value })}
              className="input-field"
            >
              <option>Fall 2024</option>
              <option>Spring 2024</option>
              <option>Summer 2024</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Academic Year</label>
            <input
              type="text"
              value={metadata.academic_year}
              onChange={(e) => setMetadata({ ...metadata, academic_year: e.target.value })}
              className="input-field"
            />
          </div>
        </div>

        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">CSV File</label>
          <div
            onClick={() => fileInputRef.current.click()}
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary-500 transition-colors"
          >
            {file ? (
              <div className="flex items-center justify-center gap-3">
                <FileSpreadsheet className="w-8 h-8 text-green-500" />
                <div className="text-left">
                  <p className="font-medium text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
            ) : (
              <div>
                <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600">Click to select CSV file</p>
                <p className="text-sm text-gray-400 mt-1">or drag and drop</p>
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-4">
          <button
            type="button"
            onClick={downloadTemplate}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            Download Template CSV
          </button>
          <button
            type="submit"
            disabled={uploading || predicting || !file}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            {(uploading || predicting) && <Loader2 className="w-4 h-4 animate-spin" />}
            {uploading ? 'Uploading...' : predicting ? 'Analyzing...' : 'Upload & Analyze'}
          </button>
        </div>
      </form>

      {/* Required Columns Info */}
      <div className="card bg-blue-50 border-blue-200">
        <h4 className="font-medium text-blue-800 mb-2">Required CSV Columns</h4>
        <div className="grid grid-cols-2 gap-2 text-sm text-blue-700">
          <span className="font-mono">student_id*</span>
          <span className="font-mono">student_name*</span>
          <span className="font-mono">attendance_percentage*</span>
          <span className="font-mono">assignment_avg*</span>
          <span className="font-mono">midterm_score</span>
          <span className="font-mono">quiz_avg</span>
          <span className="font-mono">lab_score</span>
          <span className="font-mono">previous_gpa</span>
          <span className="font-mono">study_hours_per_week</span>
          <span className="font-mono">extracurricular_activities</span>
          <span className="font-mono">socioeconomic_status</span>
          <span className="font-mono">parent_education</span>
          <span className="font-mono">internet_access</span>
        </div>
        <p className="text-xs text-blue-600 mt-2">* = Required columns</p>
      </div>
    </div>
  );
}
