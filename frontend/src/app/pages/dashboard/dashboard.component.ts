// src/app/pages/dashboard/dashboard.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { SidebarComponent } from '../../shared/sidebar/sidebar.component';
import { DashboardService } from '../../core/services/dashboard.service';
import { AuthService } from '../../core/services/auth.service';
import { DashboardStats } from '../../core/models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, SidebarComponent],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  stats: DashboardStats | null = null;
  loading = true;
  
  get user() { return this.auth.currentUser; }

  get progressPct(): number {
    if (!this.stats || this.stats.total_tasks === 0) return 0;
    return Math.round((this.stats.done / this.stats.total_tasks) * 100);
  }

  constructor(
    private dashboardService: DashboardService,
    private auth: AuthService
  ) {}

  ngOnInit() {
    this.dashboardService.getStats().subscribe({
      next: (data) => { this.stats = data; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  getStatusClass(status: string): string {
    const map: Record<string, string> = {
      todo: 'badge badge-todo',
      in_progress: 'badge badge-progress',
      done: 'badge badge-done',
    };
    return map[status] || 'badge badge-todo';
  }

  getStatusLabel(status: string): string {
    const map: Record<string, string> = { todo: 'To Do', in_progress: 'In Progress', done: 'Done' };
    return map[status] || status;
  }

  getPriorityClass(priority: string): string {
    const map: Record<string, string> = {
      low: 'badge badge-low',
      medium: 'badge badge-medium',
      high: 'badge badge-high',
    };
    return map[priority] || 'badge badge-medium';
  }
}
