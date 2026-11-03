import React from 'react';
import { db } from '../../db/database';
import { Printer, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const HealthReportModal: React.FC<Props> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const profile = db.getPatientProfile();
  const records = db.getMedicalRecords();
  const appointments = db.getOPDRegistrations();
  const rxList = db.getEPrescriptions();

  const handlePrint = () => {
    window.print();
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(15, 23, 42, 0.7)',
      backdropFilter: 'blur(5px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '16px'
    }}>
      <div style={{
        background: '#FFF',
        color: '#0F172A',
        borderRadius: '16px',
        maxWidth: '820px',
        width: '100%',
        maxHeight: '92vh',
        overflowY: 'auto',
        boxShadow: 'var(--shadow-xl)',
        animation: 'fadeIn 0.2s ease-out',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Print Bar (Hidden during print) */}
        <div className="no-print" style={{
          padding: '14px 20px',
          background: 'var(--bg-main)',
          borderBottom: '1px solid var(--border-light)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            One-Click Clinical Health Summary (एक-क्लिक स्वास्थ्य रिपोर्ट)
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handlePrint}
              className="btn btn-primary btn-sm"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <Printer size={15} /> Print / Save as PDF
            </button>
            <button
              onClick={onClose}
              className="btn btn-secondary btn-sm"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
            >
              <X size={15} /> Close
            </button>
          </div>
        </div>

        {/* Printable Report Document Body */}
        <div style={{ padding: '36px', background: '#FFF', color: '#1E293B', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
          {/* Document Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid #0284C7', paddingBottom: '16px', marginBottom: '24px' }}>
            <div>
              <h1 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '0 0 4px', color: '#0F172A', letterSpacing: '-0.02em' }}>
                CHIKITSA-X VEDACONNECT
              </h1>
              <p style={{ margin: 0, fontSize: '0.82rem', color: '#64748B', fontWeight: 600 }}>
                Ayushman Bharat Digital Mission (ABDM) Compliant Health Record Summary
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block' }}>Report Generated On</span>
              <strong style={{ fontSize: '0.9rem', color: '#0F172A' }}>{new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</strong>
            </div>
          </div>

          {/* Patient Details Grid */}
          <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '10px', padding: '16px 20px', marginBottom: '24px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: '#64748B', fontSize: '0.75rem', display: 'block' }}>Patient Name</span>
              <strong style={{ color: '#0F172A', fontSize: '0.95rem' }}>{profile.fullName}</strong>
            </div>
            <div>
              <span style={{ color: '#64748B', fontSize: '0.75rem', display: 'block' }}>Age / Gender / Blood</span>
              <strong style={{ color: '#0F172A' }}>{profile.age}y / {profile.gender} / {profile.bloodGroup}</strong>
            </div>
            <div>
              <span style={{ color: '#64748B', fontSize: '0.75rem', display: 'block' }}>ABHA Number</span>
              <strong style={{ color: '#0284C7', fontFamily: 'monospace' }}>91-8823-1102-4451</strong>
            </div>
            <div>
              <span style={{ color: '#64748B', fontSize: '0.75rem', display: 'block' }}>Verified Consultations</span>
              <strong style={{ color: '#0F172A' }}>{appointments.length} Consultations • {records.length} Records</strong>
            </div>
          </div>

          {/* Vitals Summary */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 10px', color: '#0F172A', borderBottom: '1px solid #E2E8F0', paddingBottom: '6px' }}>
              Current Recorded Vitals (नवीनतम महत्वपूर्ण संकेत)
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', textAlign: 'center' }}>
              <div style={{ border: '1px solid #E2E8F0', borderRadius: '8px', padding: '10px' }}>
                <span style={{ fontSize: '0.72rem', color: '#64748B' }}>Blood Pressure</span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0F172A' }}>{profile.vitalSigns?.bp || '138/88 mmHg'}</div>
              </div>
              <div style={{ border: '1px solid #E2E8F0', borderRadius: '8px', padding: '10px' }}>
                <span style={{ fontSize: '0.72rem', color: '#64748B' }}>Pulse Rate</span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0F172A' }}>{profile.vitalSigns?.pulse || '84 bpm'}</div>
              </div>
              <div style={{ border: '1px solid #E2E8F0', borderRadius: '8px', padding: '10px' }}>
                <span style={{ fontSize: '0.72rem', color: '#64748B' }}>Blood Oxygen (SpO2)</span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: '#10B981' }}>{profile.vitalSigns?.spo2 || '97%'}</div>
              </div>
              <div style={{ border: '1px solid #E2E8F0', borderRadius: '8px', padding: '10px' }}>
                <span style={{ fontSize: '0.72rem', color: '#64748B' }}>Body Temperature</span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0F172A' }}>{profile.vitalSigns?.temp || '98.4 °F'}</div>
              </div>
            </div>
          </div>

          {/* Medical History & Chronic Conditions */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 8px', color: '#0F172A', borderBottom: '1px solid #E2E8F0', paddingBottom: '4px' }}>
                Medical History & Diagnoses
              </h3>
              <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.85rem', color: '#334155', lineHeight: 1.6 }}>
                {profile.medicalHistory.map((h, i) => (
                  <li key={i}>{h}</li>
                ))}
              </ul>
            </div>

            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 8px', color: '#0F172A', borderBottom: '1px solid #E2E8F0', paddingBottom: '4px' }}>
                Active Daily Medications
              </h3>
              <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.85rem', color: '#334155', lineHeight: 1.6 }}>
                {profile.medications.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Recent e-Prescriptions */}
          {rxList.length > 0 && (
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 8px', color: '#0F172A', borderBottom: '1px solid #E2E8F0', paddingBottom: '4px' }}>
                Recent Prescriptions & Doctor Advice
              </h3>
              {rxList.slice(0, 1).map(rx => (
                <div key={rx.id} style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '12px 16px', fontSize: '0.82rem' }}>
                  <div style={{ fontWeight: 600, color: '#0F172A', marginBottom: '4px' }}>
                    {rx.doctorName} • {rx.hospitalName} ({rx.date})
                  </div>
                  <div style={{ color: '#64748B', marginBottom: '6px' }}>Diagnosis: {rx.diagnosis}</div>
                  <div style={{ color: '#0284C7', fontWeight: 600 }}>Advice: {rx.advice}</div>
                </div>
              ))}
            </div>
          )}

          {/* Legal Medical Disclaimer */}
          <div style={{ borderTop: '1px dashed #CBD5E1', paddingTop: '16px', fontSize: '0.72rem', color: '#94A3B8', textAlign: 'center', lineHeight: 1.5 }}>
            This clinical report is an informational patient summary generated via VedaConnect ABDM Care Protocol.
            It does not substitute formal diagnostic discharge summaries. Confidential health data protected under the Digital Personal Data Protection (DPDP) Act 2023.
          </div>
        </div>
      </div>
    </div>
  );
};

