import json
import os
import sys


class AssetResolver:
    FALLBACK_MESSAGE = "Visual demonstration unavailable"
    FALLBACK_IMAGE = "/assets/signs/UNKNOWN/placeholder.svg"

    def __init__(self, json_path=None):
        if json_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(base_dir, "assets", "signs.json")
        with open(json_path, "r", encoding="utf-8") as f:
            self._signs = json.load(f)
        self._unknown_template = self._signs.get("UNKNOWN", {})

    def resolve(self, sign_key):
        meta = self._signs.get(sign_key)
        if meta is None:
            meta = dict(self._unknown_template)
            meta["display"] = sign_key
            meta["description"] = "Unrecognized sign key: " + sign_key
            key = "UNKNOWN"
        else:
            meta = dict(meta)
            key = sign_key
        result = {
            "key": key,
            "display": meta.get("display", sign_key),
            "description": meta.get("description", ""),
            "type": meta.get("type", "fallback"),
            "video": meta.get("video", None),
            "image": meta.get("image", self.FALLBACK_IMAGE),
            "svg_animation": meta.get("svg_animation", None),
            "translations": meta.get("translations", {}),
            "fallback": self.FALLBACK_MESSAGE,
            "fallback_image": self.FALLBACK_IMAGE,
        }
        return result


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    resolver = AssetResolver()
    print("=== resolve('HELLO') ===")
    hello = resolver.resolve("HELLO")
    for k, v in hello.items():
        print(f"  {k}: {v}")
    print()
    print("=== resolve('ZEBRA') ===")
    zebra = resolver.resolve("ZEBRA")
    for k, v in zebra.items():
        print(f"  {k}: {v}")
