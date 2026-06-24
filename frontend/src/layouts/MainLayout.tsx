import React from 'react';
import { 
  LayoutDashboard, 
  Cpu, 
  Network, 
  ShieldCheck, 
  Wrench, 
  Play, 
  LineChart, 
  History, 
  Plus, 
  Search, 
  Bell, 
  Terminal,
  Settings,
  BookOpen,
  BrainCircuit
} from 'lucide-react';

interface MainLayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  currentProjectId: string;
  onNewEvolution: () => void;
  systemVersion: string;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  activeTab,
  setActiveTab,
  onNewEvolution,
  systemVersion
}) => {
  const menuItems = [
    { id: 'ai-architect', label: 'AI Architect', icon: BrainCircuit },
    { id: 'compiler', label: 'Contracts', icon: Cpu },
    { id: 'architecture', label: 'Architecture', icon: Network },
    { id: 'validation', label: 'Review', icon: ShieldCheck },
    { id: 'repair', label: 'Repair', icon: Wrench },
    { id: 'dashboard', label: 'Projects', icon: LayoutDashboard },
    { id: 'simulation', label: 'Simulation', icon: Play },
    { id: 'evaluation', label: 'Evaluation', icon: LineChart },
    { id: 'timeline', label: 'Timeline', icon: History }
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0A0A0A', color: '#FFFFFF', overflow: 'hidden' }}>
      {/* Sidebar Section */}
      <aside style={{
        width: '260px',
        backgroundColor: '#121212',
        borderRight: '1px solid #1E1E1E',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '24px 16px',
        flexShrink: 0
      }}>
        <div>
          {/* Logo Branding */}
          <div style={{ marginBottom: '32px', paddingLeft: '8px' }}>
            <h1 style={{ fontSize: '20px', fontWeight: 'bold', letterSpacing: '-0.5px', color: '#FFFFFF' }}>GenesisAI</h1>
            <p style={{ fontSize: '11px', color: '#666666', marginTop: '2px' }}>AI Application Compiler</p>
          </div>

          {/* Navigation Links */}
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    width: '100%',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    border: 'none',
                    backgroundColor: isActive ? '#0070F3' : 'transparent',
                    color: isActive ? '#FFFFFF' : '#888888',
                    fontFamily: 'inherit',
                    fontSize: '14px',
                    fontWeight: isActive ? 600 : 400,
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Primary Action Button */}
          <button
            onClick={onNewEvolution}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              width: '100%',
              backgroundColor: '#0070F3',
              color: '#FFFFFF',
              border: 'none',
              padding: '12px',
              borderRadius: '8px',
              fontFamily: 'inherit',
              fontWeight: '600',
              fontSize: '14px',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(0, 112, 243, 0.2)',
              transition: 'background-color 0.2s'
            }}
          >
            <Plus size={16} />
            <span>New Architecture</span>
          </button>

          <hr style={{ border: 'none', borderTop: '1px solid #1E1E1E' }} />

          {/* Utility Links */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', paddingLeft: '8px' }}>
            <a href="#help" style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#666666', textDecoration: 'none', fontSize: '13px' }}>
              <Settings size={16} />
              <span>Help & Settings</span>
            </a>
            <a href="#docs" style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#666666', textDecoration: 'none', fontSize: '13px' }}>
              <BookOpen size={16} />
              <span>Docs</span>
            </a>
          </div>

          {/* User Status Panel */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px',
            backgroundColor: '#0A0A0A',
            borderRadius: '12px',
            border: '1px solid #1E1E1E'
          }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: '#0070F3',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              fontSize: '12px'
            }}>
              GA
            </div>
            <div>
              <p style={{ fontSize: '13px', fontWeight: 'bold', margin: 0 }}>Genesis Admin</p>
              <p style={{ fontSize: '11px', color: '#666666', margin: 0 }}>Superuser | ID: 99x-evolve</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Workspace Frame */}
      <div style={{ display: 'flex', flexDirection: 'column', flexGrow: 1, overflow: 'hidden' }}>
        {/* Top Header Bar */}
        <header style={{
          height: '64px',
          backgroundColor: '#121212',
          borderBottom: '1px solid #1E1E1E',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          flexShrink: 0
        }}>
          {/* Header Navigation Tabs */}
          <div style={{ display: 'flex', gap: '24px' }}>
            <span style={{ color: '#FFFFFF', fontWeight: '600', fontSize: '14px', borderBottom: '2px solid #0070F3', paddingBottom: '21px' }}>Requirements</span>
            <span style={{ color: '#666666', fontSize: '14px', paddingBottom: '21px' }}>Architecture</span>
            <span style={{ color: '#666666', fontSize: '14px', paddingBottom: '21px' }}>Contracts</span>
          </div>

          {/* Search bar & Badges */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            {/* Search Input */}
            <div style={{ position: 'relative' }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#666666' }} />
              <input
                type="text"
                placeholder="Search project outputs..."
                style={{
                  backgroundColor: '#0A0A0A',
                  border: '1px solid #1E1E1E',
                  borderRadius: '6px',
                  color: '#FFFFFF',
                  padding: '8px 12px 8px 36px',
                  fontSize: '13px',
                  width: '240px',
                  outline: 'none'
                }}
              />
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              borderRadius: '20px',
              padding: '6px 12px',
              fontSize: '12px',
              fontWeight: '500',
              color: '#10B981'
            }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10B981' }}></span>
              Project {systemVersion}
            </div>

            {/* Icon buttons */}
            <div style={{ display: 'flex', gap: '12px', color: '#888888' }}>
              <button style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}><Bell size={18} /></button>
              <button style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}><Terminal size={18} /></button>
            </div>
          </div>
        </header>

        {/* Render Active Page Content */}
        <main style={{ flexGrow: 1, overflowY: 'auto', padding: '24px' }}>
          <div className="animate-slide-in" style={{ maxWidth: '1400px', margin: '0 auto' }}>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
