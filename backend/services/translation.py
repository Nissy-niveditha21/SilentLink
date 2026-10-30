import re


class TranslationService:
    LANGS = ("en", "hi", "te", "es", "fr")
    SENTENCE_TRANSLATIONS = {
        "I LOVE YOU": {
            "en": "I love you",
            "hi": "मुझे तुमसे प्यार है",
            "te": "నేను నిన్ను ప్రేమిస్తున్నాను",
            "es": "Te quiero",
            "fr": "Je t’aime",
        }
    }
    WORD_ALIASES = {"U": "YOU"}

    def __init__(self, asset_resolver):
        self._asset_resolver = asset_resolver

    def _canonical_words(self, text: str) -> list[str]:
        words = re.findall(r"[^\W_]+(?:['’][^\W_]+)?", text, flags=re.UNICODE)
        return [self.WORD_ALIASES.get(word.upper(), word.upper()) for word in words]

    def _lookup(self, words: list[str]) -> dict:
        key = "_".join(words)
        resolved = self._asset_resolver.lookup_translation(key)
        translations = resolved.get("translations", {}) if resolved else {}
        if resolved and all(translations.get(lang) for lang in self.LANGS):
            return {lang: translations[lang] for lang in self.LANGS}
        return {}

    def translate_phrase(self, sign_key: str) -> dict:
        resolved = self._asset_resolver.lookup_translation(sign_key)
        translations = resolved.get("translations", {}) if resolved else {}

        result = {"auto_translated": False}
        all_present = True
        for lang in self.LANGS:
            value = translations.get(lang)
            if not value:
                result[lang] = None
                all_present = False
            else:
                result[lang] = value
        result["auto_translated"] = resolved is not None and all_present
        return result

    def translate_fingerspelled(self, word: str) -> dict:
        words = self._canonical_words(word)
        translations = self._lookup(words) if words else {}
        if translations:
            return {**translations, "auto_translated": True}
        return {
            "en": word,
            "hi": None,
            "te": None,
            "es": None,
            "fr": None,
            "auto_translated": False,
        }

    def translate_sentence(self, sentence_str: str, signs_arr=None, kind_arr=None) -> dict:
        if signs_arr or kind_arr:
            signs = signs_arr or []
            kinds = kind_arr or []
            translations = {lang: [] for lang in self.LANGS}
            auto_translated = True

            for index in range(max(len(signs), len(kinds))):
                sign = signs[index] if index < len(signs) else None
                kind = kinds[index] if index < len(kinds) else None
                part = (
                    self.translate_phrase(str(sign))
                    if kind == "phrase" and sign is not None
                    else self.translate_fingerspelled(str(sign or ""))
                )
                auto_translated = auto_translated and part["auto_translated"]
                for lang in self.LANGS:
                    if part.get(lang):
                        translations[lang].append(part[lang])

            result = {
                lang: " ".join(values) if values else None
                for lang, values in translations.items()
            }
            result["auto_translated"] = auto_translated
            return result

        words = self._canonical_words(sentence_str)
        normalized = " ".join(words)
        exact = self.SENTENCE_TRANSLATIONS.get(normalized)
        if exact:
            return {**exact, "auto_translated": True}

        full_phrase = self._lookup(words) if words else {}
        if full_phrase:
            return {**full_phrase, "auto_translated": True}

        parts = {lang: [] for lang in self.LANGS[1:]}
        index = 0
        while index < len(words):
            match = None
            match_length = 0
            for length in range(min(4, len(words) - index), 0, -1):
                match = self._lookup(words[index:index + length])
                if match:
                    match_length = length
                    break
            if not match:
                return {
                    "en": sentence_str,
                    "hi": None,
                    "te": None,
                    "es": None,
                    "fr": None,
                    "auto_translated": False,
                }
            for lang in self.LANGS[1:]:
                parts[lang].append(match[lang])
            index += match_length

        result = {"en": sentence_str, "auto_translated": bool(words)}
        result.update({
            lang: " ".join(translated_parts) if translated_parts else None
            for lang, translated_parts in parts.items()
        })
        return result

    def is_phrase_key(self, key) -> bool:
        resolved = self._asset_resolver.lookup_translation(key)
        return resolved is not None and resolved.get("type") == "phrase"
