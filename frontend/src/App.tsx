import { useState, useEffect, useRef } from 'react';
import { Layout } from './components/Layout/Layout';
import { CameraStage } from './components/Dashboard/CameraStage';
import { OutputPanel } from './components/Dashboard/OutputPanel';
import { MessagingModule } from './components/Modules/MessagingModule';
import { GestureControlPanel } from './components/Modules/GestureControlPanel';
import { LoginScreen } from './components/Auth/LoginScreen';

type Command = 'append' | 'backspace' | 'clear_message' | 'send_message';

type EngineState = {
  status: string;
  pose: string;
  progress: number;
  confidence: number;
};

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => sessionStorage.getItem('silentlink-auth') === 'true');
  const [operatorName, setOperatorName] = useState(() => sessionStorage.getItem('silentlink-operator') || 'Operator');
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcription, setTranscription] = useState(() => isAuthenticated ? 'System ready. Sign to begin...' : 'System locked. Sign in to continue.');
  const [engineState, setEngineState] = useState<EngineState>({ status: 'idle', pose: 'Tracking Active', progress: 0, confidence: 0 });
  const [messageDraft, setMessageDraft] = useState("");
  const [chatHistory, setChatHistory] = useState<{ text: string, time: string }[]>([]);
  const [targetLanguage, setTargetLanguage] = useState("en");

  const draftRef = useRef("");
  useEffect(() => { draftRef.current = messageDraft; }, [messageDraft]);

  const speak = (text: string) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = targetLanguage === 'hi' ? 'hi-IN' : targetLanguage === 'es' ? 'es-ES' : targetLanguage === 'fr' ? 'fr-FR' : 'en-US';
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  };

  const sendCurrentDraft = () => {
    const currentDraft = draftRef.current.trim();

    if (currentDraft !== "") {
      setChatHistory(prev => [...prev, { text: currentDraft, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }]);
      setMessageDraft("");
      speak(currentDraft);
    }
  };

  const clearDraft = () => {
    setMessageDraft("");
  };

  const replayDraft = () => {
    const spokenText = draftRef.current.trim() || chatHistory.at(-1)?.text || transcription;
    if (spokenText) {
      speak(spokenText);
    }
  };

  const handleCommand = (cmd: Command, payload?: string) => {
    if (!isAuthenticated) return;

    if (cmd === "append" && payload) {
      setMessageDraft(prev => prev + payload);
    } else if (cmd === "backspace") {
      setMessageDraft(prev => prev.slice(0, -1));
    } else if (cmd === "clear_message") {
      clearDraft();
    } else if (cmd === "send_message") {
      sendCurrentDraft();
    }
  };

  const handleLogin = (name: string) => {
    sessionStorage.setItem('silentlink-auth', 'true');
    sessionStorage.setItem('silentlink-operator', name);
    setOperatorName(name);
    setIsAuthenticated(true);
    setIsProcessing(false);
    setEngineState({ status: 'idle', pose: 'Tracking Active', progress: 0, confidence: 0 });
    setTranscription('System ready. Sign to begin...');
  };

  const handleLogout = () => {
    window.speechSynthesis.cancel();
    sessionStorage.removeItem('silentlink-auth');
    sessionStorage.removeItem('silentlink-operator');
    setIsAuthenticated(false);
    setIsProcessing(false);
    setEngineState({ status: 'idle', pose: 'Tracking Active', progress: 0, confidence: 0 });
    setTranscription('System locked. Sign in to continue.');
    setMessageDraft("");
    setChatHistory([]);
  };

  if (!isAuthenticated) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <Layout
      language={targetLanguage}
      setLanguage={setTargetLanguage}
      isProcessing={isProcessing}
      engineState={engineState}
      operatorName={operatorName}
      onLogout={handleLogout}
    >
      <main className="workspace-shell">
        <div className="workspace-primary">
          <section className="panel camera-panel" id="camera">
            <CameraStage
              isProcessing={isProcessing}
              setIsProcessing={setIsProcessing}
              setTranscription={setTranscription}
              handleCommand={handleCommand}
              targetLanguage={targetLanguage}
              engineState={engineState}
              setEngineState={setEngineState}
            />
          </section>

          <section className="panel output-panel" id="transcription">
            <OutputPanel transcription={transcription} engineState={engineState} />
          </section>
        </div>

        <aside className="workspace-rail">
          <section className="panel messaging-panel" id="messages">
            <MessagingModule
              chatHistory={chatHistory}
              messageDraft={messageDraft}
              onSend={sendCurrentDraft}
              onClear={clearDraft}
              onReplay={replayDraft}
            />
          </section>
          
          <section className="panel gestures-panel" id="gestures">
            <GestureControlPanel engineState={engineState} />
          </section>
        </aside>

      </main>

      <footer className="status-bar">
        <div className="status-cluster">
          <span className="status-chip">
            <span className={`live-dot ${isProcessing ? 'live-dot--on' : 'live-dot--off'}`}></span>
            {isProcessing ? 'System Active' : 'System Paused'}
          </span>
          <span className="status-divider"></span>
          <span>Confidence {(engineState.confidence * 100).toFixed(0)}%</span>
          <span className="status-divider"></span>
          <span>{engineState.pose || 'No pose'}</span>
        </div>
        <div className="engine-version">
          Silentlink Engine v1.0.0
        </div>
      </footer>
    </Layout>
  );
}

export default App;
