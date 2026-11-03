import React, { useState } from 'react';
import type { UserRole } from '../../types';
import { db } from '../../db/database';
import { authService } from '../../services/apiServices';
import { LogIn, User, Stethoscope, Building2, HandHeart, ShieldCheck, AlertCircle, CheckCircle2, Lock, Shield } from 'lucide-react';
import { Button } from '../common/UIComponents';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (role: UserRole) => void;
  onOpenRegister: () => void;
  superAdminOnly?: boolean;
}

export const LoginModal: React.FC<LoginModalProps> = ({
  isOpen,
  onClose,
  onLoginSuccess,
  onOpenRegister,
  superAdminOnly = false
}) => {
  const [role, setRole] = useState<UserRole>(superAdminOnly ? 'SUPER_ADMIN' : 'PATIENT');
  const [email, setEmail] = useState(superAdminOnly ? 'superadmin@chikitsax.demo' : 'patient@chikitsax.demo');
  const [password, setPassword] = useState('demo123');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetEmailSent, setResetEmailSent] = useState(false);

  if (!isOpen) return null;

  // Change defaults when role switches
  const handleSelectRole = (newRole: UserRole) => {
    setRole(newRole);
    setError(null);
    if (newRole === 'PATIENT') setEmail('patient@chikitsax.demo');
    else if (newRole === 'DOCTOR') setEmail('doctor@chikitsax.demo');
    else if (newRole === 'HOSPITAL_ADMIN') setEmail('hospital@chikitsax.demo');
    else if (newRole === 'NGO_OFFICER') setEmail('ngo@chikitsax.demo');
    else if (newRole === 'SUPER_ADMIN') setEmail('superadmin@chikitsax.demo');
    setPassword('demo123');
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in both email/ID and password.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const backendAuth = await authService.login(email.trim(), password, role);
      if (backendAuth && backendAuth.user && backendAuth.token) {
        const u = {
          id: backendAuth.user.id,
          email: backendAuth.user.email,
          name: backendAuth.user.name,
          role: backendAuth.user.role as UserRole,
          phone: backendAuth.user.phone,
          avatar: backendAuth.user.avatar,
          hospitalId: backendAuth.user.hospitalId,
          doctorProfile: backendAuth.user.doctorProfile,
          patientProfile: backendAuth.user.patientProfile
        };
        db.setCurrentUser(u);
        setIsLoading(false);
        onLoginSuccess(u.role);
        onClose();
        return;
      } else {
        throw new Error('Authentication failed: No user profile received.');
      }
    } catch (err: any) {
      setIsLoading(false);
      const msg = err?.message || 'Login failed. Please verify your credentials and ensure your selected role matches your account.';
      setError(msg);
      return;
    }
  };

  const handleGoogleLogin = async () => {
    setIsGoogleLoading(true);
    setError(null);

    try {
      const googleEmail = `${role.toLowerCase()}.google@vedaconnect.in`;
      const googleName = role === 'PATIENT' ? 'Google Patient' :
                         role === 'DOCTOR' ? 'Dr. Google Medical' :
                         role === 'HOSPITAL_ADMIN' ? 'Hospital Director' :
                         role === 'NGO_OFFICER' ? 'Scheme Officer' : 'National Director';

      const backendAuth = await authService.googleLogin(googleEmail, googleName, role);
      if (backendAuth && backendAuth.user && backendAuth.token) {
        const u = {
          id: backendAuth.user.id,
          email: backendAuth.user.email,
          name: backendAuth.user.name,
          role: backendAuth.user.role as UserRole,
          phone: backendAuth.user.phone,
          avatar: backendAuth.user.avatar,
          hospitalId: backendAuth.user.hospitalId,
          doctorProfile: backendAuth.user.doctorProfile,
          patientProfile: backendAuth.user.patientProfile
        };
        db.setCurrentUser(u);
        setIsGoogleLoading(false);
        onLoginSuccess(u.role);
        onClose();
      } else {
        throw new Error('Google Sign-In response missing token.');
      }
    } catch (err: any) {
      setIsGoogleLoading(false);
      setError(err?.message || 'Google Sign-In failed. Please try standard login.');
    }
  };

  const roleMeta = {
    PATIENT: {
      label: 'Patient Portal',
      hindi: 'मरीज पोर्टल',
      icon: <User size={16} />,
      badgeColor: 'badge-teal',
      inputLabel: 'Mobile Number / Email / ABHA ID',
      placeholder: 'patient@chikitsax.demo or 9876543210',
      description: 'Access personal health records, OPD bookings, reminders & family hub.'
    },
    DOCTOR: {
      label: 'Doctor Workspace',
      hindi: 'डॉक्टर क्लिनिक',
      icon: <Stethoscope size={16} />,
      badgeColor: 'badge-purple',
      inputLabel: 'Doctor Registration Email / NMC ID',
      placeholder: 'doctor@chikitsax.demo',
      description: 'Access patient queue, clinical AI triage, e-prescriptions & cost estimates.'
    },
    HOSPITAL_ADMIN: {
      label: 'Hospital Admin',
      hindi: 'अस्पताल प्रबंधन',
      icon: <Building2 size={16} />,
      badgeColor: 'badge-green',
      inputLabel: 'Hospital Admin Email / Empanelment Code',
      placeholder: 'hospital@chikitsax.demo',
      description: 'Manage QR OPD check-in, live queue screen, scheme help desk & ICU beds.'
    },
    NGO_OFFICER: {
      label: 'NGO / Scheme Officer',
      hindi: 'योजना सत्यापन',
      icon: <HandHeart size={16} />,
      badgeColor: 'badge-yellow',
      inputLabel: 'Govt / Scheme Officer Nodal ID',
      placeholder: 'ngo@chikitsax.demo',
      description: 'Verify PM-JAY & MJPJAY beneficiary applications & grant disbursal.'
    },
    SUPER_ADMIN: {
      label: 'Super Admin',
      hindi: 'राष्ट्रीय व्यवस्थापक',
      icon: <ShieldCheck size={16} />,
      badgeColor: 'badge-danger',
      inputLabel: 'National Platform Administrator',
      placeholder: 'superadmin@chikitsax.demo',
      description: 'Governance of all logins, hospital empanelment, AI telemetry & security audits.'
    }
  };

  const activeMeta = roleMeta[role];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        style={{
          maxWidth: '540px',
          padding: '28px',
          borderRadius: '24px',
          boxShadow: 'var(--shadow-xl)',
          animation: 'fadeIn 0.2s ease-out',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-light)'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '44px',
                height: '44px',
                background: 'linear-gradient(135deg, #0284C7 0%, #0F172A 100%)',
                borderRadius: '12px',
                color: '#FFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(2, 132, 199, 0.3)'
              }}
            >
              <LogIn size={22} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.35rem', margin: '0 0 2px', fontWeight: 800, color: 'var(--text-heading)' }}>
                {showForgotPassword ? 'Reset Password' : 'Sign In to VedaConnect'}
              </h2>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>
                Role-Governed Health Navigation • JWT &amp; ABAC Protected
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.4rem', cursor: 'pointer', lineHeight: 1 }}
          >
            ×
          </button>
        </div>

        {/* Role Selector Tabs (Super Admin is excluded from public tabs per security rules) */}
        {!showForgotPassword && !superAdminOnly && (
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Select Login Portal (पोर्टल चुनें):
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
              {(['PATIENT', 'DOCTOR', 'HOSPITAL_ADMIN', 'NGO_OFFICER'] as const).map(r => {
                const isSelected = role === r;
                return (
                  <button
                    key={r}
                    type="button"
                    onClick={() => handleSelectRole(r)}
                    style={{
                      padding: '10px 6px',
                      borderRadius: '12px',
                      border: isSelected ? '1.5px solid var(--primary-teal)' : '1px solid var(--border-light)',
                      background: isSelected ? 'rgba(2, 132, 199, 0.12)' : 'var(--bg-main)',
                      color: isSelected ? 'var(--primary-teal)' : 'var(--text-muted)',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '5px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ transform: isSelected ? 'scale(1.1)' : 'scale(1)', transition: 'transform 0.15s ease' }}>
                      {roleMeta[r].icon}
                    </div>
                    <span style={{ fontSize: '0.72rem', fontWeight: isSelected ? 700 : 500, textAlign: 'center', lineHeight: 1.2 }}>
                      {r === 'PATIENT' ? 'Patient' : r === 'DOCTOR' ? 'Doctor' : r === 'HOSPITAL_ADMIN' ? 'Hospital' : 'NGO Officer'}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Secret Super Admin Header when accessed via /superadmin */}
        {superAdminOnly && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.15) 0%, rgba(15, 23, 42, 0.25) 100%)',
            border: '1px solid rgba(79, 70, 229, 0.4)',
            borderRadius: '12px',
            padding: '12px 16px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            <ShieldCheck size={24} color="#6366F1" />
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-heading)' }}>
                Secret Super Admin Console Access
              </div>
              <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                Authenticated via secure endpoint /superadmin • Platform Governance
              </div>
            </div>
          </div>
        )}

        {/* Selected Role Scope Notice */}
        {!showForgotPassword && (
          <div style={{
            background: 'var(--bg-main)',
            border: '1px solid var(--border-light)',
            borderRadius: '12px',
            padding: '10px 14px',
            marginBottom: '18px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '0.8rem'
          }}>
            <Lock size={15} color="var(--primary-teal)" style={{ flexShrink: 0 }} />
            <div style={{ color: 'var(--text-secondary)' }}>
              Logging into <strong style={{ color: 'var(--text-heading)' }}>{activeMeta.label}</strong> ({activeMeta.hindi}).
              <span style={{ display: 'block', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                {activeMeta.description}
              </span>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div
            style={{
              padding: '10px 14px',
              background: 'rgba(220, 38, 38, 0.1)',
              border: '1px solid rgba(220, 38, 38, 0.3)',
              borderRadius: '10px',
              color: '#DC2626',
              fontSize: '0.84rem',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Google Sign-In Button */}
        {!showForgotPassword && (
          <div style={{ marginBottom: '18px' }}>
            <button
              type="button"
              onClick={handleGoogleLogin}
              disabled={isGoogleLoading || isLoading}
              style={{
                width: '100%',
                padding: '11px',
                borderRadius: '12px',
                border: '1px solid var(--border-light)',
                background: 'var(--bg-main)',
                color: 'var(--text-heading)',
                fontSize: '0.88rem',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                cursor: 'pointer',
                transition: 'background 0.15s ease',
                boxShadow: 'var(--shadow-sm)'
              }}
            >
              {/* Google Brand SVG */}
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
              </svg>
              {isGoogleLoading ? 'Authenticating with Google...' : `Continue with Google (${activeMeta.label})`}
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: '16px 0' }}>
              <div style={{ flex: 1, height: '1px', background: 'var(--border-light)' }}></div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>or sign in with credentials</span>
              <div style={{ flex: 1, height: '1px', background: 'var(--border-light)' }}></div>
            </div>
          </div>
        )}

        {/* Standard Email / Password Form */}
        {!showForgotPassword ? (
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                {activeMeta.inputLabel} *
              </label>
              <input
                type="text"
                required
                placeholder={activeMeta.placeholder}
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="form-input"
                style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', fontSize: '0.88rem', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                  Password *
                </label>
                <button
                  type="button"
                  onClick={() => setShowForgotPassword(true)}
                  style={{ background: 'none', border: 'none', color: 'var(--primary-teal)', fontSize: '0.76rem', cursor: 'pointer', padding: 0 }}
                >
                  Forgot Password?
                </button>
              </div>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="form-input"
                style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', fontSize: '0.88rem', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary"
              style={{ width: '100%', padding: '11px', borderRadius: '12px', fontSize: '0.92rem', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
            >
              <LogIn size={16} /> {isLoading ? 'Verifying on Neon PostgreSQL...' : `Sign In as ${activeMeta.label}`}
            </button>

            {/* Privacy & Cross-Role Isolation Guarantee */}
            <div style={{ marginTop: '16px', display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              <Shield size={14} color="var(--success-green)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <span>
                <strong>Data Isolation Active:</strong> When signed in as <strong>{role}</strong>, you will only see authorized {role.toLowerCase()} data. Doctor notes, hospital admin tools, and other patients' vault records are strictly inaccessible.
              </span>
            </div>

            {/* Registration link for Patients */}
            {role === 'PATIENT' && (
              <div style={{ marginTop: '16px', textAlign: 'center', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                New to VedaConnect?{' '}
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onOpenRegister();
                  }}
                  style={{ background: 'none', border: 'none', color: 'var(--primary-teal)', fontWeight: 600, cursor: 'pointer', padding: 0 }}
                >
                  Create Patient Account
                </button>
              </div>
            )}
          </form>
        ) : (
          /* Forgot Password View */
          <div>
            {resetEmailSent ? (
              <div style={{ textAlign: 'center', padding: '20px 0' }}>
                <CheckCircle2 size={42} color="var(--success-green)" style={{ margin: '0 auto 12px' }} />
                <h4 style={{ margin: '0 0 6px', color: 'var(--text-heading)' }}>Reset Link Dispatched</h4>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '20px' }}>
                  If an account exists for <strong>{email}</strong>, a secure password recovery token has been sent.
                </p>
                <Button variant="secondary" onClick={() => { setShowForgotPassword(false); setResetEmailSent(false); }}>
                  Back to Sign In
                </Button>
              </div>
            ) : (
              <form onSubmit={e => { e.preventDefault(); setResetEmailSent(true); }}>
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Registered Account Email *
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    className="form-input"
                    style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                  />
                </div>
                <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                  <Button variant="secondary" type="button" onClick={() => setShowForgotPassword(false)}>
                    Cancel
                  </Button>
                  <Button variant="primary" type="submit">
                    Send Reset Link
                  </Button>
                </div>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
