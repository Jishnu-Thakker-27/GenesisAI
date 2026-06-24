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
  BrainCircuit,
  CheckCircle2,
  CircleHelp,
  FileJson,
  GitBranch,
  Lightbulb,
  Play,
  RotateCw,
  ShieldAlert,
  Sparkles
} from 'lucide-react';

interface AIArchitectProps {
  projectId: string;
}

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

export const AIArchitect: React.FC<AIArchitectProps> = ({ projectId }) => {
  const [project, setProject] = useState<FinalCompiledApplication | null>(null);
  const [prompt, setPrompt] = useState('Build me a restaurant app');
  const [loading, setLoading] = useState(false);
  const [compiling, setCompiling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jsonTarget, setJsonTarget] = useState<'requirements' | 'blueprint' | 'spec' | 'validation' | 'repair' | 'contract'>('requirements');

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
      setPrompt(res.data.prompt || 'Build me a restaurant app');
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
  const domain = report?.detected_domain || project?.intent?.detected_domain || 'Awaiting compile';
  const subdomain = report?.detected_subdomain || project?.intent?.detected_subdomain || 'Describe an application to begin';
  const actors = report?.actors?.length ? report.actors : project?.blueprint?.actors?.map((actor: any) => actor.name) || [];
  const entities = report?.entities?.length ? report.entities : spec?.entities?.map((entity: any) => entity.name) || [];
  const workflows = report?.workflows?.length ? report.workflows : spec?.workflows?.map((workflow: any) => workflow.workflow_name) || [];
  const businessRules = spec?.business_rules || [];
  const reportAny = report as any;
  const recommendations = [
    ...(reportAny?.recommended_entities?.map((item: any) => `Entity: ${item.name} - ${item.reason}`) || []),
    ...(reportAny?.recommended_workflows?.map((item: any) => `Workflow: ${item.name} - ${item.reason}`) || []),
    ...(report?.confidence_explanation || [])
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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
                placeholder="Describe your application"
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
        <EmptyArchitectState />
      ) : (
        <>
          <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            <SummaryPanel title="Detected Actors" items={actors} icon={<CheckCircle2 size={16} color="#10B981" />} />
            <SummaryPanel title="Detected Entities" items={entities} icon={<Sparkles size={16} color="#0070F3" />} />
            <SummaryPanel title="Detected Workflows" items={workflows} icon={<GitBranch size={16} color="#F59E0B" />} />
          </section>

          <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <FindingPanel
              title="Missing Requirements"
              icon={<AlertTriangle size={17} color="#F59E0B" />}
              items={report.missing_information.map((item) => ({
                title: item.category,
                body: item.description,
                level: item.impact
              }))}
              emptyText="No major missing requirements detected."
            />
            <FindingPanel
              title="Clarification Questions"
              icon={<CircleHelp size={17} color="#0070F3" />}
              items={report.clarification_questions.map((item) => ({
                title: item.category,
                body: item.question,
                level: item.priority
              }))}
              emptyText="No clarification questions required."
            />
          </section>

          <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <FindingPanel
              title="Assumptions"
              icon={<Lightbulb size={17} color="#0070F3" />}
              items={report.assumptions_made.map((item) => ({
                title: item.assumption,
                body: item.reason,
                level: item.risk_level
              }))}
              emptyText="No assumptions were needed."
            />
            <FindingPanel
              title="Business Risks"
              icon={<ShieldAlert size={17} color="#EF4444" />}
              items={report.risks.map((item: any) => ({
                title: item.category || item.risk || 'Risk',
                body: item.explanation || item.mitigation || '',
                level: item.level || item.severity || 'LOW'
              }))}
              emptyText="No business risks detected."
            />
          </section>

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
                {(report.reasoning_trace?.length ? report.reasoning_trace : report.architecture_reasoning_trace.map((item: ArchitectureReasoningItem) => `${item.component}: ${item.reason}`)).map((step, index) => (
                  <div key={`${step}-${index}`} style={{ display: 'grid', gridTemplateColumns: '68px 1fr', gap: 10, backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: 8, padding: 11 }}>
                    <span style={{ color: '#0070F3', fontSize: 11, fontWeight: 700 }}>STEP {index + 1}</span>
                    <p style={{ color: '#D4D4D4', fontSize: 12, lineHeight: 1.5 }}>{step}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section style={{ ...cardStyle, padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <FileJson size={17} color="#0070F3" />
              <h3 style={{ fontSize: 15 }}>Generated Contracts</h3>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
              {[
                ['requirements', 'Requirements Report'],
                ['blueprint', 'Blueprint'],
                ['spec', 'Master Specification'],
                ['validation', 'Validation Report'],
                ['repair', 'Repair Report'],
                ['contract', 'Final Contract']
              ].map(([id, label]) => (
                <button
                  key={id}
                  onClick={() => setJsonTarget(id as typeof jsonTarget)}
                  style={{
                    backgroundColor: jsonTarget === id ? '#0070F3' : '#0A0A0A',
                    border: '1px solid #1E1E1E',
                    color: '#FFFFFF',
                    borderRadius: 6,
                    padding: '8px 10px',
                    cursor: 'pointer',
                    fontSize: 12
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
            <JsonInspector title={jsonTarget.replace('-', ' ')} data={jsonData} filename={`${jsonTarget}.json`} />
          </section>
        </>
      )}
    </div>
  );
};

const EmptyArchitectState = () => (
  <section style={{ ...cardStyle, padding: 24, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
    <div>
      <h3 style={{ fontSize: 18 }}>Start with a requirement prompt</h3>
      <p style={{ color: '#888888', fontSize: 13, lineHeight: 1.6, marginTop: 8 }}>
        Try: Build me a restaurant app. GenesisAI will detect domain, actors, entities, workflows, open questions, and produce the architecture contract.
      </p>
    </div>
    <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: 8, padding: 16 }}>
      <p style={{ color: '#666666', fontSize: 11, textTransform: 'uppercase' }}>Compiler Flow</p>
      <p style={{ color: '#D4D4D4', fontSize: 13, lineHeight: 1.8, marginTop: 8 }}>
        Prompt → Requirements Intelligence → Blueprint → System Design → Validation → Repair → Final Contract
      </p>
    </div>
  </section>
);

const SummaryPanel: React.FC<{ title: string; items: string[]; icon: React.ReactNode }> = ({ title, items, icon }) => (
  <div style={{ ...cardStyle, padding: 16 }}>
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
  <div style={{ ...cardStyle, padding: 18 }}>
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
