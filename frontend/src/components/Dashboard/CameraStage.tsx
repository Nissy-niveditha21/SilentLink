import WebcamView from '../WebcamView';
import { motion } from 'framer-motion';
import { Camera, ShieldAlert, Sparkles } from 'lucide-react';

type Command = 'append' | 'backspace' | 'clear_message' | 'send_message';

type EngineState = {
  status: string;
  pose: string;
  progress: number;
  confidence: number;
};

interface Props {
  setIsProcessing: (status: boolean) => void;
  setTranscription: (text: string) => void;
  handleCommand: (cmd: Command, payload?: string) => void;
  targetLanguage: string;
  engineState: EngineState;
  isProcessing: boolean;
  setEngineState: (state: EngineState) => void;
}

export const CameraStage = ({ setIsProcessing, setTranscription, handleCommand, targetLanguage, engineState, isProcessing, setEngineState }: Props) => {
  return (
    <div className="camera-stage">
      <WebcamView
        onProcessingChange={setIsProcessing}
        onPrediction={setTranscription}
        onCommand={handleCommand}
        targetLanguage={targetLanguage}
        onEngineState={setEngineState}
      />

      <div className="camera-hud camera-hud--left">
        <div className={`camera-status ${isProcessing ? 'camera-status--on' : 'camera-status--off'}`}>
          <span className="status-dot-wrap">
            {isProcessing && <span className="status-dot-ping"></span>}
            <span className={`live-dot ${isProcessing ? 'live-dot--on' : 'live-dot--off'}`}></span>
          </span>
          {isProcessing ? 'Lens Connected' : 'Video Paused'}
        </div>
        <div className="camera-meta">
          <Camera />
          1280 x 720 stream
        </div>
      </div>

      <div className="camera-hud camera-hud--right">
        <div className="camera-meta camera-meta--bright">
          <Sparkles />
          {engineState.pose || 'Tracking Active'}
        </div>
      </div>

      <div className="detection-layer">
        {engineState.status === 'holding' && (
          <div className="hold-card">
            <div className="hold-ring">
              <svg viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="36" className="hold-ring__track" />
                <motion.circle
                  cx="40" cy="40" r="36"
                  className="hold-ring__value"
                  initial={{ strokeDasharray: 226, strokeDashoffset: 226 }}
                  animate={{ strokeDashoffset: 226 - (226 * engineState.progress) }}
                  transition={{ duration: 0.1, ease: 'linear' }}
                />
              </svg>
              <div className="hold-percent">
                {Math.round(engineState.progress * 100)}%
              </div>
            </div>
            <p className="hold-title">{engineState.pose}</p>
            <p className="hold-subtitle">Hold to confirm</p>
          </div>
        )}

        {engineState.status === 'listening' && (
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }} 
            animate={{ scale: 1, opacity: 1 }} 
            className="detected-pill"
          >
            Detected: {engineState.pose}
          </motion.div>
        )}

        {engineState.status === 'conflict' && (
          <div className="failsafe-banner">
            <ShieldAlert />
            <span>Failsafe: {engineState.pose}</span>
          </div>
        )}
      </div>
    </div>
  )
}
