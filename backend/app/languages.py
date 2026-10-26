"""The six target languages (same set as Langogo) and the learner-language options."""

LANGUAGES = {
    "fr": {
        "code": "fr",
        "name": "French",
        "native": "Français",
        "locale": "fr-FR",
        "join": " ",
        "reading_label": None,
        "focus": (
            "liaison and enchainement, silent final consonants, nasal vowels, "
            "the front rounded vowels /y/ and /ø/, the uvular r, phrase-final stress"
        ),
        "placeholder_type": "Je voudrais un café au lait, s'il vous plaît.",
        "placeholder_mix": "Je voudrais … a coffee with milk, s'il vous plaît.",
    },
    "es": {
        "code": "es",
        "name": "Spanish",
        "native": "Español",
        "locale": "es-ES",
        "join": " ",
        "reading_label": None,
        "focus": (
            "tapped vs trilled r, five pure vowels, silent h and the silent u in que/qui/gue/gui, "
            "b and v sounding the same, syllable-timed rhythm, stress position"
        ),
        "placeholder_type": "Quisiera un café con leche, por favor.",
        "placeholder_mix": "Quisiera … a coffee with milk, por favor.",
    },
    "de": {
        "code": "de",
        "name": "German",
        "native": "Deutsch",
        "locale": "de-DE",
        "join": " ",
        "reading_label": None,
        "focus": (
            "the ich-Laut /ç/ vs the ach-Laut /x/, umlauts, final devoicing, "
            "schwa in -en and -e endings, the glottal stop, word-initial sp and st as /ʃp/ /ʃt/"
        ),
        "placeholder_type": "Ich hätte gern einen Kaffee mit Milch, bitte.",
        "placeholder_mix": "Ich hätte gern … a coffee with milk, bitte.",
    },
    "ja": {
        "code": "ja",
        "name": "Japanese",
        "native": "日本語",
        "locale": "ja-JP",
        "join": "",
        "reading_label": "Romaji",
        "focus": (
            "long vs short vowels, geminate consonants (small っ), moraic ん, "
            "devoiced vowels (です/ます), pitch accent, the ra-row flap"
        ),
        "placeholder_type": "ミルク入りのコーヒーをお願いします。",
        "placeholder_mix": "コーヒーを … with milk お願いします。",
    },
    "ko": {
        "code": "ko",
        "name": "Korean",
        "native": "한국어",
        "locale": "ko-KR",
        "join": " ",
        "reading_label": "Romanization",
        "focus": (
            "the three-way consonant contrast (plain / tense / aspirated), batchim and linking, "
            "ㅓ vs ㅗ, consonant assimilation and weakening of ㅎ"
        ),
        "placeholder_type": "우유를 넣은 커피 한 잔 주세요.",
        "placeholder_mix": "커피 … with milk 주세요.",
    },
    "zh": {
        "code": "zh",
        "name": "Chinese (Mandarin)",
        "native": "中文",
        "locale": "zh-CN",
        "join": "",
        "reading_label": "Pinyin",
        "focus": (
            "the four tones and the neutral tone, third-tone sandhi, retroflex vs alveolar "
            "(zh/ch/sh vs z/c/s), aspirated vs unaspirated consonants, ü"
        ),
        "placeholder_type": "请给我一杯加牛奶的咖啡。",
        "placeholder_mix": "请给我一杯 … coffee with milk。",
    },
}

PUBLIC_FIELDS = (
    "code",
    "name",
    "native",
    "locale",
    "join",
    "reading_label",
    "placeholder_type",
    "placeholder_mix",
)

# Language the learner already speaks: used for meanings, tips and feedback.
L1_OPTIONS = {
    "en": "English",
    "zh": "Chinese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
    "ko": "Korean",
}

CONTEXTS = {
    "cafe": "ordering at a café",
    "meeting": "meeting someone new",
    "friends": "chatting with friends",
    "work": "talking at work",
}

REGISTERS = {"polite": "polite", "casual": "casual, friendly"}


def public_languages() -> list[dict]:
    return [{k: v[k] for k in PUBLIC_FIELDS} for v in LANGUAGES.values()]
