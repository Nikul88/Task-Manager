// src/app/shared/sidebar/sidebar.component.ts
import { Component } from '@angular/core';
import { CommonModule, TitleCasePipe } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, TitleCasePipe],
  templateUrl: './sidebar.component.html',
})
export class SidebarComponent {
  get user() { return this.auth.currentUser; }

  constructor(private auth: AuthService) {}

  logout() { this.auth.logout(); }
}
