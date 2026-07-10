import math
import time
from cursor_controller import CursorController
from deep_translator import GoogleTranslator

def detect_asl_letter(hand):
    thumb_up = hand[4]['y'] < hand[3]['y']
    index_up = hand[8]['y'] < hand[6]['y']
    middle_up = hand[12]['y'] < hand[10]['y']
    ring_up = hand[16]['y'] < hand[14]['y']
    pinky_up = hand[20]['y'] < hand[18]['y']

    if not index_up and not middle_up and not ring_up and not pinky_up:
        if abs(hand[4]['x'] - hand[5]['x']) > 0.05: 
            return "A"
    if index_up and middle_up and ring_up and pinky_up:
       if hand[4]['x'] > hand[17]['x'] - 0.1: 
           return "B"
    if index_up and not middle_up and not ring_up and not pinky_up:
         if abs(hand[4]['x'] - hand[5]['x']) > 0.08: 
             return "L"
    if index_up and middle_up and not ring_up and not pinky_up:
         dist = math.sqrt((hand[8]['x']-hand[12]['x'])**2 + (hand[8]['y']-hand[12]['y'])**2)
         if dist > 0.05:
             return "V"
    if index_up and middle_up and ring_up and not pinky_up:
         return "W"
    if not index_up and not middle_up and not ring_up and pinky_up:
         if abs(hand[4]['x'] - hand[5]['x']) > 0.08:
             return "Y"
    return None

def point_distance(a, b):
    return math.sqrt((a['x'] - b['x'])**2 + (a['y'] - b['y'])**2)

class GestureEngine:
    def __init__(self):
        self.last_command_time = 0.0
        self.cooldown = 1.0 
        self.cursor = CursorController()
        
        self.pinched_start = None
        self.last_scroll_y = None
        
        # Hold-to-confirm attributes for UI progress rings
        self.current_holding_intent = None
        self.hold_start_time = None
        self.hold_threshold = 0.8 # 800ms to confirm action
        
    def _evaluate_hold(self, pose_name, intent_payload, current_time):
        if self.current_holding_intent != pose_name:
            self.current_holding_intent = pose_name
            self.hold_start_time = current_time
            return {"status": "listening", "pose": pose_name, "progress": 0.0, "confidence": 0.85}
            
        duration = current_time - self.hold_start_time
        progress = min(1.0, duration / self.hold_threshold)
        
        if progress >= 1.0:
            if current_time - self.last_command_time > self.cooldown:
                self.last_command_time = current_time
                self.current_holding_intent = None # Reset
                intent_payload["status"] = "confirmed"
                intent_payload["pose"] = pose_name
                intent_payload["progress"] = 1.0
                return intent_payload
            else:
                return {"status": "cooldown", "pose": pose_name, "progress": 1.0}
        else:
            return {"status": "holding", "pose": pose_name, "progress": progress, "confidence": 0.9}

    def process(self, landmarks_data, target_lang="en"):
        result = self._detect(landmarks_data)
        if target_lang != "en" and result:
            try:
                if "transcription" in result and result["transcription"]:
                     result["transcription"] = GoogleTranslator(source='auto', target=target_lang).translate(result["transcription"])
                if "text" in result and result["text"]:
                     base_text = result["text"].strip()
                     translated = GoogleTranslator(source='auto', target=target_lang).translate(base_text)
                     result["text"] = translated + " " if result["text"].endswith(" ") else translated
            except Exception as e:
                pass
        return result

    def _detect(self, landmarks_data):
        if not landmarks_data or len(landmarks_data) == 0:
             self.current_holding_intent = None
             return {"status": "idle", "transcription": "No hand detected. Guidance: Raise your hand to frame.", "confidence": 0}

        hand = landmarks_data[0]
        if len(hand) < 21:
            return {"status": "idle", "transcription": "Analyzing hand landmarks...", "confidence": 0.3}

        thumb_tip = hand[4]
        index_tip = hand[8]
        middle_tip = hand[12]
        ring_tip = hand[16]
        pinky_tip = hand[20]
        wrist = hand[0]
        
        dx = thumb_tip['x'] - index_tip['x']
        dy = thumb_tip['y'] - index_tip['y']
        distance = math.sqrt(dx*dx + dy*dy)
        
        current_time = time.time()

        # --- Global Finger States ---
        index_up = index_tip['y'] < hand[6]['y']
        middle_up = middle_tip['y'] < hand[10]['y']
        ring_up = ring_tip['y'] < hand[14]['y']
        pinky_up = pinky_tip['y'] < hand[18]['y']
        thumb_up = thumb_tip['y'] < hand[3]['y']
        thumb_down = thumb_tip['y'] > hand[3]['y'] + 0.08
        ring_down = not ring_up
        pinky_down = not pinky_up
        fingers_folded = not index_up and not middle_up and ring_down and pinky_down
        thumb_out = thumb_tip['x'] > hand[5]['x'] + 0.05
        four_fingers_up = index_up and middle_up and ring_up and pinky_up
        all_up = four_fingers_up and thumb_out
        index_middle_distance = point_distance(index_tip, middle_tip)

        # --- Priority Message Commands ---
        # Send Message (Thumbs Up)
        if thumb_up and fingers_folded:
             return self._evaluate_hold("Thumbs Up", {"transcription": "Thumbs Up! (Message Sent)", "command": "send_message", "confidence": 0.95}, current_time)

        # Append No (Thumbs Down)
        if thumb_down and fingers_folded:
             return self._evaluate_hold("Thumbs Down (No)", {
                "transcription": "No",
                "command": "append",
                "text": "No ",
                "confidence": 0.9
             }, current_time)

        # Fist / Stop tracking
        if fingers_folded and not thumb_up:
             self.cursor.toggle_active(False)
             self.current_holding_intent = None
             return {"status": "conflict", "pose": "Closed Fist", "transcription": "Tracking Paused (Fist)", "confidence": 0.95}
        else:
             self.cursor.toggle_active(True)
        
        # Continuous Cursor Control
        self.cursor.update_cursor(index_tip['x'], index_tip['y'])

        # Two open palms: Thank you
        if len(landmarks_data) > 1:
            second_hand = landmarks_data[1]
            if len(second_hand) >= 21:
                second_open = (
                    second_hand[8]['y'] < second_hand[6]['y'] and
                    second_hand[12]['y'] < second_hand[10]['y'] and
                    second_hand[16]['y'] < second_hand[14]['y'] and
                    second_hand[20]['y'] < second_hand[18]['y']
                )
                if four_fingers_up and second_open:
                    return self._evaluate_hold("Two Palms (Thank You)", {
                        "transcription": "Thank you",
                        "command": "append",
                        "text": "Thank you ",
                        "confidence": 0.96
                    }, current_time)

        # OK sign: thumb and index pinched while the other fingers are raised.
        if distance < 0.05 and middle_up and ring_up and pinky_up:
            return self._evaluate_hold("OK Sign", {
                "transcription": "OK",
                "command": "append",
                "text": "OK ",
                "confidence": 0.94
            }, current_time)

        # Scroll
        if index_up and middle_up and ring_down and pinky_down:
            if index_middle_distance < 0.08:
                self.current_holding_intent = None
                avg_y = (index_tip['y'] + middle_tip['y']) / 2
                if self.last_scroll_y is None:
                    self.last_scroll_y = avg_y
                else:
                    delta_y = self.last_scroll_y - avg_y
                    self.last_scroll_y = avg_y
                    if abs(delta_y) > 0.005:
                        direction = 1 if delta_y > 0 else -1
                        self.cursor.scroll(direction)
                        return {"status": "holding", "pose": "Two Fingers Scroll", "transcription": "Scrolling...", "command": "scroll"}
            else:
                self.last_scroll_y = None
        else:
            self.last_scroll_y = None

        # Pinch / Drag
        if distance < 0.05:
            self.current_holding_intent = None
            if self.pinched_start is None:
                self.pinched_start = current_time
                return {"status": "listening", "pose": "Pinch"}
            elif current_time - self.pinched_start > 0.25:
                self.cursor.mouse_down()
                return {"status": "holding", "pose": "Pinch Drag", "transcription": "Dragging...", "command": "drag", "progress": 1.0}
        else:
            if self.pinched_start is not None:
                duration = current_time - self.pinched_start
                self.pinched_start = None
                if duration <= 0.25:
                    if current_time - self.last_command_time > 0.5:
                        self.last_command_time = current_time
                        self.cursor.click()
                        return {"status": "confirmed", "pose": "Click", "transcription": "Cursor Click!", "command": "click"}
                else:
                    self.cursor.mouse_up()
                    return {"status": "confirmed", "pose": "Drop", "transcription": "Dropped", "command": "drop"}

        # --- Basic Signs & Words ---
        # Hello (Open Palm)
        if all_up:
            return self._evaluate_hold("Palm Open (Hello)", {
                "transcription": "Hello!", 
                "command": "append", 
                "text": "Hello ", 
                "confidence": 0.98
            }, current_time)

        # Please (four fingers up, thumb tucked)
        if four_fingers_up and not thumb_out:
            return self._evaluate_hold("Flat Palm (Please)", {
                "transcription": "Please",
                "command": "append",
                "text": "Please ",
                "confidence": 0.9
            }, current_time)

        # I love you (thumb, index and pinky extended)
        if thumb_out and index_up and not middle_up and ring_down and pinky_up:
            return self._evaluate_hold("ILY Sign", {
                "transcription": "I love you",
                "command": "append",
                "text": "I love you ",
                "confidence": 0.93
            }, current_time)

        # Yes (peace sign with spread fingers)
        if index_up and middle_up and ring_down and pinky_down and index_middle_distance > 0.09:
            return self._evaluate_hold("V Sign (Yes)", {
                "transcription": "Yes",
                "command": "append",
                "text": "Yes ",
                "confidence": 0.9
            }, current_time)

        # Need help (phone/Y sign)
        if not index_up and not middle_up and ring_down and pinky_up and thumb_out:
            return self._evaluate_hold("Y Sign (Help)", {
                "transcription": "Need help",
                "command": "append",
                "text": "Need help ",
                "confidence": 0.9
            }, current_time)

        # Backspace (ring finger only)
        if not index_up and not middle_up and ring_up and pinky_down:
            return self._evaluate_hold("Ring Finger (Backspace)", {
                "transcription": "Backspace",
                "command": "backspace",
                "confidence": 0.88
            }, current_time)

        # Launch WhatsApp (W Sign)
        if index_up and middle_up and ring_up and not pinky_up and thumb_tip['y'] > hand[13]['y']:
             return self._evaluate_hold("W Sign (WhatsApp)", {
                "transcription": "W Sign caught (Launching WhatsApp)",
                "command": "launch",
                "app_name": "whatsapp",
                "confidence": 0.95
            }, current_time)

        # Clear Message (Pinky Up)
        if pinky_tip['y'] < hand[17]['y'] - 0.05 and index_tip['y'] > hand[5]['y'] and middle_tip['y'] > hand[9]['y']:
             return self._evaluate_hold("Pinky Up", {"transcription": "Pinky Up! (Cleared Text)", "command": "clear_message", "confidence": 0.95}, current_time)

        # Launch App
        index_y = index_tip['y']
        middle_y = middle_tip['y']
        if index_y < wrist['y'] - 0.2 and middle_y < wrist['y'] - 0.2 and pinky_tip['y'] > hand[17]['y']:
            return self._evaluate_hold("App Launcher (Two Fingers)", {
                "transcription": "Two Fingers Up! (Launching YouTube)",
                "command": "launch",
                "app_name": "youtube",
                "confidence": 0.92
            }, current_time)

        # Custom ASL Symbols
        asl = detect_asl_letter(hand)
        if asl:
            return self._evaluate_hold(f"ASL: {asl}", {"transcription": f"Sign: {asl}", "command": "append", "text": asl}, current_time)

        # Reset if no discrete poses match
        self.current_holding_intent = None
        return {"status": "idle", "pose": "Active Tracking", "transcription": "Tracking Active", "confidence": 0.5, "progress": 0}
