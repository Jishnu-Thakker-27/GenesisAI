import React, { useState, useEffect } from 'react';
import { getDashboard, compileProject, getProject } from '../../frontend_api_client';
import { DashboardScreen, FinalCompiledApplication } from '../../frontend_models';
import { Search, ChevronRight, Play, CheckCircle2, RotateCw } from 'lucide-react';

interface DashboardProps {
  currentProjectId: string;
  onViewSpec: (projectId: string) => void;
  onSetProjectId: (id: string) => void;
  onCompileStart: (prompt: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ currentProjectId, onViewSpec, onSetProjectId, onCompileStart }) => {  
  const [data, setData] = useState<DashboardScreen | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState('Build me a restaurant app');
  const [compiling, setCompiling] = useState(false);
  const [project, setProject] = useState<FinalCompiledApplication | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (currentProjectId) {
      loadProject(currentProjectId);
    }
  }, [currentProjectId]);

  const loadProject = async (id: string) => {
    const res = await getProject(id);
    if (res.success && res.data) {
      setProject(res.data);
    }
  };

  const loadDashboard = async () => {
    setLoading(true);
    const res = await getDashboard();
    if (res.success && res.data) {
      setData(res.data);
      setError(null);
      if (res.data.recent_projects && res.data.recent_projects.length > 0) {
        onSetProjectId(res.data.recent_projects[0].project_id);
      }
    } else {
      setError(res.error || 'Failed to fetch dashboard metrics.');
    }
    setLoading(false);
  };

  const handleCompile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setCompiling(true);
    onCompileStart(prompt);
    const res = await compileProject(prompt);
    if (res.success && res.data) {
      onSetProjectId(res.data.project_id);
      onViewSpec(res.data.project_id);
    } else {
      alert(res.error || 'Compilation failed.');
    }
    setCompiling(false);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px', flexDirection: 'column', gap: '16px' }}>
        <RotateCw className="pulse" size={48} style={{ color: '#0070F3' }} />
        <p style={{ color: '#666666', fontSize: '14px' }}>Loading operational workspace dashboard...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '24px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)', borderRadius: '12px' }}>
        <h3 style={{ color: '#EF4444' }}>System Dashboard Error</h3>
        <p style={{ color: '#888888', marginTop: '8px' }}>{error || 'Dashboard data unavailable.'}</p>
        <button onClick={loadDashboard} style={{ marginTop: '16px', padding: '8px 16px', backgroundColor: '#EF4444', border: 'none', color: '#FFF', borderRadius: '4px', cursor: 'pointer' }}>Retry</button>
      </div>
    );
  }

  // Dynamic metrics derived from project
  const valHealth = project?.validation_report?.is_valid ? 100 : Math.max(10, 100 - (project?.validation_report?.errors?.length || 0) * 15 - (project?.validation_report?.warnings?.length || 0) * 5);
  const missingActorDeduction = (project?.ai_architect_report?.missing_information?.filter(m => m.category === 'actors').length || 0) * 10;
  const missingEntityDeduction = (project?.ai_architect_report?.missing_information?.filter(m => m.category === 'workflows').length || 0) * 10;
  const integrityScore = project ? Math.max(10, Math.min(100, Math.round((valHealth + (project?.ai_architect_report?.confidence_scores?.architecture_confidence || 0.8) * 100) / 2) - missingActorDeduction - missingEntityDeduction)) : 98;

  const confidenceScore = project ? Math.round((project?.ai_architect_report?.confidence_scores?.overall_score || 0.9) * 100) : 94;

  const riskCount = project?.ai_architect_report?.risks?.length || 0;
  const missingCount = project?.ai_architect_report?.missing_information?.length || 0;
  const riskScore = project ? Math.min(100, Math.max(10, (riskCount * 15) + (missingCount * 8))) : 12;

  const valRate = project?.validation_report?.is_valid ? 100 : 70;
  const repRate = project?.repair_report ? (project.repair_report.revalidation_results.is_valid ? 100 : 50) : 100;
  const simRate = project ? Math.round(project.simulation_report?.success_rate || 97) : 97;
  const readinessScore = project ? Math.round((valRate + repRate + simRate) / 3) : 97;

  const isRepaired = valHealth === 100;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Banner Row: Evolution Input & Pipeline Flow */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '24px'
      }}>
        {/* Evolution Input Card */}
        <div style={{
          backgroundColor: '#121212',
          border: '1px solid #1E1E1E',
          borderRadius: '16px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>Describe Application Requirements</h3>
            <p style={{ fontSize: '13px', color: '#666666', marginBottom: '16px' }}>Compile natural language into actors, entities, workflows, validation findings, and final contracts.</p>
          </div>
          
          <form onSubmit={handleCompile} style={{ display: 'flex', gap: '12px', position: 'relative' }}>
            <div style={{ position: 'relative', flexGrow: 1 }}>
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Build me a restaurant app..."
                style={{
                  width: '100%',
                  backgroundColor: '#0A0A0A',
                  border: '1px solid #1E1E1E',
                  borderRadius: '8px',
                  color: '#FFFFFF',
                  padding: '12px 48px 12px 16px',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.2s'
                }}
              />
              <Search size={18} style={{ position: 'absolute', right: '16px', top: '50%', transform: 'translateY(-50%)', color: '#666666' }} />
            </div>
            <button
              type="submit"
              disabled={compiling}
              style={{
                backgroundColor: compiling ? '#1E1E1E' : '#0070F3',
                color: '#FFFFFF',
                border: 'none',
                padding: '0 20px',
                borderRadius: '8px',
                cursor: compiling ? 'not-allowed' : 'pointer',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              {compiling ? <RotateCw className="pulse" size={16} /> : <Play size={16} />}
              <span>{compiling ? 'Compiling' : 'Compile'}</span>
            </button>
          </form>
        </div>

        {/* Live Compiler Pipeline View */}
        <div style={{
          backgroundColor: '#121212',
          border: '1px solid #1E1E1E',
          borderRadius: '16px',
          padding: '24px'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '16px' }}>Live Compiler Pipeline</h3>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '16px' }}>
            {['Intent', 'Blueprint', 'Design', 'Schema', 'Validate', 'Repair', 'Simulate', 'Evaluate', 'Evolve'].map((stage, idx) => (
              <React.Fragment key={stage}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: idx <= 4 ? '#0070F3' : '#1E1E1E',
                    border: idx === 4 ? '2px solid #FFFFFF' : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    color: '#FFFFFF'
                  }}>
                    {idx < 4 ? '✓' : idx + 1}
                  </div>
                  <span style={{ fontSize: '11px', color: idx <= 4 ? '#FFFFFF' : '#666666', fontWeight: idx === 4 ? 'bold' : 'normal' }}>{stage}</span>
                </div>
                {idx < 8 && <ChevronRight size={14} style={{ color: idx < 4 ? '#0070F3' : '#1E1E1E', marginBottom: '20px' }} />}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Grid: Radial Score Card & Metrics List */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '320px 1fr',
        gap: '24px'
      }}>
        {/* Integrity Score Radial Panel */}
        <div style={{
          backgroundColor: '#121212',
          border: '1px solid #1E1E1E',
          borderRadius: '16px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          justifyContent: 'space-between'
        }}>
          <h3 style={{ fontSize: '14px', color: '#888888', fontWeight: '500' }}>Compiler Findings</h3>
          
          <div style={{ position: 'relative', width: '140px', height: '140px', margin: '20px 0' }}>
            <div style={{
              width: '100%',
              height: '100%',
              borderRadius: '50%',
              background: `conic-gradient(#10B981 0% ${integrityScore}%, #1E1E1E ${integrityScore}% 100%)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <div style={{
                width: '112px',
                height: '112px',
                borderRadius: '50%',
                backgroundColor: '#121212',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ fontSize: '28px', fontWeight: 'bold', color: '#10B981' }}>{missingCount}</span>
                <span style={{ fontSize: '10px', color: '#666666', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Gaps</span>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '20px', width: '100%' }}>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: '11px', color: '#666666' }}>Validation</p>
              <p style={{ fontSize: '14px', fontWeight: 'bold', color: '#10B981', marginTop: '2px' }}>
                {project?.validation_report?.is_valid ? 'Valid' : 'Review'}
              </p>
            </div>
            <div style={{ flex: 1, borderLeft: '1px solid #1E1E1E' }}>
              <p style={{ fontSize: '11px', color: '#666666' }}>Questions</p>
              <p style={{ fontSize: '14px', fontWeight: 'bold', color: '#10B981', marginTop: '2px' }}>
                {project?.ai_architect_report?.clarification_questions.length || 0}
              </p>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '24px'
        }}>
          {/* Card 1 */}
          <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontSize: '13px', color: '#666666' }}>Detected Domain</p>
              <h4 style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '8px' }}>
                {project?.ai_architect_report?.detected_domain || 'No compile yet'}
              </h4>
            </div>
            <div style={{ height: '4px', backgroundColor: '#1E1E1E', borderRadius: '2px', overflow: 'hidden', marginTop: '16px' }}>
              <div style={{ width: project ? '100%' : '0%', height: '100%', backgroundColor: '#0070F3' }}></div>
            </div>
          </div>

          {/* Card 2 */}
          <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontSize: '13px', color: '#666666' }}>Validation Findings</p>
              <h4 style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '8px', color: isRepaired ? '#10B981' : '#F59E0B' }}>
                {project?.validation_report?.errors.length || 0} errors{' '}
                <span style={{ fontSize: '12px', color: '#888888', fontWeight: 'normal' }}>
                  ({project?.validation_report?.warnings.length || 0} warnings)
                </span>
              </h4>
            </div>
            <div style={{ height: '4px', backgroundColor: '#1E1E1E', borderRadius: '2px', overflow: 'hidden', marginTop: '16px' }}>
              <div style={{ width: `${valHealth}%`, height: '100%', backgroundColor: isRepaired ? '#10B981' : '#F59E0B' }}></div>
            </div>
          </div>

          {/* Card 3 */}
          <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontSize: '13px', color: '#666666' }}>Requirement Gaps</p>
              <h4 style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '8px', color: riskScore > 50 ? '#EF4444' : riskScore > 25 ? '#F59E0B' : '#10B981' }}>
                {missingCount}{' '}
                <span style={{ fontSize: '12px', fontWeight: 'normal', color: '#888888' }}>
                  ({riskCount} risks)
                </span>
              </h4>
            </div>
            <div style={{ height: '4px', backgroundColor: '#1E1E1E', borderRadius: '2px', overflow: 'hidden', marginTop: '16px' }}>
              <div style={{ width: `${riskScore}%`, height: '100%', backgroundColor: riskScore > 50 ? '#EF4444' : riskScore > 25 ? '#F59E0B' : '#10B981' }}></div>
            </div>
          </div>

          {/* Card 4 */}
          <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontSize: '13px', color: '#666666' }}>Generated Architecture</p>
              <h4 style={{ fontSize: '18px', fontWeight: 'bold', marginTop: '8px', color: '#FFFFFF' }}>
                {(project?.system_design?.entities?.length || 0)} entities, {(project?.system_design?.workflows?.length || 0)} workflows
              </h4>
              <p style={{ fontSize: '11px', color: '#666666', marginTop: '2px' }}>Target: {project?.app_type || 'Microservice API'}</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '16px', fontSize: '12px', color: '#10B981' }}>
              <CheckCircle2 size={14} />
              <span>Derived from compiled contract</span>
            </div>
          </div>
        </div>
      </div>

      {/* Row: Active AST & Recent Repositories / History */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1.2fr',
        gap: '24px'
      }}>
        {/* Active AST Snapshot Card */}
        <div style={{
          backgroundColor: '#121212',
          border: '1px solid #1E1E1E',
          borderRadius: '16px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '16px' }}>Active AST Snapshot</h3>
          
          <pre style={{
            flexGrow: 1,
            backgroundColor: '#0A0A0A',
            border: '1px solid #1E1E1E',
            borderRadius: '8px',
            padding: '16px',
            fontSize: '12px',
            color: '#A9B2C3',
            overflow: 'auto',
            maxHeight: '260px'
          }}>
{project ? JSON.stringify({
  app_name: project.app_name,
  app_type: project.app_type,
  prompt_summary: project.prompt.substring(0, 60) + "...",
  actors: project.blueprint?.actors?.map((a: any) => a.name) || [],
  entities: project.system_design?.entities?.map((e: any) => e.name) || [],
  workflows: project.system_design?.workflows?.map((w: any) => w.workflow_name) || []
}, null, 2) : `{
  "actors": [
    {"type": "SuperAdmin", "scope": "Global"},
    {"type": "ProjectCompiler", "permissions": "Full"}
  ],
  "entities": [
    {"id": "Schema_Node_01", "relationship": "Many-to-Many"}
  ],
  "constraints": [
     "// 12 Active Validation Rules..."
  ]
}`}
          </pre>
          
          <button
            onClick={() => onViewSpec(project?.project_id || data.recent_projects[0]?.project_id || 'proj_01')}
            style={{
              marginTop: '16px',
              backgroundColor: 'transparent',
              border: '1px solid #0070F3',
              color: '#0070F3',
              padding: '12px',
              borderRadius: '8px',
              fontFamily: 'inherit',
              fontWeight: '600',
              fontSize: '13px',
              cursor: 'pointer',
              transition: 'background-color 0.2s',
              textAlign: 'center'
            }}
          >
            VIEW FULL SPECIFICATION
          </button>
        </div>

        {/* History / Recent Evolutions */}
        <div style={{
          backgroundColor: '#121212',
          border: '1px solid #1E1E1E',
          borderRadius: '16px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px'
        }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 'bold' }}>Evolution History</h3>
            <p style={{ fontSize: '12px', color: '#666666', marginTop: '2px' }}>Real-time audit log of compiled schema translations.</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {data.recent_projects.slice(0, 3).map((p, idx) => (
              <div key={p.project_id || idx} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                <div style={{ padding: '6px', backgroundColor: 'rgba(0, 112, 243, 0.1)', borderRadius: '6px', color: '#0070F3', fontSize: '11px', fontWeight: 'bold' }}>
                  {p.project_id.substring(5, 8).toUpperCase() || 'EVO'}
                </div>
                <div>
                  <p style={{ fontSize: '13px', fontWeight: 'bold' }}>
                    {p.prompt.substring(0, 45)}...{' '}
                    <span style={{ fontSize: '11px', color: p.final_status === 'SUCCESS' ? '#10B981' : '#EF4444', fontWeight: 'normal', marginLeft: '8px' }}>
                      {p.final_status}
                    </span>
                  </p>
                  <p style={{ fontSize: '12px', color: '#666666', marginTop: '2px' }}>
                    Created {p.created_at || 'Just now'}. {p.latency ? `Latency: ${p.latency.toFixed(0)}ms` : ''}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
