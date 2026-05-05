// src/app/core/models/index.ts – Shared TypeScript interfaces

export interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'member';
  is_verified: boolean;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  owner_id: number;
  owner_name: string;
  created_at?: string;
  member_count: number;
  task_count: number;
}

export interface ProjectDetail {
  id: number;
  name: string;
  description?: string;
  owner_id: number;
  owner_name: string;
  created_at?: string;
  members: Member[];
}

export interface Member {
  id: number;
  user_id: number;
  user_name: string;
  user_email: string;
  role: 'admin' | 'member';
  joined_at?: string;
}

export interface Task {
  id: number;
  title: string;
  description?: string;
  status: 'todo' | 'in_progress' | 'done';
  priority: 'low' | 'medium' | 'high';
  due_date?: string;
  project_id: number;
  project_name?: string;
  assignee_id?: number;
  assignee_name?: string;
  created_by?: number;
  creator_name?: string;
  created_at?: string;
  updated_at?: string;
  is_overdue: boolean;
}

export interface DashboardStats {
  total_tasks: number;
  todo: number;
  in_progress: number;
  done: number;
  overdue: number;
  recent_tasks: Task[];
}

export interface ApiError {
  detail: string;
}
