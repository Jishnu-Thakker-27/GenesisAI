import React, { useEffect, useMemo, useState } from 'react';
import { compileProject, getProject } from '../../frontend_api_client';
import {
  AIArchitectReport,
  ArchitectureReasoningItem,
  FinalCompiledApplication
} from '../../frontend_models';
import { JsonInspector } from '../components/JsonInspector';
import {
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  CircleHelp,
  ExternalLink,
  FileJson,
  FileText,
  FolderOpen,
  GitBranch,
  Lightbulb,
  Network,
  Play,
  RotateCw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Cpu,
  Wrench
} from 'lucide-react';

interface AIArchitectProps {
  projectId: string;
  onSetProjectId?: (id: string) => void;
  onOpenArtifact?: (artifact: 'architecture' | 'contracts' | 'validation') => void;
  onNavigate?: (tab: string) => void;
}

type JsonTarget = 'requirements' | 'blueprint' | 'spec' | 'validation' | 'repair' | 'contract';

const cardStyle: React.CSSProperties = {
  backgroundColor: '#121212',
  border: '1px solid #1E1E1E',
  borderRadius: '8px'
};

const severityColor = (severity: string) => {
  if (severity === 'HIGH' || severity === 'CRITICAL') return '#EF4444';
  if (severity === 'MEDIUM') return '#F59E0B';
  return '#10B981';
};

const pillStyle: React.CSSProperties = {
  backgroundColor: '#0A0A0A',
  border: '1px solid #1E1E1E',
  borderRadius: '6px',
  padding: '7px 9px',
  color: '#D4D4D4',
  fontSize: '12px'
};

export const AIArchitect: React.FC<AIArchitectProps> = ({ projectId, onSetProjectId, onOpenArtifact, onNavigate }) => {
  const [project, setProject] = useState<FinalCompiledApplication | null>(null);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [compiling, setCompiling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jsonTarget, setJsonTarget] = useState<JsonTarget>('requirements');

  useEffect(() => {
    if (projectId) {
      loadProject(projectId);
    }
  }, [projectId]);

  const loadProject = async (id: string) => {
    setLoading(true);
    const res = await getProject(id);
    if (res.success && res.data) {
      setProject(res.data);
      setPrompt(res.data.prompt || '');
      setError(null);
    } else {
      setError(null);
    }
    setLoading(false);
  };

  const handleCompile = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!prompt.trim()) return;
    setCompiling(true);
    const res = await compileProject(prompt, project?.execution_mode || 'BALANCED', project?.ai_architect_report?.mode || 'HYBRID');
    if (res.success && res.data) {
      setProject(res.data);
      onSetProjectId?.(res.data.project_id);
      setError(null);
    } else {
      setError(res.error || 'Compilation failed.');
    }
    setCompiling(false);
  };

  const report = project?.ai_architect_report;
  const spec = project?.system_design;

  const contractViews = useMemo(() => {
    if (!project || !report) return {};
    return {
      requirements: report,
      blueprint: project.blueprint,
      spec: project.system_design,
      validation: project.validation_report,
      repair: project.repair_report || { repair_status: 'No repair was required for this compile.' },
      contract: project
    };
  }, [project, report]);

  const jsonData = (contractViews as Record<string, unknown>)[jsonTarget] || {};
  const jsonLabels: Record<JsonTarget, string> = {
    requirements: 'Requirements Report',
    blueprint: 'Blueprint',
    spec: 'Master Specification',
    validation: 'Validation Report',
    repair: 'Repair Report',
    contract: 'Final Contract'
  };
  const outputButtons: Array<{ id: JsonTarget | 'architecture'; label: string }> = [
    { id: 'architecture', label: 'Architecture' },
    { id: 'requirements', label: 'Requirements Report' },
    { id: 'blueprint', label: 'Blueprint' },
    { id: 'spec', label: 'Master Specification' },
    { id: 'validation', label: 'Validation Report' },
    { id: 'repair', label: 'Repair Report' },
    { id: 'contract', label: 'Final Contract' }
  ];
  const projectFileGroups: Array<{ title: string; files: Array<{ target: JsonTarget; name: string }> }> = [
    { title: 'Requirements', files: [{ target: 'requirements', name: 'requirements_report.json' }] },
    { title: 'Architecture', files: [{ target: 'blueprint', name: 'blueprint.json' }, { target: 'spec', name: 'master_specification.json' }] },
    { title: 'Validation', files: [{ target: 'validation', name: 'validation_report.json' }, { target: 'repair', name: 'repair_report.json' }] },
    { title: 'Final Output', files: [{ target: 'contract', name: 'final_contract.json' }] }
  ];
  const openOutput = (target: JsonTarget | 'architecture') => {
    if (target === 'architecture') {
      onOpenArtifact?.('architecture');
      return;
    }
    setJsonTarget(target);
  };
  const domain = report?.detected_domain || project?.intent?.detected_domain || 'Awaiting compile';
  const subdomain = report?.detected_subdomain || project?.intent?.detected_subdomain || 'Describe an application to begin';
  const actors = report?.actors?.length ? report.actors : project?.blueprint?.actors?.map((actor: any) => actor.name) || [];
  const entities = report?.entities?.length ? report.entities : spec?.entities?.map((entity: any) => entity.name) || [];
  const workflows = report?.workflows?.length ? report.workflows : spec?.workflows?.map((workflow: any) => workflow.workflow_name) || [];
  const businessRules = spec?.business_rules || [];
  const reportAny = report as any;
  const recommendations = [
    ...(reportAny?.recommended_entities?.map((item: any) => `Entity: ${item.name} — ${item.reason}`) || []),
    ...(reportAny?.recommended_workflows?.map((item: any) => `Workflow: ${item.name} — ${item.reason}`) || []),
    ...(report?.confidence_explanation || [])
  ];

  // Structured ambiguities (from ambiguity_classifications or derived from risks)
  const ambiguities: Array<{ category: string; severity: string; issue: string }> = 
    (reportAny?.ambiguity_classifications || []).length > 0
      ? reportAny.ambiguity_classifications
      : (report?.risks || []).slice(0, 5).map((risk: any) => ({
          category: risk.category || 'Architecture',
          severity: risk.level || risk.severity || 'MEDIUM',
          issue: risk.explanation || risk.mitigation || risk.risk || ''
        }));

  // Confidence explanation lines (from confidence_explanation or derived)
  const confidenceLines: string[] = (report?.confidence_explanation || []).length > 0
    ? report!.confidence_explanation!
    : [
        domain !== 'Awaiting compile' ? `${domain} domain clearly detected.` : 'Domain detection pending.',
        actors.length > 0 ? `${actors.length} core actors identified: ${actors.slice(0, 3).join(', ')}.` : 'Actor extraction pending.',
        entities.length > 0 ? `${entities.length} domain entities resolved.` : 'Entity extraction pending.',
        workflows.length > 0 ? `${workflows.length} workflows mapped.` : 'Workflow mapping pending.',
      ].filter(Boolean);

  const confidenceScore = report ? Math.round((report as any).overall_confidence * 100 || (1 - (report?.ambiguity_score || 0.3)) * 100) : null;
  const ambiguityPct = report ? Math.round((report?.ambiguity_score || 0) * 100) : null;

  // Pipeline workflow steps for the output navigation bar
  const pipelineSteps = [
    { label: 'AI Architect', tab: 'ai-architect', icon: BrainCircuit, done: !!report },
    { label: 'Architecture', tab: 'architecture', icon: Network, done: !!spec },
    { label: 'Contracts', tab: 'compiler', icon: Cpu, done: !!project?.schema_bundle },
    { label: 'Validation & Repair', tab: 'validation', icon: ShieldCheck, done: !!project?.validation_report },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Compile Input Card */}
      <section style={{ ...cardStyle, padding: '22px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: '24px', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: 42, height: 42, borderRadius: 8, backgroundColor: 'rgba(0,112,243,0.14)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0070F3' }}>
                <BrainCircuit size={23} />
              </div>
              <div>
                <h2 style={{ fontSize: 22, fontWeight: 700 }}>AI Software Architect</h2>
                <p style={{ color: '#888888', fontSize: 13, marginTop: 4 }}>Describe an app. GenesisAI extracts requirements, resolves ambiguity, and compiles an architecture contract.</p>
              </div>
            </div>

            <form onSubmit={handleCompile} style={{ display: 'flex', gap: '10px', marginTop: '18px' }}>
              <input
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="Describe the application you want to build..."
                style={{
                  flexGrow: 1,
                  backgroundColor: '#0A0A0A',
                  border: '1px solid #1E1E1E',
                  borderRadius: '8px',
                  color: '#FFFFFF',
                  padding: '13px 14px',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
              <button type="submit" disabled={compiling} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                backgroundColor: compiling ? '#1E1E1E' : '#0070F3',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '8px',
                padding: '0 18px',
                cursor: compiling ? 'not-allowed' : 'pointer',
                fontWeight: 700
              }}>
                {compiling ? <RotateCw className="pulse" size={16} /> : <Play size={16} />}
                {compiling ? 'Compiling' : 'Compile'}
              </button>
            </form>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
              <span style={{ fontSize: '11px', color: '#666666' }}>Try examples:</span>
              {[
                'Build me a restaurant app',
                'Build me a hospital management system',
                'Build me an ecommerce platform'
              ].map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => setPrompt(ex)}
                  style={{
                    backgroundColor: '#1E1E1E',
                    border: '1px solid #2E2E2E',
                    borderRadius: '4px',
                    color: '#A3A3A3',
                    padding: '4px 8px',
                    fontSize: '11px',
                    cursor: 'pointer',
                    fontFamily: 'inherit',
                    transition: 'all 0.2s'
                  }}
                >
                  {ex.replace('Build me a ', '').replace('Build me an ', '')}
                </button>
              ))}
            </div>
            {error && <p style={{ color: '#EF4444', fontSize: 12, marginTop: 10 }}>{error}</p>}
          </div>

          <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: 8, padding: 16 }}>
            <p style={{ color: '#666666', fontSize: 11, textTransform: 'uppercase' }}>Current Architecture Brief</p>
            <h3 style={{ fontSize: 18, marginTop: 8 }}>{domain}</h3>
            <p style={{ color: '#888888', fontSize: 13, marginTop: 4 }}>{subdomain}</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 14 }}>
              <span style={pillStyle}>{actors.length} actors</span>
              <span style={pillStyle}>{entities.length} entities</span>
              <span style={pillStyle}>{workflows.length} workflows</span>
              <span style={pillStyle}>{businessRules.length} business rules</span>
            </div>
          </div>
        </div>
      </section>

      {loading && !project ? (
        <div style={{ ...cardStyle, padding: 24, textAlign: 'center', color: '#888888' }}>Loading current project...</div>
      ) : !project || !report ? (
        <EmptyArchitectState onNavigate={onNavigate} />
      ) : (
        <>
          {/* Pipeline Navigation Bar */}
          <section style={{ ...cardStyle, padding: '14px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
              {pipelineSteps.map((step, index) => {
                const Icon = step.icon;
                const isCurrent = step.tab === 'ai-architect';
                return (
                  <React.Fragment key={step.tab}>
                    <button
                      onClick={() => onNavigate?.(step.tab)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 7,
                        background: isCurrent ? 'rgba(0,112,243,0.12)' : 'transparent',
                        border: isCurrent ? '1px solid rgba(0,112,243,0.3)' : '1px solid transparent',
                        borderRadius: 6,
                        color: isCurrent ? '#FFFFFF' : step.done ? '#10B981' : '#555555',
                        padding: '7px 13px',
                        cursor: 'pointer',
                        fontSize: 12,
                        fontWeight: isCurrent ? 700 : 500,
                        fontFamily: 'inherit'
                      }}
                    >
                      {step.done && !isCurrent
                        ? <CheckCircle2 size={14} color="#10B981" />
                        : <Icon size={14} />
                      }
                      {step.label}
                    </button>
                    {index < pipelineSteps.length - 1 && (
                      <ArrowRight size={14} style={{ color: '#333333', margin: '0 4px' }} />
                    )}
                  </React.Fragment>
                );
              })}
              <div style={{ flexGrow: 1 }} />
              {confidenceScore !== null && (
                <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
                  <span style={{ color: '#10B981' }}>
                    Confidence: <strong>{confidenceScore}%</strong>
                  </span>
                  <span style={{ color: '#F59E0B' }}>
                    Ambiguity: <strong>{ambiguityPct}%</strong>
                  </span>
                </div>
              )}
            </div>
          </section>

          {/* Quick Actions Panel */}
          <section style={{ ...cardStyle, padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Sparkles size={16} color="#0070F3" />
              <span style={{ fontSize: 13, fontWeight: 700, color: '#FFFFFF' }}>Compilation Successful: Quick Actions</span>
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button
                onClick={() => onNavigate?.('architecture')}
                style={{
                  backgroundColor: '#1E1E1E',
                  border: '1px solid #333333',
                  borderRadius: 6,
                  color: '#FFFFFF',
                  padding: '8px 14px',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  transition: 'all 0.2s'
                }}
              >
                <Network size={14} color="#0070F3" />
                View Architecture
              </button>
              <button
                onClick={() => onNavigate?.('compiler')}
                style={{
                  backgroundColor: '#1E1E1E',
                  border: '1px solid #333333',
                  borderRadius: 6,
                  color: '#FFFFFF',
                  padding: '8px 14px',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  transition: 'all 0.2s'
                }}
              >
                <Cpu size={14} color="#10B981" />
                View Generated Contracts
              </button>
              <button
                onClick={() => onNavigate?.('validation')}
                style={{
                  backgroundColor: '#1E1E1E',
                  border: '1px solid #333333',
                  borderRadius: 6,
                  color: '#FFFFFF',
                  padding: '8px 14px',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  transition: 'all 0.2s'
                }}
              >
                <ShieldCheck size={14} color="#F59E0B" />
                View Validation Report
              </button>
              <button
                onClick={() => onNavigate?.('compiler-final-contract')}
                style={{
                  backgroundColor: '#0070F3',
                  border: 'none',
                  borderRadius: 6,
                  color: '#FFFFFF',
                  padding: '8px 14px',
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  transition: 'background-color 0.2s'
                }}
              >
                <FileText size={14} />
                View Final Contract
              </button>
            </div>
          </section>

          {/* Actors / Entities / Workflows */}
          <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            <SummaryPanel title="Detected Actors" items={actors} icon={<CheckCircle2 size={16} color="#10B981" />} />
            <SummaryPanel title="Detected Entities" items={entities} icon={<Sparkles size={16} color="#0070F3" />} />
            <SummaryPanel title="Detected Workflows" items={workflows} icon={<GitBranch size={16} color="#F59E0B" />} />
          </section>

          {/* Confidence Explanation + Ambiguity Classification */}
          <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Confidence Explanation */}
            <div style={{ ...cardStyle, padding: 18 }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 15, marginBottom: 14 }}>
                <CheckCircle2 size={17} color="#10B981" /> Confidence Explanation
                {confidenceScore !== null && (
                  <span style={{ marginLeft: 'auto', fontSize: 22, fontWeight: 700, color: confidenceScore >= 70 ? '#10B981' : '#F59E0B' }}>
                    {confidenceScore}%
                  </span>
                )}
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {confidenceLines.map((line, i) => (
                  <div key={i} style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 8,
                    backgroundColor: '#0A0A0A',
                    border: '1px solid #1E1E1E',
                    borderRadius: 8,
                    padding: '10px 12px',
                    fontSize: 12,
                    color: '#D4D4D4',
                    lineHeight: 1.5
                  }}>
                    <CheckCircle2 size={13} color="#10B981" style={{ flexShrink: 0, marginTop: 1 }} />
                    {line}
                  </div>
                ))}
              </div>
            </div>

            {/* Ambiguity Classification */}
            <div style={{ ...cardStyle, padding: 18 }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 15, marginBottom: 14 }}>
                <AlertTriangle size={17} color="#F59E0B" /> Ambiguity Classification
                {ambiguityPct !== null && (
                  <span style={{ marginLeft: 'auto', fontSize: 22, fontWeight: 700, color: ambiguityPct > 40 ? '#EF4444' : '#F59E0B' }}>
                    {ambiguityPct}%
                  </span>
                )}
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {ambiguities.length > 0 ? ambiguities.map((item, i) => (
                  <div key={i} style={{
                    backgroundColor: '#0A0A0A',
                    border: '1px solid #1E1E1E',
                    borderRadius: 8,
                    padding: '10px 12px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontSize: 12, fontWeight: 700, color: '#FFFFFF' }}>{item.category}</span>
                      <span style={{ fontSize: 11, fontWeight: 700, color: severityColor(item.severity) }}>{item.severity}</span>
                    </div>
                    <p style={{ fontSize: 11, color: '#888888', lineHeight: 1.5, margin: 0 }}>{item.issue}</p>
                  </div>
                )) : (
                  <p style={{ color: '#666666', fontSize: 12 }}>No significant ambiguities detected.</p>
                )}
              </div>
            </div>
          </section>

          {/* Missing Requirements + Clarification Questions */}
          <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <FindingPanel
              title="Missing Requirements"
              icon={<AlertTriangle size={17} color="#F59E0B" />}
              items={(report.missing_information || []).map((item) => ({
                title: item.category,
                body: item.description,
                level: item.impact
              }))}
              emptyText="No major missing requirements detected."
            />
            <FindingPanel
              title="Clarification Questions"
              icon={<CircleHelp size={17} color="#0070F3" />}
              items={(report.clarification_questions || []).map((item) => ({
                title: item.category,
                body: item.question,
                level: item.priority
              }))}
              emptyText="No clarification questions required."
            />
          </section>

          {/* Assumptions + Business Risks */}
          <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <FindingPanel
              title="Assumptions"
              icon={<Lightbulb size={17} color="#0070F3" />}
              items={(report.assumptions_made || []).map((item) => ({
                title: item.assumption,
                body: item.reason,
                level: item.risk_level
              }))}
              emptyText="No assumptions were needed."
            />
            <FindingPanel
              title="Business Risks"
              icon={<ShieldAlert size={17} color="#EF4444" />}
              items={(report.risks || []).map((item: any) => ({
                title: item.category || item.risk || 'Risk',
                body: item.explanation || item.mitigation || '',
                level: item.level || item.severity || 'LOW'
              }))}
              emptyText="No business risks detected."
            />
          </section>

          {/* Recommendations + Reasoning Trace */}
          <section style={{ display: 'grid', gridTemplateColumns: '0.9fr 1.1fr', gap: '16px' }}>
            <div style={{ ...cardStyle, padding: 18 }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 15 }}><Sparkles size={17} color="#0070F3" /> Recommendations</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 14 }}>
                {(recommendations.length ? recommendations : [report.recommended_architecture_strategy]).slice(0, 8).map((item, index) => (
                  <div key={`${item}-${index}`} style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: 8, padding: 12, color: '#D4D4D4', fontSize: 12, lineHeight: 1.5 }}>
                    {item}
                  </div>
                ))}
              </div>
            </div>
            <div style={{ ...cardStyle, padding: 18 }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 15 }}><GitBranch size={17} color="#0070F3" /> Reasoning Trace</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 14, maxHeight: 330, overflowY: 'auto' }}>
                {(report.reasoning_trace?.length ? report.reasoning_trace : (report.architecture_reasoning_trace || []).map((item: ArchitectureReasoningItem) => `${item.component}: ${item.reason}`)).map((step, index) => (
                  <div key={`${step}-${index}`} style={{ display: 'grid', gridTemplateColumns: '68px 1fr', gap: 10, backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: 8, padding: 11 }}>
                    <span style={{ color: '#0070F3', fontSize: 11, fontWeight: 700 }}>STEP {index + 1}</span>
                    <p style={{ color: '#D4D4D4', fontSize: 12, lineHeight: 1.5 }}>{step}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Generated Outputs / Contract Explorer */}
          <section style={{ ...cardStyle, padding: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <FileJson size={18} color="#0070F3" />
                <div>
                  <h3 style={{ fontSize: 16 }}>Generated Outputs</h3>
                  <p style={{ color: '#888888', fontSize: 12, marginTop: 3 }}>Open compiler artifacts directly from the architect workspace.</p>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {[
                  { label: 'View Architecture', action: () => onNavigate?.('architecture'), icon: <Network size={14} /> },
                  { label: 'View Contracts', action: () => onNavigate?.('compiler'), icon: <Cpu size={14} /> },
                  { label: 'Validation & Repair', action: () => onNavigate?.('validation'), icon: <Wrench size={14} /> },
                ].map((item) => (
                  <button
                    key={item.label}
                    onClick={item.action}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 7,
                      backgroundColor: '#0070F3',
                      border: '1px solid #0070F3',
                      color: '#FFFFFF',
                      borderRadius: 6,
                      padding: '9px 11px',
                      cursor: 'pointer',
                      fontSize: 12,
                      fontWeight: 700
                    }}
                  >
                    {item.icon}
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
              {outputButtons.map((item) => (
                <button
                  key={item.id}
                  onClick={() => openOutput(item.id)}
                  style={{
                    backgroundColor: item.id === jsonTarget ? '#0070F3' : '#0A0A0A',
                    border: '1px solid #1E1E1E',
                    color: '#FFFFFF',
                    borderRadius: 6,
                    padding: '8px 10px',
                    cursor: 'pointer',
                    fontSize: 12
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '280px minmax(0, 1fr)', gap: 14, alignItems: 'start' }}>
              <aside style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: 8, padding: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <FolderOpen size={16} color="#0070F3" />
                  <h4 style={{ fontSize: 13 }}>Project Files</h4>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 13 }}>
                  {projectFileGroups.map((group) => (
                    <div key={group.title}>
                      <div style={{ color: '#D4D4D4', fontSize: 12, fontWeight: 700, marginBottom: 7 }}>▼ {group.title}</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                        {group.files.map((file) => (
                          <button
                            key={file.name}
                            onClick={() => setJsonTarget(file.target)}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 7,
                              width: '100%',
                              textAlign: 'left',
                              backgroundColor: jsonTarget === file.target ? 'rgba(0,112,243,0.18)' : 'transparent',
                              border: '1px solid transparent',
                              color: jsonTarget === file.target ? '#FFFFFF' : '#A3A3A3',
                              borderRadius: 6,
                              padding: '7px 8px',
                              cursor: 'pointer',
                              fontSize: 12
                            }}
                          >
                            <FileText size={14} />
                            {file.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </aside>
              <JsonInspector title={jsonLabels[jsonTarget]} data={jsonData} filename={`${jsonTarget}.json`} />
            </div>
          </section>
        </>
      )}
    </div>
  );
};

const EmptyArchitectState = ({ onNavigate }: { onNavigate?: (tab: string) => void }) => (
  <section style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: 8, padding: 28, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
    <div>
      <h3 style={{ fontSize: 18 }}>Start with a requirement prompt</h3>
      <p style={{ color: '#888888', fontSize: 13, lineHeight: 1.7, marginTop: 10 }}>
        Try: <em>"Build me a restaurant app"</em>. GenesisAI will detect domain, actors, entities, 
        workflows, open questions, and produce the architecture contract.
      </p>
      <p style={{ color: '#666666', fontSize: 12, lineHeight: 1.6, marginTop: 10 }}>
        The compiler pipeline runs: Requirements Intelligence → Blueprint → System Design → 
        Validation → Repair → Final Contract.
      </p>
    </div>
    <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: 8, padding: 18 }}>
      <p style={{ color: '#666666', fontSize: 11, textTransform: 'uppercase', marginBottom: 14 }}>Compiler Workflow</p>
      {[
        { label: 'AI Architect', tab: 'ai-architect', icon: BrainCircuit, desc: 'Requirements intelligence & ambiguity detection' },
        { label: 'Architecture', tab: 'architecture', icon: Network, desc: 'Actors, entities, relationships, workflows' },
        { label: 'Generated Contracts', tab: 'compiler', icon: Cpu, desc: 'Schema bundle & master specification' },
        { label: 'Validation & Repair', tab: 'validation', icon: ShieldCheck, desc: 'Integrity scan & self-healing repair' },
      ].map((step, i, arr) => {
        const Icon = step.icon;
        return (
          <div key={step.tab}>
            <button
              onClick={() => onNavigate?.(step.tab)}
              style={{
                display: 'flex', alignItems: 'center', gap: 10, background: 'transparent',
                border: 'none', color: '#D4D4D4', cursor: 'pointer', padding: '8px 0',
                fontFamily: 'inherit', width: '100%', textAlign: 'left'
              }}
            >
              <div style={{ width: 30, height: 30, borderRadius: '50%', backgroundColor: 'rgba(0,112,243,0.1)', border: '1px solid rgba(0,112,243,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Icon size={14} color="#0070F3" />
              </div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{step.label}</div>
                <div style={{ fontSize: 11, color: '#666666' }}>{step.desc}</div>
              </div>
            </button>
            {i < arr.length - 1 && (
              <div style={{ width: 1, height: 12, backgroundColor: '#1E1E1E', marginLeft: 14 }} />
            )}
          </div>
        );
      })}
    </div>
  </section>
);

const SummaryPanel: React.FC<{ title: string; items: string[]; icon: React.ReactNode }> = ({ title, items, icon }) => (
  <div style={{ ...{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '8px' }, padding: 16 }}>
    <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>{icon} {title}</h3>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 12 }}>
      {items.length ? items.map((item) => <span key={item} style={pillStyle}>{item}</span>) : <span style={{ color: '#666666', fontSize: 12 }}>None detected yet</span>}
    </div>
  </div>
);

const FindingPanel: React.FC<{
  title: string;
  icon: React.ReactNode;
  items: Array<{ title: string; body: string; level: string }>;
  emptyText: string;
}> = ({ title, icon, items, emptyText }) => (
  <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '8px', padding: 18 }}>
    <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 15 }}>{icon} {title}</h3>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 14 }}>
      {items.length ? items.map((item, index) => (
        <div key={`${item.title}-${index}`} style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: 8, padding: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
            <strong style={{ color: '#FFFFFF', fontSize: 12, textTransform: 'capitalize' }}>{item.title}</strong>
            <span style={{ color: severityColor(item.level), fontSize: 11, fontWeight: 700 }}>{item.level}</span>
          </div>
          <p style={{ color: '#888888', fontSize: 12, lineHeight: 1.5, marginTop: 7 }}>{item.body}</p>
        </div>
      )) : <p style={{ color: '#666666', fontSize: 12 }}>{emptyText}</p>}
    </div>
  </div>
);
