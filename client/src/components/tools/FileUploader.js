// Unused generic drag-and-drop file input used by the Dashboard's agent components.
import React from 'react';
import { useFileUpload } from '../../hooks/useFileUpload';

const FileUploader = ({ onFileSelect, accept = ".pdf,.doc,.docx" }) => {
  const { file, error, handleFileSelect, clearFile } = useFileUpload();

  const handleChange = (e) => {
    const selectedFile = e.target.files[0];
    handleFileSelect(selectedFile);
    if (onFileSelect) {
      onFileSelect(selectedFile);
    }
  };

  return (
    <div className="w-full">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
        <input
          type="file"
          accept={accept}
          onChange={handleChange}
          className="hidden"
          id="file-upload"
        />
        <label htmlFor="file-upload" className="cursor-pointer">
          <div className="text-gray-600">
            <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <p className="mt-2">Click to upload or drag and drop</p>
            <p className="text-sm text-gray-500">PDF, DOC, DOCX files only</p>
          </div>
        </label>
      </div>
      
      {file && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
          <div className="flex justify-between items-center">
            <span className="text-sm text-green-700">{file.name}</span>
            <button onClick={clearFile} className="text-red-500 hover:text-red-700">
              ×
            </button>
          </div>
        </div>
      )}
      
      {error && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}
    </div>
  );
};

export default FileUploader;