import React, { useState } from 'react';
import { db } from '../../db/database';
import type { FamilyMember } from '../../types';
import { Users, UserPlus, Shield, Activity, Calendar, Pill, X } from 'lucide-react';

interface Props {
  onSelectMember?: (member: FamilyMember) => void;
  onBookForMember?: (member: FamilyMember) => void;
}

export const FamilyHubView: React.FC<Props> = ({ onSelectMember, onBookForMember }) => {
  const [members, setMembers] = useState<FamilyMember[]>(() => db.getFamilyMembers());
  const [showAddModal, setShowAddModal] = useState(false);
  const [activeMemberId, setActiveMemberId] = useState<string>(members[0]?.id || 'fam-1');

  // Form State
  const [name, setName] = useState('');
  const [relationship, setRelationship] = useState<FamilyMember['relationship']>('Father');
  const [age, setAge] = useState<number>(65);
  const [gender, setGender] = useState('Male');
  const [bloodGroup, setBloodGroup] = useState('B+');
  const [abhaId, setAbhaId] = useState('');
  const [conditions, setConditions] = useState('');

  const activeMember = members.find(m => m.id === activeMemberId) || members[0];
  const allReminders = db.getReminders();
  const memberReminders = allReminders.filter(r => r.memberName?.includes(activeMember?.name?.split(' ')[0] || ''));

  const handleAddMember = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const newMember: FamilyMember = {
      id: `fam-${Date.now()}`,
      patientId: 'usr-patient-1',
      name: name.trim(),
      relationship,
      age: Number(age),
      gender,
      bloodGroup,
      abhaId: abhaId.trim() || `91-${Math.floor(1000 + Math.random() * 9000)}-${Math.floor(1000 + Math.random() * 9000)}-${Math.floor(1000 + Math.random() * 9000)}`,
      activeConditions: conditions.split(',').map(c => c.trim()).filter(Boolean)
    };

    db.addFamilyMember(newMember);
    setMembers(db.getFamilyMembers());
    setName('');
    setConditions('');
    setAbhaId('');
    setShowAddModal(false);
    setActiveMemberId(newMember.id);
  };

  return (
    <div style={{ animation: 'fadeIn 0.25s ease-out' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.08) 0%, rgba(99, 102, 241, 0.05) 100%)',
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
            background: 'var(--primary-teal)',
            color: '#FFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(2, 132, 199, 0.25)'
          }}>
            <Users size={24} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, margin: '0 0 4px', color: 'var(--text-heading)' }}>
              Family Health Hub (परिवार स्वास्थ्य केंद्र)
            </h2>
            <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-muted)' }}>
              Manage appointments, prescriptions & medication reminders for parents, spouse, and children from a single window.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="btn btn-primary"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '10px 18px', borderRadius: '10px' }}
        >
          <UserPlus size={16} /> Add Family Member
        </button>
      </div>

      {/* Member Selection Pills */}
      <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '12px', marginBottom: '20px' }}>
        {members.map(m => {
          const isSelected = m.id === activeMemberId;
          return (
            <button
              key={m.id}
              onClick={() => {
                setActiveMemberId(m.id);
                if (onSelectMember) onSelectMember(m);
              }}
              style={{
                background: isSelected ? 'var(--primary-teal)' : 'var(--bg-card)',
                color: isSelected ? '#FFF' : 'var(--text-main)',
                border: isSelected ? '1px solid var(--primary-teal)' : '1px solid var(--border-light)',
                borderRadius: '12px',
                padding: '10px 18px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                cursor: 'pointer',
                transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
                boxShadow: isSelected ? '0 4px 14px rgba(2, 132, 199, 0.28)' : 'var(--shadow-sm)',
                whiteSpace: 'nowrap'
              }}
            >
              <div style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                background: isSelected ? 'rgba(255,255,255,0.2)' : 'var(--bg-main)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.8rem',
                fontWeight: 700
              }}>
                {m.relationship[0]}
              </div>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{m.name}</div>
                <div style={{ fontSize: '0.72rem', opacity: isSelected ? 0.9 : 0.65 }}>
                  {m.relationship} • {m.age}y • {m.bloodGroup}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Member Details Card */}
      {activeMember && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '20px',
          marginBottom: '28px'
        }}>
          {/* Profile Overview */}
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-light)',
            borderRadius: '16px',
            padding: '24px',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <span className="badge badge-teal" style={{ marginBottom: '8px' }}>
                  {activeMember.relationship.toUpperCase()}
                </span>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '4px 0', color: 'var(--text-heading)' }}>
                  {activeMember.name}
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>
                  ABHA ID: <strong style={{ color: 'var(--text-main)', fontFamily: 'monospace' }}>{activeMember.abhaId || '91-8823-1102-4451'}</strong>
                </p>
              </div>

              <div style={{
                background: 'rgba(2, 132, 199, 0.1)',
                color: 'var(--primary-teal)',
                padding: '8px 12px',
                borderRadius: '10px',
                fontWeight: 700,
                fontSize: '0.95rem'
              }}>
                {activeMember.bloodGroup}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', margin: '20px 0', textAlign: 'center' }}>
              <div style={{ padding: '12px', background: 'var(--bg-main)', borderRadius: '10px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Age</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-heading)' }}>{activeMember.age} yrs</div>
              </div>
              <div style={{ padding: '12px', background: 'var(--bg-main)', borderRadius: '10px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Gender</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-heading)' }}>{activeMember.gender}</div>
              </div>
              <div style={{ padding: '12px', background: 'var(--bg-main)', borderRadius: '10px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ABHA Status</span>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--success-green)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                  <Shield size={14} /> Linked
                </div>
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>
                Active Chronic Conditions / Health Notes:
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {activeMember.activeConditions?.length > 0 ? (
                  activeMember.activeConditions.map((cond, i) => (
                    <span key={i} className="badge badge-purple" style={{ fontSize: '0.78rem', padding: '4px 10px' }}>
                      {cond}
                    </span>
                  ))
                ) : (
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No chronic conditions recorded</span>
                )}
              </div>
            </div>

            <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-light)', display: 'flex', gap: '10px' }}>
              <button
                onClick={() => onBookForMember && onBookForMember(activeMember)}
                className="btn btn-primary"
                style={{ flex: 1, padding: '9px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
              >
                <Calendar size={14} /> Book OPD Visit
              </button>
            </div>
          </div>

          {/* Active Member Reminders & Care Schedule */}
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-light)',
            borderRadius: '16px',
            padding: '24px',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Pill size={18} color="var(--primary-teal)" />
                <h4 style={{ margin: 0, fontWeight: 700, color: 'var(--text-heading)' }}>
                  Active Care & Dose Schedule
                </h4>
              </div>
              <span className="badge badge-teal" style={{ fontSize: '0.72rem' }}>
                {memberReminders.length} Active Alerts
              </span>
            </div>

            {memberReminders.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {memberReminders.map(rem => (
                  <div key={rem.id} style={{
                    padding: '12px 14px',
                    borderRadius: '12px',
                    background: 'var(--bg-main)',
                    border: '1px solid var(--border-light)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-heading)' }}>
                        {rem.title}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        {rem.dosage} • {rem.frequency}
                      </div>
                    </div>
                    <div style={{
                      background: 'rgba(2, 132, 199, 0.1)',
                      color: 'var(--primary-teal)',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: 700
                    }}>
                      {rem.time}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '30px 20px', color: 'var(--text-muted)' }}>
                <Activity size={32} style={{ opacity: 0.4, margin: '0 auto 8px' }} />
                <p style={{ margin: 0, fontSize: '0.88rem' }}>No pending medication alerts for {activeMember.name}.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Add Family Member Modal */}
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
            maxWidth: '520px',
            width: '100%',
            padding: '28px',
            boxShadow: 'var(--shadow-xl)',
            animation: 'fadeIn 0.2s ease-out'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <UserPlus size={20} color="var(--primary-teal)" />
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-heading)' }}>
                  Add Family Member
                </h3>
              </div>
              <button onClick={() => setShowAddModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAddMember}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Full Name (पूरा नाम) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Sharma"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="form-input"
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Relationship (रिश्ता) *
                  </label>
                  <select
                    value={relationship}
                    onChange={e => setRelationship(e.target.value as any)}
                    className="form-input"
                    style={{ width: '100%', padding: '10px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                  >
                    <option value="Father">Father (पिताजी)</option>
                    <option value="Mother">Mother (माताजी)</option>
                    <option value="Spouse">Spouse (पति/पत्नी)</option>
                    <option value="Child">Child (बच्चा)</option>
                    <option value="Grandparent">Grandparent (दादा/दादी)</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Age (उम्र) *
                  </label>
                  <input
                    type="number"
                    required
                    min={1}
                    max={120}
                    value={age}
                    onChange={e => setAge(Number(e.target.value))}
                    className="form-input"
                    style={{ width: '100%', padding: '10px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Gender (लिंग)
                  </label>
                  <select
                    value={gender}
                    onChange={e => setGender(e.target.value)}
                    className="form-input"
                    style={{ width: '100%', padding: '10px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Blood Group (रक्त समूह)
                  </label>
                  <select
                    value={bloodGroup}
                    onChange={e => setBloodGroup(e.target.value)}
                    className="form-input"
                    style={{ width: '100%', padding: '10px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                  >
                    {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(bg => (
                      <option key={bg} value={bg}>{bg}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  ABHA ID (आभा कार्ड नंबर - optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 91-8823-1102-4451"
                  value={abhaId}
                  onChange={e => setAbhaId(e.target.value)}
                  className="form-input"
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Known Health Conditions (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Hypertension, Joint Pain, Diabetes"
                  value={conditions}
                  onChange={e => setConditions(e.target.value)}
                  className="form-input"
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                />
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
                  Save Member Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

