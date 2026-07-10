import React from 'react';
import { Sidebar } from './Sidebar';
import { LogOut } from 'lucide-react';

type EngineState = {
  status: string;
  pose: string;
  progress: number;
  confidence: number;
};

interface LayoutProps {
  children: React.ReactNode;
  language: string;
  setLanguage: (l: string) => void;
  isProcessing: boolean;
  engineState: EngineState;
  operatorName: string;
  onLogout: () => void;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  language,
  setLanguage,
  isProcessing,
  engineState,
  operatorName,
  onLogout,
}) => {
  return (
    <div className="app-frame">
      <Sidebar language={language} setLanguage={setLanguage} />
      <div className="app-main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Gesture accessibility engine</p>
            <h1>Interface Command Center</h1>
          </div>
          <div className="topbar-metrics" aria-label="Current engine metrics">
            <div className="metric-pill">Signed in: {operatorName}</div>
            <div className="metric-pill">
              <span className={`live-dot ${isProcessing ? 'live-dot--on' : 'live-dot--off'}`}></span>
              {isProcessing ? 'Live' : 'Paused'}
            </div>
            <div className="metric-pill">{engineState.status || 'idle'}</div>
            <div className="metric-pill metric-pill--accent">{(engineState.confidence * 100).toFixed(0)}%</div>
            <button type="button" className="icon-button" onClick={onLogout} title="Sign out">
              <LogOut />
            </button>
          </div>
        </header>
        <div className="app-scroll">
          {children}
        </div>
      </div>
    </div>
  );
};
