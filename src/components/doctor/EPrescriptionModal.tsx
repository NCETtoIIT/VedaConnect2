import React, { useState } from 'react';
import { db } from '../../db/database';
import type { EPrescription } from '../../types';
import { Stethoscope, Plus, Trash2, Send, Printer, CheckCircle, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  patientName?: string;
}

export const EPrescriptionModal: React.FC<Props> = ({ isOpen, onClose, patientName = 'Ramesh Sharma' }) => {
  if (!isOpen) return null;

  const [diagnosis, setDiagnosis] = useState('Coronary Artery Disease suspect / Angina pectoris evaluation');
  const [advice, setAdvice] = useState('Low sodium diet (<4g salt), 20 min morning walk, avoid physical exertion, repeat ECG if chest pain persists.');
  const [nextFollowUp, setNextFollowUp] = useState('2026-03-30');
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [meds, setMeds] = useState([
    { name: 'Tab Ecosprin 75mg', dosage: '75 mg', frequency: 'Once daily after lunch', duration: '30 Days', instructions: 'Take with full glass of water' },
    { name: 'Tab Metoprolol Succinate 25mg', dosage: '25 mg', frequency: 'Once daily morning', duration: '30 Days', instructions: 'Monitor morning pulse' },
    { name: 'Tab Sorbitrate 5mg', dosage: '5 mg', frequency: 'SOS (Sublingually)', duration: '15 Days', instructions: 'Place under tongue if chest tightness occurs' }
  ]);

  const [newMedName, setNewMedName] = useState('');
  const [newMedDosage, setNewMedDosage] = useState('');
  const [newMedFreq, setNewMedFreq] = useState('Once daily');
  const [newMedDuration, setNewMedDuration] = useState('15 Days');

  const handleAddMed = () => {
    if (!newMedName.trim()) return;
    setMeds([
      ...meds,
      {
        name: newMedName.trim(),
        dosage: newMedDosage.trim() || '1 Tab',
        frequency: newMedFreq,
        duration: newMedDuration,
        instructions: 'As directed by physician'
      }
    ]);
    setNewMedName('');
    setNewMedDosage('');
  };

  const handleRemoveMed = (index: number) => {
    setMeds(meds.filter((_, idx) => idx !== index));
  };

  const handleSaveAndSend = () => {
    const rxNumber = `RX-PUN-2026-${Math.floor(1000 + Math.random() * 9000)}`;
    const newRx: EPrescription = {
      id: `rx-${Date.now()}`,
      prescriptionNumber: rxNumber,
      doctorId: 'usr-doctor-1',
      doctorName: 'Dr. Rajesh Kulkarni (MD, DM Cardiology)',
      hospitalName: 'CarePlus Multi-Specialty Hospital',
      patientId: 'usr-patient-1',
      patientName,
      age: 48,
      gender: 'Male',
      date: new Date().toISOString().split('T')[0],
      symptoms: ['Chest tightness', 'Mild breathlessness'],
      diagnosis,
      medications: meds,
      advice,
      nextFollowUpDate: nextFollowUp
    };

    db.saveEPrescription(newRx);
    setSuccessMessage(`✅ Digital e-Prescription ${rxNumber} generated and sent via WhatsApp to ${patientName} (+91 98765 43210)!`);
    setTimeout(() => {
      setSuccessMessage(null);
      onClose();
    }, 2800);
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
        background: 'var(--bg-card)',
        border: '1px solid var(--border-light)',
        borderRadius: '20px',
        maxWidth: '740px',
        width: '100%',
        maxHeight: '92vh',
        overflowY: 'auto',
        padding: '28px',
        boxShadow: 'var(--shadow-xl)',
        animation: 'fadeIn 0.2s ease-out'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'rgba(99, 102, 241, 0.12)',
              color: 'var(--primary-purple)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Stethoscope size={20} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-heading)' }}>
                Digital e-Prescription Generator (डिजिटल नुस्खा)
              </h3>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Patient: <strong style={{ color: 'var(--text-heading)' }}>{patientName}</strong> (OPD Consultation #VC-2026-A3F8B)
              </span>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
            <X size={20} />
          </button>
        </div>

        {successMessage && (
          <div style={{
            background: 'linear-gradient(135deg, #065F46 0%, #047857 100%)',
            color: '#FFF',
            padding: '14px 18px',
            borderRadius: '12px',
            marginBottom: '18px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '0.88rem'
          }}>
            <CheckCircle size={18} />
            {successMessage}
          </div>
        )}

        {/* Clinical Diagnosis Input */}
        <div style={{ marginBottom: '18px' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
            Clinical Diagnosis / Findings *
          </label>
          <input
            type="text"
            value={diagnosis}
            onChange={e => setDiagnosis(e.target.value)}
            className="form-input"
            style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
          />
        </div>

        {/* Prescribed Medications Table */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
            Rx Medications & Regimen ({meds.length} Drugs Prescribed)
          </label>
          <div style={{ border: '1px solid var(--border-light)', borderRadius: '12px', overflow: 'hidden', marginBottom: '12px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ background: 'var(--bg-main)', borderBottom: '1px solid var(--border-light)', textAlign: 'left' }}>
                  <th style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>Drug Name</th>
                  <th style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>Dosage</th>
                  <th style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>Frequency</th>
                  <th style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>Duration</th>
                  <th style={{ padding: '8px 12px', textAlign: 'center' }}></th>
                </tr>
              </thead>
              <tbody>
                {meds.map((m, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: 'var(--text-heading)' }}>{m.name}</td>
                    <td style={{ padding: '10px 12px' }}>{m.dosage}</td>
                    <td style={{ padding: '10px 12px' }}>{m.frequency}</td>
                    <td style={{ padding: '10px 12px' }}>{m.duration}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                      <button onClick={() => handleRemoveMed(idx)} style={{ background: 'none', border: 'none', color: 'var(--danger-red)', cursor: 'pointer' }}>
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Quick Add Medicine Row */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr auto', gap: '8px', alignItems: 'center' }}>
            <input
              type="text"
              placeholder="Drug name (e.g. Tab Pantop 40)"
              value={newMedName}
              onChange={e => setNewMedName(e.target.value)}
              className="form-input"
              style={{ padding: '8px 10px', fontSize: '0.8rem', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
            />
            <input
              type="text"
              placeholder="Dose (40mg)"
              value={newMedDosage}
              onChange={e => setNewMedDosage(e.target.value)}
              className="form-input"
              style={{ padding: '8px 10px', fontSize: '0.8rem', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
            />
            <select
              value={newMedFreq}
              onChange={e => setNewMedFreq(e.target.value)}
              className="form-input"
              style={{ padding: '8px', fontSize: '0.8rem', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
            >
              <option value="Once daily">Once daily</option>
              <option value="Twice daily">Twice daily</option>
              <option value="Thrice daily">Thrice daily</option>
              <option value="SOS">SOS</option>
            </select>
            <input
              type="text"
              placeholder="15 Days"
              value={newMedDuration}
              onChange={e => setNewMedDuration(e.target.value)}
              className="form-input"
              style={{ padding: '8px 10px', fontSize: '0.8rem', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
            />
            <button
              onClick={handleAddMed}
              className="btn btn-secondary btn-sm"
              style={{ padding: '8px 12px' }}
              title="Add drug"
            >
              <Plus size={15} /> Add
            </button>
          </div>
        </div>

        {/* Doctor Advice & Follow-up */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '14px', marginBottom: '20px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
              Lifestyle Advice / Precaution Instructions
            </label>
            <textarea
              rows={2}
              value={advice}
              onChange={e => setAdvice(e.target.value)}
              className="form-input"
              style={{ width: '100%', padding: '8px 12px', fontSize: '0.82rem', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
              Next Follow-up Date
            </label>
            <input
              type="date"
              value={nextFollowUp}
              onChange={e => setNextFollowUp(e.target.value)}
              className="form-input"
              style={{ width: '100%', padding: '8px 12px', fontSize: '0.82rem', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
            />
          </div>
        </div>

        {/* Modal Actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            onClick={() => window.print()}
            className="btn btn-secondary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '9px 16px', fontSize: '0.85rem' }}
          >
            <Printer size={15} /> Print Rx
          </button>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={onClose}
              className="btn btn-secondary"
              style={{ padding: '9px 16px', fontSize: '0.85rem' }}
            >
              Cancel
            </button>
            <button
              onClick={handleSaveAndSend}
              className="btn btn-primary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '9px 20px', fontSize: '0.85rem' }}
            >
              <Send size={15} /> Save & Send via WhatsApp
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

