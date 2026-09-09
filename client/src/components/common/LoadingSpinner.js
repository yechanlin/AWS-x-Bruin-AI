// Unused generic spinner used by the Dashboard's agent components while a request is in flight.
import React from 'react';

const LoadingSpinner = ({ message = 'Processing...' }) => {
  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <p className="mt-4 text-gray-600">{message}</p>
    </div>
  );
};

export default LoadingSpinner;