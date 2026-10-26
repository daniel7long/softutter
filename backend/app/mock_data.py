"""Demo-mode content: one café-order scaffold per language.

Used when no OPENAI_API_KEY is set, so the whole app can be explored offline.
The IPA and tips are sample content; real mode generates them with the LLM.
"""

N = "none"


def seg(*pairs):
    return [{"text": t, "tag": g} for t, g in pairs]


MEANING = "I'd like a coffee with milk, please."

MOCK = {
    "fr": {
        "target": "Je voudrais un café au lait, s'il vous plaît.",
        "reading": "",
        "ipa": "/ʒə vu.dʁɛ œ̃ ka.fe o lɛ sil vu plɛ/",
        "chunks": [
            {"text": "Je voudrais", "ipa": "/ʒə vu.dʁɛ/", "reading": "", "tip": "“Je” is almost a whisper.",
             "segments": seg(("Je voud", N), ("r", "care"), ("ai", N), ("s", "silent"))},
            {"text": "un café au lait,", "ipa": "/œ̃ ka.fe o lɛ/", "reading": "", "tip": "Keep “un” nasal. No hard n.",
             "segments": seg(("un", "care"), (" café au lai", N), ("t", "silent"), (",", N))},
            {"text": "s'il vous plaît.", "ipa": "/sil vu plɛ/", "reading": "", "tip": "Fall gently on “plaît”.",
             "segments": seg(("s'il vou", N), ("s", "silent"), (" plaî", N), ("t", "silent"), (".", N))},
        ],
        "sounds": [
            {"symbol": "œ̃", "title": "Nasal “un”", "tip": "Air flows through nose and mouth. No hard n at the end.", "tag": "care"},
            {"symbol": "ʁ", "title": "French r in “voudrais”", "tip": "Made at the back of the throat, like a soft gargle.", "tag": "care"},
            {"symbol": "s t", "title": "Silent endings", "tip": "The last s and t in voudrais, lait, vous and plaît stay quiet.", "tag": "silent"},
            {"symbol": "♪", "title": "Chunk rhythm", "tip": "Weight falls on the last syllable of each chunk, not on every word.", "tag": "link"},
        ],
        "hints": [
            "Your opening is already polite. Keep it.",
            "“Coffee with milk” is one fixed phrase in French. It starts with café.",
            "French says “coffee at the milk”. What small word means “at the”?",
        ],
        "frame": {"text": "Je voudrais un ___ au ___, s'il vous plaît.", "note": "Two blanks: the drink and what goes in it."},
        "variants": [
            {"label": "Polite", "text": "Je voudrais un café au lait, s'il vous plaît."},
            {"label": "Everyday", "text": "Je vais prendre un café au lait."},
            {"label": "Quick", "text": "Un café au lait, s'il vous plaît."},
        ],
        "stt": "Je voudrais un café au lait, s'il vous plaît.",
    },
    "es": {
        "target": "Quisiera un café con leche, por favor.",
        "reading": "",
        "ipa": "/kiˈsjeɾa un kaˈfe kon ˈle.tʃe poɾ faˈβoɾ/",
        "chunks": [
            {"text": "Quisiera", "ipa": "/kiˈsjeɾa/", "reading": "", "tip": "The u in “qui” is silent.",
             "segments": seg(("Q", N), ("u", "silent"), ("isie", N), ("r", "care"), ("a", N))},
            {"text": "un café con leche,", "ipa": "/un kaˈfe kon ˈle.tʃe/", "reading": "", "tip": "Stress falls on “fé” and “le”.",
             "segments": seg(("un caf", N), ("é", "care"), (" con le", N), ("ch", "care"), ("e,", N))},
            {"text": "por favor.", "ipa": "/poɾ faˈβoɾ/", "reading": "", "tip": "Tap the r with one quick flick of the tongue.",
             "segments": seg(("po", N), ("r", "care"), (" favo", N), ("r", "care"), (".", N))},
        ],
        "sounds": [
            {"symbol": "ɾ", "title": "Tapped r", "tip": "One quick flick of the tongue tip, like the tt in “butter”.", "tag": "care"},
            {"symbol": "u", "title": "Silent u in “qui”", "tip": "Qu sounds like k before e and i.", "tag": "silent"},
            {"symbol": "tʃ", "title": "ch in “leche”", "tip": "Like the ch in “cheese”.", "tag": "care"},
            {"symbol": "´", "title": "Stress", "tip": "The accent mark shows which syllable is loudest.", "tag": "link"},
        ],
        "hints": [
            "Start with a polite “I would like” verb.",
            "“Coffee with milk” uses the small word for “with”.",
            "Finish with the word for “please”.",
        ],
        "frame": {"text": "Quisiera un ___ con ___, por favor.", "note": "Two blanks: the drink and what goes in it."},
        "variants": [
            {"label": "Polite", "text": "Quisiera un café con leche, por favor."},
            {"label": "Everyday", "text": "Me pones un café con leche, por favor."},
            {"label": "Quick", "text": "Un café con leche, por favor."},
        ],
        "stt": "Quisiera un café con leche, por favor.",
    },
    "de": {
        "target": "Ich hätte gern einen Kaffee mit Milch, bitte.",
        "reading": "",
        "ipa": "/ɪç ˈhɛtə ɡɛʁn ˈaɪnən ˈkafe mɪt mɪlç ˈbɪtə/",
        "chunks": [
            {"text": "Ich hätte gern", "ipa": "/ɪç ˈhɛtə ɡɛʁn/", "reading": "", "tip": "“ch” after i is a soft hiss, not a k.",
             "segments": seg(("I", N), ("ch", "care"), (" h", N), ("ä", "care"), ("tte gern", N))},
            {"text": "einen Kaffee mit Milch,", "ipa": "/ˈaɪnən ˈkafe mɪt mɪlç/", "reading": "", "tip": "Reduce “-en” to a quick, light syllable.",
             "segments": seg(("ein", N), ("en", "silent"), (" Kaffee mit Mil", N), ("ch", "care"), (",", N))},
            {"text": "bitte.", "ipa": "/ˈbɪtə/", "reading": "", "tip": "The final e is a short, relaxed “uh”.",
             "segments": seg(("bitt", N), ("e", "silent"), (".", N))},
        ],
        "sounds": [
            {"symbol": "ç", "title": "The ich-Laut", "tip": "Shape your tongue for “ee”, then push air through.", "tag": "care"},
            {"symbol": "ɛ", "title": "Umlaut ä", "tip": "Like the e in “bed”.", "tag": "care"},
            {"symbol": "ə", "title": "Reduced endings", "tip": "-en and -e endings are short and relaxed.", "tag": "silent"},
            {"symbol": "ˈ", "title": "Word stress", "tip": "Stress usually lands on the first syllable.", "tag": "link"},
        ],
        "hints": [
            "A polite way to order starts with “I would have gladly”.",
            "German capitalizes every noun, including Kaffee and Milch.",
            "“With” is a short word, then the thing that goes in.",
        ],
        "frame": {"text": "Ich hätte gern einen ___ mit ___, bitte.", "note": "Two blanks: the drink and what goes in it."},
        "variants": [
            {"label": "Polite", "text": "Ich hätte gern einen Kaffee mit Milch, bitte."},
            {"label": "Everyday", "text": "Ich nehme einen Milchkaffee."},
            {"label": "Quick", "text": "Einen Kaffee mit Milch, bitte."},
        ],
        "stt": "Ich hätte gern einen Kaffee mit Milch, bitte.",
    },
    "ja": {
        "target": "ミルク入りのコーヒーをお願いします。",
        "reading": "miruku-iri no kōhī o onegai shimasu.",
        "ipa": "/mi.ɾɯ.kɯ i.ɾi no koː.çiː o o.ne.ɡai ɕi.ma.sɯ/",
        "chunks": [
            {"text": "ミルク入りの", "ipa": "/mi.ɾɯ.kɯ i.ɾi no/", "reading": "miruku-iri no", "tip": "The r is a quick tap, like the t in “butter”.",
             "segments": seg(("ミ", N), ("ル", "care"), ("ク入りの", N))},
            {"text": "コーヒーを", "ipa": "/koː.çiː o/", "reading": "kōhī o", "tip": "Hold each long vowel for two beats.",
             "segments": seg(("コ", N), ("ー", "care"), ("ヒ", N), ("ー", "care"), ("を", N))},
            {"text": "お願いします。", "ipa": "/o.ne.ɡai ɕi.ma.sɯ/", "reading": "onegai shimasu", "tip": "The final す is whispered: “shimas”.",
             "segments": seg(("お願い", N), ("し", "care"), ("ま", N), ("す", "silent"), ("。", N))},
        ],
        "sounds": [
            {"symbol": "ー", "title": "Long vowels", "tip": "A long vowel lasts twice as long. コーヒー has two long ones.", "tag": "care"},
            {"symbol": "ɾ", "title": "The ra-row flap", "tip": "One light tap of the tongue, not an English r.", "tag": "care"},
            {"symbol": "す", "title": "Devoiced endings", "tip": "です and ます end in a whispered u.", "tag": "silent"},
            {"symbol": "♪", "title": "Pitch", "tip": "Japanese pitch rises and falls by beat. Copy the target's melody.", "tag": "tone"},
        ],
        "hints": [
            "Start with what goes in: milk, then the word for “containing”.",
            "“Coffee” is borrowed from English and written in katakana.",
            "Finish with the polite request ending.",
        ],
        "frame": {"text": "___入りの___をお願いします。", "note": "Two blanks: what goes in and the drink."},
        "variants": [
            {"label": "Polite", "text": "ミルク入りのコーヒーをお願いします。"},
            {"label": "Everyday", "text": "ミルク入りのコーヒーください。"},
            {"label": "Quick", "text": "ミルクコーヒー、お願いします。"},
        ],
        "stt": "ミルク入りのコーヒーをお願いします。",
    },
    "ko": {
        "target": "우유를 넣은 커피 한 잔 주세요.",
        "reading": "uyureul neoeun keopi han jan juseyo.",
        "ipa": "/u.ju.ɾɯl nʌ.ɯn kʰʌ.pʰi han tɕan tɕu.se.jo/",
        "chunks": [
            {"text": "우유를 넣은", "ipa": "/u.ju.ɾɯl nʌ.ɯn/", "reading": "uyureul neoeun", "tip": "In 넣은 the ㅎ goes quiet, so it sounds like 너은.",
             "segments": seg(("우유를 ", N), ("넣", "link"), ("은", N))},
            {"text": "커피 한 잔", "ipa": "/kʰʌ.pʰi han tɕan/", "reading": "keopi han jan", "tip": "ㅋ and ㅍ are breathy. Feel a puff of air on your hand.",
             "segments": seg(("커", "care"), ("피", "care"), (" 한 잔", N))},
            {"text": "주세요.", "ipa": "/tɕu.se.jo/", "reading": "juseyo", "tip": "Keep it light and even.",
             "segments": seg(("주세요.", N))},
        ],
        "sounds": [
            {"symbol": "kʰ", "title": "Aspirated consonants", "tip": "ㅋ ㅍ ㅌ ㅊ come with a puff of air. Plain ㄱ ㅂ ㄷ ㅈ do not.", "tag": "care"},
            {"symbol": "ʌ", "title": "ㅓ vs ㅗ", "tip": "ㅓ is open, like the u in “but”. ㅗ is rounded.", "tag": "care"},
            {"symbol": "ㅎ", "title": "Weak ㅎ", "tip": "Between vowels, ㅎ fades and the syllables link.", "tag": "link"},
        ],
        "hints": [
            "Start with the word for milk plus the object marker.",
            "“Put in” is a verb that describes the milk going into the coffee.",
            "Korean orders end with “please give me”.",
        ],
        "frame": {"text": "___ 넣은 ___ 한 잔 주세요.", "note": "Two blanks: what goes in and the drink."},
        "variants": [
            {"label": "Polite", "text": "우유를 넣은 커피 한 잔 주세요."},
            {"label": "Everyday", "text": "우유 넣은 커피 한 잔 주세요."},
            {"label": "Quick", "text": "우유 커피 주세요."},
        ],
        "stt": "우유를 넣은 커피 한 잔 주세요.",
    },
    "zh": {
        "target": "请给我一杯加牛奶的咖啡。",
        "reading": "qǐng gěi wǒ yì bēi jiā niúnǎi de kāfēi.",
        "ipa": "/tɕʰiŋ kei wo i pei tɕja niu.nai tɤ kʰa.fei/",
        "chunks": [
            {"text": "请给我", "ipa": "/tɕʰiŋ kei wo/", "reading": "qǐng gěi wǒ", "tip": "Three third tones in a row: the first two lift slightly (qíng géi wǒ).",
             "segments": seg(("请", "tone"), ("给", "tone"), ("我", "tone"))},
            {"text": "一杯", "ipa": "/i pei/", "reading": "yì bēi", "tip": "“一” becomes yì before a first-tone syllable.",
             "segments": seg(("一", N), ("杯", N))},
            {"text": "加牛奶的咖啡。", "ipa": "/tɕja niu.nai tɤ kʰa.fei/", "reading": "jiā niúnǎi de kāfēi", "tip": "“的” is a neutral tone: short and light.",
             "segments": seg(("加牛", N), ("奶", "tone"), ("的", "silent"), ("咖啡。", N))},
        ],
        "sounds": [
            {"symbol": "ǎ", "title": "Third tone", "tip": "Dip down then up. Before another third tone, only the dip stays.", "tag": "tone"},
            {"symbol": "q", "title": "q is aspirated", "tip": "Say it with a puff of air, like “ch” in “cheese” with tongue flat.", "tag": "care"},
            {"symbol": "的", "title": "Neutral tone", "tip": "Short, light, no tone of its own.", "tag": "silent"},
        ],
        "hints": [
            "Start with the polite “please give me”.",
            "Use the measure word for cups before the drink.",
            "“Coffee with milk” is built as “add-milk-de coffee”.",
        ],
        "frame": {"text": "请给我一杯加___的___。", "note": "Two blanks: what goes in and the drink."},
        "variants": [
            {"label": "Polite", "text": "请给我一杯加牛奶的咖啡。"},
            {"label": "Everyday", "text": "我要一杯牛奶咖啡。"},
            {"label": "Quick", "text": "一杯牛奶咖啡，谢谢。"},
        ],
        "stt": "请给我一杯加牛奶的咖啡。",
    },
}


def mock_payload(language: str) -> dict:
    data = dict(MOCK[language])
    data["meaning"] = MEANING
    data["feedback"] = "Demo mode: this is sample content. Add an OpenAI key to scaffold your own sentences."
    data["gap_filled"] = []
    return data


# Which chunks each demo sound occurs in (same order as each language's "sounds" list).
SOUND_CHUNKS = {
    "fr": [[1], [0], [0, 1, 2], [0, 1, 2]],
    "es": [[0, 2], [0], [1], [1]],
    "de": [[0, 1], [0], [1, 2], [0, 1]],
    "ja": [[1], [0], [2], [0, 1, 2]],
    "ko": [[1], [0, 1], [0]],
    "zh": [[0, 2], [0], [2]],
}
for _lang, _chunks in SOUND_CHUNKS.items():
    assert len(_chunks) == len(MOCK[_lang]["sounds"]), _lang
    for _sound, _idx in zip(MOCK[_lang]["sounds"], _chunks):
        _sound["chunks"] = _idx
