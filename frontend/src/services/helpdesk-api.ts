/**
 * Helpdesk API Service
 */

import apiClient from '@/lib/api-client';

export interface Ticket {
  id: string;
  subject: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: string;
  created_at: string;
  updated_at: string;
  responses: number;
}

export interface TicketResponse {
  id: string;
  ticket_id: string;
  message: string;
  author: string;
  created_at: string;
}

export const helpdeskApi = {
  async getTickets(params?: { status?: string; page?: number; size?: number }) {
    const response = await apiClient.get<{ items: Ticket[]; total: number }>('/helpdesk/tickets', { params });
    return response.data;
  },

  async createTicket(data: { subject: string; description: string; category: string; priority: string }) {
    const response = await apiClient.post<Ticket>('/helpdesk/tickets', data);
    return response.data;
  },

  async getTicketResponses(ticketId: string) {
    const response = await apiClient.get<TicketResponse[]>(`/helpdesk/tickets/${ticketId}/responses`);
    return response.data;
  },

  async respondToTicket(ticketId: string, message: string) {
    const response = await apiClient.post<TicketResponse>(`/helpdesk/tickets/${ticketId}/responses`, {
      message,
    });
    return response.data;
  },

  async closeTicket(ticketId: string) {
    const response = await apiClient.patch(`/helpdesk/tickets/${ticketId}`, { status: 'closed' });
    return response.data;
  },

  async getFaqs() {
    const response = await apiClient.get('/helpdesk/faqs');
    return response.data;
  },
};
