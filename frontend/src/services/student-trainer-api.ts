/**
 * Student AI Trainer API Client
 */

import apiClient from '@/lib/api-client';

export interface GenerateQuizRequest {
  syllabus_subject_id: string;
  topic_ids: string[];
  class_id: string;
  section_id?: string;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  num_questions: number;
  question_types: string[];
  time_limit_minutes?: number;
  focus_bloom_levels?: string[];
  include_explanations: boolean;
}

export interface QuizQuestion {
  id: string;
  question_text: string;
  question_type: string;
  marks: number;
  order: number;
  options?: Array<{ id: string; text: string }>;
  explanation?: string;
  difficulty?: string;
}

export interface Quiz {
  id: string;
  title: string;
  description?: string;
  difficulty: string;
  total_questions: number;
  total_marks: number;
  time_limit_minutes?: number;
  passing_percentage: number;
  status: string;
  ai_generated: boolean;
  published_at?: string;
}

export interface QuizWithQuestions extends Quiz {
  questions: QuizQuestion[];
}

export interface QuizSubmission {
  id: string;
  quiz_id: string;
  student_id: string;
  status: string;
  started_at: string;
  submitted_at?: string;
  time_taken_seconds?: number;
  score?: number;
  max_score?: number;
  percentage?: number;
  passed?: boolean;
}

export interface QuizResult extends QuizSubmission {
  quiz_title: string;
  correct_answers: number;
  incorrect_answers: number;
  unanswered: number;
  question_results: Array<{
    question_id: string;
    question_text: string;
    student_answer: any;
    correct_answer: any;
    is_correct: boolean;
    marks_awarded: number;
    max_marks: number;
    explanation?: string;
  }>;
  feedback?: string;
}

export const studentTrainerApi = {
  // Syllabus Analysis
  async analyzeSyllabus(syllabusSubjectId: string) {
    const response = await apiClient.post('/ai/student-trainer/analyze-syllabus', null, {
      params: { syllabus_subject_id: syllabusSubjectId }
    });
    return response.data;
  },

  // Quiz Generation
  async generateQuiz(data: GenerateQuizRequest) {
    const response = await apiClient.post('/ai/student-trainer/generate-quiz', data);
    return response.data;
  },

  // Quiz Management
  async listQuizzes(params?: { class_id?: string; subject_id?: string; status?: string; page?: number; size?: number }) {
    const response = await apiClient.get<{ items: Quiz[]; total: number }>('/ai/student-trainer/quizzes', { params });
    return response.data;
  },

  async getQuiz(quizId: string) {
    const response = await apiClient.get<QuizWithQuestions>(`/ai/student-trainer/quizzes/${quizId}`);
    return response.data;
  },

  async publishQuiz(quizId: string) {
    const response = await apiClient.post(`/ai/student-trainer/quizzes/${quizId}/publish`);
    return response.data;
  },

  // Quiz Taking
  async startQuiz(quizId: string) {
    const response = await apiClient.post<{ submission_id: string; quiz_id: string; started_at: string; time_limit_minutes?: number }>(
      `/ai/student-trainer/quizzes/${quizId}/start`
    );
    return response.data;
  },

  async submitQuiz(submissionId: string, answers: Record<string, any>) {
    const response = await apiClient.post<QuizResult>(
      `/ai/student-trainer/submissions/${submissionId}/submit`,
      { answers }
    );
    return response.data;
  },

  async getSubmissionResult(submissionId: string) {
    const response = await apiClient.get<QuizResult>(`/ai/student-trainer/submissions/${submissionId}`);
    return response.data;
  },

  async listMySubmissions(params?: { quiz_id?: string; page?: number; size?: number }) {
    const response = await apiClient.get<{ items: QuizSubmission[]; total: number }>('/ai/student-trainer/my-submissions', { params });
    return response.data;
  },

  // Practice Tasks
  async generateTask(data: {
    syllabus_subject_id: string;
    topic_id: string;
    class_id: string;
    title: string;
    task_type: string;
    difficulty: string;
    num_problems: number;
    estimated_time_minutes?: number;
    include_hints: boolean;
    include_solutions: boolean;
  }) {
    const response = await apiClient.post('/ai/student-trainer/generate-task', data);
    return response.data;
  },

  async listTasks(params?: { class_id?: string; topic_id?: string; page?: number; size?: number }) {
    const response = await apiClient.get('/ai/student-trainer/tasks', { params });
    return response.data;
  },

  async getTask(taskId: string) {
    const response = await apiClient.get(`/ai/student-trainer/tasks/${taskId}`);
    return response.data;
  },

  // Analytics
  async getMyStats() {
    const response = await apiClient.get('/ai/student-trainer/my-stats');
    return response.data;
  },

  async getQuizAnalytics(quizId: string) {
    const response = await apiClient.get(`/ai/student-trainer/quizzes/${quizId}/analytics`);
    return response.data;
  }
};
