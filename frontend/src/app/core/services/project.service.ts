// src/app/core/services/project.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Project, ProjectDetail, Member } from '../models';

@Injectable({ providedIn: 'root' })
export class ProjectService {
  private base = `${environment.apiUrl}/projects`;

  constructor(private http: HttpClient) {}

  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(this.base);
  }

  getProject(id: number): Observable<ProjectDetail> {
    return this.http.get<ProjectDetail>(`${this.base}/${id}`);
  }

  createProject(name: string, description?: string): Observable<Project> {
    return this.http.post<Project>(this.base, { name, description });
  }

  updateProject(id: number, name: string, description?: string): Observable<Project> {
    return this.http.put<Project>(`${this.base}/${id}`, { name, description });
  }

  deleteProject(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.base}/${id}`);
  }

  getMembers(projectId: number): Observable<Member[]> {
    return this.http.get<Member[]>(`${this.base}/${projectId}/members`);
  }

  addMember(projectId: number, email: string, role: string = 'member'): Observable<Member> {
    return this.http.post<Member>(`${this.base}/${projectId}/members`, { email, role });
  }

  removeMember(projectId: number, userId: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.base}/${projectId}/members/${userId}`);
  }
}
