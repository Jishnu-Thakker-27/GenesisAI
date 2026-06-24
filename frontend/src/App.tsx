import React, { useState } from 'react';
import { MainLayout } from './layouts/MainLayout';
import { Dashboard } from './pages/Dashboard';
import { CompilerWorkspace } from './pages/CompilerWorkspace';
import { ValidationRepair } from './pages/ValidationRepair';
import { ArchitectureMap } from './pages/ArchitectureMap';
import { SimulationPlatform } from './pages/SimulationPlatform';
import { VersionHistory } from './pages/VersionHistory';
import { Evaluation } from './pages/Evaluation';
import { AIArchitect } from './pages/AIArchitect';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [projectId, setProjectId] = useState<string>('proj_01');
  const [systemVersion, setSystemVersion] = useState<string>('v1.2.8');

  // Triggered when a new compilation completes or requirement evolved
  const handleNewEvolution = () => {
    setActiveTab('dashboard');
  };

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <Dashboard 
            onViewSpec={(id) => {
              setProjectId(id);
              setActiveTab('compiler');
            }}
            onSetProjectId={setProjectId}
            onCompileStart={(prompt) => {
              console.log('Compiling evolution prompt:', prompt);
            }}
          />
        );
      case 'compiler':
        return <CompilerWorkspace projectId={projectId} />;
      case 'ai-architect':
        return <AIArchitect projectId={projectId} />;
      case 'architecture':
        return <ArchitectureMap projectId={projectId} />;
      case 'validation':
      case 'repair':
        return <ValidationRepair projectId={projectId} />;
      case 'simulation':
        return <SimulationPlatform projectId={projectId} />;
      case 'evaluation':
        return <Evaluation />;
      case 'timeline':
        return <VersionHistory projectId={projectId} />;
      default:
        return <Dashboard onViewSpec={() => {}} onSetProjectId={() => {}} onCompileStart={() => {}} />;
    }
  };

  return (
    <MainLayout
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      currentProjectId={projectId}
      onNewEvolution={handleNewEvolution}
      systemVersion={systemVersion}
    >
      {renderActivePage()}
    </MainLayout>
  );
};

export default App;
