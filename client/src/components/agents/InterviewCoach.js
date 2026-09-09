// Unused standalone UI for the interview-coach agent, reachable only via the unused Dashboard - not part of App.js's active wizard.
import React, { useState } from 'react';
import LoadingSpinner from '../common/LoadingSpinner';
import ResultsDisplay from '../tools/ResultsDisplay';
import { useAgent } from '../../hooks/useAgent';

const InterviewCoach = () => {
  const [jobDescription, setJobDescription] = useState('');
  const [experience, setExperience] = useState('');
  const { loading, result, error, executeAgent } = useAgent();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!jobDescription.trim() || !experience.trim()) return;
    
    await executeAgent('interview_coach', {
      jobDescription,
      experience
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Interview Coach</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Job Description
          </label>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the job description here..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Experience & Background
          </label>
          <textarea
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
            placeholder="Describe your relevant experience, skills, and background..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        
        <button
          type="submit"
          disabled={loading || !jobDescription.trim() || !experience.trim()}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? 'Preparing Interview Tips...' : 'Get Interview Coaching'}
        </button>
      </form>
      
      {loading && <LoadingSpinner message="Preparing your interview coaching..." />}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}
      {result && <ResultsDisplay result={result} title="Interview Coaching Tips" />}
    </div>
  );
};

export default InterviewCoach;