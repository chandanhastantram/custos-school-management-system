/**
 * Hostel API Service
 * 
 * Handles all hostel-related API calls.
 */

import apiClient, { PaginatedResponse } from '@/lib/api-client';

// Types
export interface Hostel {
  id: string;
  name: string;
  code: string;
  gender: 'male' | 'female' | 'mixed';
  total_capacity: number;
  is_active: boolean;
  address?: string;
  contact_number?: string;
  rooms_count?: number;
  occupied_beds?: number;
}

export interface Room {
  id: string;
  hostel_id: string;
  room_number: string;
  floor: number;
  capacity: number;
  is_active: boolean;
  beds_count?: number;
  occupied_beds?: number;
  available_beds?: number;
}

export interface Bed {
  id: string;
  room_id: string;
  bed_number: string;
  is_occupied: boolean;
  is_active: boolean;
}

export interface Warden {
  id: string;
  name: string;
  phone: string;
  email?: string;
  is_chief_warden: boolean;
  assigned_hostel_id?: string;
  hostel_name?: string;
  is_active: boolean;
}

export interface StudentHostelAssignment {
  id: string;
  student_id: string;
  hostel_id: string;
  room_id: string;
  bed_id: string;
  assigned_date: string;
  is_active: boolean;
}

// API Functions
export const hostelApi = {
  // Hostels
  async getHostels(params?: { active_only?: boolean; gender?: string }) {
    const response = await apiClient.get<Hostel[]>('/hostel/hostels', { params });
    return response.data;
  },

  async getHostel(id: string) {
    const response = await apiClient.get<Hostel>(`/hostel/hostels/${id}`);
    return response.data;
  },

  async createHostel(data: Partial<Hostel>) {
    const response = await apiClient.post<Hostel>('/hostel/hostels', data);
    return response.data;
  },

  async updateHostel(id: string, data: Partial<Hostel>) {
    const response = await apiClient.patch<Hostel>(`/hostel/hostels/${id}`, data);
    return response.data;
  },

  async deleteHostel(id: string) {
    const response = await apiClient.delete(`/hostel/hostels/${id}`);
    return response.data;
  },

  // Rooms
  async getRooms(hostelId: string, params?: { active_only?: boolean; floor?: number }) {
    const response = await apiClient.get<Room[]>(`/hostel/hostels/${hostelId}/rooms`, { params });
    return response.data;
  },

  async getRoom(id: string) {
    const response = await apiClient.get<Room>(`/hostel/rooms/${id}`);
    return response.data;
  },

  async createRoom(data: Partial<Room>) {
    const response = await apiClient.post<Room>('/hostel/rooms', data);
    return response.data;
  },

  async updateRoom(id: string, data: Partial<Room>) {
    const response = await apiClient.patch<Room>(`/hostel/rooms/${id}`, data);
    return response.data;
  },

  async deleteRoom(id: string) {
    const response = await apiClient.delete(`/hostel/rooms/${id}`);
    return response.data;
  },

  // Beds
  async createBeds(roomId: string, beds: Partial<Bed>[]) {
    const response = await apiClient.post<Bed[]>(`/hostel/rooms/${roomId}/beds`, beds);
    return response.data;
  },

  async updateBed(id: string, data: Partial<Bed>) {
    const response = await apiClient.patch<Bed>(`/hostel/beds/${id}`, data);
    return response.data;
  },

  // Wardens
  async getWardens(params?: { active_only?: boolean; hostel_id?: string }) {
    const response = await apiClient.get<Warden[]>('/hostel/wardens', { params });
    return response.data;
  },

  async getWarden(id: string) {
    const response = await apiClient.get<Warden>(`/hostel/wardens/${id}`);
    return response.data;
  },

  async createWarden(data: Partial<Warden>) {
    const response = await apiClient.post<Warden>('/hostel/wardens', data);
    return response.data;
  },

  async updateWarden(id: string, data: Partial<Warden>) {
    const response = await apiClient.patch<Warden>(`/hostel/wardens/${id}`, data);
    return response.data;
  },

  async assignWarden(data: { warden_id: string; hostel_id: string }) {
    const response = await apiClient.post<Warden>('/hostel/assign-warden', data);
    return response.data;
  },

  // Student Assignments
  async assignStudent(data: {
    student_id: string;
    hostel_id: string;
    room_id: string;
    bed_id: string;
  }) {
    const response = await apiClient.post<StudentHostelAssignment>('/hostel/students/assign', data);
    return response.data;
  },

  async unassignStudent(data: { student_id: string }) {
    const response = await apiClient.post('/hostel/students/unassign', data);
    return response.data;
  },

  async getStudentsInHostel(hostelId: string, activeOnly: boolean = true) {
    const response = await apiClient.get<StudentHostelAssignment[]>(
      `/hostel/students/hostel/${hostelId}`,
      { params: { active_only: activeOnly } }
    );
    return response.data;
  },

  // Occupancy
  async getOccupancy() {
    const response = await apiClient.get('/hostel/occupancy');
    return response.data;
  },

  async getHostelOccupancy(hostelId: string) {
    const response = await apiClient.get(`/hostel/occupancy/${hostelId}`);
    return response.data;
  },

  async getAvailableBeds(params?: { hostel_id?: string; floor?: number }) {
    const response = await apiClient.get('/hostel/available-beds', { params });
    return response.data;
  },
};
