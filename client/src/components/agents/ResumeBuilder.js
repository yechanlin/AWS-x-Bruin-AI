// Unused standalone UI for the resume-tailor agent, reachable only via the unused Dashboard - not part of App.js's active wizard.
import React, { useState } from 'react';
import FileUploader from '../tools/FileUploader';
import LoadingSpinner from '../common/LoadingSpinner';
import ResultsDisplay from '../tools/ResultsDisplay';
import { useAgent } from '../../hooks/useAgent';

const ResumeBuilder = () => {
  const [jobDescription, setJobDescription] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const { loading, result, error, executeAgent } = useAgent();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!resumeFile || !jobDescription.trim()) return;
    
    await executeAgent('resume_tailor', {
      resume: resumeFile,
      jobDescription: jobDescription
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Resume Tailor</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Your Resume
          </label>
          <FileUploader onFileSelect={setResumeFile} />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Job Description
          </label>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the job description here..."
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        
        <button
          type="submit"
          disabled={loading || !resumeFile || !jobDescription.trim()}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? 'Tailoring Resume...' : 'Tailor Resume'}
        </button>
      </form>
      
      {loading && <LoadingSpinner message="Tailoring your resume..." />}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}
      {result && <ResultsDisplay result={result} title="Tailored Resume Suggestions" />}
    </div>
  );
};

export default ResumeBuilder;