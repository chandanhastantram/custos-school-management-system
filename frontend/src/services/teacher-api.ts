/**
 * Teacher API Service
 */

import apiClient from '@/lib/api-client';

export interface LessonPlan {
  id: string;
  subject_id: string;
  topic: string;
  objectives: string[];
  activities: string[];
  resources: string[];
  scheduled_date: string;
}

export interface Question {
  id: string;
  subject_id: string;
  question_text: string;
  question_type: string;
  difficulty: string;
  bloom_level: string;
  marks: number;
}

export const teacherApi = {
  // Lesson Plans
  async getLessonPlans(params?: { subject_id?: string; page?: number }) {
    const response = await apiClient.get<LessonPlan[]>('/academics/lesson-plans', { params });
    return response.data;
  },

  async createLessonPlan(data: Partial<LessonPlan>) {
    const response = await apiClient.post<LessonPlan>('/academics/lesson-plans', data);
    return response.data;
  },

  async updateLessonPlan(id: string, data: Partial<LessonPlan>) {
    const response = await apiClient.patch<LessonPlan>(`/academics/lesson-plans/${id}`, data);
    return response.data;
  },

  async generateLessonPlan(data: { subject: string; topic: string; grade: number }) {
    const response = await apiClient.post('/ai/lesson-plan/generate', data);
    return response.data;
  },

  // Question Bank
  async getQuestions(params?: { subject_id?: string; difficulty?: string; page?: number }) {
    const response = await apiClient.get<Question[]>('/questions', { params });
    return response.data;
  },

  async createQuestion(data: Partial<Question>) {
    const response = await apiClient.post<Question>('/questions', data);
    return response.data;
  },

  async generateQuestions(data: { subject: string; topic: string; count: number; difficulty: string }) {
    const response = await apiClient.post('/ai/generate-questions', data);
    return response.data;
  },

  // Attendance
  async markAttendance(data: {
    class_id: string;
    date: string;
    attendance: Array<{ student_id: string; status: string }>;
  }) {
    const response = await apiClient.post('/attendance/mark', data);
    return response.data;
  },

  async getClassAttendance(classId: string, date: string) {
    const response = await apiClient.get(`/attendance/class/${classId}`, {
      params: { date }
    });
    return response.data;
  },

  // Student Analytics
  async getStudentAnalytics(studentId: string) {
    const response = await apiClient.get(`/analytics/students/${studentId}`);
    return response.data;
  },

  async getClassAnalytics(classId: string) {
    const response = await apiClient.get(`/analytics/class/${classId}`);
    return response.data;
  },

  // Syllabus
  async getSyllabus(subjectId: string) {
    const response = await apiClient.get(`/academics/syllabus/${subjectId}`);
    return response.data;
  },

  async updateSyllabusProgress(syllabusId: string, topicId: string, status: string) {
    const response = await apiClient.patch(`/academics/syllabus/${syllabusId}/topics/${topicId}`, {
      status
    });
    return response.data;
  },
};
