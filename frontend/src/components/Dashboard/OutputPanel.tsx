import React from 'react';
import { Radio, SignalHigh } from 'lucide-react';

type EngineState = {
  status: string;
  pose: string;
  progress: number;
  confidence: number;
};

interface Props {
  transcription: string;
  engineState: EngineState;
}

export const OutputPanel: React.FC<Props> = ({ transcription, engineState }) => {
  return (
    <div className="output-module">
      <div className="section-heading">
        <div>
          <span className="section-kicker"><Radio /> Live Transcription</span>
          <h2>{engineState.status === 'idle' ? 'Awaiting gesture input' : engineState.pose}</h2>
        </div>
        <div className="confidence-badge">
          <span>Confidence</span>
          <strong>{(engineState.confidence * 100).toFixed(0)}%</strong>
        </div>
      </div>
      
      <div className="transcription-window">
        <p>
          {transcription || "..."}
        </p>
      </div>

      <div className="signal-row">
        <SignalHigh />
        <div className="signal-track">
          <div 
            className="signal-value"
            style={{ width: `${engineState.confidence * 100}%` }}
          ></div>
        </div>
        <span>Signal</span>
      </div>
    </div>
  );
};
