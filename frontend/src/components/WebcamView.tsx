import React, { useEffect, useRef, useState } from 'react';
import { FilesetResolver, HandLandmarker } from '@mediapipe/tasks-vision';

interface Props {
  onProcessingChange: (status: boolean) => void;
  onPrediction: (text: string) => void;
  onCommand: (cmd: 'append' | 'backspace' | 'clear_message' | 'send_message', payload?: string) => void;
  targetLanguage: string;
  onEngineState: (state: { status: string; pose: string; progress: number; confidence: number }) => void;
}

const WebcamView: React.FC<Props> = ({ onProcessingChange, onPrediction, onCommand, targetLanguage, onEngineState }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hasCameraError, setHasCameraError] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const targetLanguageRef = useRef(targetLanguage);
  const handlersRef = useRef({ onProcessingChange, onPrediction, onCommand, onEngineState });

  useEffect(() => {
    targetLanguageRef.current = targetLanguage;
  }, [targetLanguage]);

  useEffect(() => {
    handlersRef.current = { onProcessingChange, onPrediction, onCommand, onEngineState };
  }, [onProcessingChange, onPrediction, onCommand, onEngineState]);

  useEffect(() => {
    let isMounted = true;
    let reconnectTimer: number | undefined;
    let activeStream: MediaStream | null = null;
    let activeVideo: HTMLVideoElement | null = null;

    const connectWs = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/landmarks`);
      ws.onopen = () => console.log('Connected to backend API');
      ws.onmessage = (event) => {
        try {
          const result = JSON.parse(event.data);
          
          if (result.status) {
             handlersRef.current.onEngineState({ status: result.status, pose: result.pose || '', progress: result.progress || 0, confidence: result.confidence || 0 });
          }
          if (result.transcription) {
            handlersRef.current.onPrediction(result.transcription);
          }
          if (result.command) {
            console.log("System Command Triggered:", result.command);
            handlersRef.current.onCommand(result.command, result.text);
          }
        } catch (e) {
             console.error('Error parsing backend WS message', e);
        }
      };
      ws.onclose = () => {
         if (isMounted) {
           reconnectTimer = window.setTimeout(connectWs, 2000);
         }
      };
      ws.onerror = (err) => console.error('WebSocket error:', err);
      wsRef.current = ws;
    };
    connectWs();

    let handLandmarker: HandLandmarker;
    let animationFrameId: number;

    const initializeMediaPipe = async () => {
      try {
        const vision = await FilesetResolver.forVisionTasks(
          "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
        );
        handLandmarker = await HandLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
            delegate: "GPU"
          },
          runningMode: "VIDEO",
          numHands: 2,
          minHandDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5,
        });

        startCamera();
      } catch (err) {
        console.error("Error initializing MediaPipe:", err);
      }
    };

    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
        activeStream = stream;
        activeVideo = videoRef.current;

        if (activeVideo) {
          activeVideo.srcObject = stream;
          activeVideo.addEventListener('loadeddata', predictWebcam);
        }
      } catch {
        setHasCameraError(true);
      }
    };

    let lastVideoTime = -1;
    const predictWebcam = async () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas || !handLandmarker) return;

      const startTimeMs = performance.now();
      if (lastVideoTime !== video.currentTime) {
        lastVideoTime = video.currentTime;
        handlersRef.current.onProcessingChange(true);
        const results = handLandmarker.detectForVideo(video, startTimeMs);
        
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.save();
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          
          if (results.landmarks && results.landmarks.length > 0) {
            // Send to backend via WS if open
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                // Throttle sending periodically in a real scenario, but for now send every frame (or rely on backend throttling)
                wsRef.current.send(JSON.stringify({
                    landmarks: results.landmarks,
                    target_lang: targetLanguageRef.current
                }));
            }

            for (const landmarks of results.landmarks) {
              for (const point of landmarks) {
                 ctx.beginPath();
                 ctx.arc(point.x * canvas.width, point.y * canvas.height, 4, 0, 2 * Math.PI);
                 ctx.fillStyle = "#2dd4bf";
                 ctx.shadowColor = "rgba(45, 212, 191, 0.75)";
                 ctx.shadowBlur = 8;
                 ctx.fill();
              }
            }
          }
          ctx.restore();
        }
      }
      animationFrameId = requestAnimationFrame(predictWebcam);
    };

    initializeMediaPipe();

    return () => {
      isMounted = false;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      if (handLandmarker) handLandmarker.close();
      if (wsRef.current) wsRef.current.close();
      if (activeVideo) {
        activeVideo.removeEventListener('loadeddata', predictWebcam);
        activeVideo.srcObject = null;
      }
      if (activeStream) {
         activeStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  if (hasCameraError) {
    return <div className="camera-error">Error: Could not access camera. Please allow camera permissions.</div>;
  }

  return (
    <div className="webcam-layer">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        className="webcam-video"
      ></video>
      <canvas
        ref={canvasRef}
        className="webcam-canvas"
        width={1280}
        height={720}
      ></canvas>
    </div>
  );
};

export default WebcamView;
