import os
import json
import math
import logging
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger("silentlink.gif_agent")

class AutoGifAgent:
    """
    Enhanced Cartoon Avatar Sign Language GIF Generator Agent.
    Generates enlarged, highly-expressive cartoon avatar animations:
    - Enlarged face with vivid facial expressions (Smiles, Bows, Open Mouth, Surprised, Heart-eyes).
    - Specific real-world sign actions:
      * THANK_YOU: Folded Namaste hands with respectful head-and-body bow.
      * PLEASE / SORRY: Circular heart chest rub with apologetic/grateful expression.
      * YES / GOOD: Excited thumbs-up nod with big happy smile.
      * NO / STOP: Firm stop palm push with serious expression & red indicator.
      * HI / HELLO / BYE: Cheerful arm wave with big open-mouth smile.
      * WHAT / WHERE / HOW: Shrugging shoulders with raised eyebrows & open hands.
    """

    PALETTES = {
        "HELLO": ("#7C4DFF", "#00E5FF", "wave", "happy"),
        "HI": ("#7C4DFF", "#00E5FF", "wave", "happy"),
        "BYE": ("#FF4081", "#FFD54F", "wave", "happy"),
        "GOODBYE": ("#FF4081", "#FFD54F", "wave", "happy"),
        "YES": ("#00E676", "#1DE9B6", "thumb_nod", "super_happy"),
        "GOOD": ("#00E676", "#69F0AE", "thumb_nod", "super_happy"),
        "NO": ("#FF1744", "#FF5252", "palm_stop", "serious"),
        "STOP": ("#D50000", "#FF1744", "palm_stop", "serious"),
        "THANK_YOU": ("#FF9100", "#FFEA00", "folded_bow", "grateful"),
        "PLEASE": ("#00B0FF", "#80D8FF", "rub_chest", "gentle"),
        "SORRY": ("#AA00FF", "#E040FB", "fist_chest", "apologetic"),
        "HELP": ("#FF3D00", "#FF6E40", "wave", "surprised"),
        "I": ("#2979FF", "#40C4FF", "point_self", "neutral"),
        "YOU": ("#3D5AFC", "#536DFE", "point_out", "friendly"),
        "WE": ("#00E5FF", "#18FFFF", "shrug", "happy"),
        "WHAT": ("#FFC400", "#FFD740", "shrug", "confused"),
        "WHERE": ("#FF9100", "#FFAB40", "shrug", "confused"),
        "HOW": ("#AEEA00", "#EEFF41", "shrug", "confused"),
        "LOVE": ("#F50057", "#FF4081", "rub_chest", "heart_eyes"),
        "HAPPY": ("#FFAB00", "#FFD600", "thumb_nod", "super_happy"),
    }

    DEFAULT_PALETTE = ("#7C4DFF", "#00E5FF", "wave", "happy")

    def __init__(self, assets_dir: str):
        self.assets_dir = os.path.abspath(assets_dir)
        self.signs_dir = os.path.join(self.assets_dir, "signs")
        self.signs_json = os.path.join(self.assets_dir, "signs.json")

    def _draw_cartoon_character(self, draw, cx, cy, action_type, emotion, t, bg_accent="#00E5FF"):
        """Draws an enlarged, expressive cartoon avatar with distinct facial emotions & body actions."""

        # Head physics (Enlarged head for clear facial expression visibility)
        head_r = 42  # Enlarged head radius
        head_bounce = math.sin(t * 2) * 5

        # Body bowing physics for THANK_YOU
        bow_offset_y = 0
        if action_type == "folded_bow":
            bow_offset_y = math.sin(t) * 14  # Respectful downward bowing motion

        head_cx = cx
        head_cy = cy - 45 + head_bounce + bow_offset_y

        # Body physics
        body_top = head_cy + head_r - 6
        body_bottom = body_top + 65
        draw.rounded_rectangle([cx - 28, body_top, cx + 28, body_bottom], radius=14, fill="#38D9F5", outline="#0F172A", width=3)
        # Shirt collar / detail
        draw.polygon([(cx - 12, body_top), (cx + 12, body_top), (cx, body_top + 16)], fill="#FFFFFF")

        # Head / Face
        draw.ellipse([head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r], fill="#FFD1B3", outline="#0F172A", width=3)
        # Hair (Stylish brown locks)
        draw.chord([head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy - 4], start=180, end=360, fill="#4A2E1A")
        draw.ellipse([head_cx - head_r - 2, head_cy - 12, head_cx - head_r + 14, head_cy + 10], fill="#4A2E1A")
        draw.ellipse([head_cx + head_r - 14, head_cy - 12, head_cx + head_r + 2, head_cy + 10], fill="#4A2E1A")

        # ---------------- EYES & EMOTIONS ----------------
        eye_y = head_cy - 4
        if emotion in ("super_happy", "happy", "excited"):
            # Big joyful smiling arc eyes ^ ^
            draw.arc([head_cx - 22, eye_y - 8, head_cx - 6, eye_y + 6], start=180, end=360, fill="#0F172A", width=4)
            draw.arc([head_cx + 6, eye_y - 8, head_cx + 22, eye_y + 6], start=180, end=360, fill="#0F172A", width=4)
            if emotion == "excited":
                # Star sparkles around eyes
                draw.text((head_cx - 24, eye_y - 12), "✨", anchor="mm")
                draw.text((head_cx + 24, eye_y - 12), "✨", anchor="mm")
        elif emotion in ("surprised", "open_mouthed"):
            # Wide open round eyes 👁️ 👁️
            draw.ellipse([head_cx - 22, eye_y - 12, head_cx - 6, eye_y + 6], fill="#FFFFFF", outline="#0F172A", width=2)
            draw.ellipse([head_cx + 6, eye_y - 12, head_cx + 22, eye_y + 6], fill="#FFFFFF", outline="#0F172A", width=2)
            draw.ellipse([head_cx - 16, eye_y - 8, head_cx - 10, eye_y + 2], fill="#0F172A")
            draw.ellipse([head_cx + 10, eye_y - 8, head_cx + 16, eye_y + 2], fill="#0F172A")
        elif emotion == "cool":
            # Sunglasses 😎
            draw.rectangle([head_cx - 24, eye_y - 8, head_cx - 4, eye_y + 4], fill="#0F172A")
            draw.rectangle([head_cx + 4, eye_y - 8, head_cx + 24, eye_y + 4], fill="#0F172A")
            draw.line([(head_cx - 4, eye_y - 2), (head_cx + 4, eye_y - 2)], fill="#0F172A", width=3)
        elif emotion == "relaxed":
            # Soft relaxed eyes - -
            draw.line([(head_cx - 20, eye_y - 2), (head_cx - 6, eye_y - 2)], fill="#0F172A", width=3)
            draw.line([(head_cx + 6, eye_y - 2), (head_cx + 20, eye_y - 2)], fill="#0F172A", width=3)
        elif emotion == "grateful" or emotion == "gentle":
            # Soft peaceful closed eyes ~ ~
            draw.arc([head_cx - 20, eye_y - 6, head_cx - 6, eye_y + 4], start=160, end=380, fill="#0F172A", width=3)
            draw.arc([head_cx + 6, eye_y - 6, head_cx + 20, eye_y + 4], start=160, end=380, fill="#0F172A", width=3)
        elif emotion == "confused":
            # One eye wide, one eye squinted (Raised eyebrow)
            draw.ellipse([head_cx - 20, eye_y - 10, head_cx - 8, eye_y + 6], fill="#0F172A")
            draw.ellipse([head_cx - 17, eye_y - 7, head_cx - 12, eye_y - 2], fill="#FFFFFF")
            draw.line([(head_cx + 6, eye_y - 4), (head_cx + 20, eye_y + 2)], fill="#0F172A", width=3)
            # Raised eyebrow
            draw.line([(head_cx - 22, eye_y - 15), (head_cx - 6, eye_y - 18)], fill="#4A2E1A", width=3)
        elif emotion in ("serious", "apologetic"):
            # Concerned / Determined eyes with inner tilted brows
            draw.ellipse([head_cx - 18, eye_y - 8, head_cx - 8, eye_y + 4], fill="#0F172A")
            draw.ellipse([head_cx + 8, eye_y - 8, head_cx + 18, eye_y + 4], fill="#0F172A")
            # Tilted eyebrows
            draw.line([(head_cx - 20, eye_y - 16), (head_cx - 6, eye_y - 11)], fill="#4A2E1A", width=3)
            draw.line([(head_cx + 20, eye_y - 16), (head_cx + 6, eye_y - 11)], fill="#4A2E1A", width=3)
        elif emotion == "heart_eyes":
            # Heart Eyes ❤️ ❤️
            draw.text((head_cx - 14, eye_y), "❤️", anchor="mm", font_size=18)
            draw.text((head_cx + 14, eye_y), "❤️", anchor="mm", font_size=18)
        else:
            # Standard Big Anime Eyes
            draw.ellipse([head_cx - 20, eye_y - 10, head_cx - 8, eye_y + 6], fill="#0F172A")
            draw.ellipse([head_cx + 8, eye_y - 10, head_cx + 20, eye_y + 6], fill="#0F172A")
            # Highlights
            draw.ellipse([head_cx - 17, eye_y - 7, head_cx - 12, eye_y - 2], fill="#FFFFFF")
            draw.ellipse([head_cx + 11, eye_y - 7, head_cx + 16, eye_y - 2], fill="#FFFFFF")

        # Rosy Cheeks
        draw.ellipse([head_cx - 26, head_cy + 6, head_cx - 16, head_cy + 14], fill="#FF8A8A")
        draw.ellipse([head_cx + 16, head_cy + 6, head_cx + 26, head_cy + 14], fill="#FF8A8A")

        # ---------------- MOUTH & EXPRESSIONS ----------------
        mouth_y = head_cy + 16
        if emotion in ("super_happy", "grateful", "excited"):
            # Big open smiling mouth :D
            draw.chord([head_cx - 12, mouth_y - 4, head_cx + 12, mouth_y + 16], start=0, end=180, fill="#D50000", outline="#0F172A", width=2)
            # Tongue
            draw.chord([head_cx - 7, mouth_y + 4, head_cx + 7, mouth_y + 14], start=0, end=180, fill="#FF8A8A")
        elif emotion in ("surprised", "confused", "open_mouthed"):
            # O-shaped surprised mouth
            draw.ellipse([head_cx - 8, mouth_y - 2, head_cx + 8, mouth_y + 12], fill="#0F172A")
        elif emotion == "serious":
            # Firm straight mouth
            draw.line([(head_cx - 10, mouth_y + 2), (head_cx + 10, mouth_y + 2)], fill="#0F172A", width=3)
        else:
            # Cute gentle smile curve
            draw.arc([head_cx - 10, mouth_y - 4, head_cx + 10, mouth_y + 8], start=0, end=180, fill="#0F172A", width=3)

        # ---------------- ARMS & SIGN ACTIONS ----------------
        shoulder_l = (cx - 26, body_top + 10)
        shoulder_r = (cx + 26, body_top + 10)

        if action_type == "folded_bow":  # THANK YOU: Respectful folded hands (Namaste) + Bowing
            pray_x = cx
            pray_y = body_top + 22 + (bow_offset_y * 0.5)
            # Left & Right arms meeting in center
            draw.line([shoulder_l, (cx - 12, pray_y + 10), (pray_x, pray_y)], fill="#FFD1B3", width=7)
            draw.line([shoulder_r, (cx + 12, pray_y + 10), (pray_x, pray_y)], fill="#FFD1B3", width=7)
            # Folded Palms Together
            draw.ellipse([pray_x - 9, pray_y - 16, pray_x + 9, pray_y + 8], fill="#FFD1B3", outline="#0F172A", width=2)
            # Gratitude sparkles
            draw.line([(pray_x - 18, pray_y - 20), (pray_x - 24, pray_y - 28)], fill="#FFEA00", width=3)
            draw.line([(pray_x + 18, pray_y - 20), (pray_x + 24, pray_y - 28)], fill="#FFEA00", width=3)

        elif action_type == "wave":  # HI / HELLO / BYE: Arm Waving
            wave_angle = math.sin(t) * 28
            hand_r_x = shoulder_r[0] + 34 + math.sin(math.radians(wave_angle)) * 16
            hand_r_y = shoulder_r[1] - 30 + math.cos(math.radians(wave_angle)) * 8
            # Left arm on hip
            draw.line([shoulder_l, (shoulder_l[0] - 12, shoulder_l[1] + 20), (shoulder_l[0] - 4, shoulder_l[1] + 32)], fill="#FFD1B3", width=7)
            # Right arm raised waving
            draw.line([shoulder_r, (shoulder_r[0] + 16, shoulder_r[1] - 14), (hand_r_x, hand_r_y)], fill="#FFD1B3", width=7)
            # Open Waving Hand Palm
            draw.ellipse([hand_r_x - 10, hand_r_y - 10, hand_r_x + 10, hand_r_y + 10], fill="#FFD1B3", outline="#0F172A", width=2)
            # Wave arcs
            draw.arc([hand_r_x - 16, hand_r_y - 18, hand_r_x + 16, hand_r_y - 2], start=200, end=340, fill=bg_accent, width=3)

        elif action_type == "thumb_nod":  # YES / GOOD: Thumbs up
            nod_y = math.sin(t) * 10
            hand_r_x = shoulder_r[0] + 26
            hand_r_y = shoulder_r[1] + nod_y
            draw.line([shoulder_l, (shoulder_l[0] - 14, shoulder_l[1] + 22)], fill="#FFD1B3", width=7)
            draw.line([shoulder_r, (hand_r_x - 8, hand_r_y + 12), (hand_r_x, hand_r_y)], fill="#FFD1B3", width=7)
            # Thumbs Up Fist & Raised Thumb
            draw.ellipse([hand_r_x - 9, hand_r_y - 6, hand_r_x + 9, hand_r_y + 9], fill="#FFD1B3", outline="#0F172A", width=2)
            draw.line([(hand_r_x + 3, hand_r_y - 2), (hand_r_x + 3, hand_r_y - 22)], fill="#FFD1B3", width=6)
            # Green sparkle line
            draw.line([(hand_r_x + 12, hand_r_y - 24), (hand_r_x + 20, hand_r_y - 32)], fill="#00E676", width=3)

        elif action_type == "palm_stop":  # NO / STOP: Stop Palm Pushing
            push_z = math.sin(t) * 8
            hand_r_x = shoulder_r[0] + 26 + push_z
            hand_r_y = shoulder_r[1] + 6
            draw.line([shoulder_l, (cx - 12, body_top + 25)], fill="#FFD1B3", width=7)
            draw.line([shoulder_r, (hand_r_x, hand_r_y)], fill="#FFD1B3", width=7)
            # Palm Front
            draw.ellipse([hand_r_x - 12, hand_r_y - 14, hand_r_x + 12, hand_r_y + 12], fill="#FFD1B3", outline="#FF1744", width=3)
            # Red Stop aura ring
            r_stop = int(20 + abs(push_z))
            draw.ellipse([hand_r_x - r_stop, hand_r_y - r_stop, hand_r_x + r_stop, hand_r_y + r_stop], outline="#FF1744", width=3)

        elif action_type == "rub_chest" or action_type == "fist_chest":  # PLEASE / SORRY / LOVE
            rub_x = cx + math.cos(t) * 12
            rub_y = body_top + 26 + math.sin(t) * 12
            draw.line([shoulder_l, (shoulder_l[0] - 10, shoulder_l[1] + 32)], fill="#FFD1B3", width=7)
            draw.line([shoulder_r, (shoulder_r[0] + 8, body_top + 34), (rub_x, rub_y)], fill="#FFD1B3", width=7)
            draw.ellipse([rub_x - 10, rub_y - 10, rub_x + 10, rub_y + 10], fill="#FFD1B3", outline="#0F172A", width=2)

        else:  # WHAT / WHERE / HOW: Shrugging palms
            shrug_y = math.sin(t) * 8
            draw.line([shoulder_l, (shoulder_l[0] - 24, shoulder_l[1] - 6 + shrug_y)], fill="#FFD1B3", width=7)
            draw.line([shoulder_r, (shoulder_r[0] + 24, shoulder_r[1] - 6 + shrug_y)], fill="#FFD1B3", width=7)
            draw.ellipse([shoulder_l[0] - 32, shoulder_l[1] - 16 + shrug_y, shoulder_l[0] - 16, shoulder_l[1] + 2 + shrug_y], fill="#FFD1B3", outline="#0F172A", width=2)
            draw.ellipse([shoulder_r[0] + 16, shoulder_r[1] - 16 + shrug_y, shoulder_r[0] + 32, shoulder_r[1] + 2 + shrug_y], fill="#FFD1B3", outline="#0F172A", width=2)

    def generate_gif_for_sign(self, sign_key: str, display_text: str = None) -> str:
        key = sign_key.upper().strip()
        sign_folder = os.path.join(self.signs_dir, key)
        os.makedirs(sign_folder, exist_ok=True)

        gif_path = os.path.join(sign_folder, "clip.gif")
        rel_url = f"/assets/signs/{key}/clip.gif"

        log.info("AutoGifAgent rendering ENLARGED EXPRESSIVE CARTOON GIF for: %s", key)

        colors = self.PALETTES.get(key, self.DEFAULT_PALETTE)
        primary_color, accent_color, action_type, emotion = colors[0], colors[1], colors[2], colors[3]
        label = display_text or key.capitalize()

        width, height = 320, 320
        num_frames = 24
        frames = []

        for f_idx in range(num_frames):
            t = (f_idx / float(num_frames)) * 2 * math.pi
            img = Image.new("RGBA", (width, height), (15, 23, 42, 255))
            draw = ImageDraw.Draw(img)

            # Stage Glow Ring
            cx, cy = width // 2, height // 2 - 6
            draw.ellipse([cx - 138, cy - 138, cx + 138, cy + 138], fill=(26, 35, 50, 255), outline=primary_color, width=4)

            # Render Expressive Avatar Action
            self._draw_cartoon_character(draw, cx, cy + 18, action_type, emotion, t, bg_accent=accent_color)

            # Label Pill
            draw.rectangle([0, height - 46, width, height], fill=(10, 15, 30, 245))
            draw.text((width // 2, height - 23), f"✨ {label}", fill=(240, 240, 255), anchor="mm")

            frames.append(img.convert("RGB"))

        # Save GIF
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            optimize=True,
            duration=50,
            loop=0
        )

        return rel_url

    def ensure_all_gifs(self):
        """Pre-generates expressive cartoon action GIFs for all configured signs in signs.json."""
        if not os.path.exists(self.signs_json):
            return

        try:
            with open(self.signs_json, "r", encoding="utf-8") as f:
                signs_data = json.load(f)
        except Exception as e:
            log.error("Failed to read signs.json: %s", e)
            return

        updated = False
        for key, info in signs_data.items():
            rel_gif = self.generate_gif_for_sign(key, info.get("display"))
            if info.get("video") != rel_gif:
                info["video"] = rel_gif
                updated = True

        if updated:
            try:
                with open(self.signs_json, "w", encoding="utf-8") as f:
                    json.dump(signs_data, f, indent=2, ensure_ascii=False)
                log.info("AutoGifAgent updated signs.json with expressive cartoon GIF paths.")
            except Exception as e:
                log.error("Failed to write signs.json: %s", e)
