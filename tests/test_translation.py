from backend.services.translation import TranslationService


class FakeAssetResolver:
    def __init__(self):
        self.translations = {
            "HELLO": {"en": "Hello", "hi": "नमस्ते", "te": "నమస్కారం", "es": "Hola", "fr": "Bonjour"},
            "I": {"en": "I", "hi": "मैं", "te": "నేను", "es": "Yo", "fr": "Je"},
            "LOVE": {"en": "Love", "hi": "प्यार", "te": "ప్రేమ", "es": "Amor", "fr": "Amour"},
            "YOU": {"en": "You", "hi": "तुम", "te": "నువ్వు", "es": "Tú", "fr": "Tu"},
            "THANK_YOU": {"en": "Thank You", "hi": "धन्यवाद", "te": "ధన్యవాదాలు", "es": "Gracias", "fr": "Merci"},
        }

    def lookup_translation(self, key):
        normalized = key.strip().upper()
        return {
            "key": normalized if normalized in self.translations else "UNKNOWN",
            "type": "phrase",
            "translations": self.translations[normalized],
        } if normalized in self.translations else None


def test_common_sentence_translates_u_alias_to_hindi_and_telugu():
    service = TranslationService(FakeAssetResolver())

    result = service.translate_sentence("I love u")

    assert result["en"] == "I love you"
    assert result["hi"] == "मुझे तुमसे प्यार है"
    assert result["te"] == "నేను నిన్ను ప్రేమిస్తున్నాను"
    assert result["auto_translated"] is True


def test_known_words_compose_translations():
    service = TranslationService(FakeAssetResolver())

    result = service.translate_sentence("I love")

    assert result["hi"] == "मैं प्यार"
    assert result["te"] == "నేను ప్రేమ"
    assert result["auto_translated"] is True


def test_known_multiword_phrases_compose_in_sentences():
    service = TranslationService(FakeAssetResolver())

    result = service.translate_sentence("Hello thank you")

    assert result["hi"] == "नमस्ते धन्यवाद"
    assert result["te"] == "నమస్కారం ధన్యవాదాలు"


def test_unknown_words_are_not_reported_as_translated():
    service = TranslationService(FakeAssetResolver())

    result = service.translate_sentence("I love unknownword")

    assert result["hi"] is None
    assert result["te"] is None
    assert result["auto_translated"] is False
