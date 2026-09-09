// The active application: the 3-step club-application wizard (club info -> profile -> questions) that calls POST /agents/application-coach and renders the results.
import React, { useState } from 'react';
// Local CSS disabled to avoid PostCSS build during demo.
import ApiService from './services/api';

const ClubInfoPage = ({ clubInfo, handleClubInputChange, handleClubSubmit }) => (
  <div className="form-container">
    <h1 className="glitch-text">Club Application Assistant</h1>
    <p className="subtitle">Let's start by gathering some information about the club you want to apply to.</p>
    
    <form onSubmit={handleClubSubmit} className="tech-form">
      <div className="form-group">
        <label htmlFor="clubName">Club Name *</label>
        <input
          type="text"
          id="clubName"
          name="clubName"
          value={clubInfo.clubName}
          onChange={handleClubInputChange}
          placeholder="Enter the club name"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="schoolName">School Name *</label>
        <input
          type="text"
          id="schoolName"
          name="schoolName"
          value={clubInfo.schoolName}
          onChange={handleClubInputChange}
          placeholder="Enter the school name"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="position">Position/Role *</label>
        <input
          type="text"
          id="position"
          name="position"
          value={clubInfo.position}
          onChange={handleClubInputChange}
          placeholder="e.g., Software Engineer, Marketing Director, General Member"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="clubWebsite">Club Website</label>
        <input
          type="url"
          id="clubWebsite"
          name="clubWebsite"
          value={clubInfo.clubWebsite}
          onChange={handleClubInputChange}
          placeholder="https://example.com"
        />
      </div>

      <div className="form-group">
        <label htmlFor="clubInstagram">Club Instagram (optional)</label>
        <input
          type="url"
          id="clubInstagram"
          name="clubInstagram"
          value={clubInfo.clubInstagram}
          onChange={handleClubInputChange}
          placeholder="https://instagram.com/club_handle"
        />
      </div>

      <div className="form-group">
        <label htmlFor="applicationStage">Application Stage *</label>
        <select
          id="applicationStage"
          name="applicationStage"
          value={clubInfo.applicationStage}
          onChange={handleClubInputChange}
          required
        >
          <option value="">Select your current stage</option>
          <option value="online-application">Filling out online application</option>
          <option value="coffee-chat">Coffee chat / Networking</option>
          <option value="interview">Interview preparation</option>
        </select>
      </div>

      <button type="submit" className="cyber-btn">
        <span>Continue</span>
        <div className="btn-glow"></div>
      </button>
    </form>
  </div>
);

const ShortAnswersPage = ({ shortAnswers, handleQuestionsUpload, handleQuestionChange, addQuestion, handleFinalSubmit, setCurrentStep, loading, suggestions }) => (
  <div className="form-container">
    <h1 className="glitch-text">Application & Interview Preparation</h1>
    <p className="subtitle">Upload your application questions or enter them manually for personalized suggestions.</p>
    
    <div className="upload-section">
      <h3>Upload Questions (.txt, one question per line)</h3>
      <label className="upload-label">
        <input type="file" accept=".txt,text/plain" onChange={handleQuestionsUpload} />
        <div className="upload-box">
          <div className="upload-icon">📋</div>
          <p>{shortAnswers.questionsFile ? shortAnswers.questionsFile.name : 'Click to upload questions document'}</p>
        </div>
      </label>
    </div>

    <div className="manual-questions">
      <h3>Or Enter Questions Manually</h3>
      {shortAnswers.questions.map((question, index) => (
        <div key={index} className="question-group">
          <label htmlFor={`question-${index}`}>Question {index + 1}</label>
          <textarea
            id={`question-${index}`}
            value={question}
            onChange={(e) => {
              // auto-resize to fit content height
              e.target.style.height = 'auto';
              e.target.style.height = e.target.scrollHeight + 'px';
              handleQuestionChange(index, e.target.value);
            }}
            onInput={(e) => {
              e.target.style.height = 'auto';
              e.target.style.height = e.target.scrollHeight + 'px';
            }}
            placeholder="Enter the application question here..."
            rows={3}
            style={{background:'#0f0f14', color:'#fff'}}
          />
        </div>
      ))}
      
      <button type="button" onClick={addQuestion} className="add-question-btn">
        + Add Question
      </button>
    </div>

    <button onClick={handleFinalSubmit} className="cyber-btn" disabled={loading}>
      <span>{loading ? 'Generating…' : 'Generate guidance'}</span>
      <div className="btn-glow"></div>
    </button>

    <button onClick={() => setCurrentStep(2)} className="back-btn">
      ← Back
    </button>

    {suggestions && (
      <div className="results-panel" style={{marginTop: 24}}>
        {suggestions.warnings?.length > 0 && <div role="status"><h3>About these results</h3><ul>{suggestions.warnings.map((warning, i) => <li key={i}>{warning}</li>)}</ul></div>}

        {/* The direct answer to what you typed - shown first and always expanded. */}
        {Array.isArray(suggestions.answers) && suggestions.answers.length > 0 && (
          <div style={{marginBottom: 20}}>
            <h3 style={{marginBottom: 8}}>Your Answers</h3>
            <ul style={{listStyle: 'none', padding: 0, margin: 0}}>
              {suggestions.answers.map((qs, i) => (
                <li key={i} style={{marginBottom: 16}}>
                  <div style={{marginBottom: 6}}><strong>Q:</strong> {qs.question}</div>
                  {qs.example_answer && <div>{qs.example_answer}</div>}
                  {(qs.structure || qs.do_donts) && (
                    <details className="result-details" style={{marginTop: 8, marginBottom: 0}}>
                      <summary style={{fontSize: 14}}>Structure &amp; tips</summary>
                      {qs.structure && <div style={{marginTop: 8}}><strong>Structure:</strong> {qs.structure}</div>}
                      {qs.do_donts && <div style={{marginTop: 4}}><strong>Do/Don't:</strong> {qs.do_donts.join(' • ')}</div>}
                    </details>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Everything below is supporting material, collapsed by default so it
            doesn't bury the direct answer above. */}
        {suggestions.interview && (
          <details className="result-details">
            <summary>Interview &amp; Coffee Chat Preparation</summary>
            <div style={{marginTop: 10}}>
              <p>{suggestions.interview.similar_experiences_summary}</p>
              <h4>Likely questions</h4>
              <ul>{suggestions.interview.likely_questions.map((q, i) => <li key={i}>{q}</li>)}</ul>
              <h4>Stories to prepare</h4>
              <ul>{suggestions.interview.stories_to_prepare.map((q, i) => <li key={i}>{q}</li>)}</ul>
              <h4>Pitch template</h4>
              <p>{suggestions.interview.quick_pitch_template}</p>
              <h4>Questions to ask</h4>
              <ul>{suggestions.interview.followup_questions.map((q, i) => <li key={i}>{q}</li>)}</ul>
            </div>
          </details>
        )}

        {suggestions.club && (
          <details className="result-details">
            <summary>About the club</summary>
            <div style={{marginTop: 10}}>
              <div style={{opacity: 0.9}}>{suggestions.club.overview}</div>
              {Array.isArray(suggestions.club.mission_values) && suggestions.club.mission_values.length > 0 && (
                <div style={{marginTop: 8}}>
                  <strong>Values:</strong> {suggestions.club.mission_values.join(', ')}
                </div>
              )}
              {suggestions.application && Array.isArray(suggestions.application.values_alignment) && suggestions.application.values_alignment.length > 0 && (
                <div style={{marginTop: 12}}>
                  <h4>Values Alignment</h4>
                  <ul>
                    {suggestions.application.values_alignment.map((v, i) => (
                      <li key={i}>
                        <strong>{v.value || 'Value'}:</strong> {v.how_to_show_it || ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </details>
        )}

        {suggestions.resume && (
          <details className="result-details">
            <summary>Resume edits to get in</summary>
            <div style={{marginTop: 10}}>
              {Array.isArray(suggestions.resume.top5_fixes) && suggestions.resume.top5_fixes.length > 0 && (
                <div style={{marginBottom: 8}}>
                  <strong>Top fixes:</strong>
                  <ul>
                    {suggestions.resume.top5_fixes.map((t, i) => (<li key={i}>{t}</li>))}
                  </ul>
                </div>
              )}
              {Array.isArray(suggestions.resume.tailored_bullets) && suggestions.resume.tailored_bullets.length > 0 && (
                <div style={{marginBottom: 8}}>
                  <strong>Tailored bullets:</strong>
                  <ul>
                    {suggestions.resume.tailored_bullets.map((t, i) => (<li key={i}>{t}</li>))}
                  </ul>
                </div>
              )}
            </div>
          </details>
        )}
      </div>
    )}
  </div>
);

const PersonalInfoPage = ({ personalInfo, setPersonalInfo, handleFileUpload, handlePersonalSubmit, handlePersonalInputChange, clubInfo, setCurrentStep }) => (
    <div className="form-container">
      <h1 className="glitch-text">Personal Information</h1>
      <p className="subtitle">Tell us about yourself to create the perfect application.</p>
      
      <div className="resume-choice">
        <h3>Do you have a resume ready?</h3>
        <div className="choice-buttons">
          <button 
            type="button" 
            className={`choice-btn ${personalInfo.hasResume === true ? 'active' : ''}`}
            onClick={() => setPersonalInfo(prev => ({ ...prev, hasResume: true }))}
          >
            Yes, I have a resume
          </button>
          <button 
            type="button" 
            className={`choice-btn ${personalInfo.hasResume === false ? 'active' : ''}`}
            onClick={() => setPersonalInfo(prev => ({ ...prev, hasResume: false }))}
          >
            No, I'll fill it out manually
          </button>
        </div>
      </div>

      {personalInfo.hasResume === true && (
        <div className="upload-section">
          <label className="upload-label">
            <input type="file" accept=".pdf,application/pdf" onChange={handleFileUpload} />
            <div className="upload-box">
              <div className="upload-icon">📄</div>
              <p>{personalInfo.resumeFile ? personalInfo.resumeFile.name : 'Click to upload your resume'}</p>
            </div>
          </label>
        </div>
      )}

      {personalInfo.hasResume === false && (
        <form onSubmit={handlePersonalSubmit} className="tech-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="name">Full Name *</label>
              <input
                type="text"
                id="name"
                name="name"
                value={personalInfo.name}
                onChange={handlePersonalInputChange}
                placeholder="Your full name"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input
                type="email"
                id="email"
                name="email"
                value={personalInfo.email}
                onChange={handlePersonalInputChange}
                placeholder="your.email@example.com"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="education">Education *</label>
            <textarea
              id="education"
              name="education"
              value={personalInfo.education}
              onChange={handlePersonalInputChange}
              placeholder="Your educational background (degree, school, graduation year, GPA, etc.)"
              rows={3}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="experiences">Work/Leadership Experience</label>
            <textarea
              id="experiences"
              name="experiences"
              value={personalInfo.experiences}
              onChange={handlePersonalInputChange}
              placeholder="Describe your work experience, internships, leadership roles, etc."
              rows={4}
            />
          </div>

          <div className="form-group">
            <label htmlFor="projects">Projects</label>
            <textarea
              id="projects"
              name="projects"
              value={personalInfo.projects}
              onChange={handlePersonalInputChange}
              placeholder="Describe any relevant projects you've worked on"
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="skills">Skills & Technologies</label>
            <textarea
              id="skills"
              name="skills"
              value={personalInfo.skills}
              onChange={handlePersonalInputChange}
              placeholder="List your technical skills, programming languages, tools, etc."
              rows={2}
            />
          </div>

          <div className="form-group">
            <label htmlFor="achievements">Achievements & Awards</label>
            <textarea
              id="achievements"
              name="achievements"
              value={personalInfo.achievements}
              onChange={handlePersonalInputChange}
              placeholder="Any notable achievements, awards, or recognitions"
              rows={2}
            />
          </div>

          <button type="submit" className="cyber-btn">
            <span>{clubInfo.applicationStage === 'online-application' ? 'Continue to Questions' : 'Continue to Preparation'}</span>
            <div className="btn-glow"></div>
          </button>
        </form>
      )}

      {personalInfo.hasResume === true && personalInfo.resumeFile && (
        <button onClick={handlePersonalSubmit} className="cyber-btn">
          <span>{clubInfo.applicationStage === 'online-application' ? 'Continue to Questions' : 'Continue to Preparation'}</span>
          <div className="btn-glow"></div>
        </button>
      )}

      <button onClick={() => setCurrentStep(1)} className="back-btn">
        ← Back
      </button>
    </div>
  );


function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [clubInfo, setClubInfo] = useState({
    clubName: '',
    schoolName: '',
    position: '',
    clubWebsite: '',
    clubInstagram: '',
    applicationStage: ''
  });
  const [personalInfo, setPersonalInfo] = useState({
    hasResume: null,
    resumeFile: null,
    name: '',
    email: '',
    phone: '',
    education: '',
    experiences: '',
    projects: '',
    skills: '',
    achievements: ''
  });
  const [shortAnswers, setShortAnswers] = useState({
    questionsFile: null,
    questions: ['']
  });
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(null);
  const [error, setError] = useState('');
  const [runtime, setRuntime] = useState(null);

  React.useEffect(() => {
    setSuggestions(null);
  }, [clubInfo, personalInfo, shortAnswers]);

  React.useEffect(() => {
    ApiService.request('/health').then(setRuntime).catch(() => setError('Cannot reach the backend. Start the API on port 8000.'));
  }, []);

  const handleClubInputChange = (e) => {
    const { name, value } = e.target;
    setClubInfo(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handlePersonalInputChange = (e) => {
    const { name, value } = e.target;
    setPersonalInfo(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    setError('');
    if (file && (!file.name.toLowerCase().endsWith('.pdf') || file.size > 5 * 1024 * 1024)) {
      setError('Choose a PDF resume smaller than 5 MB.');
      e.target.value = '';
      setPersonalInfo(prev => ({ ...prev, resumeFile: null }));
      return;
    }
    setPersonalInfo(prev => ({
      ...prev,
      resumeFile: file
    }));
  };

  const handleClubSubmit = (e) => {
    e.preventDefault();
    setCurrentStep(2);
  };

  const handlePersonalSubmit = (e) => {
    e.preventDefault();
    setCurrentStep(3);
  };

  const handleQuestionsUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setError('');
    if (!file.name.toLowerCase().endsWith('.txt') || file.size > 100 * 1024) {
      setError('Choose a plain-text (.txt) file smaller than 100 KB, with one question per line.');
      e.target.value = '';
      return;
    }
    try {
      const questions = (await file.text()).split(/\r?\n/).map(q => q.trim()).filter(Boolean);
      setShortAnswers({ questionsFile: file, questions: questions.length ? questions : [''] });
    } catch {
      setError('Could not read that questions file. Enter the questions manually.');
    }
  };

  const handleQuestionChange = (index, value) => {
    const newQuestions = [...shortAnswers.questions];
    newQuestions[index] = value;
    setShortAnswers(prev => ({
      ...prev,
      questions: newQuestions
    }));
  };

  const addQuestion = () => {
    setShortAnswers(prev => ({
      ...prev,
      questions: [...prev.questions, '']
    }));
  };

  const handleFinalSubmit = async () => {
    try {
      setLoading(true);
      setError('');
      setSuggestions(null);
      const qs = (shortAnswers.questions || []).map(q => (q || '').trim()).filter(Boolean);
      const jobDesc = `${clubInfo.position} position at ${clubInfo.clubName}, ${clubInfo.schoolName}${clubInfo.clubWebsite ? ' - ' + clubInfo.clubWebsite : ''}`;
      const body = {
        job_description: jobDesc,
        questions: qs,
        include_interview: clubInfo.applicationStage !== 'online-application',
        website_url: clubInfo.clubWebsite || undefined,
        instagram_url: clubInfo.clubInstagram || undefined,
        club_name: clubInfo.clubName,
        school_name: clubInfo.schoolName,
      };
      if (personalInfo.hasResume === false) {
        body.resume_text = ['education', 'experiences', 'projects', 'skills', 'achievements']
          .filter(key => personalInfo[key].trim())
          .map(key => `${key}: ${personalInfo[key]}`).join('\n');
      }
      if (personalInfo.hasResume === true && personalInfo.resumeFile) {
        const up = await ApiService.uploadFile('/upload/resume', personalInfo.resumeFile);
        if (up && up.resume_text) {
          body.resume_text = up.resume_text;
        }
      }
      const resp = await ApiService.post('/agents/application-coach', body);
      setSuggestions(resp);
    } catch (e) {
      console.error('Failed to generate suggestions', e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };




  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return <ClubInfoPage 
          clubInfo={clubInfo} 
          handleClubInputChange={handleClubInputChange} 
          handleClubSubmit={handleClubSubmit} 
        />;
      case 2:
        return <PersonalInfoPage personalInfo={personalInfo} setPersonalInfo={setPersonalInfo} handleFileUpload={handleFileUpload} handlePersonalSubmit={handlePersonalSubmit} handlePersonalInputChange={handlePersonalInputChange} clubInfo={clubInfo} setCurrentStep={setCurrentStep} />;
      case 3:
        return <ShortAnswersPage 
          shortAnswers={shortAnswers}
          handleQuestionsUpload={handleQuestionsUpload}
          handleQuestionChange={handleQuestionChange}
          addQuestion={addQuestion}
          handleFinalSubmit={handleFinalSubmit}
          loading={loading}
          suggestions={suggestions}
          setCurrentStep={setCurrentStep}
        />;
      default:
        return <ClubInfoPage 
          clubInfo={clubInfo} 
          handleClubInputChange={handleClubInputChange} 
          handleClubSubmit={handleClubSubmit} 
        />;
    }
  };

  return (
    <div className="App">
      <div className="tech-bg"></div>
      {runtime?.model_mode === 'offline' && <p role="status" style={{padding: 16, textAlign: 'center'}}>Offline demo — generic guidance only. No AI provider is connected.</p>}
      {error && <p role="alert" style={{padding: 16, color: '#ffb4ab', textAlign: 'center'}}>{error}</p>}
      {renderCurrentStep()}
    </div>
  );
}

export default App;
