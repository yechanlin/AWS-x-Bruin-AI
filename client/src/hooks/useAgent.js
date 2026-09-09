// Unused hook that dispatches to agentService by agent-type string and tracks loading/result/error state, for the Dashboard flow.
import { useState } from 'react';
import { agentService } from '../services/agentService';

export const useAgent = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const executeAgent = async (agentType, params) => {
    setLoading(true);
    setError(null);
    
    try {
      let response;
      switch (agentType) {
        case 'resume_tailor':
          response = await agentService.tailorResume(params.resume, params.jobDescription);
          break;
        case 'interview_coach':
          response = await agentService.coachInterview(params.jobDescription, params.experience);
          break;
        case 'application_coach':
          response = await agentService.coachApplication(params.resume, params.jobDescription);
          break;
        case 'instagram_analyzer':
          response = await agentService.analyzeInstagram(params.profileUrl);
          break;
        case 'website_analyzer':
          response = await agentService.analyzeWebsite(params.websiteUrl);
          break;
        case 'summarizer':
          response = await agentService.summarizeContent(params.content);
          break;
        default:
          throw new Error('Unknown agent type');
      }
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { loading, result, error, executeAgent };
};