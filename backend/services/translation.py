class TranslationService:
    LANGS = ("en", "hi", "te", "es", "fr")

    def __init__(self, asset_resolver):
        self._asset_resolver = asset_resolver

    def translate_phrase(self, sign_key: str) -> dict:
        resolved = self._asset_resolver.resolve(sign_key)
        translations = resolved.get("translations", {}) or {}
        key_found = resolved.get("key") != "UNKNOWN"

        result = {"auto_translated": False}
        all_present = True

        for lang in self.LANGS:
            val = translations.get(lang)
            if val is None or val == "":
                result[lang] = None
                all_present = False
            else:
                result[lang] = val

        result["auto_translated"] = key_found and all_present
        return result

    def translate_fingerspelled(self, word: str) -> dict:
        return {
            "en": word,
            "hi": None,
            "te": None,
            "es": None,
            "fr": None,
            "auto_translated": False,
        }

    def translate_sentence(self, sentence_str: str, signs_arr=None, kind_arr=None) -> dict:
        if signs_arr is None:
            signs_arr = []
        if kind_arr is None:
            kind_arr = []

        n = max(len(signs_arr), len(kind_arr))
        per_lang_parts = {lang: [] for lang in self.LANGS}
        all_auto = True

        for i in range(n):
            sign = signs_arr[i] if i < len(signs_arr) else None
            kind = kind_arr[i] if i < len(kind_arr) else None

            if kind == "phrase" and sign is not None:
                tr = self.translate_phrase(sign)
            else:
                word = sign if isinstance(sign, str) else (sentence_str.split()[i] if i < len(sentence_str.split()) else "")
                tr = self.translate_fingerspelled(word)

            if not tr["auto_translated"]:
                all_auto = False

            for lang in self.LANGS:
                if tr.get(lang) is not None:
                    per_lang_parts[lang].append(tr[lang])

        result = {"auto_translated": all_auto}
        for lang in self.LANGS:
            joined = " ".join(per_lang_parts[lang]) if per_lang_parts[lang] else None
            result[lang] = joined

        if not signs_arr and not kind_arr:
            result["en"] = sentence_str
            for lang in ("hi", "te", "es", "fr"):
                # If only english string is provided without signs/kinds, try to auto-translate or just leave none
                result[lang] = None
            result["auto_translated"] = False

        return result

    def is_phrase_key(self, key) -> bool:
        resolved = self._asset_resolver.resolve(key)
        return resolved is not None and resolved.get("type") == "phrase"
