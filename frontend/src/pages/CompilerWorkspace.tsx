import React, { useState, useEffect } from 'react';
import { getProject, compileProject } from '../../frontend_api_client';
import { FinalCompiledApplication } from '../../frontend_models';
import { Play, ShieldAlert, Terminal, CheckCircle2, RotateCw } from 'lucide-react';

interface CompilerWorkspaceProps {
  projectId: string;
}

export const CompilerWorkspace: React.FC<CompilerWorkspaceProps> = ({ projectId }) => {
  const [project, setProject] = useState<FinalCompiledApplication | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [evolving, setEvolving] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    setLoading(true);
    const res = await getProject(projectId);
    if (res.success && res.data) {
      setProject(res.data);
      setError(null);
    } else {
      setError(res.error || 'Failed to fetch project specifications.');
    }
    setLoading(false);
  };

  const handleEvolve = async () => {
    if (!project) return;
    setEvolving(true);
    const res = await compileProject(project.prompt);
    if (res.success && res.data) {
      setProject(res.data);
      setToastMessage('Evolution Successful - Genesis Schema EV-002-TRS in action.');
      setTimeout(() => setToastMessage(null), 4000);
    } else {
      alert(res.error || 'Evolution failed.');
    }
    setEvolving(false);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px', flexDirection: 'column', gap: '16px' }}>
        <RotateCw className="pulse" size={48} style={{ color: '#0070F3' }} />
        <p style={{ color: '#666666', fontSize: '14px' }}>Compiling master specification AST...</p>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div style={{ padding: '24px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)', borderRadius: '12px' }}>
        <h3 style={{ color: '#EF4444' }}>Compiler workspace loading error</h3>
        <p style={{ color: '#888888', marginTop: '8px' }}>{error || 'Failed to load compiled project.'}</p>
        <button onClick={loadProject} style={{ marginTop: '16px', padding: '8px 16px', backgroundColor: '#EF4444', border: 'none', color: '#FFF', borderRadius: '4px', cursor: 'pointer' }}>Retry</button>
      </div>
    );
  }

  // Define compiler stage checkpoints
  const stages = [
    { name: 'Intent Extraction', status: 'Checked' },
    { name: 'Blueprint Recommendation', status: 'Checked' },
    { name: 'System Design', status: 'Checked' },
    { name: 'Schema Generation', status: 'Active' },
    { name: 'Validation', status: 'Pending' },
    { name: 'Repair', status: 'Pending' },
    { name: 'Simulation', status: 'Pending' },
    { name: 'Evaluation', status: 'Pending' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Workspace Header Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#121212',
        border: '1px solid #1E1E1E',
        borderRadius: '12px',
        padding: '16px 24px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontSize: '12px', color: '#888888', letterSpacing: '0.5px' }}>GENESIS STATUS</span>
          <span style={{
            fontSize: '13px',
            fontWeight: 'bold',
            color: evolving ? '#F59E0B' : '#0070F3',
            backgroundColor: evolving ? 'rgba(245, 158, 11, 0.1)' : 'rgba(0, 112, 243, 0.1)',
            padding: '6px 12px',
            borderRadius: '4px'
          }}>
            {evolving ? 'EVOLVING...' : 'STABLE'}
          </span>
        </div>
        <div style={{ fontSize: '13px', color: '#666666' }}>
          Latency: <strong style={{ color: '#FFFFFF' }}>1.2s</strong>
        </div>
      </div>

      {/* Main Grid: Checklist - JSON Spec Editor - Reasoning side panel */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '240px 1fr 340px',
        gap: '24px',
        height: 'calc(100vh - 280px)',
        minHeight: '500px'
      }}>
        
        {/* Left Stage Checklist */}
        <div style={{
          backgroundColor: '#121212',
          border: '1px solid #1E1E1E',
          borderRadius: '16px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          <h3 style={{ fontSize: '14px', fontWeight: 'bold', color: '#FFFFFF' }}>Compiler Stages</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {stages.map((stage) => (
              <div key={stage.name} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '18px',
                  height: '18px',
                  borderRadius: '4px',
                  border: stage.status === 'Pending' ? '1px solid #333333' : 'none',
                  backgroundColor: stage.status === 'Checked' ? '#0070F3' : stage.status === 'Active' ? '#F59E0B' : 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontSize: '10px',
                  fontWeight: 'bold'
                }}>
                  {stage.status === 'Checked' ? '✓' : stage.status === 'Active' ? '•' : ''}
                </div>
                <span style={{
                  fontSize: '13px',
                  color: stage.status === 'Pending' ? '#666666' : '#FFFFFF',
                  fontWeight: stage.status === 'Active' ? 'bold' : 'normal'
                }}>
                  {stage.name}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Center Specification Editor */}
        <div style={{
          backgroundColor: '#121212',
          border: '1px solid #1E1E1E',
          borderRadius: '16px',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          {/* Editor Header */}
          <div style={{
            padding: '12px 20px',
            borderBottom: '1px solid #1E1E1E',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#161616'
          }}>
            <span style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', color: '#888888' }}>master_spec.json (1402 lines)</span>
            <span style={{ fontSize: '11px', color: '#666666' }}>UTF-8 | JSON</span>
          </div>

          {/* Editor Content */}
          <pre style={{
            flexGrow: 1,
            margin: 0,
            padding: '20px',
            backgroundColor: '#0A0A0A',
            overflow: 'auto',
            fontFamily: 'var(--font-mono)',
            fontSize: '13px',
            lineHeight: '1.6',
            color: '#D4D4D4'
          }}>
            <code>
{JSON.stringify({
  schema_version: "2.4.0-alpha",
  application: {
    name: project.app_name,
    type: project.app_type,
    prompt: project.prompt
  },
  entities: project.system_design.entities,
  relationships: project.system_design.relationships,
  workflows: project.system_design.workflows
}, null, 2)}
            </code>
          </pre>
        </div>

        {/* Right Reasoning & Traceability Panel */}
        <div style={{
          backgroundColor: '#121212',
          border: '1px solid #1E1E1E',
          borderRadius: '16px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
          overflowY: 'auto'
        }}>
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 'bold', color: '#FFFFFF' }}>Reasoning & Traceability</h3>
            <p style={{ fontSize: '12px', color: '#666666', marginTop: '4px' }}>Underlying rationales for compiled design entities.</p>
          </div>

          <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
            <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Active Analysis</p>
            <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>Entity: Booking</p>
            <p style={{ fontSize: '12px', color: '#888888', marginTop: '6px', lineHeight: '1.4' }}>
              Generated to satisfy core Genesis requirements for transactional integrity and client scheduling.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px' }}>
              <p style={{ fontSize: '11px', color: '#666666' }}>Coverage</p>
              <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#10B981', marginTop: '4px' }}>98.4%</p>
            </div>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px' }}>
              <p style={{ fontSize: '11px', color: '#666666' }}>Latency</p>
              <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#FFFFFF', marginTop: '4px' }}>12ms</p>
            </div>
          </div>

          <div style={{ flexGrow: 1, backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
            <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Genesis Context</p>
            <pre style={{
              fontSize: '11px',
              color: '#888888',
              whiteSpace: 'pre-wrap',
              marginTop: '8px',
              lineHeight: '1.4'
            }}>
SOURCE_1: Genesis core 'Feeder' evolves 'Booking' via the primary interface.
            </pre>
          </div>
        </div>

      </div>

      {/* Control Action Buttons Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#121212',
        border: '1px solid #1E1E1E',
        borderRadius: '12px',
        padding: '16px 24px'
      }}>
        <div style={{ display: 'flex', gap: '16px', color: '#888888', fontSize: '13px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><CheckCircle2 size={16} style={{ color: '#10B981' }} /> 0 Errors</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><ShieldAlert size={16} style={{ color: '#666666' }} /> 0 Warnings</span>
        </div>
        
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={handleEvolve}
            disabled={evolving}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: '#0070F3',
              color: '#FFFFFF',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '6px',
              fontWeight: '600',
              fontSize: '13px',
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
          >
            {evolving ? <RotateCw className="pulse" size={14} /> : <Play size={14} />}
            <span>{evolving ? 'Evolving...' : 'EVOLVE CORE'}</span>
          </button>
          
          <button style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'transparent',
            border: '1px solid #333333',
            color: '#FFFFFF',
            padding: '10px 20px',
            borderRadius: '6px',
            fontWeight: '600',
            fontSize: '13px',
            cursor: 'pointer'
          }}>
            <Terminal size={14} />
            <span>INSPECT</span>
          </button>
        </div>
      </div>

      {/* Floating Toast Notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          backgroundColor: '#121212',
          border: '1px solid #10B981',
          color: '#FFFFFF',
          borderRadius: '8px',
          padding: '12px 20px',
          fontSize: '13px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          animation: 'slideIn 0.3s ease-out forwards'
        }}>
          <CheckCircle2 size={16} style={{ color: '#10B981' }} />
          <span>{toastMessage}</span>
        </div>
      )}

    </div>
  );
};
