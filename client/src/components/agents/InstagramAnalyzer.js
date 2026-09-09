// Unused standalone UI for the Instagram-analyzer agent, reachable only via the unused Dashboard - not part of App.js's active wizard.
import React from 'react';
import URLInput from '../tools/URLInput';
import LoadingSpinner from '../common/LoadingSpinner';
import ResultsDisplay from '../tools/ResultsDisplay';
import { useAgent } from '../../hooks/useAgent';

const InstagramAnalyzer = () => {
  const { loading, result, error, executeAgent } = useAgent();

  const handleUrlSubmit = async (profileUrl) => {
    await executeAgent('instagram_analyzer', { profileUrl });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Instagram Profile Analyzer</h2>
      
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-blue-800">
          <strong>Note:</strong> This tool analyzes public Instagram profiles to provide professional insights 
          and recommendations for career development.
        </p>
      </div>
      
      <URLInput
        onUrlSubmit={handleUrlSubmit}
        placeholder="https://instagram.com/username"
        label="Instagram Profile URL"
      />
      
      {loading && <LoadingSpinner message="Analyzing Instagram profile..." />}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}
      {result && <ResultsDisplay result={result} title="Instagram Profile Analysis" />}
    </div>
  );
};

export default InstagramAnalyzer;