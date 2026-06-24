import React, { useEffect, useState } from 'react';
import { getAIArchitectReport } from '../../frontend_api_client';
import { AIArchitectReport } from '../../frontend_models';
import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  CircleHelp,
  GitBranch,
  Lightbulb,
  RotateCw,
  ShieldAlert,
  Target
} from 'lucide-react';

interface AIArchitectProps {
  projectId: string;
}

const scoreItems = [
  ['prompt_completeness', 'Prompt'],
  ['architecture_confidence', 'Architecture'],
  ['requirement_confidence', 'Requirements'],
  ['assumption_confidence', 'Assumptions'],
  ['overall_score', 'Overall']
] as const;

const severityColor = (severity: string) => {
  if (severity === 'HIGH') return '#EF4444';
  if (severity === 'MEDIUM') return '#F59E0B';
  return '#10B981';
};

const cardStyle: React.CSSProperties = {
  backgroundColor: '#121212',
  border: '1px solid #1E1E1E',
  borderRadius: '8px'
};

export const AIArchitect: React.FC<AIArchitectProps> = ({ projectId }) => {
  const [report, setReport] = useState<AIArchitectReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReport();
  }, [projectId]);

  const loadReport = async () => {
    setLoading(true);
    const res = await getAIArchitectReport(projectId);
    if (res.success && res.data) {
      setReport(res.data.report);
      setError(null);
    } else {
      setError(res.error || 'Failed to load AI architect report.');
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '420px', flexDirection: 'column', gap: '16px' }}>
        <RotateCw className="pulse" size={46} style={{ color: '#0070F3' }} />
        <p style={{ color: '#666666', fontSize: '14px' }}>Loading requirements intelligence...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div style={{ ...cardStyle, padding: '24px', borderColor: '#EF4444', backgroundColor: 'rgba(239, 68, 68, 0.08)' }}>
        <h3 style={{ color: '#EF4444', fontSize: '16px' }}>AI Architect loading error</h3>
        <p style={{ color: '#888888', marginTop: '8px', fontSize: '13px' }}>{error || 'Report unavailable.'}</p>
        <button onClick={loadReport} style={{ marginTop: '16px', padding: '8px 14px', backgroundColor: '#EF4444', border: 'none', color: '#FFFFFF', borderRadius: '6px', cursor: 'pointer' }}>Retry</button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <section style={{ ...cardStyle, padding: '22px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '8px', backgroundColor: 'rgba(0, 112, 243, 0.14)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0070F3' }}>
            <BrainCircuit size={24} />
          </div>
          <div>
            <h2 style={{ fontSize: '22px', fontWeight: 700, letterSpacing: 0 }}>AI Architect</h2>
            <p style={{ color: '#888888', fontSize: '13px', marginTop: '4px' }}>{report.recommended_architecture_strategy}</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ color: '#666666', fontSize: '12px' }}>MODE</span>
          <span style={{ backgroundColor: 'rgba(0, 112, 243, 0.14)', color: '#0070F3', border: '1px solid rgba(0, 112, 243, 0.35)', borderRadius: '6px', padding: '8px 10px', fontSize: '12px', fontWeight: 700 }}>{report.mode}</span>
          <span style={{ backgroundColor: 'rgba(245, 158, 11, 0.12)', color: '#F59E0B', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '6px', padding: '8px 10px', fontSize: '12px', fontWeight: 700 }}>
            Ambiguity {Math.round(report.ambiguity_score * 100)}%
          </span>
        </div>
      </section>

      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(130px, 1fr))', gap: '14px' }}>
        {scoreItems.map(([key, label]) => (
          <div key={key} style={{ ...cardStyle, padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#666666', fontSize: '12px' }}>
              <Target size={14} />
              <span>{label}</span>
            </div>
            <p style={{ fontSize: '24px', fontWeight: 700, marginTop: '10px', color: key === 'overall_score' ? '#0070F3' : '#FFFFFF' }}>
              {Math.round(report.confidence_scores[key] * 100)}%
            </p>
          </div>
        ))}
      </section>

      <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div style={{ ...cardStyle, padding: '20px' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '15px' }}><Lightbulb size={18} color="#0070F3" /> Assumptions</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
            {report.assumptions_made.map((item) => (
              <div key={item.assumption} style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
                  <strong style={{ fontSize: '13px' }}>{item.assumption}</strong>
                  <span style={{ color: severityColor(item.risk_level), fontSize: '11px', fontWeight: 700 }}>{Math.round(item.confidence * 100)}%</span>
                </div>
                <p style={{ color: '#888888', fontSize: '12px', marginTop: '8px', lineHeight: 1.5 }}>{item.reason}</p>
              </div>
            ))}
          </div>
        </div>

        <div style={{ ...cardStyle, padding: '20px' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '15px' }}><CircleHelp size={18} color="#0070F3" /> Clarification Questions</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
            {report.clarification_questions.map((item) => (
              <div key={item.question} style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
                  <p style={{ fontSize: '13px', lineHeight: 1.5 }}>{item.question}</p>
                  <span style={{ color: severityColor(item.priority), fontSize: '11px', fontWeight: 700 }}>{item.priority}</span>
                </div>
                <p style={{ color: '#666666', fontSize: '11px', marginTop: '6px' }}>{item.category}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ display: 'grid', gridTemplateColumns: '0.9fr 1.1fr', gap: '20px' }}>
        <div style={{ ...cardStyle, padding: '20px' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '15px' }}><ShieldAlert size={18} color="#F59E0B" /> Risk Analysis</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
            {report.risks.map((item) => (
              <div key={item.risk} style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '14px' }}>
                <p style={{ display: 'flex', alignItems: 'center', gap: '8px', color: severityColor(item.severity), fontSize: '12px', fontWeight: 700 }}>
                  <AlertTriangle size={14} /> {item.severity}
                </p>
                <p style={{ color: '#FFFFFF', fontSize: '13px', marginTop: '8px' }}>{item.risk}</p>
                <p style={{ color: '#888888', fontSize: '12px', marginTop: '8px', lineHeight: 1.5 }}>{item.mitigation}</p>
              </div>
            ))}
          </div>
        </div>

        <div style={{ ...cardStyle, padding: '20px' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '15px' }}><GitBranch size={18} color="#0070F3" /> Architecture Reasoning Trace</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '16px', maxHeight: '420px', overflowY: 'auto', paddingRight: '4px' }}>
            {report.architecture_reasoning_trace.map((item, index) => (
              <div key={`${item.component}-${index}`} style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '14px', backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '12px' }}>
                <div>
                  <p style={{ color: '#FFFFFF', fontSize: '13px', fontWeight: 700 }}>{item.component}</p>
                  <p style={{ color: '#0070F3', fontSize: '11px', marginTop: '4px' }}>{item.component_type}</p>
                </div>
                <p style={{ color: '#888888', fontSize: '12px', lineHeight: 1.5 }}>{item.reason}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ ...cardStyle, padding: '18px 20px', display: 'flex', alignItems: 'center', gap: '12px', color: '#10B981' }}>
        <CheckCircle2 size={18} />
        <span style={{ color: '#D4D4D4', fontSize: '13px' }}>{report.missing_information.length} missing requirement signals analyzed before blueprint generation.</span>
      </section>
    </div>
  );
};
