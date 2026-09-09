// Per-agent API call helpers (tailorResume, coachInterview, etc.) used by the unused Dashboard flow, not by the active App.js.
import ApiService from './api';

export const agentService = {
  async tailorResume(resumeFile, jobDescription, clubName, schoolName) {
    // Upload the file first, then call the tailor endpoint with the server path
    const up = await ApiService.uploadFile('/upload/resume', resumeFile);
    return ApiService.post('/agents/resume-tailor', {
      resume_path: up.resume_path,
      job_description: jobDescription,
      club_name: clubName,
      school_name: schoolName,
    });
  },

  async coachInterview(jobDescription, experience) {
    return ApiService.post('/agents/interview-coach', {
      job_description: jobDescription,
      experience: experience
    });
  },

  async coachApplication(resumeFile, jobDescription) {
    // Application coach doesn't need the resume file directly; send only description.
    return ApiService.post('/agents/application-coach', {
      job_description: jobDescription
    });
  },

  async analyzeInstagram(profileUrl) {
    return ApiService.post('/agents/instagram-analyzer', {
      profile_url: profileUrl
    });
  },

  async analyzeWebsite(websiteUrl) {
    return ApiService.post('/agents/website-analyzer', {
      website_url: websiteUrl
    });
  },

  async summarizeContent(content) {
    return ApiService.post('/agents/summarizer', {
      content: content
    });
  }
};
