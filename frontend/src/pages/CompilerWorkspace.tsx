import React, { useState, useEffect } from 'react';
import { getProject, compileProject } from '../../frontend_api_client';
import { FinalCompiledApplication } from '../../frontend_models';
import { Play, ShieldAlert, Terminal, CheckCircle2, RotateCw, Cpu, BrainCircuit, ShieldCheck, Database, Wrench } from 'lucide-react';
import { JsonInspector } from '../components/JsonInspector';

interface CompilerWorkspaceProps {
  projectId: string;
}

export const CompilerWorkspace: React.FC<CompilerWorkspaceProps> = ({ projectId }) => {
  const [project, setProject] = useState<FinalCompiledApplication | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [evolving, setEvolving] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [selectedStage, setSelectedStage] = useState<string>('System Design');

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

  // Compiler stages linked to selected tabs
  const stages = [
    { name: 'Intent Extraction', icon: Cpu, desc: 'Natural language semantic parsing.' },
    { name: 'AI Architect Report', icon: BrainCircuit, desc: 'Ambiguity & assumptions engine.' },
    { name: 'Blueprint Recommendation', icon: Database, desc: 'Recommended actors and structures.' },
    { name: 'System Design', icon: Terminal, desc: 'Specification of entities and relations.' },
    { name: 'Schema Generation', icon: Database, desc: 'Database, API, and UI schemas.' },
    { name: 'Validation', icon: ShieldCheck, desc: 'Multi-layer integrity scan.' },
    { name: 'Self-Healing Repair', icon: Wrench, desc: 'Autonomous conflict patch engine.' }
  ];

  // Dynamic code viewer selector content
  const renderStageContent = () => {
    switch (selectedStage) {
      case 'Intent Extraction':
        return {
          filename: 'intent_extraction.json',
          content: JSON.stringify({
            prompt: project.prompt,
            extracted_intent: project.intent
          }, null, 2)
        };
      case 'AI Architect Report':
        return {
          filename: 'ai_architect_report.json',
          content: JSON.stringify({
            mode: project.ai_architect_report.mode,
            ambiguity_score: project.ai_architect_report.ambiguity_score,
            missing_information: project.ai_architect_report.missing_information,
            assumptions_made: project.ai_architect_report.assumptions_made,
            clarification_questions: project.ai_architect_report.clarification_questions,
            confidence_scores: project.ai_architect_report.confidence_scores
          }, null, 2)
        };
      case 'Blueprint Recommendation':
        return {
          filename: 'blueprint_recommendation.json',
          content: JSON.stringify(project.blueprint, null, 2)
        };
      case 'System Design':
        return {
          filename: 'master_specification.json',
          content: JSON.stringify({
            schema_version: '2.4.0-alpha',
            metadata: project.system_design.metadata || {},
            entities: project.system_design.entities,
            relationships: project.system_design.relationships,
            workflows: project.system_design.workflows,
            design_decisions: project.system_design.design_decisions
          }, null, 2)
        };
      case 'Schema Generation':
        return {
          filename: 'compiled_schema_bundle.json',
          content: JSON.stringify(project.schema_bundle, null, 2)
        };
      case 'Validation':
        return {
          filename: 'validation_report.json',
          content: JSON.stringify(project.validation_report, null, 2)
        };
      case 'Self-Healing Repair':
        return {
          filename: 'repair_report.json',
          content: JSON.stringify(project.repair_report || {
            repair_status: 'No repair needed',
            validation_passed: project.validation_report.is_valid,
            repair_history: []
          }, null, 2)
        };
      default:
        return { filename: 'unknown.json', content: '{}' };
    }
  };

  const activeViewer = renderStageContent();

  // Dynamic Right-Sidebar Reasoning details based on current stage
  const renderReasoningMeta = () => {
    switch (selectedStage) {
      case 'Intent Extraction':
        return (
          <>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Extraction Engine</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>Intent Confidence</p>
              <p style={{ fontSize: '18px', fontWeight: 'bold', color: '#10B981', marginTop: '4px' }}>
                {Math.round((project.intent?.confidence_score || 0.9) * 100)}%
              </p>
            </div>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Actors Found</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>
                {project.intent?.actors?.length || 0} Actors Extracted
              </p>
              <p style={{ fontSize: '12px', color: '#888888', marginTop: '4px' }}>
                {project.intent?.actors?.map((a: any) => a.name).join(', ')}
              </p>
            </div>
          </>
        );
      case 'AI Architect Report':
        return (
          <>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Ambiguity Rating</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>Ambiguity Level</p>
              <p style={{ fontSize: '18px', fontWeight: 'bold', color: '#F59E0B', marginTop: '4px' }}>
                {Math.round(project.ai_architect_report.ambiguity_score * 100)}%
              </p>
            </div>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Clarification Triggered</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>
                {project.ai_architect_report.clarification_questions.length} Open Questions
              </p>
            </div>
          </>
        );
      case 'Blueprint Recommendation':
        return (
          <>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Blueprint Contents</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>{project.blueprint.actors.length} actors</p>
              <p style={{ fontSize: '12px', color: '#888888', marginTop: '4px' }}>{project.blueprint.features.length} features, {project.blueprint.workflows.length} workflows</p>
            </div>
          </>
        );
      case 'System Design':
        return (
          <>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Active Specification</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>Compiled Spec</p>
              <p style={{ fontSize: '12px', color: '#888888', marginTop: '6px', lineHeight: '1.4' }}>
                Generated dynamically from natural language requirements mapping core relational models.
              </p>
            </div>
          </>
        );
      case 'Validation':
        return (
          <>
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Scan Verdict</p>
              <p style={{ fontSize: '13px', fontWeight: 'bold', marginTop: '6px' }}>Integrity Scan</p>
              <p style={{ fontSize: '18px', fontWeight: 'bold', color: project.validation_report.is_valid ? '#10B981' : '#F59E0B', marginTop: '4px' }}>
                {project.validation_report.is_valid ? 'PASSED' : 'WARNING'}
              </p>
            </div>
          </>
        );
      default:
        return (
          <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
            <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Pipeline Log</p>
            <p style={{ fontSize: '12px', color: '#888888', marginTop: '6px', lineHeight: '1.4' }}>
              Select a compiler stage on the left sidebar to audit its serialized code outputs.
            </p>
          </div>
        );
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
          <h3 style={{ fontSize: '14px', fontWeight: 'bold', color: '#FFFFFF' }}>Compiler Stages</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {stages.map((stage) => {
              const StageIcon = stage.icon;
              const isSelected = selectedStage === stage.name;
              return (
                <button
                  key={stage.name}
                  onClick={() => setSelectedStage(stage.name)}
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
                    <StageIcon size={14} />
                    <span>{stage.name}</span>
                  </div>
                  <span style={{ fontSize: '10px', color: isSelected ? 'rgba(255,255,255,0.7)' : '#666666' }}>{stage.desc}</span>
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
{project.pipeline_traces.map((trace) => `${trace.phase_name}: ${trace.status}`).join('\n')}
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
