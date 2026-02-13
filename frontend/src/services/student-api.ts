/**
 * Student API Service
 */

import apiClient from '@/lib/api-client';

export interface Student {
  id: string;
  user_id: string;
  roll_number: string;
  class_id: string;
  section_id: string;
  admission_date: string;
  is_active: boolean;
}

export interface Timetable {
  id: string;
  class_id: string;
  day_of_week: number;
  periods: Period[];
}

export interface Period {
  period_number: number;
  subject: string;
  teacher: string;
  start_time: string;
  end_time: string;
  room: string;
}

export interface Fee {
  id: string;
  student_id: string;
  fee_type: string;
  amount: number;
  due_date: string;
  status: 'pending' | 'paid' | 'overdue';
  paid_amount?: number;
  paid_date?: string;
}

export interface Attendance {
  id: string;
  student_id: string;
  date: string;
  status: 'present' | 'absent' | 'late' | 'excused';
  subject_id?: string;
}

export const studentApi = {
  // Timetable
  async getTimetable(studentId: string) {
    const response = await apiClient.get<Timetable>(`/scheduling/student/timetable`, {
      params: { student_id: studentId }
    });
    return response.data;
  },

  // Fees
  async getFees(studentId: string) {
    const response = await apiClient.get<Fee[]>(`/finance/student/${studentId}/fees`);
    return response.data;
  },

  async payFee(feeId: string, amount: number) {
    const response = await apiClient.post(`/payments/initiate`, {
      fee_id: feeId,
      amount,
    });
    return response.data;
  },

  // Attendance
  async getAttendance(studentId: string, params?: { start_date?: string; end_date?: string }) {
    const response = await apiClient.get<Attendance[]>(`/attendance/student/${studentId}`, {
      params
    });
    return response.data;
  },

  async getAttendanceSummary(studentId: string) {
    const response = await apiClient.get(`/attendance/student/summary`, {
      params: { student_id: studentId }
    });
    return response.data;
  },

  // Exam Registration
  async getAvailableExams() {
    const response = await apiClient.get('/examinations/available');
    return response.data;
  },

  async registerForExam(examId: string) {
    const response = await apiClient.post('/examinations/register', {
      exam_id: examId
    });
    return response.data;
  },

  async getHallTicket(examId: string) {
    const response = await apiClient.get(`/examinations/hall-ticket`, {
      params: { exam_id: examId }
    });
    return response.data;
  },

  // Virtual Classroom
  async getUpcomingClasses() {
    const response = await apiClient.get('/meetings/student/upcoming');
    return response.data;
  },

  async joinClass(meetingId: string) {
    const response = await apiClient.post(`/meetings/${meetingId}/join`);
    return response.data;
  },

  // Extracurricular
  async getActivities() {
    const response = await apiClient.get('/activity-points/activities');
    return response.data;
  },

  async enrollActivity(activityId: string) {
    const response = await apiClient.post(`/activity-points/enroll`, {
      activity_id: activityId
    });
    return response.data;
  },
};
