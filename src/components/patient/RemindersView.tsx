import React, { useState } from 'react';
import { db } from '../../db/database';
import type { ReminderItem } from '../../types';
import { Bell, Clock, Plus, MessageSquare, X } from 'lucide-react';

export const RemindersView: React.FC = () => {
  const [reminders, setReminders] = useState<ReminderItem[]>(() => db.getReminders());
  const [showAddModal, setShowAddModal] = useState(false);
  const [alertSimulation, setAlertSimulation] = useState<string | null>(null);

  // Form State
  const [title, setTitle] = useState('');
  const [memberName, setMemberName] = useState('Ramesh Sharma (Self)');
  const [dosage, setDosage] = useState('');
  const [time, setTime] = useState('09:00');
  const [frequency, setFrequency] = useState<ReminderItem['frequency']>('Once Daily');
  const [type, setType] = useState<ReminderItem['type']>('MEDICINE');

  const familyMembers = db.getFamilyMembers();

  const handleToggle = (id: string) => {
    db.toggleReminder(id);
    setReminders(db.getReminders());
  };

  const handleTriggerTestAlert = (reminder: ReminderItem) => {
    setAlertSimulation(`📲 WhatsApp & SMS Alert Sent to Registered Phone (+91 98765 43210):\n"नमस्ते! ${reminder.memberName} के लिए समय हो गया है: ${reminder.title} (${reminder.dosage}) at ${reminder.time}."`);
    setTimeout(() => {
      setAlertSimulation(null);
    }, 6000);
  };

  const handleAddReminder = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const newRem: ReminderItem = {
      id: `rem-${Date.now()}`,
      patientId: 'usr-patient-1',
      memberName,
      title: title.trim(),
      dosage: dosage.trim() || '1 Dose',
      time,
      frequency,
      type,
      isActive: true
    };

    db.addReminder(newRem);
    setReminders(db.getReminders());
    setTitle('');
    setDosage('');
    setShowAddModal(false);
  };

  return (
    <div style={{ animation: 'fadeIn 0.25s ease-out' }}>
      {/* Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(2, 132, 199, 0.06) 100%)',
        border: '1px solid var(--border-light)',
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'var(--success-green)',
            color: '#FFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.25)'
          }}>
            <Bell size={24} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, margin: '0 0 4px', color: 'var(--text-heading)' }}>
              Smart Care & Medicine Reminders (दवा और जांच रिमाइंडर)
            </h2>
            <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-muted)' }}>
              SMS & WhatsApp alerts for daily medicines, OPD follow-ups and blood tests so no family member misses a dose.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="btn btn-primary"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '10px 18px', borderRadius: '10px' }}
        >
          <Plus size={16} /> New Reminder
        </button>
      </div>

      {/* Alert Simulation Toast */}
      {alertSimulation && (
        <div style={{
          background: 'linear-gradient(135deg, #065F46 0%, #047857 100%)',
          color: '#FFF',
          padding: '16px 20px',
          borderRadius: '14px',
          marginBottom: '20px',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          animation: 'slideDown 0.3s ease-out',
          whiteSpace: 'pre-line',
          fontSize: '0.9rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <MessageSquare size={20} />
            <span>{alertSimulation}</span>
          </div>
          <button onClick={() => setAlertSimulation(null)} style={{ background: 'none', border: 'none', color: '#FFF', cursor: 'pointer', opacity: 0.8 }}>
            <X size={18} />
          </button>
        </div>
      )}

      {/* Reminders List */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
        {reminders.map(rem => (
          <div
            key={rem.id}
            style={{
              background: 'var(--bg-card)',
              border: rem.isActive ? '1px solid var(--border-light)' : '1px dashed var(--border-light)',
              borderRadius: '16px',
              padding: '20px',
              boxShadow: rem.isActive ? 'var(--shadow-sm)' : 'none',
              opacity: rem.isActive ? 1 : 0.65,
              transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className={`badge ${rem.type === 'MEDICINE' ? 'badge-teal' : rem.type === 'FOLLOWUP' ? 'badge-purple' : 'badge-green'}`} style={{ fontSize: '0.72rem' }}>
                  {rem.type}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {rem.memberName}
                </span>
              </div>

              <button
                onClick={() => handleToggle(rem.id)}
                style={{
                  background: rem.isActive ? 'rgba(16, 185, 129, 0.12)' : 'var(--bg-main)',
                  color: rem.isActive ? 'var(--success-green)' : 'var(--text-muted)',
                  border: 'none',
                  borderRadius: '20px',
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {rem.isActive ? 'Active' : 'Paused'}
              </button>
            </div>

            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: '0 0 6px', color: 'var(--text-heading)' }}>
              {rem.title}
            </h3>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '0 0 16px' }}>
              {rem.dosage} • {rem.frequency}
            </p>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingTop: '12px',
              borderTop: '1px solid var(--border-light)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-heading)', fontWeight: 700, fontSize: '0.95rem' }}>
                <Clock size={16} color="var(--primary-teal)" />
                {rem.time}
              </div>

              <button
                onClick={() => handleTriggerTestAlert(rem)}
                className="btn btn-secondary btn-sm"
                style={{ fontSize: '0.75rem', padding: '6px 10px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                title="Send test WhatsApp alert"
              >
                <MessageSquare size={13} /> Test Alert
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add Reminder Modal */}
      {showAddModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(15, 23, 42, 0.65)',
          backdropFilter: 'blur(4px)',
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
            maxWidth: '480px',
            width: '100%',
            padding: '28px',
            boxShadow: 'var(--shadow-xl)',
            animation: 'fadeIn 0.2s ease-out'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Bell size={20} color="var(--success-green)" />
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-heading)' }}>
                  Set New Health Reminder
                </h3>
              </div>
              <button onClick={() => setShowAddModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAddReminder}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Reminder Type *
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                  {(['MEDICINE', 'FOLLOWUP', 'LAB_TEST'] as const).map(t => (
                    <button
                      type="button"
                      key={t}
                      onClick={() => setType(t)}
                      style={{
                        padding: '8px',
                        borderRadius: '8px',
                        border: type === t ? '1px solid var(--primary-teal)' : '1px solid var(--border-light)',
                        background: type === t ? 'rgba(2, 132, 199, 0.12)' : 'var(--bg-main)',
                        color: type === t ? 'var(--primary-teal)' : 'var(--text-main)',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      {t === 'MEDICINE' ? '💊 Medicine' : t === 'FOLLOWUP' ? '👨‍⚕️ OPD Visit' : '🧪 Lab Test'}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Family Member *
                </label>
                <select
                  value={memberName}
                  onChange={e => setMemberName(e.target.value)}
                  className="form-input"
                  style={{ width: '100%', padding: '10px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                >
                  {familyMembers.map(m => (
                    <option key={m.id} value={m.name}>{m.name} ({m.relationship})</option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Title / Medicine Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Tab Telmisartan 40mg"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  className="form-input"
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Dosage / Instructions
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 1 Tab after breakfast"
                    value={dosage}
                    onChange={e => setDosage(e.target.value)}
                    className="form-input"
                    style={{ width: '100%', padding: '10px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Time (समय) *
                  </label>
                  <input
                    type="time"
                    required
                    value={time}
                    onChange={e => setTime(e.target.value)}
                    className="form-input"
                    style={{ width: '100%', padding: '10px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Frequency (आवृत्ति)
                </label>
                <select
                  value={frequency}
                  onChange={e => setFrequency(e.target.value as any)}
                  className="form-input"
                  style={{ width: '100%', padding: '10px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                >
                  <option value="Once Daily">Once Daily (दिन में एक बार)</option>
                  <option value="Twice Daily">Twice Daily (सुबह - शाम)</option>
                  <option value="Thrice Daily">Thrice Daily (सुबह - दोपहर - रात)</option>
                  <option value="As Needed">As Needed (जरूरत पड़ने पर)</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn btn-secondary"
                  style={{ padding: '10px 18px', borderRadius: '10px' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ padding: '10px 20px', borderRadius: '10px' }}
                >
                  Schedule Reminder
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

