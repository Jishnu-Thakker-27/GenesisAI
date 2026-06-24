import React, { useEffect, useState } from 'react';
import { getProject } from '../../frontend_api_client';
import { FinalCompiledApplication } from '../../frontend_models';
import { JsonInspector } from '../components/JsonInspector';
import { ChevronRight, GitBranch, KeyRound, Network, RotateCw } from 'lucide-react';

interface ArchitectureMapProps {
  projectId: string;
  onNavigate?: (tab: string) => void;
}

const sectionOrder = [
  'overview',
  'actors',
  'entities',
  'relationships',
  'workflows',
  'permissions',
  'businessRules',
  'decisions',
  'json'
];

export const ArchitectureMap: React.FC<ArchitectureMapProps> = ({ projectId, onNavigate }) => {
  const [project, setProject] = useState<FinalCompiledApplication | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>(
    Object.fromEntries(sectionOrder.map((section) => [section, section !== 'json']))
  );

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
      setError(res.error || 'Failed to fetch architecture output.');
    }
    setLoading(false);
  };

  const toggle = (id: string) => setOpenSections((prev) => ({ ...prev, [id]: !prev[id] }));

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
          <Network size={28} />
        </div>
        <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#FFFFFF', margin: '0 0 8px 0' }}>No Architecture Generated Yet</h3>
        <p style={{ color: '#888888', fontSize: '14px', maxWidth: '400px', margin: '0 0 24px 0', lineHeight: '1.5' }}>
          The system architecture map is compiled automatically from your prompt requirements.
        </p>
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
        <p style={{ color: '#666666', fontSize: '14px' }}>Loading compiled architecture...</p>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div style={{ padding: '24px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)', borderRadius: '8px' }}>
        <h3 style={{ color: '#EF4444' }}>Architecture Loading Error</h3>
        <p style={{ color: '#888888', marginTop: '8px' }}>{error || 'Architecture unavailable.'}</p>
        <button onClick={loadProject} style={{ marginTop: '16px', padding: '8px 16px', backgroundColor: '#EF4444', border: 'none', color: '#FFF', borderRadius: '6px', cursor: 'pointer' }}>Retry</button>
      </div>
    );
  }

  const spec = project.system_design;
  const report = project.ai_architect_report;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <section style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '20px 22px' }}>
        <p style={{ color: '#666666', fontSize: 11, textTransform: 'uppercase' }}>Compiled Architecture</p>
        <h2 style={{ fontSize: 22, marginTop: 6 }}>{report.detected_domain || project.app_type}</h2>
        <p style={{ color: '#888888', fontSize: 13, marginTop: 5 }}>{project.prompt}</p>
      </section>

      <Collapsible title="Application Overview" id="overview" open={openSections.overview} onToggle={toggle}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          <OverviewTile label="Domain" value={report.detected_domain || project.app_type} />
          <OverviewTile label="Subdomain" value={report.detected_subdomain || 'Not specified'} />
          <OverviewTile label="App Name" value={project.app_name} />
          <OverviewTile label="Execution Mode" value={project.execution_mode} />
        </div>
      </Collapsible>

      <Collapsible title="Actors" id="actors" open={openSections.actors} onToggle={toggle}>
        <div style={gridStyle}>
          {spec.actors.map((actor: any) => (
            <ItemCard key={actor.name} title={actor.name} subtitle={actor.description} details={actor.permissions?.length ? `Permissions: ${actor.permissions.join(', ')}` : 'No direct permissions listed'} />
          ))}
        </div>
      </Collapsible>

      <Collapsible title="Entities" id="entities" open={openSections.entities} onToggle={toggle}>
        <div style={gridStyle}>
          {spec.entities.map((entity: any) => (
            <ItemCard
              key={entity.name}
              title={entity.name}
              subtitle={entity.description}
              details={`${entity.fields?.length || 0} fields: ${(entity.fields || []).slice(0, 5).map((field: any) => field.name).join(', ')}`}
            />
          ))}
        </div>
      </Collapsible>

      <Collapsible title="Relationships" id="relationships" open={openSections.relationships} onToggle={toggle}>
        <div style={gridStyle}>
          {spec.relationships.map((relationship: any) => (
            <ItemCard
              key={relationship.relationship_id}
              title={`${relationship.source_entity} → ${relationship.target_entity}`}
              subtitle={relationship.description}
              details={relationship.relationship_type}
            />
          ))}
        </div>
      </Collapsible>

      <Collapsible title="Workflows" id="workflows" open={openSections.workflows} onToggle={toggle}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {spec.workflows.map((workflow: any) => (
            <div key={workflow.workflow_id} style={cardInnerStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                <strong>{workflow.workflow_name}</strong>
                <span style={{ color: '#F59E0B', fontSize: 11 }}>{workflow.criticality}</span>
              </div>
              <p style={{ color: '#888888', fontSize: 12, marginTop: 6 }}>{workflow.description}</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, marginTop: 10 }}>
                {(workflow.workflow_steps || []).map((step: string) => <span key={step} style={pillStyle}>{step}</span>)}
              </div>
            </div>
          ))}
        </div>
      </Collapsible>

      <Collapsible title="Permissions" id="permissions" open={openSections.permissions} onToggle={toggle}>
        <div style={gridStyle}>
          {spec.permissions.map((permission: any) => (
            <ItemCard
              key={permission.role}
              title={permission.role}
              subtitle={permission.reason}
              details={(permission.permissions || []).join(', ') || 'No permission actions listed'}
              icon={<KeyRound size={15} color="#0070F3" />}
            />
          ))}
        </div>
      </Collapsible>

      <Collapsible title="Business Rules" id="businessRules" open={openSections.businessRules} onToggle={toggle}>
        <div style={gridStyle}>
          {spec.business_rules.map((rule: any) => (
            <ItemCard key={rule.rule_id} title={rule.rule} subtitle={rule.enforcement_logic || rule.description} details={`Affects: ${(rule.affected_entities || []).join(', ')}`} />
          ))}
        </div>
      </Collapsible>

      <Collapsible title="Design Decisions" id="decisions" open={openSections.decisions} onToggle={toggle}>
        <div style={gridStyle}>
          {spec.design_decisions.map((decision: any) => (
            <ItemCard
              key={decision.decision_id}
              title={decision.decision}
              subtitle={decision.reason}
              details={`Affected: ${(decision.affected_components || []).join(', ')}`}
              icon={<GitBranch size={15} color="#0070F3" />}
            />
          ))}
        </div>
      </Collapsible>

      <Collapsible title="Secondary Graph Data / JSON" id="json" open={openSections.json} onToggle={toggle}>
        <JsonInspector title="Master Specification" data={spec} filename="master-specification.json" />
      </Collapsible>
    </div>
  );
};

const Collapsible: React.FC<{
  title: string;
  id: string;
  open: boolean;
  onToggle: (id: string) => void;
  children: React.ReactNode;
}> = ({ title, id, open, onToggle, children }) => (
  <section style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '8px', overflow: 'hidden' }}>
    <button
      onClick={() => onToggle(id)}
      style={{
        width: '100%',
        background: '#161616',
        border: 'none',
        borderBottom: open ? '1px solid #1E1E1E' : 'none',
        color: '#FFFFFF',
        padding: '14px 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        cursor: 'pointer',
        fontFamily: 'inherit'
      }}
    >
      <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700 }}>
        <Network size={15} color="#0070F3" /> {title}
      </span>
      <ChevronRight size={16} style={{ transform: open ? 'rotate(90deg)' : 'rotate(0deg)' }} />
    </button>
    {open && <div style={{ padding: 16 }}>{children}</div>}
  </section>
);

const OverviewTile: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div style={cardInnerStyle}>
    <p style={{ color: '#666666', fontSize: 11, textTransform: 'uppercase' }}>{label}</p>
    <p style={{ color: '#FFFFFF', fontSize: 14, fontWeight: 700, marginTop: 6 }}>{value}</p>
  </div>
);

const ItemCard: React.FC<{ title: string; subtitle?: string; details?: string; icon?: React.ReactNode }> = ({ title, subtitle, details, icon }) => (
  <div style={cardInnerStyle}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      {icon}
      <strong style={{ fontSize: 13 }}>{title}</strong>
    </div>
    {subtitle && <p style={{ color: '#888888', fontSize: 12, lineHeight: 1.5, marginTop: 7 }}>{subtitle}</p>}
    {details && <p style={{ color: '#666666', fontSize: 11, lineHeight: 1.5, marginTop: 7 }}>{details}</p>}
  </div>
);

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
  gap: 12
};

const cardInnerStyle: React.CSSProperties = {
  backgroundColor: '#0A0A0A',
  border: '1px solid #1E1E1E',
  borderRadius: '8px',
  padding: '13px'
};

const pillStyle: React.CSSProperties = {
  backgroundColor: '#121212',
  border: '1px solid #1E1E1E',
  borderRadius: '6px',
  padding: '5px 8px',
  color: '#D4D4D4',
  fontSize: 11
};
