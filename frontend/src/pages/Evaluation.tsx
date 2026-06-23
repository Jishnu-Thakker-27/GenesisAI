import React from 'react';
import { LineChart, RotateCw, CheckCircle2, ShieldCheck, DollarSign } from 'lucide-react';

export const Evaluation: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Banner */}
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
            <LineChart size={24} style={{ color: '#0070F3' }} />
            <span>Cost vs Quality Evaluation</span>
          </h2>
          <p style={{ fontSize: '13px', color: '#666666', marginTop: '6px' }}>Assess performance index, system footprint, and cloud resource cost projections.</p>
        </div>
      </div>

      {/* Grid of stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '24px'
      }}>
        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px' }}>
          <p style={{ fontSize: '13px', color: '#666666' }}>Average Compilation Latency</p>
          <h4 style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '8px', color: '#FFFFFF' }}>1200ms</h4>
          <span style={{ fontSize: '11px', color: '#10B981', display: 'block', marginTop: '8px' }}>Within optimal threshold limits</span>
        </div>

        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px' }}>
          <p style={{ fontSize: '13px', color: '#666666' }}>Execution Cost Projection</p>
          <h4 style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '8px', color: '#10B981' }}>$0.0015 <span style={{ fontSize: '12px', color: '#888888', fontWeight: 'normal' }}>/ Evolve Run</span></h4>
          <span style={{ fontSize: '11px', color: '#10B981', display: 'block', marginTop: '8px' }}>99.2% cost reduction compared to manual dev</span>
        </div>

        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px' }}>
          <p style={{ fontSize: '13px', color: '#666666' }}>Overall Quality Rating</p>
          <h4 style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '8px', color: '#0070F3' }}>A+ Stable</h4>
          <span style={{ fontSize: '11px', color: '#10B981', display: 'block', marginTop: '8px' }}>Passed all 121 regression test audits</span>
        </div>
      </div>

      {/* Latency and footprint analysis cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1.5fr 1fr',
        gap: '24px'
      }}>
        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '16px' }}>Latency Logs Graph</h3>
          <div style={{ height: '200px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', padding: '20px 0', borderBottom: '1px solid #1E1E1E' }}>
            <div style={{ height: '40%', width: '12%', backgroundColor: '#0070F3', borderRadius: '4px 4px 0 0' }}></div>
            <div style={{ height: '35%', width: '12%', backgroundColor: '#0070F3', borderRadius: '4px 4px 0 0' }}></div>
            <div style={{ height: '60%', width: '12%', backgroundColor: '#0070F3', borderRadius: '4px 4px 0 0' }}></div>
            <div style={{ height: '80%', width: '12%', backgroundColor: '#0070F3', borderRadius: '4px 4px 0 0' }}></div>
            <div style={{ height: '45%', width: '12%', backgroundColor: '#0070F3', borderRadius: '4px 4px 0 0' }}></div>
            <div style={{ height: '30%', width: '12%', backgroundColor: '#10B981', borderRadius: '4px 4px 0 0' }}></div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#666666', marginTop: '8px' }}>
            <span>Run 1</span>
            <span>Run 2</span>
            <span>Run 3</span>
            <span>Run 4</span>
            <span>Run 5</span>
            <span>Run 6 (Optimized)</span>
          </div>
        </div>

        <div style={{ backgroundColor: '#121212', border: '1px solid #1E1E1E', borderRadius: '16px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 'bold' }}>Resource Allocation Snapshot</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#888888' }}>Compiler DB Footprint</span>
              <strong>487 KB</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#888888' }}>Memory Consumption</span>
              <strong>12.4 MB</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#888888' }}>Active Thread count</span>
              <strong>2 Threads</strong>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};
