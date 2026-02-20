/**
 * Notifications API Service
 */
import apiClient from '@/lib/api-client';

export const notificationsApi = {
  async getNotifications(params?: { unread_only?: boolean; page?: number; size?: number }) {
    const response = await apiClient.get('/notifications', { params });
    return response.data;
  },

  async markRead(notificationId: string) {
    const response = await apiClient.post(`/notifications/${notificationId}/read`);
    return response.data;
  },

  async getUnreadCount() {
    const response = await apiClient.get('/notifications/unread-count');
    return response.data;
  },
};
