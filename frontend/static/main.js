/* global Hands, Camera, drawConnectors, drawLandmarks */
(function () {
    window.HAND_CONNECTIONS = [
        [0, 1], [1, 2], [2, 3], [3, 4],
        [0, 5], [5, 6], [6, 7], [7, 8],
        [5, 9], [9, 10], [10, 11], [11, 12],
        [9, 13], [13, 14], [14, 15], [15, 16],
        [13, 17], [17, 18], [18, 19], [19, 20],
        [0, 17],
    ];
    const SETTINGS_KEY = 'silentlink:settings';
    const HISTORY_KEY = 'silentlink:history';
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    document.querySelectorAll('.fade-up').forEach(el => {
        el.style.animationPlayState = 'paused';
        observer.observe(el);
    });

    const path = window.location.pathname;
    document.querySelectorAll('.nav-links a').forEach(a => {
        if (a.getAttribute('href') === path) {
            a.style.color = 'var(--text)';
            a.style.background = 'var(--glass)';
            a.style.borderRadius = 'var(--radius-full)';
        }
    });

    const dot = document.getElementById('cursor-dot');
    const ring = document.getElementById('cursor-ring');
    if (dot && ring && !document.body.classList.contains('user-no-custom-cursor')) {
        let mouseX = 0, mouseY = 0;
        let ringX = 0, ringY = 0;
        document.addEventListener('mousemove', e => {
            mouseX = e.clientX; mouseY = e.clientY;
            dot.style.left = mouseX + 'px';
            dot.style.top = mouseY + 'px';
        });
        (function animateRing() {
            ringX += (mouseX - ringX) * 0.12;
            ringY += (mouseY - ringY) * 0.12;
            ring.style.left = ringX + 'px';
            ring.style.top = ringY + 'px';
            requestAnimationFrame(animateRing);
        })();
        const hoverTargets = 'a, button, input, [role="button"], label, select, textarea';
        document.querySelectorAll(hoverTargets).forEach(el => {
            el.addEventListener('mouseenter', () => document.body.classList.add('cursor-hover'));
            el.addEventListener('mouseleave', () => document.body.classList.remove('cursor-hover'));
        });
        document.addEventListener('mousedown', () => document.body.classList.add('cursor-click'));
        document.addEventListener('mouseup', () => document.body.classList.remove('cursor-click'));
        document.addEventListener('mouseleave', () => { dot.style.opacity = '0'; ring.style.opacity = '0'; });
        document.addEventListener('mouseenter', () => { dot.style.opacity = '1'; ring.style.opacity = '1'; });
        const SPARK_COLORS = ['#38d9f5', '#7dd3fc', '#ffffff', '#8b5cf6', '#34d399'];
        function spawnSparks(x, y) {
            const count = 10 + Math.floor(Math.random() * 6);
            for (let i = 0; i < count; i++) {
                const el = document.createElement('div');
                el.classList.add('spark');
                const angle = Math.random() * 2 * Math.PI;
                const dist = 45 + Math.random() * 75;
                const tx = Math.cos(angle) * dist;
                const ty = Math.sin(angle) * dist;
                const size = 6 + Math.random() * 8;
                const dur = 0.5 + Math.random() * 0.35;
                const color = SPARK_COLORS[Math.floor(Math.random() * SPARK_COLORS.length)];
                el.style.cssText = `left:${x}px;top:${y}px;width:${size}px;height:${size}px;background:${color};box-shadow:0 0 ${size * 2}px ${color};--tx:${tx}px;--ty:${ty}px;--dur:${dur}s;`;
                document.body.appendChild(el);
                el.addEventListener('animationend', () => el.remove());
            }
        }
        document.addEventListener('click', e => spawnSparks(e.clientX, e.clientY));
    }

    const spotlightCards = document.querySelectorAll('.feature-card, .stat-card, .about-card, .auth-card, .sidebar-card, .phrase-box, .settings-card, .step-card, .history-item');
    spotlightCards.forEach(card => {
        card.addEventListener('mousemove', e => {
            const rect = card.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            card.style.setProperty('--mx', `${x}%`);
            card.style.setProperty('--my', `${y}%`);
        });
    });

    function loadSettings() {
        const DEFAULTS = {
            threshold: 0.6, hold: 8, timeout: 1800,
            language: 'en', ttsrate: 1.0,
            lands: true, speakauto: false,
            reducemotion: false, customcursor: true, font: '1'
        };
        try { return { ...DEFAULTS, ...(JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}')) }; }
        catch { return { ...DEFAULTS }; }
    }

    const onAppPage = document.querySelector('.translator-page');
    if (onAppPage) initTranslatorPage();

    function saveHistoryEntry(entry) {
        try {
            const arr = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
            arr.push(entry);
            if (arr.length > 200) arr.splice(0, arr.length - 200);
            localStorage.setItem(HISTORY_KEY, JSON.stringify(arr));
            window.dispatchEvent(new Event('silentlink:history-updated'));
        } catch { }
    }

    function initTranslatorPage() {
        const settings = loadSettings();
        const video = document.getElementById('camera-preview');
        const canvas = document.getElementById('landmark-canvas');
        const canvasCtx = canvas.getContext('2d');
        const cameraBadge = document.getElementById('camera-status-badge');
        const connStatus = document.getElementById('connection-status');
        const recStatusEl = document.getElementById('rec-status');
        const recSignEl = document.getElementById('rec-sign');
        const recConfEl = document.getElementById('rec-conf');
        const modeLabel = document.getElementById('mode-label');
        const sentenceEl = document.getElementById('sentence-display');
        const wordEl = document.getElementById('word-display');
        const defaultInfo = document.getElementById('default-info');
        const phraseBox = document.getElementById('phrase-box');

        let currentMode = 'COMMUNICATION';
        let ws = null;
        let wsReconnectAttempts = 0;
        let wsReconnectTimer = null;
        let frameSeq = 0;
        let lastSentenceSent = '';

        function setMode(mode) {
            currentMode = mode;
            ['COMMUNICATION', 'CONTROL', 'PHRASE'].forEach(m => {
                const btn = document.getElementById('btn-' + m);
                if (btn) {
                    btn.classList.toggle('active', m === mode);
                    btn.setAttribute('aria-selected', String(m === mode));
                }
            });
            if (modeLabel) modeLabel.textContent = mode;
            if (phraseBox && defaultInfo) {
                if (mode === 'PHRASE') {
                    phraseBox.classList.remove('hidden');
                    defaultInfo.classList.add('hidden');
                    updateSignClip('HELLO');
                } else {
                    phraseBox.classList.add('hidden');
                    defaultInfo.classList.remove('hidden');
                }
            }
            sendControl({ action: 'set_mode', mode });
            fetch('/api/mode?mode=' + mode, { method: 'POST' }).catch(() => { });
        }

        function attachModeButtons() {
            ['COMMUNICATION', 'CONTROL', 'PHRASE'].forEach(mode => {
                const btn = document.getElementById('btn-' + mode);
                if (btn) btn.addEventListener('click', () => setMode(mode));
            });
        }

        function attachCtrlButtons() {
            document.querySelectorAll('[data-action]').forEach(btn => {
                btn.addEventListener('click', () => {
                    const action = btn.getAttribute('data-action');
                    sendControl({ action });
                    fetch('/api/mode?mode=' + currentMode, { method: 'POST' }).catch(() => { });
                });
            });
        }

        function startWS() {
            if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
            const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const url = `${proto}//${window.location.host}/ws/sign`;
            if (connStatus) connStatus.textContent = 'Connecting…';
            try {
                ws = new WebSocket(url);
            } catch (err) {
                scheduleReconnect();
                return;
            }
            ws.onopen = () => {
                if (connStatus) connStatus.textContent = 'Connected';
                wsReconnectAttempts = 0;
                sendControl({ action: 'start' });
                sendControl({ action: 'set_mode', mode: currentMode });
                sendControl({ action: 'set_threshold', threshold: settings.threshold });
            };
            ws.onclose = () => {
                if (connStatus) connStatus.textContent = 'Disconnected (reconnecting)';
                scheduleReconnect();
            };
            ws.onerror = () => { try { ws.close(); } catch { } };
            ws.onmessage = evt => {
                let msg; try { msg = JSON.parse(evt.data); } catch { return; }
                handleServerMessage(msg);
            };
        }

        function scheduleReconnect() {
            if (wsReconnectTimer) return;
            wsReconnectAttempts++;
            const delay = Math.min(1000 * (2 ** Math.min(wsReconnectAttempts - 1, 5)), 15000);
            wsReconnectTimer = setTimeout(() => { wsReconnectTimer = null; startWS(); }, delay);
        }

        function send(obj) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                try { ws.send(JSON.stringify(obj)); } catch { }
            }
        }

        function sendFrame(landmarks, width, height) {
            const hand21 = [];
            for (let i = 0; i < 21; i++) {
                const p = landmarks[i];
                hand21.push([p.x, p.y, p.z]);
            }
            send({
                type: 'frame',
                frame: {
                    hand_landmarks: hand21,
                    timestamp_ms: performance.now(),
                    camera_width: width,
                    camera_height: height,
                },
                echo_id: String(frameSeq++),
            });
        }

        function sendControl(partial) {
            const payload = { type: 'control', control: partial };
            send(payload);
        }

        function handleServerMessage(msg) {
            if (msg.type === 'recognition' && msg.recognition) {
                const r = msg.recognition;
                if (recStatusEl) recStatusEl.textContent = r.status || 'idle';
                if (recSignEl) recSignEl.textContent = r.sign || '—';
                if (recConfEl) recConfEl.textContent = Math.round((r.confidence || 0) * 100) + '%';
                if (r.sign && r.sign !== '—') {
                    updateSignClip(r.sign);
                }
                if (sentenceEl) {
                    const s = r.sentence || '';
                    sentenceEl.textContent = s || '\u00a0';
                    if (s && s !== lastSentenceSent && r.changed) {
                        lastSentenceSent = s;
                        const langs = msg.translation && msg.translation.translations
                            ? msg.translation.translations
                            : (msg.phrase_status ? { en: msg.phrase_status.english, hi: msg.phrase_status.hindi, te: msg.phrase_status.telugu, es: msg.phrase_status.spanish, fr: msg.phrase_status.french } : {});
                        saveHistoryEntry({ ts: Date.now(), text: s, mode: currentMode, languages: langs });
                        if (settings.speakauto) speakText(s, settings.language);
                    }
                }
                if (wordEl) wordEl.textContent = r.current_word ? `[ ${r.current_word} ]` : '\u00a0';
            }
            if (msg.type === 'control_status' && msg.recognition) {
                const r = msg.recognition;
                if (recStatusEl) recStatusEl.textContent = r.status || 'idle';
                if (recSignEl) recSignEl.textContent = r.sign || '—';
                if (recConfEl) recConfEl.textContent = Math.round((r.confidence || 0) * 100) + '%';
                if (sentenceEl) {
                    const s = r.sentence || '';
                    sentenceEl.textContent = s || '\u00a0';
                }
                if (wordEl) wordEl.textContent = r.current_word ? `[ ${r.current_word} ]` : '\u00a0';
            }
            if (msg.phrase_status) {
                renderPhraseTranslations(msg.phrase_status);
                if (msg.phrase_status.english) {
                    updateSignClip(msg.phrase_status.english);
                }
            } else if (msg.translation && msg.translation.translations) {
                renderTranslations(msg.translation.translations);
            }
        }

        function updateSignClip(signKey) {
            const clipImg = document.getElementById('sign-clip-img');
            const avatarImg = document.getElementById('avatar-clip-img');
            const avatarTitle = document.getElementById('avatar-sign-title');
            if (!signKey) return;
            fetch('/api/sign/' + encodeURIComponent(signKey))
                .then(res => res.json())
                .then(data => {
                    const mediaSrc = data.video || data.image;
                    if (mediaSrc) {
                        const cachedUrl = mediaSrc + '?v=' + Date.now();
                        if (clipImg) {
                            clipImg.src = cachedUrl;
                            clipImg.style.display = 'block';
                        }
                        if (avatarImg) {
                            avatarImg.src = cachedUrl;
                        }
                        if (avatarTitle) {
                            avatarTitle.textContent = 'Sign: ' + (data.display || signKey);
                        }
                    }
                })
                .catch(() => {});
        }

        function initVoiceToGifConverter() {
            const micBtn = document.getElementById('btn-voice-input');
            const micText = document.getElementById('voice-btn-text');
            const voiceInput = document.getElementById('voice-text-input');
            const convertBtn = document.getElementById('btn-voice-convert');

            function triggerGifPlayback(phrase) {
                if (!phrase) return;
                const cleanKey = phrase.trim().toUpperCase();
                updateSignClip(cleanKey);
            }

            if (convertBtn && voiceInput) {
                convertBtn.addEventListener('click', () => {
                    triggerGifPlayback(voiceInput.value);
                });
                voiceInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') triggerGifPlayback(voiceInput.value);
                });
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                if (micText) micText.textContent = 'Use Chrome/Edge for Mic';
                return;
            }

            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            let isListening = false;

            if (micBtn) {
                micBtn.addEventListener('click', () => {
                    if (isListening) {
                        try { recognition.stop(); } catch(e){}
                    } else {
                        try {
                            recognition.start();
                        } catch (err) {
                            console.error('SR start error:', err);
                            // Fallback to getUserMedia prompt if recognition.start fails
                            navigator.mediaDevices?.getUserMedia({ audio: true }).then(() => {
                                try { recognition.start(); } catch(e){}
                            }).catch(gerr => {
                                console.warn('Mic permission error:', gerr);
                                if (micText) micText.textContent = 'Mic Denied in Chrome';
                            });
                        }
                    }
                });
            }

            recognition.onstart = () => {
                isListening = true;
                if (micBtn) micBtn.classList.add('recording');
                if (micText) micText.textContent = 'Listening…';
            };

            recognition.onresult = (evt) => {
                const transcript = evt.results[0][0].transcript;
                console.log('Voice transcript recognized:', transcript);
                if (voiceInput) voiceInput.value = transcript;
                triggerGifPlayback(transcript);
            };

            recognition.onerror = (err) => {
                console.error('Speech recognition error event:', err);
                isListening = false;
                if (micBtn) micBtn.classList.remove('recording');
                if (micText) micText.textContent = 'Error: ' + (err.error || 'Mic Fail');
                setTimeout(() => { if (micText) micText.textContent = 'Speak to Sign'; }, 3000);
            };

            recognition.onend = () => {
                isListening = false;
                if (micBtn) micBtn.classList.remove('recording');
                if (micText) micText.textContent = 'Speak to Sign';
            };
        }

        initVoiceToGifConverter();


        function renderPhraseTranslations(ps) {
            ['en', 'hi', 'te', 'es', 'fr'].forEach((lang, idx) => {
                const valMap = { en: ps.english, hi: ps.hindi, te: ps.telugu, es: ps.spanish, fr: ps.french };
                setPhraseRow(lang, valMap[lang]);
            });
        }

        function renderTranslations(tr) {
            ['en', 'hi', 'te', 'es', 'fr'].forEach(lang => setPhraseRow(lang, tr[lang]));
        }

        function setPhraseRow(lang, value) {
            const el = document.getElementById('phrase-' + lang);
            const row = document.getElementById('row-' + lang);
            if (el) el.textContent = value || '—';
            if (row) row.classList.toggle('has-value', !!value);
        }

        function onResults(results) {
            if (!canvas || !video) return;
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            canvasCtx.save();
            canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
            canvasCtx.drawImage(results.image, 0, 0, canvas.width, canvas.height);

            const hand = results.multiHandLandmarks && results.multiHandLandmarks[0];
            if (hand) {
                if (settings.lands) {
                    const HAND_CONNECTIONS = window.HAND_CONNECTIONS || [];
                    if (typeof drawConnectors === 'function' && HAND_CONNECTIONS.length) {
                        drawConnectors(canvasCtx, hand, HAND_CONNECTIONS, { color: '#00E5FF', lineWidth: 2 });
                    }
                    if (typeof drawLandmarks === 'function') {
                        drawLandmarks(canvasCtx, hand, { color: '#7C4DFF', lineWidth: 1, radius: 3 });
                    }
                }
                sendFrame(hand, canvas.width, canvas.height);
            } else {
                send({ type: 'ping' });
            }
            canvasCtx.restore();
        }

        async function startCamera() {
            const mpReady = () => typeof window.Hands === 'function' && typeof window.Camera === 'function' && typeof window.drawConnectors === 'function';
            if (!mpReady()) {
                if (cameraBadge) cameraBadge.innerHTML = '<span class="live-dot" style="background:var(--amber)"></span>Loading MediaPipe…';
                const startTs = Date.now();
                while (!mpReady() && Date.now() - startTs < 10000) {
                    await new Promise(r => setTimeout(r, 100));
                }
            }
            if (!mpReady()) {
                if (cameraBadge) cameraBadge.innerHTML = '<span class="live-dot" style="background:var(--rose)"></span>MediaPipe failed to load — check your network/CDN access to jsdelivr.net';
                return;
            }
            try {
                const hands = new Hands({
                    locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675469240/${f}`,
                });
                hands.setOptions({
                    maxNumHands: 1,
                    modelComplexity: 1,
                    minDetectionConfidence: typeof settings.threshold === 'number' ? settings.threshold : 0.6,
                    minTrackingConfidence: 0.6,
                });
                hands.onResults(onResults);

                const cam = new Camera(video, {
                    onFrame: async () => { await hands.send({ image: video }); },
                    width: 640,
                    height: 480,
                });
                await cam.start();
                if (cameraBadge) cameraBadge.innerHTML = '<span class="live-dot"></span>Camera Active';
            } catch (err) {
                console.error(err);
                if (cameraBadge) cameraBadge.innerHTML = `<span class="live-dot" style="background:var(--amber)"></span>Camera: ${err && err.name || 'error'}`;
                if (video) video.style.display = 'none';
            }
        }

        attachModeButtons();
        attachCtrlButtons();
        setMode('COMMUNICATION');
        startWS();
        startCamera();
    }

    window.speakPhrase = function speakPhrase(lang) {
        const el = document.getElementById('phrase-' + lang);
        if (!el) return;
        const text = el.textContent;
        if (!text || text === '—') return;
        speakText(text, lang);
    };

    function speakText(text, lang) {
        try {
            if (!window.speechSynthesis) return;
            const utter = new SpeechSynthesisUtterance(text);
            const map = { en: 'en-US', hi: 'hi-IN', te: 'te-IN', es: 'es-ES', fr: 'fr-FR' };
            const settings = loadSettings();
            utter.lang = map[lang] || 'en-US';
            utter.rate = Number(settings.ttsrate) || 1.0;
            speechSynthesis.cancel();
            speechSynthesis.speak(utter);
        } catch { }
    }
})();
