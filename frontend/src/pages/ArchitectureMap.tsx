import React, { useState, useEffect } from 'react';
import { getArchitecture } from '../../frontend_api_client';
import { ArchitectureMapScreen } from '../../frontend_models';
import { Network, Search, ShieldCheck, Activity, RotateCw, ZoomIn, ZoomOut, Maximize } from 'lucide-react';

interface ArchitectureMapProps {
  projectId: string;
}

export const ArchitectureMap: React.FC<ArchitectureMapProps> = ({ projectId }) => {
  const [data, setData] = useState<ArchitectureMapScreen | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>('Booking');
  const [zoom, setZoom] = useState(100);

  useEffect(() => {
    loadArchitecture();
  }, [projectId]);

  const loadArchitecture = async () => {
    setLoading(true);
    const res = await getArchitecture(projectId);
    if (res.success && res.data) {
      setData(res.data);
      setError(null);
    } else {
      setError(res.error || 'Failed to fetch architecture dependency graphs.');
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px', flexDirection: 'column', gap: '16px' }}>
        <RotateCw className="pulse" size={48} style={{ color: '#0070F3' }} />
        <p style={{ color: '#666666', fontSize: '14px' }}>Loading canvas layout nodes and edges...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '24px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)', borderRadius: '12px' }}>
        <h3 style={{ color: '#EF4444' }}>Architecture Canvas Loading Error</h3>
        <p style={{ color: '#888888', marginTop: '8px' }}>{error || 'Architecture graph map unavailable.'}</p>
        <button onClick={loadArchitecture} style={{ marginTop: '16px', padding: '8px 16px', backgroundColor: '#EF4444', border: 'none', color: '#FFF', borderRadius: '4px', cursor: 'pointer' }}>Retry</button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Main Grid: Node Inspector (left) - Graph Canvas (right) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '360px 1fr',
        gap: '24px'
      }}>
        
        {/* Left Control Column: Inspector & Health Metrics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Node Inspector Panel */}
          <div style={{
            backgroundColor: '#121212',
            border: '1px solid #1E1E1E',
            borderRadius: '16px',
            padding: '24px'
          }}>
            <h3 style={{ fontSize: '15px', fontWeight: 'bold', marginBottom: '16px' }}>Node Inspector</h3>
            
            <div style={{ backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', borderRadius: '8px', padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#FFFFFF' }}>{selectedNode}</span>
                <span style={{ fontSize: '10px', color: '#10B981', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>VERIFIED</span>
              </div>
              <p style={{ fontSize: '11px', color: '#666666', marginTop: '6px' }}>ID: ENT_88A2</p>

              <hr style={{ border: 'none', borderTop: '1px solid #1E1E1E', margin: '12px 0' }} />

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#666666' }}>Security Level</span>
                  <span style={{ color: '#10B981', fontWeight: 'bold' }}>STABLE</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#666666' }}>Adhered Components</span>
                  <span style={{ color: '#FFFFFF', fontWeight: 'bold' }}>12</span>
                </div>
              </div>
            </div>
          </div>

          {/* Architecture Integrity Card */}
          <div style={{
            backgroundColor: '#121212',
            border: '1px solid #1E1E1E',
            borderRadius: '16px',
            padding: '24px',
            display: 'flex',
            alignItems: 'center',
            gap: '20px'
          }}>
            <div style={{ position: 'relative', width: '80px', height: '80px', flexShrink: 0 }}>
              <div style={{
                width: '100%',
                height: '100%',
                borderRadius: '50%',
                background: 'conic-gradient(#0070F3 0% 82%, #1E1E1E 82% 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <div style={{ width: '64px', height: '64px', borderRadius: '50%', backgroundColor: '#121212', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px', fontWeight: 'bold' }}>
                  82%
                </div>
              </div>
            </div>
            <div>
              <h4 style={{ fontSize: '14px', fontWeight: 'bold' }}>Genetic Health Metrics</h4>
              <p style={{ fontSize: '12px', color: '#666666', marginTop: '2px' }}>System Status: EV-002-TRS</p>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginTop: '8px', fontSize: '11px', color: '#10B981' }}>
                <ShieldCheck size={12} />
                <span>92% Healthy (Passed All Audits)</span>
              </div>
            </div>
          </div>

          {/* Dependency Map Categories */}
          <div style={{
            backgroundColor: '#121212',
            border: '1px solid #1E1E1E',
            borderRadius: '16px',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <h4 style={{ fontSize: '14px', fontWeight: 'bold' }}>Dependency Maps</h4>
            
            <div>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Entity Map</p>
              <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                <span style={{ fontSize: '12px', backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', padding: '4px 8px', borderRadius: '4px' }}>bookings_table</span>
                <span style={{ fontSize: '12px', backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', padding: '4px 8px', borderRadius: '4px' }}>Schema_Integrity</span>
              </div>
            </div>

            <div>
              <p style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>API & UI Map</p>
              <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                <span style={{ fontSize: '12px', backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', padding: '4px 8px', borderRadius: '4px' }}>/bookings (POST)</span>
                <span style={{ fontSize: '12px', backgroundColor: '#0A0A0A', border: '1px solid #1E1E1E', padding: '4px 8px', borderRadius: '4px' }}>BookingForm</span>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: Visual Canvas editor */}
        <div style={{
          backgroundColor: '#121212',
          border: '1px solid #1E1E1E',
          borderRadius: '16px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          overflow: 'hidden',
          position: 'relative',
          height: '620px'
        }}>
          
          {/* Canvas Top Controls */}
          <div style={{
            padding: '16px 24px',
            borderBottom: '1px solid #1E1E1E',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            zIndex: 10
          }}>
            <h3 style={{ fontSize: '15px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Network size={18} style={{ color: '#0070F3' }} />
              <span>Visual Canvas Editor</span>
            </h3>
            <span style={{ fontSize: '11px', color: '#666666' }}>Validation: <strong style={{ color: '#10B981' }}>PASSED</strong> | Repair: <strong style={{ color: '#10B981' }}>STABLE</strong></span>
          </div>

          {/* Grid background / Node canvas space */}
          <div style={{
            flexGrow: 1,
            backgroundColor: '#0A0A0A',
            backgroundImage: 'radial-gradient(#1E1E1E 1px, transparent 1px)',
            backgroundSize: '20px 20px',
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden'
          }}>
            {/* Visualizing Nodes as custom HTML elements connected by flexbox and lines */}
            <div style={{
              display: 'flex',
              gap: '48px',
              alignItems: 'center',
              transform: `scale(${zoom / 100})`,
              transition: 'transform 0.2s'
            }}>
              
              <div 
                onClick={() => setSelectedNode('Admin')}
                style={{
                  backgroundColor: '#121212',
                  border: selectedNode === 'Admin' ? '2px solid #0070F3' : '1px solid #1E1E1E',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  cursor: 'pointer',
                  textAlign: 'center',
                  minWidth: '120px'
                }}
              >
                <div style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Actor</div>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginTop: '4px' }}>Admin</div>
              </div>

              <div style={{ width: '40px', height: '1px', backgroundColor: '#0070F3', position: 'relative' }}>
                <span style={{ position: 'absolute', right: 0, top: '-4px', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#0070F3' }}></span>
              </div>

              <div 
                onClick={() => setSelectedNode('/bookings')}
                style={{
                  backgroundColor: '#121212',
                  border: selectedNode === '/bookings' ? '2px solid #0070F3' : '1px solid #1E1E1E',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  cursor: 'pointer',
                  textAlign: 'center',
                  minWidth: '120px'
                }}
              >
                <div style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>API Route</div>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginTop: '4px' }}>/bookings</div>
              </div>

              <div style={{ width: '40px', height: '1px', backgroundColor: '#0070F3', position: 'relative' }}>
                <span style={{ position: 'absolute', right: 0, top: '-4px', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#0070F3' }}></span>
              </div>

              <div 
                onClick={() => setSelectedNode('Booking')}
                style={{
                  backgroundColor: '#121212',
                  border: selectedNode === 'Booking' ? '2px solid #0070F3' : '1px solid #1E1E1E',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  cursor: 'pointer',
                  textAlign: 'center',
                  minWidth: '120px'
                }}
              >
                <div style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>Entity</div>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginTop: '4px' }}>bookings_table</div>
              </div>

              <div style={{ width: '40px', height: '1px', backgroundColor: '#0070F3', position: 'relative' }}>
                <span style={{ position: 'absolute', right: 0, top: '-4px', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#0070F3' }}></span>
              </div>

              <div 
                onClick={() => setSelectedNode('BookingForm')}
                style={{
                  backgroundColor: '#121212',
                  border: selectedNode === 'BookingForm' ? '2px solid #0070F3' : '1px solid #1E1E1E',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  cursor: 'pointer',
                  textAlign: 'center',
                  minWidth: '120px'
                }}
              >
                <div style={{ fontSize: '11px', color: '#666666', textTransform: 'uppercase' }}>UI Component</div>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginTop: '4px' }}>BookingForm</div>
              </div>

            </div>

            {/* Bottom-left Canvas Utilities */}
            <div style={{
              position: 'absolute',
              bottom: '20px',
              left: '20px',
              display: 'flex',
              gap: '6px',
              backgroundColor: '#121212',
              border: '1px solid #1E1E1E',
              borderRadius: '6px',
              padding: '4px'
            }}>
              <button onClick={() => setZoom(prev => Math.max(prev - 10, 50))} style={{ background: 'none', border: 'none', color: '#FFFFFF', padding: '6px', cursor: 'pointer' }}><ZoomOut size={16} /></button>
              <button onClick={() => setZoom(100)} style={{ background: 'none', border: 'none', color: '#FFFFFF', padding: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}>{zoom}%</button>
              <button onClick={() => setZoom(prev => Math.min(prev + 10, 150))} style={{ background: 'none', border: 'none', color: '#FFFFFF', padding: '6px', cursor: 'pointer' }}><ZoomIn size={16} /></button>
              <button onClick={() => setZoom(100)} style={{ background: 'none', border: 'none', color: '#FFFFFF', padding: '6px', cursor: 'pointer' }}><Maximize size={16} /></button>
            </div>

            {/* Bottom-right Legend */}
            <div style={{
              position: 'absolute',
              bottom: '20px',
              right: '20px',
              backgroundColor: '#121212',
              border: '1px solid #1E1E1E',
              borderRadius: '8px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              fontSize: '11px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#0070F3' }}></span>
                <span style={{ color: '#888888' }}>Database Factor</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10B981' }}></span>
                <span style={{ color: '#888888' }}>API Endpoint</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#F59E0B' }}></span>
                <span style={{ color: '#888888' }}>UI Factor</span>
              </div>
            </div>

          </div>

          {/* Canvas Actions Footer */}
          <div style={{
            padding: '16px 24px',
            borderTop: '1px solid #1E1E1E',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '12px',
            backgroundColor: '#161616'
          }}>
            <button style={{
              backgroundColor: '#0070F3',
              color: '#FFFFFF',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '6px',
              fontFamily: 'inherit',
              fontWeight: '600',
              fontSize: '13px',
              cursor: 'pointer'
            }}>
              Trace Path
            </button>
            <button style={{
              backgroundColor: 'transparent',
              border: '1px solid #333333',
              color: '#FFFFFF',
              padding: '8px 16px',
              borderRadius: '6px',
              fontFamily: 'inherit',
              fontWeight: '600',
              fontSize: '13px',
              cursor: 'pointer'
            }}>
              View Schemas
            </button>
          </div>

        </div>

      </div>

    </div>
  );
};
