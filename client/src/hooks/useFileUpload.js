// Unused hook backing FileUploader: validates file type and reads its content for preview.
import { useState } from 'react';
import { FILE_TYPES } from '../utils/constants';

export const useFileUpload = () => {
  const [file, setFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [error, setError] = useState(null);

  const handleFileSelect = (selectedFile) => {
    setError(null);
    
    if (!selectedFile) {
      setFile(null);
      setFileContent('');
      return;
    }

    const validTypes = Object.values(FILE_TYPES);
    if (!validTypes.includes(selectedFile.type)) {
      setError('Please select a valid PDF or Word document');
      return;
    }

    setFile(selectedFile);
    
    // Read file content for preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setFileContent(e.target.result);
    };
    reader.readAsText(selectedFile);
  };

  const clearFile = () => {
    setFile(null);
    setFileContent('');
    setError(null);
  };

  return {
    file,
    fileContent,
    error,
    handleFileSelect,
    clearFile
  };
};