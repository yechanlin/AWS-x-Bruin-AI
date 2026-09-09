// Unused standalone UI for the website-analyzer agent, reachable only via the unused Dashboard - not part of App.js's active wizard.
import React from 'react';
import URLInput from '../tools/URLInput';
import LoadingSpinner from '../common/LoadingSpinner';
import ResultsDisplay from '../tools/ResultsDisplay';
import { useAgent } from '../../hooks/useAgent';

const WebsiteAnalyzer = () => {
  const { loading, result, error, executeAgent } = useAgent();

  const handleUrlSubmit = async (websiteUrl) => {
    await executeAgent('website_analyzer', { websiteUrl });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Website Analyzer</h2>
      
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
        <p className="text-green-800">
          <strong>Tip:</strong> Analyze company websites, job boards, or any web content 
          to extract key information and insights.
        </p>
      </div>
      
      <URLInput
        onUrlSubmit={handleUrlSubmit}
        placeholder="https://example.com"
        label="Website URL"
      />
      
      {loading && <LoadingSpinner message="Analyzing website content..." />}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}
      {result && <ResultsDisplay result={result} title="Website Analysis" />}
    </div>
  );
};

export default WebsiteAnalyzer;