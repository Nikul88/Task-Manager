// src/app/core/services/task.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Task } from '../models';

export interface TaskCreatePayload {
  title: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string;
  project_id: number;
  assignee_id?: number;
}

export interface TaskUpdatePayload {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string;
  assignee_id?: number;
}

@Injectable({ providedIn: 'root' })
export class TaskService {
  private base = `${environment.apiUrl}/tasks`;

  constructor(private http: HttpClient) {}

  getTasks(projectId?: number, status?: string, assigneeId?: number): Observable<Task[]> {
    let params = new HttpParams();
    if (projectId) params = params.set('project_id', projectId);
    if (status)    params = params.set('status', status);
    if (assigneeId) params = params.set('assignee_id', assigneeId);
    return this.http.get<Task[]>(this.base, { params });
  }

  getTask(id: number): Observable<Task> {
    return this.http.get<Task>(`${this.base}/${id}`);
  }

  createTask(payload: TaskCreatePayload): Observable<Task> {
    return this.http.post<Task>(this.base, payload);
  }

  updateTask(id: number, payload: TaskUpdatePayload): Observable<Task> {
    return this.http.put<Task>(`${this.base}/${id}`, payload);
  }

  updateStatus(id: number, status: string): Observable<Task> {
    return this.http.patch<Task>(`${this.base}/${id}/status`, { status });
  }

  deleteTask(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.base}/${id}`);
  }
}
