// Agent type keys/display names and accepted file MIME types, used by the unused Dashboard flow.
export const AGENT_TYPES = {
  RESUME_TAILOR: 'resume_tailor',
  INTERVIEW_COACH: 'interview_coach',
  APPLICATION_COACH: 'application_coach',
  INSTAGRAM_ANALYZER: 'instagram_analyzer',
  WEBSITE_ANALYZER: 'website_analyzer',
  SUMMARIZER: 'summarizer'
};

export const AGENT_NAMES = {
  [AGENT_TYPES.RESUME_TAILOR]: 'Resume Tailor',
  [AGENT_TYPES.INTERVIEW_COACH]: 'Interview Coach',
  [AGENT_TYPES.APPLICATION_COACH]: 'Application Coach',
  [AGENT_TYPES.INSTAGRAM_ANALYZER]: 'Instagram Analyzer',
  [AGENT_TYPES.WEBSITE_ANALYZER]: 'Website Analyzer',
  [AGENT_TYPES.SUMMARIZER]: 'Content Summarizer'
};

export const FILE_TYPES = {
  PDF: 'application/pdf',
  DOC: 'application/msword',
  DOCX: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
};