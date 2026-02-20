/**
 * Finance API Service
 */

import apiClient from '@/lib/api-client';

export interface Invoice {
  id: string;
  student_id: string;
  student_name: string;
  class_name: string;
  amount: number;
  due_date: string;
  status: 'paid' | 'pending' | 'overdue';
  paid_date?: string;
  description: string;
}

export interface Payment {
  id: string;
  invoice_id: string;
  student_name: string;
  amount: number;
  payment_date: string;
  method: string;
  reference_no: string;
}

export interface FeeSummary {
  total_collected: number;
  total_pending: number;
  total_overdue: number;
  collection_rate: number;
  class_summaries: Array<{
    class_name: string;
    collected: number;
    total: number;
    student_count: number;
  }>;
}

export const financeApi = {
  async getInvoices(params?: { status?: string; class_id?: string; page?: number; size?: number }) {
    const response = await apiClient.get<{ items: Invoice[]; total: number }>('/finance/invoices', { params });
    return response.data;
  },

  async createInvoice(data: Partial<Invoice>) {
    const response = await apiClient.post<Invoice>('/finance/invoices', data);
    return response.data;
  },

  async updateInvoice(id: string, data: Partial<Invoice>) {
    const response = await apiClient.patch<Invoice>(`/finance/invoices/${id}`, data);
    return response.data;
  },

  async recordPayment(data: {
    invoice_id: string;
    amount: number;
    method: string;
    reference_no?: string;
  }) {
    const response = await apiClient.post<Payment>('/finance/payments', data);
    return response.data;
  },

  async getPayments(params?: { page?: number; size?: number }) {
    const response = await apiClient.get<{ items: Payment[]; total: number }>('/finance/payments', { params });
    return response.data;
  },

  async getFeeSummary() {
    const response = await apiClient.get<FeeSummary>('/finance/summary');
    return response.data;
  },

  async exportInvoices(params?: { status?: string }) {
    const response = await apiClient.get('/finance/invoices/export', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },

  async sendReminder(invoiceId: string) {
    const response = await apiClient.post(`/finance/invoices/${invoiceId}/remind`);
    return response.data;
  },
};
