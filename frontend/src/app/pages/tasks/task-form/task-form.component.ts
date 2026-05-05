// src/app/pages/tasks/task-form/task-form.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router, ActivatedRoute } from '@angular/router';
import { SidebarComponent } from '../../../shared/sidebar/sidebar.component';
import { TaskService } from '../../../core/services/task.service';
import { ProjectService } from '../../../core/services/project.service';
import { Project, Member } from '../../../core/models';

@Component({
  selector: 'app-task-form',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, SidebarComponent],
  templateUrl: './task-form.component.html',
})
export class TaskFormComponent implements OnInit {
  // Form fields
  title = '';
  description = '';
  selectedProjectId: number | '' = '';
  assigneeId: number | null = null;
  status = 'todo';
  priority = 'medium';
  dueDate = '';

  // State
  isEdit = false;
  taskId: number | null = null;
  projectId: number | null = null;
  projects: Project[] = [];
  members: Member[] = [];
  loading = true;
  saving = false;
  error = '';
  success = '';

  constructor(
    private taskService: TaskService,
    private projectService: ProjectService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit() {
    // Check if edit mode
    const id = this.route.snapshot.paramMap.get('id');
    if (id) { this.isEdit = true; this.taskId = Number(id); }

    // Pre-fill project_id from query param (coming from project detail page)
    const qProjectId = this.route.snapshot.queryParamMap.get('project_id');
    if (qProjectId) this.projectId = Number(qProjectId);

    // Load projects first
    this.projectService.getProjects().subscribe({
      next: (ps) => {
        this.projects = ps;
        if (this.projectId) {
          this.selectedProjectId = this.projectId;
          this.loadMembers(this.projectId);
        }
        if (this.isEdit && this.taskId) {
          this.loadTask(this.taskId);
        } else {
          this.loading = false;
        }
      },
      error: () => { this.loading = false; }
    });
  }

  loadTask(id: number) {
    this.taskService.getTask(id).subscribe({
      next: (t) => {
        this.title = t.title;
        this.description = t.description || '';
        this.selectedProjectId = t.project_id;
        this.assigneeId = t.assignee_id || null;
        this.status = t.status;
        this.priority = t.priority;
        this.dueDate = t.due_date ? new Date(t.due_date).toISOString().slice(0, 16) : '';
        this.projectId = t.project_id;
        this.loadMembers(t.project_id);
        this.loading = false;
      },
      error: () => { this.loading = false; }
    });
  }

  onProjectChange() {
    if (this.selectedProjectId) {
      this.assigneeId = null;
      this.loadMembers(Number(this.selectedProjectId));
    } else {
      this.members = [];
    }
  }

  loadMembers(projectId: number) {
    this.projectService.getMembers(projectId).subscribe({
      next: (ms) => { this.members = ms; },
      error: () => {}
    });
  }

  onSubmit() {
    if (!this.title.trim() || !this.selectedProjectId) return;
    this.saving = true;
    this.error = '';

    const payload: any = {
      title: this.title.trim(),
      description: this.description.trim() || undefined,
      status: this.status,
      priority: this.priority,
      project_id: Number(this.selectedProjectId),
      assignee_id: this.assigneeId || undefined,
      due_date: this.dueDate ? new Date(this.dueDate).toISOString() : undefined,
    };

    if (this.isEdit && this.taskId) {
      this.taskService.updateTask(this.taskId, payload).subscribe({
        next: (t) => {
          this.saving = false;
          this.success = 'Task updated successfully!';
          setTimeout(() => this.router.navigate(['/projects', t.project_id]), 1000);
        },
        error: (err) => { this.saving = false; this.error = err?.error?.detail || 'Failed to update task.'; }
      });
    } else {
      this.taskService.createTask(payload).subscribe({
        next: (t) => {
          this.saving = false;
          this.success = 'Task created successfully!';
          setTimeout(() => this.router.navigate(['/projects', t.project_id]), 1000);
        },
        error: (err) => { this.saving = false; this.error = err?.error?.detail || 'Failed to create task.'; }
      });
    }
  }
}
