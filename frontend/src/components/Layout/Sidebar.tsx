import type { ReactElement } from 'react';
import { cloneElement } from 'react';
import { Activity, BrainCircuit, Camera, MessageSquare, MousePointer2, Volume2 } from 'lucide-react';

interface Props {
  language: string;
  setLanguage: (l: string) => void;
}

const scrollToPanel = (id: string) => {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

export const Sidebar: React.FC<Props> = ({ language, setLanguage }) => {
  return (
    <aside className="sidebar">
      <div className="brand-block">
        <div className="brand-mark">
          <div className="brand-icon">
            <Activity />
          </div>
          <div>
            <span className="brand-name">Silentlink</span>
            <span className="brand-subtitle">Hands-free control</span>
          </div>
        </div>
      </div>

      <nav className="nav-list" aria-label="Workspace sections">
        <NavItem icon={<Camera />} label="Camera" active onClick={() => scrollToPanel('camera')} />
        <NavItem icon={<MessageSquare />} label="Messages" onClick={() => scrollToPanel('messages')} />
        <NavItem icon={<MousePointer2 />} label="Gestures" onClick={() => scrollToPanel('gestures')} />
      </nav>

      <div className="sidebar-system">
        <div className="system-card">
          <div className="system-card__title">
            <BrainCircuit />
            Gesture Modes
          </div>
          <div className="system-stats">
            <span>Cursor</span>
            <strong>Enabled</strong>
          </div>
          <div className="system-stats">
            <span>Hold Guard</span>
            <strong>0.8s</strong>
          </div>
        </div>

        <div className="voice-card">
          <div className="voice-label">
            <Volume2 /> Voice Output
          </div>
          <select
            className="select-control"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            aria-label="Voice output language"
          >
            <option value="en">English (US)</option>
            <option value="hi">Hindi (IN)</option>
            <option value="es">Spanish (ES)</option>
            <option value="fr">French (FR)</option>
          </select>
        </div>
      </div>
    </aside>
  );
};

interface NavItemProps {
  icon: ReactElement<{ className?: string }>;
  label: string;
  active?: boolean;
  onClick: () => void;
}

const NavItem = ({ icon, label, active = false, onClick }: NavItemProps) => (
  <button type="button" className={`nav-item ${active ? 'nav-item--active' : ''}`} onClick={onClick}>
    {cloneElement(icon, { className: 'nav-item__icon' })}
    <span>{label}</span>
  </button>
);
