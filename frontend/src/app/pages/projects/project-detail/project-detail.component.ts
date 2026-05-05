// src/app/pages/projects/project-detail/project-detail.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { SidebarComponent } from '../../../shared/sidebar/sidebar.component';
import { ProjectService } from '../../../core/services/project.service';
import { TaskService } from '../../../core/services/task.service';
import { AuthService } from '../../../core/services/auth.service';
import { ProjectDetail, Task, Member } from '../../../core/models';

@Component({
  selector: 'app-project-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, SidebarComponent, DatePipe],
  templateUrl: './project-detail.component.html',
})
export class ProjectDetailComponent implements OnInit {
  project: ProjectDetail | null = null;
  tasks: Task[] = [];
  filteredTasks: Task[] = [];
  loading = true;
  statusFilter = '';

  showAddMemberModal = false;
  showDeleteTaskModal = false;
  memberEmail = '';
  memberRole = 'member';
  modalError = '';
  modalSuccess = '';
  saving = false;
  deleteTaskTarget: Task | null = null;

  constructor(
    private route: ActivatedRoute,
    private projectService: ProjectService,
    private taskService: TaskService,
    private auth: AuthService
  ) {}

  get user() { return this.auth.currentUser; }

  ngOnInit() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.loadProject(id);
    this.loadTasks(id);
  }

  loadProject(id: number) {
    this.projectService.getProject(id).subscribe({
      next: (p) => { this.project = p; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  loadTasks(id: number) {
    this.taskService.getTasks(id).subscribe({
      next: (tasks) => { this.tasks = tasks; this.filteredTasks = tasks; },
      error: () => {}
    });
  }

  filterTasks() {
    this.filteredTasks = this.statusFilter
      ? this.tasks.filter(t => t.status === this.statusFilter)
      : [...this.tasks];
  }

  updateStatus(task: Task, e: Event) {
    const newStatus = (e.target as HTMLSelectElement).value;
    this.taskService.updateStatus(task.id, newStatus).subscribe({
      next: (updated) => {
        const idx = this.tasks.findIndex(t => t.id === task.id);
        if (idx !== -1) { this.tasks[idx] = updated; this.filterTasks(); }
      },
      error: () => {}
    });
  }

  openAddMemberModal() { this.showAddMemberModal = true; this.memberEmail = ''; this.modalError = ''; this.modalSuccess = ''; }
  openDeleteTaskModal(t: Task) { this.deleteTaskTarget = t; this.showDeleteTaskModal = true; }
  closeModals() { this.showAddMemberModal = false; this.showDeleteTaskModal = false; this.deleteTaskTarget = null; this.modalError = ''; this.modalSuccess = ''; }

  addMember() {
    if (!this.project || !this.memberEmail.trim()) return;
    this.saving = true;
    this.modalError = '';
    this.projectService.addMember(this.project.id, this.memberEmail.trim(), this.memberRole).subscribe({
      next: (m) => {
        this.project!.members.push(m);
        this.saving = false;
        this.modalSuccess = `${m.user_name} added successfully!`;
        this.memberEmail = '';
        setTimeout(() => this.closeModals(), 1500);
      },
      error: (err) => { this.modalError = err?.error?.detail || 'Failed to add member.'; this.saving = false; }
    });
  }

  removeMember(m: Member) {
    if (!this.project) return;
    if (!confirm(`Remove ${m.user_name} from this project?`)) return;
    this.projectService.removeMember(this.project.id, m.user_id).subscribe({
      next: () => { this.project!.members = this.project!.members.filter(x => x.user_id !== m.user_id); },
      error: () => {}
    });
  }

  confirmDeleteTask() {
    if (!this.deleteTaskTarget) return;
    this.saving = true;
    this.taskService.deleteTask(this.deleteTaskTarget.id).subscribe({
      next: () => {
        this.tasks = this.tasks.filter(t => t.id !== this.deleteTaskTarget!.id);
        this.filterTasks();
        this.saving = false;
        this.closeModals();
      },
      error: () => { this.saving = false; this.closeModals(); }
    });
  }

  getStatusClass(s: string) {
    return { todo: 'badge badge-todo', in_progress: 'badge badge-progress', done: 'badge badge-done' }[s] || 'badge badge-todo';
  }
  getStatusLabel(s: string) {
    return { todo: 'To Do', in_progress: 'In Progress', done: 'Done' }[s] || s;
  }
  getPriorityClass(p: string) {
    return { low: 'badge badge-low', medium: 'badge badge-medium', high: 'badge badge-high' }[p] || 'badge badge-medium';
  }
  getPriorityColor(p: string) {
    return { low: 'var(--info)', medium: 'var(--warning)', high: 'var(--danger)' }[p] || 'var(--warning)';
  }
}
