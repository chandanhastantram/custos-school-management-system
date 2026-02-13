/**
 * Admin API Services
 */

import apiClient from '@/lib/api-client';

// HR & Payroll
export const hrApi = {
  async getEmployees(params?: { page?: number; size?: number }) {
    const response = await apiClient.get('/hr/employees', { params });
    return response.data;
  },

  async createEmployee(data: any) {
    const response = await apiClient.post('/hr/employees', data);
    return response.data;
  },

  async processPayroll(month: string, year: number) {
    const response = await apiClient.post('/hr/payroll/process', { month, year });
    return response.data;
  },

  async getPayrollHistory() {
    const response = await apiClient.get('/hr/payroll/history');
    return response.data;
  },
};

// Governance
export const governanceApi = {
  async getAuditLogs(params?: { page?: number; size?: number; action?: string }) {
    const response = await apiClient.get('/governance/audit-logs', { params });
    return response.data;
  },

  async exportData(dataType: string) {
    const response = await apiClient.post('/governance/export', { data_type: dataType });
    return response.data;
  },
};

// Activity Points
export const activityPointsApi = {
  async getActivities() {
    const response = await apiClient.get('/activity-points/activities');
    return response.data;
  },

  async createActivity(data: any) {
    const response = await apiClient.post('/activity-points/activities', data);
    return response.data;
  },

  async getLeaderboard(params?: { class_id?: string; limit?: number }) {
    const response = await apiClient.get('/activity-points/leaderboard', { params });
    return response.data;
  },

  async awardPoints(data: { student_id: string; activity_id: string; points: number }) {
    const response = await apiClient.post('/activity-points/award', data);
    return response.data;
  },
};

// Meetings
export const meetingsApi = {
  async getMeetings(params?: { upcoming?: boolean }) {
    const response = await apiClient.get('/meetings', { params });
    return response.data;
  },

  async createMeeting(data: any) {
    const response = await apiClient.post('/meetings', data);
    return response.data;
  },

  async updateMeeting(id: string, data: any) {
    const response = await apiClient.patch(`/meetings/${id}`, data);
    return response.data;
  },

  async deleteMeeting(id: string) {
    const response = await apiClient.delete(`/meetings/${id}`);
    return response.data;
  },
};

// Feedback
export const feedbackApi = {
  async getSurveys() {
    const response = await apiClient.get('/feedback/surveys');
    return response.data;
  },

  async createSurvey(data: any) {
    const response = await apiClient.post('/feedback/surveys', data);
    return response.data;
  },

  async getSurveyResponses(surveyId: string) {
    const response = await apiClient.get(`/feedback/surveys/${surveyId}/responses`);
    return response.data;
  },
};

// Calendar
export const calendarApi = {
  async getEvents(params?: { start_date?: string; end_date?: string }) {
    const response = await apiClient.get('/calendar/events', { params });
    return response.data;
  },

  async createEvent(data: any) {
    const response = await apiClient.post('/calendar/events', data);
    return response.data;
  },

  async updateEvent(id: string, data: any) {
    const response = await apiClient.patch(`/calendar/events/${id}`, data);
    return response.data;
  },

  async deleteEvent(id: string) {
    const response = await apiClient.delete(`/calendar/events/${id}`);
    return response.data;
  },
};

// Announcements
export const announcementsApi = {
  async getAnnouncements(params?: { page?: number; size?: number }) {
    const response = await apiClient.get('/announcements', { params });
    return response.data;
  },

  async createAnnouncement(data: any) {
    const response = await apiClient.post('/announcements', data);
    return response.data;
  },

  async deleteAnnouncement(id: string) {
    const response = await apiClient.delete(`/announcements/${id}`);
    return response.data;
  },
};

// Billing
export const billingApi = {
  async getSubscription() {
    const response = await apiClient.get('/billing/subscription');
    return response.data;
  },

  async getInvoices() {
    const response = await apiClient.get('/billing/invoices');
    return response.data;
  },

  async getUsageStats() {
    const response = await apiClient.get('/billing/usage');
    return response.data;
  },
};
