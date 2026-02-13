/**
 * Parent API Service
 */

import apiClient from '@/lib/api-client';

export interface Child {
  id: string;
  name: string;
  roll_number: string;
  class: string;
  section: string;
}

export const parentApi = {
  // Children
  async getChildren() {
    const response = await apiClient.get<Child[]>('/parents/children');
    return response.data;
  },

  async getChildDetails(childId: string) {
    const response = await apiClient.get(`/parents/child/${childId}`);
    return response.data;
  },

  // Fees
  async getChildFees(childId: string) {
    const response = await apiClient.get(`/finance/parent/child/${childId}/fees`);
    return response.data;
  },

  async payChildFee(feeId: string, amount: number) {
    const response = await apiClient.post('/payments/initiate', {
      fee_id: feeId,
      amount,
    });
    return response.data;
  },

  // Leave Requests
  async submitLeaveRequest(data: {
    student_id: string;
    start_date: string;
    end_date: string;
    reason: string;
  }) {
    const response = await apiClient.post('/attendance/leave-requests', data);
    return response.data;
  },

  async getLeaveRequests(studentId: string) {
    const response = await apiClient.get(`/attendance/leave-requests`, {
      params: { student_id: studentId }
    });
    return response.data;
  },

  // Transport
  async getChildTransport(studentId: string) {
    const response = await apiClient.get(`/transport/my-child/${studentId}`);
    return response.data;
  },

  // Hostel
  async getChildHostel(studentId: string) {
    const response = await apiClient.get(`/hostel/my-details/${studentId}`);
    return response.data;
  },

  // Attendance
  async getChildAttendance(studentId: string, params?: { start_date?: string; end_date?: string }) {
    const response = await apiClient.get(`/attendance/parent/child/${studentId}`, { params });
    return response.data;
  },
};
