import React, { useState, useEffect } from 'react';
import { getVersions } from '../../frontend_api_client';
import { VersionHistoryEvolutionScreen } from '../../frontend_models';
import { History, RotateCw, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';

interface VersionHistoryProps {
  projectId: string;
}

export const VersionHistory: React.FC<VersionHistoryProps> = ({ projectId }) => {
  const [data, setData] = useState<VersionHistoryEvolutionScreen | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<string>('v1.0');

  useEffect(() => {
    loadVersions();
  }, [projectId]);

  const loadVersions = async () => {
    setLoading(true);
    const res = await getVersions(projectId);
    if (res.success && res.data) {
      setData(res.data);
      setError(null);
      if (res.data.versions && res.data.versions.length > 0) {
        setSelectedVersion(res.data.versions[res.data.versions.length - 1].version_id);
      }
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

  // Get selected version details
  const currentVersionDetails = data.versions.find(v => v.version_id === selectedVersion);
  const currentChangeReport = data.change_reports.find(r => r.change_id === selectedVersion);

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
          <p style={{ fontSize: '12px', color: '#666666' }}>Active Selected Version</p>
          <h4 style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>{selectedVersion}</span>
            <span style={{ fontSize: '10px', color: '#10B981', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
              {selectedVersion === 'v1.0' ? 'BASELINE' : 'EVOLVED'}
            </span>
          </h4>
        </div>

        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <p style={{ fontSize: '12px', color: '#666666' }}>Rollback Required</p>
            <h4 style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '8px' }}>
              {currentChangeReport?.effectiveness.rollback_required ? 'Yes' : 'No'}
            </h4>
          </div>
          <div style={{ height: '4px', backgroundColor: '#1E1E1E', borderRadius: '2px', overflow: 'hidden', marginTop: '8px' }}>
            <div style={{ width: currentChangeReport?.effectiveness.rollback_required ? '100%' : '0%', height: '100%', backgroundColor: currentChangeReport?.effectiveness.rollback_required ? '#EF4444' : '#10B981' }}></div>
          </div>
        </div>

        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <p style={{ fontSize: '12px', color: '#666666' }}>Evolution Complexity</p>
            <h4 style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '8px', color: '#0070F3' }}>
              {currentChangeReport?.effectiveness.complexity_level || 'LOW'}
            </h4>
          </div>
          <p style={{ fontSize: '11px', color: '#666666', marginTop: '4px' }}>Calculated from entity modifications</p>
        </div>

        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '20px' }}>
          <p style={{ fontSize: '12px', color: '#666666' }}>Total Revisions</p>
          <h4 style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '8px' }}>
            {data.versions.length} <span style={{ fontSize: '12px', color: '#666666', fontWeight: 'normal' }}>Compiled</span>
          </h4>
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
          <h3 style={{ fontSize: '15px', fontWeight: 'bold' }}>Evolutionary Version Graph</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', position: 'relative', paddingLeft: '24px', borderLeft: '2px solid #1E1E1E', marginLeft: '12px' }}>
            {data.versions.map((ver, idx) => (
              <div 
                key={ver.version_id}
                onClick={() => setSelectedVersion(ver.version_id)}
                style={{
                  position: 'relative',
                  backgroundColor: selectedVersion === ver.version_id ? '#161616' : '#121212',
                  border: selectedVersion === ver.version_id ? '1px solid #0070F3' : '1px solid #1E1E1E',
                  borderRadius: '12px',
                  padding: '16px',
                  cursor: 'pointer'
                }}
              >
                {/* Connector dot */}
                <span style={{ position: 'absolute', left: '-31px', top: '24px', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: selectedVersion === ver.version_id ? '#0070F3' : '#333333', border: '3px solid #121212' }}></span>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>{ver.version_id}</span>
                    <span style={{ fontSize: '10px', color: '#888888', backgroundColor: '#1E1E1E', padding: '2px 6px', borderRadius: '4px' }}>
                      {idx === 0 ? 'BASELINE' : 'REVISION'}
                    </span>
                  </span>
                  <span style={{ fontSize: '11px', color: '#10B981', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>Compiler Verified</span>
                </div>
                <h4 style={{ fontSize: '15px', fontWeight: 'bold', marginTop: '10px' }}>{ver.change_summary}</h4>
                
                <hr style={{ border: 'none', borderTop: '1px solid #1E1E1E', margin: '12px 0' }} />

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#666666' }}>
                  <span>Created {ver.created_at.substring(0, 19).replace('T', ' ')}</span>
                  {ver.parent_version ? <span>Parent: {ver.parent_version}</span> : <span>Initial Compile</span>}
                </div>
              </div>
            ))}
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
            
            <div style={{ width: '100%', margin: '20px 0', backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px', textAlign: 'left' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Impact Level</p>
              <p style={{ fontSize: '18px', fontWeight: 'bold', color: '#F59E0B', marginTop: '6px' }}>{currentChangeReport?.effectiveness.impact_level || 'LOW'}</p>
              <p style={{ fontSize: '12px', color: '#888888', marginTop: '6px' }}>{currentChangeReport?.version_info.change_summary || 'Baseline compile has no delta impact.'}</p>
            </div>

            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#666666' }}>Components Affected</span>
                <span style={{ fontWeight: 'bold' }}>
                  {currentChangeReport?.effectiveness.components_modified.length || 0}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#666666' }}>Preserved Components</span>
                <span style={{ fontWeight: 'bold' }}>
                  {currentChangeReport?.effectiveness.components_preserved.length || 'All'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#666666' }}>Validation Result</span>
                <span style={{ fontWeight: 'bold', color: currentChangeReport?.effectiveness.validation_passed ? '#10B981' : '#EF4444' }}>
                  {currentChangeReport?.effectiveness.validation_passed ? 'PASSED' : 'STABLE'}
                </span>
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
            <h3 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '16px' }}>Version Changes Summary</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
              {currentChangeReport?.diffs.map((d, idx) => (
                <div key={idx} style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '10px' }}>
                  <p style={{ fontWeight: 'bold', color: '#FFFFFF' }}>Component: {d.component}</p>
                  <p style={{ color: '#888888', marginTop: '4px' }}>Action: {d.change_reason}</p>
                </div>
              )) || (
                <p style={{ color: '#666666' }}>No delta diffs recorded for baseline version v1.0.</p>
              )}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
