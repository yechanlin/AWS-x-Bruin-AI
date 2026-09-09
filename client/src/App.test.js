// CRA smoke test for App.js.
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import ApiService from './services/api';

jest.mock('./services/api', () => ({
  request: jest.fn(), post: jest.fn(), uploadFile: jest.fn(),
}));

beforeEach(() => {
  jest.clearAllMocks();
  ApiService.request.mockResolvedValue({ ok: true, model_mode: 'offline' });
  ApiService.post.mockResolvedValue({ club: { overview: 'Example result' }, answers: [], resume: {}, warnings: [] });
});

function enterClub(stage = 'online-application') {
  fireEvent.change(screen.getByLabelText('Club Name *'), { target: { value: 'Example AI Club' } });
  fireEvent.change(screen.getByLabelText('School Name *'), { target: { value: 'UCLA' } });
  fireEvent.change(screen.getByLabelText('Position/Role *'), { target: { value: 'Member' } });
  fireEvent.change(screen.getByLabelText('Application Stage *'), { target: { value: stage } });
  fireEvent.click(screen.getByRole('button', { name: 'Continue', exact: true }));
}

function enterManualProfile() {
  fireEvent.click(screen.getByRole('button', { name: "No, I'll fill it out manually" }));
  userEvent.type(screen.getByLabelText('Full Name *'), 'Alex Demo');
  expect(screen.getByLabelText('Full Name *')).toHaveValue('Alex Demo');
  expect(screen.getByLabelText('Full Name *')).toHaveFocus();
  fireEvent.change(screen.getByLabelText('Email *'), { target: { value: 'alex@example.test' } });
  fireEvent.change(screen.getByLabelText('Education *'), { target: { value: 'UCLA CS' } });
  fireEvent.change(screen.getByLabelText('Projects'), { target: { value: 'Python notes organizer' } });
}

test('manual application retains typing focus and submits experience to the API', async () => {
  render(<App />);
  await screen.findByText(/Offline demo/);
  enterClub();
  enterManualProfile();
  fireEvent.click(screen.getByRole('button', { name: 'Continue to Questions' }));
  fireEvent.change(screen.getByLabelText('Question 1'), { target: { value: 'Why this club?' } });
  fireEvent.click(screen.getByRole('button', { name: 'Generate guidance' }));
  await screen.findByText('Example result');
  expect(ApiService.post).toHaveBeenCalledWith('/agents/application-coach', expect.objectContaining({
    resume_text: 'education: UCLA CS\nprojects: Python notes organizer',
    questions: ['Why this club?'], include_interview: false,
  }));
});

test('PDF upload forwards extracted text and displays upload errors', async () => {
  render(<App />);
  await screen.findByText(/Offline demo/);
  enterClub();
  fireEvent.click(screen.getByRole('button', { name: 'Yes, I have a resume' }));
  const file = new File(['%PDF-demo'], 'resume.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByLabelText(/Click to upload your resume/), { target: { files: [file] } });
  fireEvent.click(screen.getByRole('button', { name: 'Continue to Questions' }));
  ApiService.uploadFile.mockRejectedValueOnce(new Error('This file is not a valid PDF.'));
  fireEvent.click(screen.getByRole('button', { name: 'Generate guidance' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('This file is not a valid PDF.');
  expect(ApiService.post).not.toHaveBeenCalled();
  ApiService.uploadFile.mockResolvedValueOnce({ resume_text: 'Demo resume extracted from PDF', name: 'resume.pdf' });
  fireEvent.click(screen.getByRole('button', { name: 'Generate guidance' }));
  await screen.findByText('Example result');
  expect(ApiService.post).toHaveBeenCalledWith('/agents/application-coach', expect.objectContaining({ resume_text: 'Demo resume extracted from PDF' }));
});

test('interview path requests preparation and imports text questions', async () => {
  render(<App />);
  await screen.findByText(/Offline demo/);
  enterClub('interview');
  enterManualProfile();
  fireEvent.click(screen.getByRole('button', { name: 'Continue to Preparation' }));
  const file = new File(['Why this club?\nWhat would you build?'], 'questions.txt', { type: 'text/plain' });
  file.text = jest.fn().mockResolvedValue('Why this club?\nWhat would you build?');
  fireEvent.change(screen.getByLabelText(/Click to upload questions document/), { target: { files: [file] } });
  await waitFor(() => expect(screen.getByLabelText('Question 2')).toHaveValue('What would you build?'));
  fireEvent.click(screen.getByRole('button', { name: 'Generate guidance' }));
  await screen.findByText('Example result');
  expect(ApiService.post).toHaveBeenCalledWith('/agents/application-coach', expect.objectContaining({ include_interview: true, questions: ['Why this club?', 'What would you build?'] }));
});
