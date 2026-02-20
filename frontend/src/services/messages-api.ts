/**
 * Messages API Service
 */
import apiClient from '@/lib/api-client';

export const messagesApi = {
  async getInbox(params?: { folder?: string; page?: number; page_size?: number }) {
    const response = await apiClient.get('/messages/inbox', { params });
    return response.data;
  },

  async getSent(params?: { page?: number; page_size?: number }) {
    const response = await apiClient.get('/messages/sent', { params });
    return response.data;
  },

  async createMessage(data: { subject: string; content: string; recipient_ids: string[]; message_type?: string }) {
    const response = await apiClient.post('/messages', data);
    return response.data;
  },

  async getMessage(messageId: string) {
    const response = await apiClient.get(`/messages/${messageId}`);
    return response.data;
  },

  async markRead(messageIds: string[]) {
    const response = await apiClient.post('/messages/inbox/read', messageIds);
    return response.data;
  },

  async getUnreadCount() {
    const response = await apiClient.get('/messages/inbox/unread-count');
    return response.data;
  },

  async deleteMessage(messageId: string) {
    const response = await apiClient.delete(`/messages/${messageId}`);
    return response.data;
  },
};
