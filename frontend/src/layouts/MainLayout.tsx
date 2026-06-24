import React, { useState } from 'react';
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
  BrainCircuit,
  ChevronRight
} from 'lucide-react';

interface MainLayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  currentProjectId: string;
  onNewEvolution: () => void;
  systemVersion: string;
}

// Workflow sections defining the core user journey
const workflowItems = [
  { id: 'ai-architect', label: 'AI Architect', icon: BrainCircuit, step: '01' },
  { id: 'architecture', label: 'Architecture', icon: Network, step: '02' },
  { id: 'compiler', label: 'Generated Contracts', icon: Cpu, step: '03' },
  { id: 'validation', label: 'Validation & Repair', icon: ShieldCheck, step: '04' },
];

// Supporting tools (less prominent)
const toolItems = [
  { id: 'dashboard', label: 'Projects', icon: LayoutDashboard },
  { id: 'simulation', label: 'Simulation', icon: Play },
  { id: 'evaluation', label: 'Evaluation', icon: LineChart },
  { id: 'timeline', label: 'Timeline', icon: History },
];

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  activeTab,
  setActiveTab,
  onNewEvolution,
  systemVersion
}) => {
  const [showAdvancedTools, setShowAdvancedTools] = useState(false);
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
          <div style={{ marginBottom: '28px', paddingLeft: '8px' }}>
            <h1 style={{ fontSize: '20px', fontWeight: 'bold', letterSpacing: '-0.5px', color: '#FFFFFF' }}>GenesisAI</h1>
            <p style={{ fontSize: '11px', color: '#666666', marginTop: '2px' }}>AI Application Compiler</p>
          </div>

          {/* Primary Workflow Navigation */}
          <div style={{ marginBottom: '8px', paddingLeft: '8px' }}>
            <p style={{ fontSize: '10px', color: '#444444', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 700 }}>Compiler Workflow</p>
          </div>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginBottom: '20px' }}>
            {workflowItems.map((item, index) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              // Also highlight validation nav item when repair is active
              const isHighlighted = isActive || (item.id === 'validation' && activeTab === 'repair');
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    width: '100%',
                    padding: '10px 16px',
                    borderRadius: '8px',
                    border: isHighlighted ? '1px solid rgba(0,112,243,0.3)' : '1px solid transparent',
                    backgroundColor: isHighlighted ? 'rgba(0,112,243,0.12)' : 'transparent',
                    color: isHighlighted ? '#FFFFFF' : '#888888',
                    fontFamily: 'inherit',
                    fontSize: '13px',
                    fontWeight: isHighlighted ? 600 : 400,
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <span style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    color: isHighlighted ? '#0070F3' : '#333333',
                    minWidth: '18px'
                  }}>
                    {item.step}
                  </span>
                  <Icon size={16} />
                  <span style={{ flexGrow: 1 }}>{item.label}</span>
                  {isHighlighted && <ChevronRight size={14} style={{ color: '#0070F3' }} />}
                </button>
              );
            })}
          </nav>

          {/* Separator */}
          <hr style={{ border: 'none', borderTop: '1px solid #1E1E1E', marginBottom: '16px' }} />

          {/* Collapsible Advanced Tools */}
          <div style={{ marginBottom: '8px', paddingLeft: '8px' }}>
            <button
              onClick={() => setShowAdvancedTools(!showAdvancedTools)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                width: '100%',
                background: 'none',
                border: 'none',
                color: '#444444',
                cursor: 'pointer',
                fontSize: '10px',
                textTransform: 'uppercase',
                letterSpacing: '1px',
                fontWeight: 700,
                padding: '4px 0',
                textAlign: 'left',
                fontFamily: 'inherit',
                outline: 'none'
              }}
            >
              <span>Advanced Tools</span>
              <span style={{ fontSize: '9px', color: '#666666' }}>{showAdvancedTools ? '▼' : '►'}</span>
            </button>
          </div>
          {showAdvancedTools && (
            <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginBottom: '20px' }}>
              {toolItems.map((item) => {
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
                      padding: '9px 16px',
                      borderRadius: '8px',
                      border: 'none',
                      backgroundColor: isActive ? '#0070F3' : 'transparent',
                      color: isActive ? '#FFFFFF' : '#666666',
                      fontFamily: 'inherit',
                      fontSize: '13px',
                      fontWeight: isActive ? 600 : 400,
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <Icon size={16} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>
          )}
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
          {/* Path / Workspace Identifier */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '14px', fontWeight: 600, color: '#E0E0E0' }}>Workspace</span>
            <span style={{ fontSize: '12px', color: '#666666' }}>/</span>
            <span style={{ fontSize: '13px', color: '#888888', fontStyle: 'italic' }}>
              {activeTab === 'ai-architect' ? 'AI Architect' :
               activeTab === 'architecture' ? 'Architecture Design' :
               activeTab === 'compiler' ? 'Generated Contracts' :
               activeTab === 'validation' || activeTab === 'repair' ? 'Validation & Repair' :
               activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
            </span>
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
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10B981', display: 'inline-block' }}></span>
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
