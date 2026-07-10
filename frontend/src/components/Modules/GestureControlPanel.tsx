import React from 'react';
import { AppWindow, Delete, Hand, Heart, MessageCircle, MousePointer2, MoveUpRight, Phone, Send, Shield, Sparkles, ThumbsDown, Trash2 } from 'lucide-react';

type EngineState = {
  status: string;
  pose: string;
  progress: number;
  confidence: number;
};

const gestures = [
  { label: 'Cursor tracking', gesture: 'Index finger', icon: MousePointer2, match: 'Active Tracking' },
  { label: 'Click / drag', gesture: 'Pinch', icon: MoveUpRight, match: 'Pinch' },
  { label: 'Scroll', gesture: 'Two fingers', icon: Hand, match: 'Two Fingers Scroll' },
  { label: 'Append hello', gesture: 'Palm open', icon: Hand, match: 'Palm Open' },
  { label: 'Append please', gesture: 'Flat palm', icon: MessageCircle, match: 'Flat Palm' },
  { label: 'Append thanks', gesture: 'Two palms', icon: Sparkles, match: 'Two Palms' },
  { label: 'Append OK', gesture: 'OK sign', icon: Sparkles, match: 'OK Sign' },
  { label: 'Append yes', gesture: 'V sign', icon: MessageCircle, match: 'V Sign' },
  { label: 'Append no', gesture: 'Thumbs down', icon: ThumbsDown, match: 'Thumbs Down' },
  { label: 'Append help', gesture: 'Y sign', icon: Phone, match: 'Y Sign' },
  { label: 'Append love', gesture: 'ILY sign', icon: Heart, match: 'ILY Sign' },
  { label: 'Backspace', gesture: 'Ring only', icon: Delete, match: 'Backspace' },
  { label: 'Send message', gesture: 'Thumbs up', icon: Send, match: 'Thumbs Up' },
  { label: 'Clear draft', gesture: 'Pinky up', icon: Trash2, match: 'Pinky Up' },
  { label: 'Launch apps', gesture: 'W / two fingers', icon: AppWindow, match: 'Launcher' },
  { label: 'Pause tracking', gesture: 'Closed fist', icon: Shield, match: 'Closed Fist' },
];

export const GestureControlPanel: React.FC<{ engineState: EngineState }> = ({ engineState }) => {
  return (
    <div className="gesture-module">
      <div className="section-heading section-heading--compact">
        <div>
          <span className="section-kicker"><MousePointer2 /> System Modalities</span>
          <h2>Gesture Map</h2>
        </div>
      </div>
      <div className="gesture-list">
        {gestures.map((cmd) => {
          const Icon = cmd.icon;
          const active = engineState.pose.includes(cmd.match);

          return (
            <div key={cmd.label} className={`gesture-item ${active ? 'gesture-item--active' : ''}`}>
              <div className="gesture-icon">
                <Icon />
              </div>
              <span>{cmd.label}</span>
              <strong>{cmd.gesture}</strong>
            </div>
          );
        })}
      </div>
      <div className="safety-note">
        <Shield />
        <p>
          Keep your hand inside the frame. A closed fist pauses tracking and releases drag state.
        </p>
      </div>
    </div>
  );
};
