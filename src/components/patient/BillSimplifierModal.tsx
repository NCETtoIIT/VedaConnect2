import React, { useState } from 'react';
import { FileSearch, X, Sparkles } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

interface BillItem {
  id: string;
  category: string;
  item: string;
  billed: number;
  benchmarkRate: number;
  status: 'FAIR' | 'HIGH' | 'CRITICAL_MARKUP';
  note: string;
}

export const BillSimplifierModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [billText, setBillText] = useState(`ICU Bed Charges (Per Day): ₹12,500
Nursing & RMO Monitoring: ₹3,200
Consumables & PPE Kit (3 units): ₹4,800
Coronary Angiography Procedure: ₹18,000
Drug: Tab Ticagrelor 90mg (Strip): ₹1,450
Biochemistry & Cardiac Enzymes: ₹4,200
Administrative & Sanitization Fee: ₹2,500`);

  const [analyzedItems, setAnalyzedItems] = useState<BillItem[] | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  if (!isOpen) return null;

  const handleAnalyze = () => {
    setIsAnalyzing(true);
    setTimeout(() => {
      setAnalyzedItems([
        {
          id: '1',
          category: 'Room / Bed',
          item: 'ICU Bed Charges (Per Day)',
          billed: 12500,
          benchmarkRate: 8500,
          status: 'HIGH',
          note: 'NABH city standard is ₹7,500–₹9,000. Ask if nursing fee is dual-billed.'
        },
        {
          id: '2',
          category: 'Nursing',
          item: 'Nursing & RMO Monitoring',
          billed: 3200,
          benchmarkRate: 2000,
          status: 'HIGH',
          note: 'Often covered within ICU bed charge per PM-JAY package guidelines.'
        },
        {
          id: '3',
          category: 'Consumables',
          item: 'Consumables & PPE Kit (3 units)',
          billed: 4800,
          benchmarkRate: 1500,
          status: 'CRITICAL_MARKUP',
          note: 'Govt cap on consumables is max 10% of procedure cost. You can challenge this.'
        },
        {
          id: '4',
          category: 'Procedure',
          item: 'Coronary Angiography Procedure',
          billed: 18000,
          benchmarkRate: 16500,
          status: 'FAIR',
          note: 'Fair market rate in line with private insurance tariff.'
        },
        {
          id: '5',
          category: 'Pharmacy',
          item: 'Tab Ticagrelor 90mg (Strip)',
          billed: 1450,
          benchmarkRate: 1380,
          status: 'FAIR',
          note: 'Standard MRP price.'
        },
        {
          id: '6',
          category: 'Investigation',
          item: 'Biochemistry & Cardiac Enzymes',
          billed: 4200,
          benchmarkRate: 3500,
          status: 'FAIR',
          note: 'Troponin-I + CK-MB emergency panel charges.'
        },
        {
          id: '7',
          category: 'Admin Overhead',
          item: 'Administrative & Sanitization Fee',
          billed: 2500,
          benchmarkRate: 0,
          status: 'CRITICAL_MARKUP',
          note: 'IRDAI prohibits standalone "Sanitization / Misc Admin" charges for insured/cashless patients.'
        }
      ]);
      setIsAnalyzing(false);
    }, 900);
  };

  const totalBilled = analyzedItems ? analyzedItems.reduce((acc, i) => acc + i.billed, 0) : 46650;
  const totalFair = analyzedItems ? analyzedItems.reduce((acc, i) => acc + (i.benchmarkRate || 0), 0) : 33380;
  const potentialSavings = totalBilled - totalFair;

  return (
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
        maxWidth: '780px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        padding: '28px',
        boxShadow: 'var(--shadow-xl)',
        animation: 'fadeIn 0.2s ease-out'
      }}>
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(2, 132, 199, 0.12)',
              color: 'var(--primary-teal)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <FileSearch size={22} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-heading)' }}>
                AI Hospital Bill Simplifier & Audit (बिल पारदर्शी विश्लेषण)
              </h3>
              <p style={{ margin: '2px 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Paste or type bill line items to check overcharging against PM-JAY & CGHS benchmark tariffs.
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
            <X size={20} />
          </button>
        </div>

        {/* Input Textarea */}
        {!analyzedItems && (
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-heading)', marginBottom: '8px' }}>
              Hospital Bill Items (Enter line items from receipt):
            </label>
            <textarea
              rows={8}
              value={billText}
              onChange={e => setBillText(e.target.value)}
              className="form-input"
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '12px',
                background: 'var(--bg-main)',
                border: '1px solid var(--border-light)',
                fontFamily: 'monospace',
                fontSize: '0.88rem',
                lineHeight: 1.6,
                marginBottom: '16px'
              }}
            />
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="btn btn-primary"
              style={{ width: '100%', padding: '12px', fontSize: '0.95rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
            >
              <Sparkles size={18} /> {isAnalyzing ? 'Auditing Billed Items...' : 'Analyze & Audit Bill Now'}
            </button>
          </div>
        )}

        {/* Audit Results View */}
        {analyzedItems && (
          <div>
            {/* Savings Callout */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(245, 158, 11, 0.08) 100%)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: '14px',
              padding: '18px 22px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '14px'
            }}>
              <div>
                <span className="badge badge-danger" style={{ marginBottom: '6px' }}>
                  OVERCHARGE AUDIT RESULT
                </span>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-heading)' }}>
                  Total Billed: ₹{totalBilled.toLocaleString('en-IN')}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Fair Market Benchmark: ₹{totalFair.toLocaleString('en-IN')}
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--danger-red)', fontWeight: 600 }}>POTENTIAL EXCESS CHARGES</span>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--danger-red)' }}>
                  ₹{potentialSavings.toLocaleString('en-IN')}
                </div>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>(~28% disputed markup)</span>
              </div>
            </div>

            {/* Line Item Table */}
            <div style={{ border: '1px solid var(--border-light)', borderRadius: '12px', overflow: 'hidden', marginBottom: '20px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-main)', borderBottom: '1px solid var(--border-light)', textAlign: 'left' }}>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Item Description</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Billed</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Benchmark</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Audit Finding</th>
                  </tr>
                </thead>
                <tbody>
                  {analyzedItems.map(item => (
                    <tr key={item.id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{item.item}</div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '2px' }}>{item.note}</div>
                      </td>
                      <td style={{ padding: '12px 14px', fontWeight: 700 }}>₹{item.billed.toLocaleString('en-IN')}</td>
                      <td style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>₹{item.benchmarkRate.toLocaleString('en-IN')}</td>
                      <td style={{ padding: '12px 14px' }}>
                        <span className={`badge ${item.status === 'FAIR' ? 'badge-green' : item.status === 'HIGH' ? 'badge-yellow' : 'badge-danger'}`} style={{ fontSize: '0.72rem' }}>
                          {item.status === 'FAIR' ? 'Fair Standard' : item.status === 'HIGH' ? 'Above Average' : 'Disputable Markup'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'space-between' }}>
              <button
                onClick={() => setAnalyzedItems(null)}
                className="btn btn-secondary"
                style={{ padding: '9px 16px', fontSize: '0.85rem' }}
              >
                ← Edit Items
              </button>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => alert('Dispute letter template copied! You can submit this to the hospital billing desk or insurance TPA.')}
                  className="btn btn-primary"
                  style={{ padding: '9px 18px', fontSize: '0.85rem' }}
                >
                  Generate Billing Dispute Letter
                </button>
                <button
                  onClick={onClose}
                  className="btn btn-secondary"
                  style={{ padding: '9px 16px', fontSize: '0.85rem' }}
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

