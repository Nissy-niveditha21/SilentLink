import json
import os
from backend.services.auto_gif_agent import AutoGifAgent


class AssetResolver:
    FALLBACK_MESSAGE = "Visual demonstration unavailable"
    FALLBACK_IMAGE = "/assets/signs/UNKNOWN/placeholder.svg"

    def __init__(self, json_path=None):
        if json_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.assets_dir = os.path.join(base_dir, "assets")
            json_path = os.path.join(self.assets_dir, "signs.json")
        else:
            self.assets_dir = os.path.dirname(json_path)

        self.gif_agent = AutoGifAgent(self.assets_dir)
        
        with open(json_path, "r", encoding="utf-8") as f:
            self._signs = json.load(f)
        self._unknown_template = self._signs.get("UNKNOWN", {})

    def resolve(self, sign_key):
        key = sign_key.strip().upper()
        meta = self._signs.get(key)
        if meta is None:
            meta = dict(self._unknown_template)
            meta["display"] = sign_key
            meta["description"] = "Unrecognized sign key: " + sign_key
            key = "UNKNOWN"
        else:
            meta = dict(meta)
            key = sign_key

        video_url = meta.get("video")
        if not video_url:
            # Dynamically generate GIF via AutoGifAgent if missing
            video_url = self.gif_agent.generate_gif_for_sign(key, meta.get("display"))

        result = {
            "key": key,
            "display": meta.get("display", sign_key),
            "description": meta.get("description", ""),
            "type": meta.get("type", "fallback"),
            "video": video_url,
            "image": meta.get("image", self.FALLBACK_IMAGE),
            "svg_animation": meta.get("svg_animation", None),
            "translations": meta.get("translations", {}),
            "fallback": self.FALLBACK_MESSAGE,
            "fallback_image": self.FALLBACK_IMAGE,
        }
        return result

