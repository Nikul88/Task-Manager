// src/app/pages/auth/verify-otp/verify-otp.component.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-verify-otp',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './verify-otp.component.html',
})
export class VerifyOtpComponent implements OnInit, OnDestroy {
  email = '';
  otpDigits: string[] = ['', '', '', '', '', ''];
  loading = false;
  error = '';
  success = '';
  resendCooldown = 0;
  private _cooldownTimer: any;

  get otpCode(): string { return this.otpDigits.join(''); }

  constructor(
    private auth: AuthService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit() {
    this.email = this.route.snapshot.queryParamMap.get('email') || '';
    if (!this.email) this.router.navigate(['/signup']);
    this._startResendCooldown(60);
  }

  ngOnDestroy() { clearInterval(this._cooldownTimer); }

  onDigitInput(e: Event, index: number) {
    const input = e.target as HTMLInputElement;
    const val = input.value.replace(/\D/g, '');
    this.otpDigits[index] = val ? val[val.length - 1] : '';
    input.value = this.otpDigits[index];
    if (val && index < 5) this._focusNext(index);
  }

  onKeyDown(e: KeyboardEvent, index: number) {
    if (e.key === 'Backspace' && !this.otpDigits[index] && index > 0) {
      this.otpDigits[index - 1] = '';
      this._focusIndex(index - 1);
    }
  }

  onPaste(e: ClipboardEvent) {
    e.preventDefault();
    const text = e.clipboardData?.getData('text') || '';
    const digits = text.replace(/\D/g, '').slice(0, 6).split('');
    digits.forEach((d, i) => { if (i < 6) this.otpDigits[i] = d; });
    if (digits.length === 6) setTimeout(() => this.onVerify(), 100);
  }

  onVerify() {
    this.error = '';
    this.loading = true;
    this.auth.verifyOtp(this.email, this.otpCode).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err?.error?.detail || 'Invalid OTP. Please try again.';
      }
    });
  }

  onResend() {
    if (this.resendCooldown > 0) return;
    this.error = '';
    this.auth.resendOtp(this.email).subscribe({
      next: () => {
        this.success = 'A new OTP has been sent to your email!';
        this._startResendCooldown(60);
        setTimeout(() => this.success = '', 4000);
      },
      error: (err) => { this.error = err?.error?.detail || 'Failed to resend OTP.'; }
    });
  }

  private _focusNext(index: number) { this._focusIndex(index + 1); }
  private _focusIndex(index: number) {
    const el = document.getElementById(`otp-${index}`);
    if (el) (el as HTMLInputElement).focus();
  }

  private _startResendCooldown(seconds: number) {
    this.resendCooldown = seconds;
    clearInterval(this._cooldownTimer);
    this._cooldownTimer = setInterval(() => {
      this.resendCooldown--;
      if (this.resendCooldown <= 0) clearInterval(this._cooldownTimer);
    }, 1000);
  }
}
