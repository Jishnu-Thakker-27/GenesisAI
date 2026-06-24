import React, { useState, useEffect } from 'react';
import { getProject, compileProject } from '../../frontend_api_client';
import { FinalCompiledApplication } from '../../frontend_models';
import { Play, ShieldAlert, Terminal, CheckCircle2, RotateCw, Cpu, BrainCircuit, ShieldCheck, Database, Wrench } from 'lucide-react';
import { JsonInspector } from '../components/JsonInspector';

interface CompilerWorkspaceProps {
  projectId: string;
  selectedFile?: string;
  onSelectFile?: (file: string) => void;
  onNavigate?: (tab: string) => void;
}

export const CompilerWorkspace: React.FC<CompilerWorkspaceProps> = ({ projectId, selectedFile, onSelectFile, onNavigate }) => {
  const [project, setProject] = useState<FinalCompiledApplication | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [evolving, setEvolving] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  
  const [selectedFileLocal, setSelectedFileLocal] = useState<string>('master_specification.json');
  const activeFile = selectedFile || selectedFileLocal;
  const setActiveFile = onSelectFile || setSelectedFileLocal;

  useEffect(() => {
    if (projectId) {
      loadProject();
    } else {
      setProject(null);
      setError(null);
    }
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
    const res = await compileProject(project.prompt, project.execution_mode || "BALANCED", project.ai_architect_report?.mode || "HYBRID");
    if (res.success && res.data) {
      setProject(res.data);
      setToastMessage('Evolution Successful - Genesis Schema EV-002-TRS in action.');
      setTimeout(() => setToastMessage(null), 4000);
    } else {
      alert(res.error || 'Evolution failed.');
    }
    setEvolving(false);
  };

  if (!projectId || (!project && !loading && !error)) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '400px',
        textAlign: 'center',
        backgroundColor: '#121212',
        border: '1px solid #1E1E1E',
        borderRadius: '12px',
        padding: '40px'
      }}>
        <div style={{
          width: 56,
          height: 56,
          borderRadius: '50%',
          backgroundColor: 'rgba(0,112,243,0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '20px',
          color: '#0070F3'
        }}>
          <Cpu size={28} />
        </div>
        <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#FFFFFF', margin: '0 0 8px 0' }}>No Contracts Generated Yet</h3>
        <p style={{ color: '#888888', fontSize: '14px', maxWidth: '480px', margin: '0 0 20px 0', lineHeight: '1.5' }}>
          Compilation produces 6 core contract artifacts:
        </p>
        <div style={{
          textAlign: 'left',
          fontSize: '13px',
          color: '#AAAAAA',
          marginBottom: '24px',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '8px 16px',
          maxWidth: '440px'
        }}>
          <div>📄 requirements_report.json</div>
          <div>📄 blueprint.json</div>
          <div>📄 master_specification.json</div>
          <div>📄 validation_report.json</div>
          <div>📄 repair_report.json</div>
          <div>📄 final_contract.json</div>
        </div>
        <button
          onClick={() => onNavigate?.('ai-architect')}
          style={{
            backgroundColor: '#0070F3',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '8px',
            padding: '10px 20px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'background-color 0.2s'
          }}
        >
          Go to AI Architect
        </button>
      </div>
    );
  }

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

  // Compiler generated artifacts List
  const filesList = [
    { name: 'requirements_report.json', label: 'requirements_report.json', icon: BrainCircuit, desc: 'Ambiguity & requirements trace.' },
    { name: 'blueprint.json', label: 'blueprint.json', icon: Database, desc: 'Extracted actors and features.' },
    { name: 'master_specification.json', label: 'master_specification.json', icon: Terminal, desc: 'Compiled specifications and schemas.' },
    { name: 'validation_report.json', label: 'validation_report.json', icon: ShieldCheck, desc: 'Integrity scan diagnostics.' },
    { name: 'repair_report.json', label: 'repair_report.json', icon: Wrench, desc: 'Autonomous patch repair details.' },
    { name: 'final_contract.json', label: 'final_contract.json', icon: Cpu, desc: 'Complete compiled application contract.' }
  ];

  // Dynamic code viewer selector content
  const renderFileContent = () => {
    switch (activeFile) {
      case 'requirements_report.json':
        return {
          filename: 'requirements_report.json',
          content: JSON.stringify(project.ai_architect_report || {}, null, 2)
        };
      case 'blueprint.json':
        return {
          filename: 'blueprint.json',
          content: JSON.stringify(project.blueprint || {}, null, 2)
        };
      case 'master_specification.json':
        return {
          filename: 'master_specification.json',
          content: JSON.stringify(project.system_design || {}, null, 2)
        };
      case 'validation_report.json':
        return {
          filename: 'validation_report.json',
          content: JSON.stringify(project.validation_report || {}, null, 2)
        };
      case 'repair_report.json':
        return {
          filename: 'repair_report.json',
          content: JSON.stringify(project.repair_report || {
            repair_status: 'No repair needed',
            validation_passed: project.validation_report?.is_valid || true,
            repair_history: []
          }, null, 2)
        };
      case 'final_contract.json':
        return {
          filename: 'final_contract.json',
          content: JSON.stringify(project, null, 2)
        };
      default:
        return { filename: 'master_specification.json', content: JSON.stringify(project.system_design || {}, null, 2) };
    }
  };

  const activeViewer = renderFileContent();

  // Dynamic Right-Sidebar Reasoning details based on current active file
  const renderReasoningMeta = () => {
    switch (activeFile) {
      case 'requirements_report.json':
        return (
          <>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Ambiguity Rating</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>Ambiguity Level</p>
              <p style={{ fontSize: '18px', fontWeight: 'bold', color: '#F59E0B', marginTop: '4px' }}>
                {Math.round((project.ai_architect_report?.ambiguity_score || 0.3) * 100)}%
              </p>
            </div>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Open Questions</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>
                {project.ai_architect_report?.clarification_questions?.length || 0} Clarifications
              </p>
            </div>
          </>
        );
      case 'blueprint.json':
        return (
          <>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Blueprint Recommendations</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>
                {project.blueprint?.actors?.length || 0} Actors, {project.blueprint?.features?.length || 0} Features
              </p>
            </div>
          </>
        );
      case 'master_specification.json':
        return (
          <>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Specification Details</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>
                {project.system_design?.entities?.length || 0} Entities, {project.system_design?.workflows?.length || 0} Workflows
              </p>
            </div>
          </>
        );
      case 'validation_report.json':
        return (
          <>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Validation Status</p>
              <p style={{ fontSize: '18px', fontWeight: 'bold', color: project.validation_report?.is_valid ? '#10B981' : '#EF4444', marginTop: '4px' }}>
                {project.validation_report?.is_valid ? 'PASSED' : 'REJECTED'}
              </p>
            </div>
          </>
        );
      case 'repair_report.json':
        return (
          <>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Healing Diagnostics</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>
                {project.repair_report?.repair_actions_executed?.length || 0} Applied Patches
              </p>
            </div>
          </>
        );
      case 'final_contract.json':
        return (
          <>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Contract Details</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>Version 1.0.0-Stable</p>
              <p style={{ fontSize: '12px', color: '#888888', marginTop: '6px', lineHeight: '1.4' }}>
                This is the complete, signed system architecture contract. Ready for deployment pipeline.
              </p>
            </div>
          </>
        );
      default:
        return null;
    }
  };

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
        gridTemplateColumns: '260px 1fr 340px',
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
          gap: '16px',
          overflowY: 'auto'
        }}>
          <h3 style={{ fontSize: '14px', fontWeight: 'bold', color: '#FFFFFF' }}>Generated Files</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {filesList.map((file) => {
              const FileIcon = file.icon;
              const isSelected = activeFile === file.name;
              return (
                <button
                  key={file.name}
                  onClick={() => setActiveFile(file.name)}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    gap: '4px',
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    border: 'none',
                    backgroundColor: isSelected ? '#0070F3' : 'transparent',
                    color: isSelected ? '#FFFFFF' : '#888888',
                    cursor: 'pointer',
                    textAlign: 'left',
                    fontFamily: 'inherit',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: isSelected ? 'bold' : 'normal' }}>
                    <FileIcon size={14} />
                    <span>{file.label}</span>
                  </div>
                  <span style={{ fontSize: '10px', color: isSelected ? 'rgba(255,255,255,0.7)' : '#666666' }}>{file.desc}</span>
                </button>
              );
            })}
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
          <JsonInspector
            title={activeViewer.filename}
            data={JSON.parse(activeViewer.content)}
            filename={activeViewer.filename}
          />
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

          {renderReasoningMeta()}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px' }}>
              <p style={{ fontSize: '11px', color: '#666666' }}>Missing Requirements</p>
              <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#F59E0B', marginTop: '4px' }}>{project.ai_architect_report.missing_information.length}</p>
            </div>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px' }}>
              <p style={{ fontSize: '11px', color: '#666666' }}>Open Questions</p>
              <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#FFFFFF', marginTop: '4px' }}>{project.ai_architect_report.clarification_questions.length}</p>
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
{(project.pipeline_traces || []).map((trace) => `${trace.phase_name}: ${trace.status}`).join('\n')}
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
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><CheckCircle2 size={16} style={{ color: '#10B981' }} /> {project.validation_report.errors.length} Errors</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><ShieldAlert size={16} style={{ color: '#666666' }} /> {project.validation_report.warnings.length} Warnings</span>
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
