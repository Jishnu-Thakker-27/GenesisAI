import React, { useState, useEffect } from 'react';
import { getVersions } from '../../frontend_api_client';
import { VersionHistoryEvolutionScreen } from '../../frontend_models';
import { History, RotateCw, GitCommit, CheckCircle2, AlertCircle, ArrowRight } from 'lucide-react';

interface VersionHistoryProps {
  projectId: string;
}

export const VersionHistory: React.FC<VersionHistoryProps> = ({ projectId }) => {
  const [data, setData] = useState<VersionHistoryEvolutionScreen | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<string>('v1.2.8');

  useEffect(() => {
    loadVersions();
  }, [projectId]);

  const loadVersions = async () => {
    setLoading(true);
    const res = await getVersions(projectId);
    if (res.success && res.data) {
      setData(res.data);
      setError(null);
    } else {
      setError(res.error || 'Failed to fetch version history.');
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px', flexDirection: 'column', gap: '16px' }}>
        <RotateCw className="pulse" size={48} style={{ color: '#0070F3' }} />
        <p style={{ color: '#666666', fontSize: '14px' }}>Loading evolution history graphs...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '24px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)', borderRadius: '12px' }}>
        <h3 style={{ color: '#EF4444' }}>Version Control Error</h3>
        <p style={{ color: '#888888', marginTop: '8px' }}>{error || 'Evolution history unavailable.'}</p>
        <button onClick={loadVersions} style={{ marginTop: '16px', padding: '8px 16px', backgroundColor: '#EF4444', border: 'none', color: '#FFF', borderRadius: '4px', cursor: 'pointer' }}>Retry</button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Evolution Process Workflow Timeline (Top Banner) */}
      <div style={{
        backgroundColor: '#121212',
        border: '1px solid #1E1E1E',
        borderRadius: '16px',
        padding: '20px 24px'
      }}>
        <p style={{ fontSize: '12px', color: '#888888', letterSpacing: '0.5px', textTransform: 'uppercase', marginBottom: '16px' }}>Evolution Process Workflow</p>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          {[
            { label: 'Requirement Change', status: 'done' },
            { label: 'Impact Analysis', status: 'done' },
            { label: 'Targeted Update', status: 'done' },
            { label: 'Validation', status: 'done' },
            { label: 'Autonomous Repair', status: 'active' }
          ].map((step, idx) => (
            <React.Fragment key={step.label}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                color: step.status === 'active' ? '#10B981' : '#FFFFFF',
                fontWeight: step.status === 'active' ? 'bold' : 'normal',
                fontSize: '13px'
              }}>
                <span style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: step.status === 'active' ? '#10B981' : '#0070F3'
                }}></span>
                <span>{step.label}</span>
              </div>
              {idx < 4 && <ArrowRight size={14} style={{ color: '#333333' }} />}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Revision Summary Metrics row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '24px'
      }}>
        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '20px' }}>
          <p style={{ fontSize: '12px', color: '#666666' }}>Current Version</p>
          <h4 style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>v1.2.8</span>
            <span style={{ fontSize: '10px', color: '#10B981', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>PRODUCTION</span>
          </h4>
        </div>

        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <p style={{ fontSize: '12px', color: '#666666' }}>Blueprint Stability</p>
            <h4 style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '8px' }}>98%</h4>
          </div>
          <div style={{ height: '4px', backgroundColor: '#1E1E1E', borderRadius: '2px', overflow: 'hidden', marginTop: '8px' }}>
            <div style={{ width: '98%', height: '100%', backgroundColor: '#10B981' }}></div>
          </div>
        </div>

        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <p style={{ fontSize: '12px', color: '#666666' }}>Evolution Score</p>
            <h4 style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '8px' }}>94%</h4>
          </div>
          <p style={{ fontSize: '11px', color: '#10B981', marginTop: '4px' }}>+2.4% trend improvement</p>
        </div>

        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '20px' }}>
          <p style={{ fontSize: '12px', color: '#666666' }}>Total Revisions</p>
          <h4 style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '8px' }}>18 <span style={{ fontSize: '12px', color: '#666666', fontWeight: 'normal' }}>since June</span></h4>
        </div>
      </div>

      {/* Main Grid Layout: Evolutionary Graph Timeline (left) - Details (right) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 380px',
        gap: '24px'
      }}>
        
        {/* Left: Evolutionary Graph Timeline */}
        <div style={{
          backgroundColor: '#121212',
          border: '1px solid #1E1E1E',
          borderRadius: '16px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px'
        }}>
          <h3 style={{ fontSize: '15px', fontWeight: 'bold' }}>Evolutionary Graph</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', position: 'relative', paddingLeft: '24px', borderLeft: '2px solid #1E1E1E', marginLeft: '12px' }}>
            
            {/* Version Node 1: v1.2.8 */}
            <div 
              onClick={() => setSelectedVersion('v1.2.8')}
              style={{
                position: 'relative',
                backgroundColor: selectedVersion === 'v1.2.8' ? '#161616' : '#121212',
                border: selectedVersion === 'v1.2.8' ? '1px solid #0070F3' : '1px solid #1E1E1E',
                borderRadius: '12px',
                padding: '16px',
                cursor: 'pointer'
              }}
            >
              {/* Connector dot */}
              <span style={{ position: 'absolute', left: '-31px', top: '24px', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#0070F3', border: '3px solid #121212' }}></span>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>v1.2.8</span>
                  <span style={{ fontSize: '10px', color: '#888888', backgroundColor: '#1E1E1E', padding: '2px 6px', borderRadius: '4px' }}>REQUIREMENT CHANGE</span>
                </span>
                <span style={{ fontSize: '11px', color: '#10B981', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>Compiler Verified</span>
              </div>
              <h4 style={{ fontSize: '15px', fontWeight: 'bold', marginTop: '10px' }}>Premium Booking Rules</h4>
              <p style={{ fontSize: '12px', color: '#666666', marginTop: '6px', lineHeight: '1.4' }}>
                Implementing tiered pricing logic and loyalty discount validators across the Booking ecosystem.
              </p>
              
              <hr style={{ border: 'none', borderTop: '1px solid #1E1E1E', margin: '12px 0' }} />

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#666666' }}>
                <span>Sarah Jenkins | 2 hours ago</span>
                <span>Repair Count: 0 | Impact: Low</span>
              </div>
            </div>

            {/* Version Node 2: v1.2.6 */}
            <div 
              onClick={() => setSelectedVersion('v1.2.6')}
              style={{
                position: 'relative',
                backgroundColor: selectedVersion === 'v1.2.6' ? '#161616' : '#121212',
                border: selectedVersion === 'v1.2.6' ? '1px solid #0070F3' : '1px solid #1E1E1E',
                borderRadius: '12px',
                padding: '16px',
                cursor: 'pointer'
              }}
            >
              {/* Connector dot */}
              <span style={{ position: 'absolute', left: '-31px', top: '24px', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#10B981', border: '3px solid #121212' }}></span>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>v1.2.6</span>
                  <span style={{ fontSize: '10px', color: '#888888', backgroundColor: '#1E1E1E', padding: '2px 6px', borderRadius: '4px' }}>AUTONOMOUS REPAIR</span>
                </span>
                <span style={{ fontSize: '11px', color: '#FFFFFF', backgroundColor: '#666666', padding: '2px 6px', borderRadius: '4px' }}>15 Aug 2023</span>
              </div>
              <h4 style={{ fontSize: '15px', fontWeight: 'bold', marginTop: '10px' }}>Heuristic Circular Ref Patch</h4>
              <p style={{ fontSize: '12px', color: '#666666', marginTop: '6px', lineHeight: '1.4' }}>
                Autonomous repair applied to fix a circular dependency detected in the Booking Schema during v1.2.4 validation.
              </p>
              
              <hr style={{ border: 'none', borderTop: '1px solid #1E1E1E', margin: '12px 0' }} />

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#666666' }}>
                <span>AI Agent "Delta"</span>
                <span>3 Repairs Applied | Readiness: 99%</span>
              </div>
            </div>

            {/* Version Node 3: v1.2.4 */}
            <div 
              onClick={() => setSelectedVersion('v1.2.4')}
              style={{
                position: 'relative',
                backgroundColor: selectedVersion === 'v1.2.4' ? '#161616' : '#121212',
                border: selectedVersion === 'v1.2.4' ? '1px solid #0070F3' : '1px solid #1E1E1E',
                borderRadius: '12px',
                padding: '16px',
                cursor: 'pointer'
              }}
            >
              {/* Connector dot */}
              <span style={{ position: 'absolute', left: '-31px', top: '24px', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#666666', border: '3px solid #121212' }}></span>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 'bold' }}>v1.2.4</span>
                <span style={{ fontSize: '11px', color: '#FFFFFF', backgroundColor: '#666666', padding: '2px 6px', borderRadius: '4px' }}>14 Aug 2023</span>
              </div>
              <h4 style={{ fontSize: '15px', fontWeight: 'bold', marginTop: '10px' }}>Dependency Optimization</h4>
              
              <hr style={{ border: 'none', borderTop: '1px solid #1E1E1E', margin: '12px 0' }} />

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#666666' }}>
                <span>Readiness: 92% (Pre-Repair)</span>
                <span>Impact: High</span>
              </div>
            </div>

          </div>
        </div>

        {/* Right Column: Evolution Impact & Architecture Snapshot */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Evolution Impact Analysis */}
          <div style={{
            backgroundColor: '#121212',
            border: '1px solid #1E1E1E',
            borderRadius: '16px',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center'
          }}>
            <h3 style={{ fontSize: '14px', fontWeight: 'bold', alignSelf: 'flex-start' }}>Evolution Impact Analysis</h3>
            
            {/* Impact radial circle */}
            <div style={{ position: 'relative', width: '100px', height: '100px', margin: '20px 0' }}>
              <div style={{
                width: '100%',
                height: '100%',
                borderRadius: '50%',
                background: 'conic-gradient(#F59E0B 0% 42%, #1E1E1E 42% 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <div style={{ width: '80px', height: '80px', borderRadius: '50%', backgroundColor: '#121212', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#F59E0B' }}>42%</span>
                  <span style={{ fontSize: '9px', color: '#666666', textTransform: 'uppercase' }}>Medium</span>
                </div>
              </div>
            </div>

            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#666666' }}>Components Affected</span>
                <span style={{ fontWeight: 'bold' }}>4</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#666666' }}>Validation Rules Updated</span>
                <span style={{ fontWeight: 'bold' }}>2</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#666666' }}>Dependencies Modified</span>
                <span style={{ fontWeight: 'bold' }}>3</span>
              </div>
            </div>
          </div>

          {/* Architecture Snapshot */}
          <div style={{
            backgroundColor: '#121212',
            border: '1px solid #1E1E1E',
            borderRadius: '16px',
            padding: '24px'
          }}>
            <h3 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '16px' }}>Architecture Snapshot <span style={{ fontSize: '11px', color: '#666666', fontWeight: 'normal', marginLeft: '6px' }}>v1.2.8</span></h3>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '12px'
            }}>
              <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px', textAlign: 'center' }}>
                <p style={{ fontSize: '10px', color: '#666666', textTransform: 'uppercase' }}>Entities</p>
                <p style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '4px' }}>8</p>
              </div>
              <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px', textAlign: 'center' }}>
                <p style={{ fontSize: '10px', color: '#666666', textTransform: 'uppercase' }}>APIs</p>
                <p style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '4px' }}>12</p>
              </div>
              <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px', textAlign: 'center' }}>
                <p style={{ fontSize: '10px', color: '#666666', textTransform: 'uppercase' }}>Validation Rules</p>
                <p style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '4px' }}>15</p>
              </div>
              <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px', textAlign: 'center' }}>
                <p style={{ fontSize: '10px', color: '#666666', textTransform: 'uppercase' }}>Dependencies</p>
                <p style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '4px' }}>22</p>
              </div>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
