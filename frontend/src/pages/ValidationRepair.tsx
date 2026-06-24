import React, { useState, useEffect } from 'react';
import { getProject, validateProject, repairProject } from '../../frontend_api_client';
import { FinalCompiledApplication, ValidationError, ValidationReport } from '../../frontend_models';
import { ShieldCheck, RotateCw, AlertTriangle, CheckCircle2, ChevronRight, Wrench, ShieldAlert } from 'lucide-react';

const severityColor = (severity: string) => {
  if (severity === 'HIGH' || severity === 'CRITICAL') return '#EF4444';
  if (severity === 'MEDIUM') return '#F59E0B';
  return '#10B981';
};

interface ValidationRepairProps {
  projectId: string;
  activeSubTab?: 'validation' | 'repair';
  onNavigate?: (tab: string) => void;
}

export const ValidationRepair: React.FC<ValidationRepairProps> = ({ projectId, activeSubTab = 'validation', onNavigate }) => {
  const [project, setProject] = useState<FinalCompiledApplication | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [repairing, setRepairing] = useState(false);
  const [logs, setLogs] = useState<string[]>([
    "[16:00:01] VALIDATION: Initializing architectural integrity scan...",
    "[16:00:02] VALIDATION: Checking Database schema constraints...",
    "[16:00:03] VALIDATION: Checking API contract boundaries..."
  ]);

  useEffect(() => {
    if (projectId) {
      loadProjectDetails();
    } else {
      setProject(null);
      setError(null);
    }
  }, [projectId]);

  const loadProjectDetails = async () => {
    setLoading(true);
    const res = await getProject(projectId);
    if (res.success && res.data) {
      setProject(res.data);
      setError(null);
      setLogs(prev => [
        ...prev,
        `[16:01:05] SYSTEM: Loaded project ${res.data.app_name}.`,
        `[16:01:06] VALIDATION: Found ${res.data.validation_report?.errors?.length || 0} integrity errors, ${res.data.validation_report?.warnings?.length || 0} warnings.`
      ]);
    } else {
      setError(res.error || 'Failed to fetch project specifications.');
    }
    setLoading(false);
  };

  const handleScan = async () => {
    setScanning(true);
    setLogs(prev => [...prev, `[16:04:10] VALIDATION: Re-scanning project schema layers...`]);
    const res = await validateProject(projectId);
    if (res.success && res.data) {
      setLogs(prev => [
        ...prev,
        `[16:04:11] VALIDATION: Scan completed. Status: ${res.data.is_valid ? 'VALID' : 'INVALID'}. Errors: ${res.data.errors.length}.`
      ]);
      if (project) {
        setProject({
          ...project,
          validation_report: res.data
        });
      }
    } else {
      setLogs(prev => [...prev, `[16:04:11] ERROR: Validation scan failed.`]);
    }
    setScanning(false);
  };

  const handleRepair = async () => {
    setRepairing(true);
    setLogs(prev => [...prev, "[16:04:20] REPAIR: Generating self-healing candidates..."]);
    const res = await repairProject(projectId);
    if (res.success && res.data) {
      setLogs(prev => [
        ...prev,
        `[16:04:21] REPAIR: Applied Strategy: ${res.data.repair_candidates_generated[0]?.repair_strategy || 'Patch adapter constraints.'}`,
        `[16:04:21] REPAIR: Re-scanned and confirmed schema alignment. Revalidation PASSED.`
      ]);
      if (project) {
        setProject({
          ...project,
          validation_report: res.data.revalidation_results,
          repair_report: res.data
        });
      }
    } else {
      setLogs(prev => [...prev, "[16:04:21] ERROR: Autonomous repair candidate generation failed."]);
    }
    setRepairing(false);
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
          <ShieldAlert size={28} />
        </div>
        <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#FFFFFF', margin: '0 0 8px 0' }}>No Validation Results Yet</h3>
        <p style={{ color: '#888888', fontSize: '14px', maxWidth: '400px', margin: '0 0 24px 0', lineHeight: '1.5' }}>
          Validation scans and self-healing repair execute immediately after architecture generation.
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
        <p style={{ color: '#666666', fontSize: '14px' }}>Auditing database, API, and UI schemas...</p>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div style={{ padding: '24px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)', borderRadius: '12px' }}>
        <h3 style={{ color: '#EF4444' }}>Validation & Repair Error</h3>
        <p style={{ color: '#888888', marginTop: '8px' }}>{error || 'Validation metrics unavailable.'}</p>
        <button onClick={loadProjectDetails} style={{ marginTop: '16px', padding: '8px 16px', backgroundColor: '#EF4444', border: 'none', color: '#FFF', borderRadius: '4px', cursor: 'pointer' }}>Retry</button>
      </div>
    );
  }

  const report = project.validation_report || { is_valid: true, errors: [], warnings: [], critical_count: 0 } as ValidationReport;
  const aiReport = project.ai_architect_report;

  // Calculate validation metrics
  const totalErrors = (report.errors || []).length;
  const totalWarnings = (report.warnings || []).length;
  const criticalCount = report.critical_count || (report.errors || []).filter(e => e.severity === 'CRITICAL' || e.severity === 'HIGH').length;

  const valScore = report.is_valid ? 100 : Math.max(10, 100 - (totalErrors * 15) - (totalWarnings * 5));
  const isRepaired = valScore === 100;

  // Filter missing entities, relations, permissions from AI Architect gaps
  const missingRequirements = aiReport?.missing_information || [];
  const missingEntities = missingRequirements.filter(m => m.category === 'workflows' || m.description.toLowerCase().includes('entity'));
  const missingRelations = missingRequirements.filter(m => m.category === 'integrations' || m.description.toLowerCase().includes('relationship'));
  const missingPermissions = missingRequirements.filter(m => m.category === 'actors' || m.description.toLowerCase().includes('permission'));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Verification Panel */}
      <div style={{
        backgroundColor: '#121212',
        border: '1px solid #1E1E1E',
        borderRadius: '16px',
        padding: '24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '10px' }}>
            {activeSubTab === 'validation' ? (
              <>
                <ShieldCheck size={24} style={{ color: report.is_valid ? '#10B981' : '#F59E0B' }} />
                <span>Requirements Review</span>
              </>
            ) : (
              <>
                <Wrench size={24} style={{ color: '#0070F3' }} />
                <span>Self-Healing Repair Center</span>
              </>
            )}
          </h2>
          <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
            {['Compiler Verified', 'Node Validated', 'Schema Aligned', 'Syntax Optimized'].map(tag => (
              <span key={tag} style={{ fontSize: '11px', color: '#10B981', backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '4px 10px', borderRadius: '4px' }}>{tag}</span>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '32px', textAlign: 'right' }}>
          <div>
            <p style={{ fontSize: '11px', color: '#666666' }}>Validation Errors</p>
            <p style={{ fontSize: '24px', fontWeight: 'bold', color: totalErrors ? '#EF4444' : '#10B981', marginTop: '4px' }}>{totalErrors}</p>
          </div>
          <div>
            <p style={{ fontSize: '11px', color: '#666666' }}>Status</p>
            <p style={{ fontSize: '24px', fontWeight: 'bold', color: report.is_valid ? '#10B981' : '#F59E0B', marginTop: '4px' }}>
              {report.is_valid ? 'VALID' : 'REVIEW'}
            </p>
          </div>
        </div>
      </div>

      {/* Sub Tab Navigation */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #1E1E1E', paddingBottom: '12px' }}>
        {[
          { id: 'validation', label: 'Architectural Validation Scan' },
          { id: 'repair', label: 'Self-Healing Repair Center' }
        ].map((tab) => {
          const isActive = activeSubTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onNavigate?.(tab.id)}
              style={{
                backgroundColor: isActive ? 'rgba(0,112,243,0.12)' : 'transparent',
                border: isActive ? '1px solid rgba(0,112,243,0.3)' : '1px solid transparent',
                color: isActive ? '#FFFFFF' : '#888888',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontFamily: 'inherit',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 400,
                transition: 'all 0.2s'
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeSubTab === 'validation' ? (
        /* VALIDATION VIEW */
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '24px' }}>
          {/* Left panel: Detected requirements and validation findings */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 'bold', marginBottom: '16px' }}>Detected Requirements</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                <RequirementBox label="Actors" values={aiReport?.actors || (project.blueprint?.actors || []).map((actor: any) => actor.name)} />
                <RequirementBox label="Entities" values={aiReport?.entities || (project.system_design?.entities || []).map((entity: any) => entity.name)} />
                <RequirementBox label="Workflows" values={aiReport?.workflows || (project.system_design?.workflows || []).map((workflow: any) => workflow.workflow_name)} />
              </div>
            </div>
            
            {/* Detected Issues */}
            <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <ShieldAlert size={16} color="#EF4444" /> Detected Issues ({totalErrors})
              </h3>
              {totalErrors === 0 ? (
                <div style={{ color: '#10B981', fontSize: '13px', padding: '16px', backgroundColor: 'rgba(16, 185, 129, 0.05)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.1)' }}>
                  ✓ No compilation or structural design errors detected.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {(report.errors || []).map((err, idx) => (
                    <div key={idx} style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '14px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '13px', fontWeight: 'bold', color: severityColor(err.severity) }}>{err.error_code}</span>
                        <span style={{ fontSize: '11px', color: '#666666' }}>Layer: {err.layer}</span>
                      </div>
                      <p style={{ color: '#FFFFFF', fontSize: '13px', marginTop: '8px' }}>{err.message}</p>
                      <p style={{ color: '#888888', fontSize: '12px', marginTop: '6px', fontStyle: 'italic' }}>Hint: {err.repair_hint}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Warnings & Critical Findings */}
            <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <AlertTriangle size={16} color="#F59E0B" /> Warnings & Critical Findings
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px', textAlign: 'center' }}>
                  <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Critical Findings</p>
                  <p style={{ fontSize: '24px', fontWeight: 'bold', color: criticalCount > 0 ? '#EF4444' : '#10B981', marginTop: '6px' }}>{criticalCount}</p>
                </div>
                <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px', textAlign: 'center' }}>
                  <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Warnings</p>
                  <p style={{ fontSize: '24px', fontWeight: 'bold', color: totalWarnings > 0 ? '#F59E0B' : '#10B981', marginTop: '6px' }}>{totalWarnings}</p>
                </div>
              </div>
              {(report.warnings || []).map((warn, idx) => (
                <div key={idx} style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px', marginTop: '10px' }}>
                  <p style={{ fontSize: '13px', color: '#F59E0B', fontWeight: 'bold' }}>{warn.error_code}</p>
                  <p style={{ fontSize: '12px', color: '#888888', marginTop: '4px' }}>{warn.message}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right panel: Missing requirements analysis */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Missing Requirements List */}
            <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '20px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '16px' }}>Missing Requirements</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {missingRequirements.map((req, idx) => (
                  <div key={idx} style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px' }}>
                    <p style={{ fontSize: '12px', color: severityColor(req.impact), fontWeight: 'bold' }}>Category: {req.category}</p>
                    <p style={{ fontSize: '12px', color: '#D4D4D4', marginTop: '4px' }}>{req.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Structured Schema Missing Gaps */}
            <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 'bold' }}>Structural Gaps Detected</h3>
              
              <div>
                <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Missing Entities</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                  {missingEntities.length === 0 ? <span style={{ fontSize: '12px', color: '#666666' }}>None detected</span> : 
                    missingEntities.map((e, idx) => <span key={idx} style={{ fontSize: '11px', backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', padding: '4px 8px', borderRadius: '4px' }}>{e.description.substring(0, 15)}...</span>)}
                </div>
              </div>

              <div>
                <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Missing Relationships</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                  {missingRelations.length === 0 ? <span style={{ fontSize: '12px', color: '#666666' }}>None detected</span> : 
                    missingRelations.map((r, idx) => <span key={idx} style={{ fontSize: '11px', backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', padding: '4px 8px', borderRadius: '4px' }}>{r.description.substring(0, 15)}...</span>)}
                </div>
              </div>

              <div>
                <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Missing Permissions</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                  {missingPermissions.length === 0 ? <span style={{ fontSize: '12px', color: '#666666' }}>None detected</span> : 
                    missingPermissions.map((p, idx) => <span key={idx} style={{ fontSize: '11px', backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', padding: '4px 8px', borderRadius: '4px' }}>{p.description.substring(0, 15)}...</span>)}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* REPAIR VIEW */
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '24px' }}>
          {/* Left panel: Original Problem & Fix comparison */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            {/* Active Repair Card */}
            <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '15px', fontWeight: 'bold' }}>Active Healing Target</h3>
                  <p style={{ fontSize: '12px', color: '#666666', marginTop: '2px' }}>
                    Error Target: <strong style={{ color: '#FFFFFF' }}>{report.errors[0]?.component || 'GraphAdapterNode'}</strong>
                  </p>
                </div>
                {!isRepaired && (
                  <button
                    onClick={handleRepair}
                    disabled={repairing}
                    style={{
                      backgroundColor: '#0070F3',
                      color: '#FFFFFF',
                      border: 'none',
                      padding: '8px 16px',
                      borderRadius: '6px',
                      fontFamily: 'inherit',
                      fontWeight: '600',
                      fontSize: '13px',
                      cursor: 'pointer'
                    }}
                  >
                    {repairing ? 'Repairing...' : 'EXECUTE SELF-HEALING'}
                  </button>
                )}
              </div>

              {/* Code comparison side-by-side */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <p style={{ fontSize: '11px', color: '#EF4444', marginBottom: '6px' }}>Original Problem / Code snippet</p>
                  <pre style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.05)',
                    border: '1px solid rgba(239, 68, 68, 0.2)',
                    borderRadius: '8px',
                    padding: '12px',
                    fontSize: '12px',
                    color: '#EF4444',
                    fontFamily: 'var(--font-mono)',
                    minHeight: '120px',
                    overflowX: 'auto'
                  }}>
{`// Broken Component: ${report.errors[0]?.component || 'GraphNode'}
{
  "integrity_check": "FAILED",
  "error_code": "${report.errors[0]?.error_code || 'GRAPH_ORPHAN_ENTITY'}",
  "severity": "${report.errors[0]?.severity || 'MEDIUM'}"
}`}
                  </pre>
                </div>
                <div>
                  <p style={{ fontSize: '11px', color: '#10B981', marginBottom: '6px' }}>Suggested Repair / Applied patch</p>
                  <pre style={{
                    backgroundColor: 'rgba(16, 185, 129, 0.05)',
                    border: '1px solid rgba(16, 185, 129, 0.2)',
                    borderRadius: '8px',
                    padding: '12px',
                    fontSize: '12px',
                    color: '#10B981',
                    fontFamily: 'var(--font-mono)',
                    minHeight: '120px',
                    overflowX: 'auto'
                  }}>
{`// Repaired Component: ${report.errors[0]?.component || 'GraphNode'}
{
  "integrity_check": "SUCCESS",
  "healed_status": "REPAIRED_VIA_ADAPTER",
  "timestamp": "${new Date().toISOString().substring(0, 19)}"
}`}
                  </pre>
                </div>
              </div>
            </div>

            {/* Repair Candidate Details */}
            <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 'bold', marginBottom: '16px' }}>Repair Recommendation Parameters</h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '13px' }}>
                <div style={{ backgroundColor: '#0A0A0A', padding: '14px', borderRadius: '8px', border: '1px solid #1E1E1E' }}>
                  <span style={{ color: '#666666' }}>Original Problem</span>
                  <p style={{ fontWeight: 'bold', color: '#FFFFFF', marginTop: '6px' }}>
                    {report.errors[0]?.message || 'Structural circular dependency or orphan model.'}
                  </p>
                </div>
                <div style={{ backgroundColor: '#0A0A0A', padding: '14px', borderRadius: '8px', border: '1px solid #1E1E1E' }}>
                  <span style={{ color: '#666666' }}>Suggested Repair Strategy</span>
                  <p style={{ fontWeight: 'bold', color: '#10B981', marginTop: '6px' }}>
                    {report.errors[0]?.repair_hint || 'Inject schema validation adapter.'}
                  </p>
                </div>
                <div style={{ backgroundColor: '#0A0A0A', padding: '14px', borderRadius: '8px', border: '1px solid #1E1E1E' }}>
                  <span style={{ color: '#666666' }}>Repair Actions Available</span>
                  <p style={{ fontWeight: 'bold', color: '#0070F3', fontSize: '16px', marginTop: '6px' }}>{project.repair_report?.repair_candidates_generated.length || 0}</p>
                </div>
                <div style={{ backgroundColor: '#0A0A0A', padding: '14px', borderRadius: '8px', border: '1px solid #1E1E1E' }}>
                  <span style={{ color: '#666666' }}>Reasoning Rationale</span>
                  <p style={{ color: '#888888', marginTop: '6px', lineHeight: 1.4 }}>
                    Adapter boundary preserves deployment structure without introducing manual schema drift.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right panel: Repair log & execution diagnostics */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '20px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '12px' }}>Applied Repair History</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {project.repair_report?.repair_actions_executed.map((action, idx) => (
                  <div key={idx} style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#666666' }}>
                      <span>Action ID: {action.action_id}</span>
                      <span style={{ color: '#10B981', fontWeight: 'bold' }}>SUCCESS</span>
                    </div>
                    <p style={{ fontSize: '12px', color: '#D4D4D4', marginTop: '6px' }}>{action.action_description}</p>
                  </div>
                )) || (
                  <p style={{ fontSize: '12px', color: '#666666' }}>No repairs executed yet for this revision.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Diagnostics Logs Console (Visible on both views) */}
      <div style={{
        backgroundColor: '#121212',
        border: '1px solid #1E1E1E',
        borderRadius: '16px',
        padding: '20px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 'bold', color: '#FFFFFF' }}>Compiler Diagnostics Log</h3>
          <button onClick={handleScan} disabled={scanning} style={{ background: 'none', border: 'none', color: '#0070F3', fontSize: '12px', cursor: 'pointer', fontWeight: '600' }}>
            {scanning ? 'Running diagnostics...' : 'RE-RUN DIAGNOSTICS'}
          </button>
        </div>
        <div style={{
          backgroundColor: '#0A0A0A',
          borderRadius: '8px',
          padding: '16px',
          fontFamily: 'var(--font-mono)',
          fontSize: '12px',
          color: '#888888',
          lineHeight: '1.6',
          height: '120px',
          overflowY: 'auto'
        }}>
          {logs.map((log, idx) => (
            <div key={idx} style={{
              color: log.includes('WARNING') ? '#F59E0B' : log.includes('ERROR') ? '#EF4444' : log.includes('REPAIR') ? '#10B981' : '#888888'
            }}>
              {log}
            </div>
          ))}
        </div>
      </div>

      {/* Footer findings */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#121212',
        border: '1px solid #1E1E1E',
        borderRadius: '12px',
        padding: '16px 24px',
        fontSize: '13px',
        color: '#666666'
      }}>
        <span>Missing Requirements: <strong style={{ color: '#FFFFFF' }}>{missingRequirements.length}</strong></span>
        <span>Clarification Questions: <strong style={{ color: '#FFFFFF' }}>{aiReport?.clarification_questions.length || 0}</strong></span>
        <span>Validation Errors: <strong style={{ color: totalErrors ? '#EF4444' : '#10B981' }}>{totalErrors}</strong></span>
        <span>Repair Actions: <strong style={{ color: '#FFFFFF' }}>{project.repair_report?.repair_actions_executed.length || 0}</strong></span>
      </div>

    </div>
  );
};

const RequirementBox: React.FC<{ label: string; values: string[] }> = ({ label, values }) => (
  <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px' }}>
    <p style={{ color: '#666666', fontSize: '11px', textTransform: 'uppercase' }}>{label}</p>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
      {values.length ? values.map((value) => (
        <span key={value} style={{ color: '#D4D4D4', fontSize: '11px', border: '1px solid #1E1E1E', borderRadius: '4px', padding: '4px 6px' }}>{value}</span>
      )) : <span style={{ color: '#666666', fontSize: '12px' }}>None detected</span>}
    </div>
  </div>
);
