// Unused generic result panel (string or pretty-printed JSON) used by the Dashboard's agent components.
import React from 'react';

const ResultsDisplay = ({ result, title = "Results" }) => {
  if (!result) return null;

  return (
    <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">{title}</h3>
      <div className="prose max-w-none">
        {typeof result === 'string' ? (
          <p className="whitespace-pre-wrap text-gray-700">{result}</p>
        ) : (
          <pre className="bg-white p-3 rounded border text-sm overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};

export default ResultsDisplay;