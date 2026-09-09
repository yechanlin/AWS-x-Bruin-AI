// Unused agent-picker screen (not on App.js's active route) that would link out to the individual agent components below.
import React from 'react';
import { AGENT_TYPES, AGENT_NAMES } from '../utils/constants';

const Dashboard = ({ onAgentSelect }) => {
  const agents = [
    {
      type: AGENT_TYPES.RESUME_TAILOR,
      name: AGENT_NAMES[AGENT_TYPES.RESUME_TAILOR],
      description: 'Optimize your resume for specific job applications',
      icon: '📄'
    },
    {
      type: AGENT_TYPES.INTERVIEW_COACH,
      name: AGENT_NAMES[AGENT_TYPES.INTERVIEW_COACH],
      description: 'Get personalized interview preparation and tips',
      icon: '🎯'
    },
    {
      type: AGENT_TYPES.APPLICATION_COACH,
      name: AGENT_NAMES[AGENT_TYPES.APPLICATION_COACH],
      description: 'Receive guidance on job application strategies',
      icon: '💼'
    },
    {
      type: AGENT_TYPES.INSTAGRAM_ANALYZER,
      name: AGENT_NAMES[AGENT_TYPES.INSTAGRAM_ANALYZER],
      description: 'Analyze Instagram profiles for professional insights',
      icon: '📱'
    },
    {
      type: AGENT_TYPES.WEBSITE_ANALYZER,
      name: AGENT_NAMES[AGENT_TYPES.WEBSITE_ANALYZER],
      description: 'Extract and analyze website content',
      icon: '🌐'
    },
    {
      type: AGENT_TYPES.SUMMARIZER,
      name: AGENT_NAMES[AGENT_TYPES.SUMMARIZER],
      description: 'Summarize long content into key insights',
      icon: '📝'
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-4">
          Choose Your AI Career Assistant
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Select an AI agent to help you with your career development needs
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <div
            key={agent.type}
            onClick={() => onAgentSelect(agent.type)}
            className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 hover:border-blue-300"
          >
            <div className="text-4xl mb-4">{agent.icon}</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              {agent.name}
            </h3>
            <p className="text-gray-600">{agent.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;