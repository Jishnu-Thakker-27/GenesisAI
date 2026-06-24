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
  const [activeTab, setActiveTab] = useState<string>('ai-architect');
  const [projectId, setProjectId] = useState<string>('');
  const [systemVersion, setSystemVersion] = useState<string>('v1.2.8');
  const [selectedFile, setSelectedFile] = useState<string>('master_specification.json');

  // Triggered when a new compilation completes or requirement evolved
  const handleNewEvolution = () => {
    setActiveTab('ai-architect');
  };

  const handleNavigate = (tab: string) => {
    if (tab === 'compiler-final-contract') {
      setSelectedFile('final_contract.json');
      setActiveTab('compiler');
    } else if (tab === 'compiler-requirements') {
      setSelectedFile('requirements_report.json');
      setActiveTab('compiler');
    } else if (tab === 'compiler-blueprint') {
      setSelectedFile('blueprint.json');
      setActiveTab('compiler');
    } else if (tab === 'compiler-validation') {
      setSelectedFile('validation_report.json');
      setActiveTab('compiler');
    } else if (tab === 'compiler-repair') {
      setSelectedFile('repair_report.json');
      setActiveTab('compiler');
    } else {
      setActiveTab(tab);
    }
  };

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <Dashboard 
            currentProjectId={projectId}
            onViewSpec={(id) => {
              setProjectId(id);
              handleNavigate('compiler');
            }}
            onSetProjectId={setProjectId}
            onCompileStart={(prompt) => {
              console.log('Compiling evolution prompt:', prompt);
            }}
          />
        );
      case 'compiler':
        return (
          <CompilerWorkspace 
            projectId={projectId} 
            selectedFile={selectedFile} 
            onSelectFile={setSelectedFile} 
            onNavigate={handleNavigate}
          />
        );
      case 'ai-architect':
        return (
          <AIArchitect
            projectId={projectId}
            onSetProjectId={setProjectId}
            onOpenArtifact={(artifact) => {
              if (artifact === 'architecture') handleNavigate('architecture');
              if (artifact === 'contracts') handleNavigate('compiler');
              if (artifact === 'validation') handleNavigate('validation');
            }}
            onNavigate={handleNavigate}
          />
        );
      case 'architecture':
        return <ArchitectureMap projectId={projectId} onNavigate={handleNavigate} />;
      case 'validation':
        return <ValidationRepair projectId={projectId} activeSubTab="validation" onNavigate={handleNavigate} />;
      case 'repair':
        return <ValidationRepair projectId={projectId} activeSubTab="repair" onNavigate={handleNavigate} />;
      case 'simulation':
        return <SimulationPlatform projectId={projectId} />;
      case 'evaluation':
        return <Evaluation />;
      case 'timeline':
        return <VersionHistory projectId={projectId} />;
      default:
        return <Dashboard currentProjectId={projectId} onViewSpec={() => {}} onSetProjectId={() => {}} onCompileStart={() => {}} />;
    }
  };

  return (
    <MainLayout
      activeTab={activeTab}
      setActiveTab={handleNavigate}
      currentProjectId={projectId}
      onNewEvolution={handleNewEvolution}
      systemVersion={systemVersion}
    >
      {renderActivePage()}
    </MainLayout>
  );
};

export default App;
