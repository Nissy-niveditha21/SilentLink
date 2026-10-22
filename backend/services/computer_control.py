import os
import sys
import time
import subprocess
import webbrowser
from typing import Optional


class ComputerControlService:
    DEBOUNCE_CLICK_S = 1.0
    DEBOUNCE_SCROLL_S = 0.5
    DEBOUNCE_LAUNCH_S = 3.0
    FIST_RESET_HOLD_S = 2.0

    def __init__(self, pyautogui=None):
        self.pyautogui_imported = False
        if pyautogui is not None:
            self.pyautogui = pyautogui
            self.pyautogui_imported = True
            self.pyautogui.FAILSAFE = False
        else:
            try:
                import pyautogui as _pg
                self.pyautogui = _pg
                self.pyautogui_imported = True
            except Exception:
                self.pyautogui = None
            
            if self.pyautogui_imported:
                self.pyautogui.PAUSE = 0
                self.pyautogui.FAILSAFE = False

        self.active = False
        self.last_click_ts = 0.0
        self.last_scroll_ts = 0.0
        self.last_launch_ts = 0.0
        self.fist_start_ts: Optional[float] = None
        self.last_scroll_prev_y = None

        if self.pyautogui_imported:
            self.screen_w, self.screen_h = self.pyautogui.size()
        else:
            self.screen_w, self.screen_h = 1920, 1080

    def set_active(self, active: bool):
        self.active = bool(active)
        if not self.active:
            self.last_scroll_prev_y = None
            self.fist_start_ts = None

    @staticmethod
    def _open_url(url: str):
        try:
            if sys.platform.startswith("win"):
                os.startfile(url)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", url])
            else:
                subprocess.Popen(["xdg-open", url])
        except Exception:
            try:
                webbrowser.open(url)
            except Exception:
                pass

    def move_cursor(self, ix: float, iy: float):
        if self.active and self.pyautogui_imported:
            x = int(ix * self.screen_w)
            y = int(iy * self.screen_h)
            self.pyautogui.moveTo(x, y)

    def click_if_pinch(self, pinch_dist: float, thr: float = 0.03) -> bool:
        now_ts = time.time()
        if (
            self.active
            and self.pyautogui_imported
            and pinch_dist < thr
            and (now_ts - self.last_click_ts) > self.DEBOUNCE_CLICK_S
        ):
            self.pyautogui.click()
            self.last_click_ts = now_ts
            return True
        return False

    def scroll_if_2finger(self, delta_y_norm: float) -> int:
        now_ts = time.time()
        if (
            self.active
            and self.pyautogui_imported
            and abs(delta_y_norm) > 0.05
            and (now_ts - self.last_scroll_ts) > self.DEBOUNCE_SCROLL_S
        ):
            clicks = int(delta_y_norm * 300)
            self.pyautogui.scroll(clicks)
            self.last_scroll_ts = now_ts
            return clicks
        return 0

    def launch_apps(self, finger_vec: tuple) -> Optional[str]:
        index_up, middle_up, ring_up, pinky_up = finger_vec
        now_ts = time.time()

        all_down = not index_up and not middle_up and not ring_up and not pinky_up
        if all_down:
            if self.fist_start_ts is None:
                self.fist_start_ts = now_ts
            elif (now_ts - self.fist_start_ts) >= self.FIST_RESET_HOLD_S:
                self.fist_start_ts = None
                return "RESET"
            return None
        else:
            self.fist_start_ts = None

        if (now_ts - self.last_launch_ts) <= 6.0:  # 6 second strict debounce
            return None

        # Ensure index finger alone opens YouTube ONCE and locks until fingers reset
        if index_up and not middle_up and not ring_up and not pinky_up:
            if getattr(self, "_launched_locked", False):
                return None
            self.last_launch_ts = now_ts
            self._launched_locked = True
            self._open_url("https://www.youtube.com")
            return "YouTube"

        if index_up and middle_up and ring_up and not pinky_up:
            if getattr(self, "_launched_locked", False):
                return None
            self.last_launch_ts = now_ts
            self._launched_locked = True
            if sys.platform.startswith("win"):
                subprocess.Popen(["notepad.exe"])
            return "Notepad"

        if index_up and middle_up and ring_up and pinky_up:
            if getattr(self, "_launched_locked", False):
                return None
            self.last_launch_ts = now_ts
            self._launched_locked = True
            self._open_url("https://web.whatsapp.com")
            return "WhatsApp"

        # Unlock when fingers change or reset
        self._launched_locked = False
        return None

    def step(self, landmarks_normalized_hand_landmarks_list):
        result = {
            "moved": False,
            "clicked": False,
            "scrolled_clicks": 0,
            "launched_app": None,
        }

        if not self.active or len(landmarks_normalized_hand_landmarks_list) < 21:
            return result

        lm = landmarks_normalized_hand_landmarks_list

        index_tip = lm[8]
        prev_active = self.active
        self.move_cursor(index_tip.x, index_tip.y)
        if self.active and self.pyautogui_imported:
            result["moved"] = True

        lm8 = lm[8]
        lm4 = lm[4]
        pinch_dist = ((lm8.x - lm4.x) ** 2 + (lm8.y - lm4.y) ** 2) ** 0.5
        if self.click_if_pinch(pinch_dist):
            result["clicked"] = True

        index_tip_y = lm[8].y
        middle_tip_y = lm[12].y
        index_up = lm[8].y < lm[6].y
        middle_up = lm[12].y < lm[10].y
        ring_up = lm[16].y < lm[14].y
        pinky_up = lm[20].y < lm[18].y

        launched = self.launch_apps((index_up, middle_up, ring_up, pinky_up))
        result["launched_app"] = launched

        if index_up and middle_up and not ring_up and not pinky_up:
            avg_y = (index_tip_y + middle_tip_y) / 2.0
            if self.last_scroll_prev_y is not None:
                delta_y_norm = self.last_scroll_prev_y - avg_y
                scrolled = self.scroll_if_2finger(delta_y_norm)
                result["scrolled_clicks"] = scrolled
            self.last_scroll_prev_y = avg_y
        else:
            self.last_scroll_prev_y = None

        return result
