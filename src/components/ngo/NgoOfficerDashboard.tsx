import React, { useState } from 'react';
import { db } from '../../db/database';
import type { SchemeApplication, GovernmentScheme } from '../../types';
import { HandHeart, Search, Plus, X } from 'lucide-react';

export const NgoOfficerDashboard: React.FC = () => {
  const [applications, setApplications] = useState<SchemeApplication[]>(() => db.getSchemeApplications());
  const [schemes, setSchemes] = useState<GovernmentScheme[]>(() => db.getGovernmentSchemes());
  const [activeTab, setActiveTab] = useState<'APPLICATIONS' | 'SCHEMES'>('APPLICATIONS');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedApp, setSelectedApp] = useState<SchemeApplication | null>(null);
  const [verificationNotes, setVerificationNotes] = useState('');
  const [showAddSchemeModal, setShowAddSchemeModal] = useState(false);

  // New Scheme Form
  const [newSchemeName, setNewSchemeName] = useState('');
  const [newSchemeCoverage, setNewSchemeCoverage] = useState('500000');

  const filteredApps = applications.filter(app => {
    const matchesStatus = filterStatus === 'ALL' || app.status === filterStatus;
    const matchesSearch = app.patientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          app.applicationNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          app.schemeName.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const handleUpdateStatus = (id: string, status: 'VERIFIED' | 'APPROVED' | 'REJECTED') => {
    db.updateSchemeApplicationStatus(id, status, verificationNotes, 'Smt. Anita Deshmukh (Nodal Officer)');
    setApplications(db.getSchemeApplications());
    setSelectedApp(null);
    setVerificationNotes('');
  };

  const handleCreateScheme = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSchemeName.trim()) return;

    const newScheme: GovernmentScheme = {
      id: `gov-scheme-${Date.now()}`,
      schemeCode: `SCH-${Date.now().toString().slice(-4)}`,
      schemeName: newSchemeName.trim(),
      description: 'Government backed healthcare assistance and critical surgery coverage scheme.',
      maxBenefitAmount: parseInt(newSchemeCoverage, 10) || 500000,
      eligibilityCriteria: {
        rationCardTypes: ['AAY', 'BPL'],
        maxAnnualIncome: 250000,
        coveredIllnesses: ['Cardiology', 'Oncology', 'Orthopedics', 'General Surgery']
      },
      requiredDocuments: ['Aadhaar Card', 'Ration Card', 'Income Certificate', 'Hospital Treatment Estimate'],
      contactHelpline: '14555'
    };

    db.addGovernmentScheme(newScheme);
    setSchemes(db.getGovernmentSchemes());
    setShowAddSchemeModal(false);
    setNewSchemeName('');
  };

  return (
    <div style={{ animation: 'fadeIn 0.25s ease-out' }}>
      {/* Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.09) 0%, rgba(16, 185, 129, 0.07) 100%)',
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
            <HandHeart size={24} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, margin: '0 0 4px', color: 'var(--text-heading)' }}>
              NGO & Government Scheme Nodal Desk (योजना सत्यापन एवं स्वीकृति)
            </h2>
            <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-muted)' }}>
              Nodal portal for PM-JAY, MJPJAY, Ayushman Bharat & NGO grant eligibility verification based on ration cards and income brackets.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setActiveTab('APPLICATIONS')}
            className={`btn btn-sm ${activeTab === 'APPLICATIONS' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 14px' }}
          >
            Applications Tracker ({applications.length})
          </button>
          <button
            onClick={() => setActiveTab('SCHEMES')}
            className={`btn btn-sm ${activeTab === 'SCHEMES' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 14px' }}
          >
            Schemes Directory ({schemes.length})
          </button>
        </div>
      </div>

      {/* KPI Stats Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: '14px', padding: '18px', boxShadow: 'var(--shadow-sm)' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Total Beneficiary Claims</span>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-heading)', marginTop: '4px' }}>
            ₹{(applications.reduce((acc, a) => acc + a.claimedAmount, 0) / 100000).toFixed(1)} Lakhs
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--success-green)' }}>100% Cashless Mandate</span>
        </div>

        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: '14px', padding: '18px', boxShadow: 'var(--shadow-sm)' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Pending Verification</span>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--warning-yellow)', marginTop: '4px' }}>
            {applications.filter(a => a.status === 'PENDING_VERIFICATION').length}
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Action required within 24h</span>
        </div>

        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: '14px', padding: '18px', boxShadow: 'var(--shadow-sm)' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Verified & Approved</span>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--success-green)', marginTop: '4px' }}>
            {applications.filter(a => a.status === 'VERIFIED' || a.status === 'APPROVED').length}
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--success-green)' }}>Pre-authorized for surgery</span>
        </div>

        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: '14px', padding: '18px', boxShadow: 'var(--shadow-sm)' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Empanelled Active Schemes</span>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--primary-teal)', marginTop: '4px' }}>
            {schemes.length}
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Central + State + Trust funds</span>
        </div>
      </div>

      {activeTab === 'APPLICATIONS' && (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: '16px', padding: '20px', boxShadow: 'var(--shadow-sm)' }}>
          {/* Filters & Search */}
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: '1', minWidth: '260px' }}>
              <div style={{ position: 'relative', width: '100%' }}>
                <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Search by patient name, application #, or scheme..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="form-input"
                  style={{ width: '100%', paddingLeft: '36px', paddingRight: '12px', paddingBlock: '9px', borderRadius: '10px', fontSize: '0.85rem', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              {(['ALL', 'PENDING_VERIFICATION', 'VERIFIED', 'APPROVED'] as const).map(st => (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  className={`btn btn-sm ${filterStatus === st ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.78rem', padding: '6px 12px' }}
                >
                  {st.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Applications Table */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ background: 'var(--bg-main)', borderBottom: '1px solid var(--border-light)', textAlign: 'left' }}>
                  <th style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>Application #</th>
                  <th style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>Beneficiary Patient</th>
                  <th style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>Ration Card & Income</th>
                  <th style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>Target Scheme</th>
                  <th style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>Claim Amount</th>
                  <th style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>Status</th>
                  <th style={{ padding: '12px 14px', textAlign: 'center', color: 'var(--text-muted)' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredApps.map(app => (
                  <tr key={app.id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <td style={{ padding: '12px 14px', fontWeight: 700, fontFamily: 'monospace', color: 'var(--primary-teal)' }}>
                      {app.applicationNumber}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{app.patientName}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Age: {app.age} yrs • {app.hospitalName}</div>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className={`badge ${app.rationCardType === 'AAY' ? 'badge-danger' : app.rationCardType === 'BPL' ? 'badge-yellow' : 'badge-teal'}`} style={{ fontSize: '0.72rem', marginRight: '6px' }}>
                        {app.rationCardType} Card
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{app.incomeCategory}</span>
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: 'var(--text-heading)' }}>
                      {app.schemeName}
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 700, color: 'var(--text-heading)' }}>
                      ₹{app.claimedAmount.toLocaleString('en-IN')}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className={`badge ${app.status === 'APPROVED' ? 'badge-green' : app.status === 'VERIFIED' ? 'badge-teal' : 'badge-yellow'}`} style={{ fontSize: '0.72rem' }}>
                        {app.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                      <button
                        onClick={() => {
                          setSelectedApp(app);
                          setVerificationNotes(app.verificationNotes || '');
                        }}
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: '0.75rem', padding: '6px 12px' }}
                      >
                        Verify
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Schemes Directory Tab */}
      {activeTab === 'SCHEMES' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
            <button
              onClick={() => setShowAddSchemeModal(true)}
              className="btn btn-primary btn-sm"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <Plus size={15} /> Add Government Scheme
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {schemes.map((sch: GovernmentScheme) => (
              <div key={sch.id} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: '16px', padding: '20px', boxShadow: 'var(--shadow-sm)' }}>
                <span className="badge badge-teal" style={{ marginBottom: '8px' }}>Active Scheme • {sch.schemeCode}</span>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: '4px 0 8px', color: 'var(--text-heading)' }}>
                  {sch.schemeName}
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '14px', lineHeight: 1.5 }}>
                  {sch.description}
                </p>

                <div style={{ padding: '10px 12px', background: 'var(--bg-main)', borderRadius: '10px', marginBottom: '14px' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Maximum Benefit Amount</span>
                  <div style={{ fontWeight: 800, color: 'var(--success-green)', fontSize: '1rem' }}>₹{sch.maxBenefitAmount.toLocaleString('en-IN')}</div>
                </div>

                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Eligible Ration Cards:</span>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '4px' }}>
                    {sch.eligibilityCriteria.rationCardTypes.map((rc, idx) => (
                      <span key={idx} className="badge badge-purple" style={{ fontSize: '0.7rem' }}>{rc}</span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verify Application Modal */}
      {selectedApp && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(15, 23, 42, 0.68)',
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
            maxWidth: '560px',
            width: '100%',
            padding: '28px',
            boxShadow: 'var(--shadow-xl)',
            animation: 'fadeIn 0.2s ease-out'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <span className="badge badge-teal" style={{ marginBottom: '4px' }}>
                  {selectedApp.applicationNumber}
                </span>
                <h3 style={{ margin: '4px 0 0', fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-heading)' }}>
                  Verify Scheme Eligibility
                </h3>
              </div>
              <button onClick={() => setSelectedApp(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ background: 'var(--bg-main)', border: '1px solid var(--border-light)', borderRadius: '12px', padding: '16px', marginBottom: '18px', fontSize: '0.85rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '8px' }}>
                <div>Patient: <strong>{selectedApp.patientName}</strong></div>
                <div>Age: <strong>{selectedApp.age} yrs</strong></div>
                <div>Ration Card: <strong>{selectedApp.rationCardType}</strong></div>
                <div>Income: <strong>{selectedApp.incomeCategory}</strong></div>
              </div>
              <div>Hospital: <strong>{selectedApp.hospitalName}</strong></div>
              <div style={{ marginTop: '8px', color: 'var(--primary-teal)', fontWeight: 700 }}>
                Claimed Coverage: ₹{selectedApp.claimedAmount.toLocaleString('en-IN')}
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                Nodal Verification Notes & Approval Remarks:
              </label>
              <textarea
                rows={3}
                placeholder="e.g. Ration card biometrics verified via Food & Civil Supplies portal. Approved for 100% cashless treatment."
                value={verificationNotes}
                onChange={e => setVerificationNotes(e.target.value)}
                className="form-input"
                style={{ width: '100%', padding: '10px 12px', borderRadius: '10px', fontSize: '0.85rem', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => handleUpdateStatus(selectedApp.id, 'REJECTED')}
                className="btn btn-secondary"
                style={{ color: 'var(--danger-red)', padding: '9px 16px', fontSize: '0.85rem' }}
              >
                Reject Claim
              </button>
              <button
                onClick={() => handleUpdateStatus(selectedApp.id, 'VERIFIED')}
                className="btn btn-secondary"
                style={{ color: 'var(--primary-teal)', padding: '9px 16px', fontSize: '0.85rem' }}
              >
                Mark Verified
              </button>
              <button
                onClick={() => handleUpdateStatus(selectedApp.id, 'APPROVED')}
                className="btn btn-primary"
                style={{ padding: '9px 20px', fontSize: '0.85rem' }}
              >
                Approve & Pre-Authorize
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Scheme Modal */}
      {showAddSchemeModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(15, 23, 42, 0.68)',
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
            maxWidth: '500px',
            width: '100%',
            padding: '28px',
            boxShadow: 'var(--shadow-xl)',
            animation: 'fadeIn 0.2s ease-out'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-heading)' }}>
                Add New Scheme / NGO Fund
              </h3>
              <button onClick={() => setShowAddSchemeModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateScheme}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Scheme / Trust Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Chief Minister Relief Fund"
                  value={newSchemeName}
                  onChange={e => setNewSchemeName(e.target.value)}
                  className="form-input"
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                />
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Coverage Amount
                </label>
                <input
                  type="text"
                  placeholder="e.g. Up to ₹2,50,000 per surgery"
                  value={newSchemeCoverage}
                  onChange={e => setNewSchemeCoverage(e.target.value)}
                  className="form-input"
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-light)' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '20px' }}>
                <button
                  type="button"
                  onClick={() => setShowAddSchemeModal(false)}
                  className="btn btn-secondary"
                  style={{ padding: '9px 16px' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ padding: '9px 20px' }}
                >
                  Save Scheme
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

