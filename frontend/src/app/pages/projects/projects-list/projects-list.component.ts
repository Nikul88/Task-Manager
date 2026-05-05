// src/app/pages/projects/projects-list/projects-list.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { SidebarComponent } from '../../../shared/sidebar/sidebar.component';
import { ProjectService } from '../../../core/services/project.service';
import { AuthService } from '../../../core/services/auth.service';
import { Project } from '../../../core/models';

@Component({
  selector: 'app-projects-list',
  standalone: true,
  imports: [CommonModule, FormsModule, SidebarComponent],
  templateUrl: './projects-list.component.html',
})
export class ProjectsListComponent implements OnInit {
  projects: Project[] = [];
  loading = true;
  error = '';

  showCreateModal = false;
  showDeleteModal = false;
  newName = '';
  newDesc = '';
  modalError = '';
  saving = false;
  deleteTarget: Project | null = null;

  constructor(
    private projectService: ProjectService, 
    private router: Router,
    private auth: AuthService
  ) {}

  get user() { return this.auth.currentUser; }

  ngOnInit() { this.loadProjects(); }

  loadProjects() {
    this.loading = true;
    this.projectService.getProjects().subscribe({
      next: (data) => { this.projects = data; this.loading = false; },
      error: () => { this.error = 'Failed to load projects.'; this.loading = false; }
    });
  }

  goToProject(id: number) { this.router.navigate(['/projects', id]); }

  openCreateModal() { this.showCreateModal = true; this.newName = ''; this.newDesc = ''; this.modalError = ''; }
  openDeleteModal(p: Project, e: Event) { e.stopPropagation(); this.deleteTarget = p; this.showDeleteModal = true; }
  closeModals() { this.showCreateModal = false; this.showDeleteModal = false; this.deleteTarget = null; this.modalError = ''; }

  createProject() {
    if (!this.newName.trim()) return;
    this.saving = true;
    this.modalError = '';
    this.projectService.createProject(this.newName.trim(), this.newDesc.trim() || undefined).subscribe({
      next: (p) => {
        this.projects.unshift(p);
        this.saving = false;
        this.closeModals();
        this.router.navigate(['/projects', p.id]);
      },
      error: (err) => { this.modalError = err?.error?.detail || 'Failed to create project.'; this.saving = false; }
    });
  }

  confirmDelete() {
    if (!this.deleteTarget) return;
    this.saving = true;
    this.projectService.deleteProject(this.deleteTarget.id).subscribe({
      next: () => {
        this.projects = this.projects.filter(p => p.id !== this.deleteTarget!.id);
        this.saving = false;
        this.closeModals();
      },
      error: (err) => { this.error = err?.error?.detail || 'Failed to delete project.'; this.saving = false; this.closeModals(); }
    });
  }
}
