// src/app/pages/auth/signup/signup.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './signup.component.html',
})
export class SignupComponent {
  name = '';
  email = '';
  password = '';
  showPwd = false;
  loading = false;
  error = '';
  success = '';

  constructor(private auth: AuthService, private router: Router) {}

  onSubmit() {
    this.error = '';
    this.success = '';
    this.loading = true;

    this.auth.signup(this.name, this.email, this.password).subscribe({
      next: (res) => {
        this.loading = false;
        this.success = res.message;
        // Navigate to OTP page with email pre-filled
        setTimeout(() => this.router.navigate(['/verify-otp'], { queryParams: { email: this.email } }), 1500);
      },
      error: (err) => {
        this.loading = false;
        this.error = err?.error?.detail || 'Signup failed. Please try again.';
      }
    });
  }
}
