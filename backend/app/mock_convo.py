"""Demo-mode conversation: one scripted café order per language (5 learner turns).

Each step has the partner's line (p), the model learner answer to it (a), the word(s) to blank out of
the answer for the sentence frame (blank), one hint, and one sound to listen for in the partner's line.
Demo mode cannot understand free speech, so every learner turn is "recast" to the model answer.
"""

import re

MEANING_NOTE = "Demo mode: a sample answer stands in for a real recast."


def S(p, pm, a, am, blank, hint, listen, pr="", ar=""):
    sym, title, tip, tag = listen
    return {
        "p": p, "pm": pm, "pr": pr,
        "a": a, "am": am, "ar": ar,
        "blank": blank, "hint": hint,
        "listen": {"symbol": sym, "title": title, "tip": tip, "tag": tag},
    }


SCRIPTS = {
    "fr": {
        "role": "Barista",
        "steps": [
            S("Bonjour ! Qu'est-ce que je vous sers ?", "Hello! What can I get you?",
              "Je voudrais un café au lait, s'il vous plaît.", "I'd like a coffee with milk, please.",
              "un café au lait", "Say what you'd like. Start with “Je voudrais”.",
              ("ʁ", "French r", "A soft r, made at the back of the throat, in “sers”.", "care")),
            S("Très bien ! Sur place ou à emporter ?", "Great! For here or to go?",
              "À emporter, s'il vous plaît.", "To go, please.",
              "À emporter", "Choose: sur place (here) or à emporter (to go).",
              ("ɑ̃", "Nasal vowels", "In “emporter” and “sur place” the vowel flows through the nose.", "care")),
            S("Et avec ça ? Un croissant, peut-être ?", "Anything with that? A croissant, maybe?",
              "Oui, un croissant aussi, merci.", "Yes, a croissant too, thanks.",
              "un croissant", "Say yes and name the pastry.",
              ("↗", "Question melody", "The voice rises at the end of “Un croissant, peut-être ?”.", "tone")),
            S("Ça fait quatre euros cinquante.", "That will be four euros fifty.",
              "Je peux payer par carte ?", "Can I pay by card?",
              "par carte", "Ask whether you can pay by card.",
              ("‿", "Linking words", "“quatre euros” runs together: katr‿øʁo.", "link")),
            S("Bien sûr. Voilà votre café. Bonne journée !", "Of course. Here's your coffee. Have a nice day!",
              "Merci, vous aussi !", "Thanks, you too!",
              "vous aussi", "Return the wish: you too!",
              ("e", "Silent endings", "The last e in “journée” and the s in “vous” stay quiet.", "silent")),
        ],
        "closing": ("À bientôt !", "See you soon!", ""),
    },
    "es": {
        "role": "Barista",
        "steps": [
            S("¡Buenos días! ¿Qué desea tomar?", "Good morning! What would you like to have?",
              "Quisiera un café con leche, por favor.", "I'd like a coffee with milk, please.",
              "un café con leche", "Say what you'd like. Start with “Quisiera”.",
              ("ð", "Soft “d”", "In “días” the d is light, a bit like a soft th.", "care")),
            S("Muy bien. ¿Para tomar aquí o para llevar?", "Very good. To have here or to go?",
              "Para llevar, por favor.", "To go, please.",
              "Para llevar", "Choose: aquí (here) or para llevar (to go).",
              ("b", "“v” sounds like “b”", "In “llevar” the v is a soft b.", "care")),
            S("¿Algo más? ¿Un cruasán, quizá?", "Anything else? A croissant, perhaps?",
              "Sí, un cruasán también, gracias.", "Yes, a croissant too, thanks.",
              "un cruasán", "Say yes and name the pastry.",
              ("↗", "Question melody", "Questions rise at the end: “¿Algo más?”.", "tone")),
            S("Son tres euros con cincuenta.", "That's three euros fifty.",
              "¿Puedo pagar con tarjeta?", "Can I pay by card?",
              "con tarjeta", "Ask whether you can pay by card.",
              ("ɾ", "Tapped “r”", "In “tres” and “euros” the r is one quick tap of the tongue.", "care")),
            S("Claro. Aquí tiene su café. ¡Que tenga un buen día!", "Of course. Here's your coffee. Have a good day!",
              "Gracias, igualmente.", "Thanks, same to you.",
              "igualmente", "Return the wish: same to you.",
              ("‿", "Words run together", "“Que tenga un buen día” flows with no gaps.", "link")),
        ],
        "closing": ("¡Hasta luego!", "See you later!", ""),
    },
    "de": {
        "role": "Barista",
        "steps": [
            S("Guten Tag! Was darf es sein?", "Good day! What can I get you?",
              "Ich hätte gern einen Milchkaffee, bitte.", "I'd like a milky coffee, please.",
              "einen Milchkaffee", "Say what you'd like. Start with “Ich hätte gern”.",
              ("k", "Final devoicing", "The g at the end of “Tag” sounds like k.", "care")),
            S("Gern. Zum Mitnehmen oder hier?", "Sure. To take away or here?",
              "Zum Mitnehmen, bitte.", "To take away, please.",
              "Zum Mitnehmen", "Choose: hier (here) or zum Mitnehmen (to go).",
              ("eː", "Long “e”", "“nehmen” has a long e: hold it for a moment.", "care")),
            S("Darf es sonst noch etwas sein? Vielleicht ein Croissant?", "Anything else? Maybe a croissant?",
              "Ja, gern, ein Croissant dazu.", "Yes, please, a croissant with it.",
              "ein Croissant", "Say yes and name the pastry.",
              ("↗", "Question melody", "Yes/no questions rise at the end.", "tone")),
            S("Das macht vier Euro fünfzig.", "That comes to four euros fifty.",
              "Kann ich mit Karte zahlen?", "Can I pay by card?",
              "mit Karte", "Ask whether you can pay by card.",
              ("y", "Rounded “ü”", "In “fünfzig” say ee with rounded lips.", "care")),
            S("Natürlich. Hier ist Ihr Kaffee. Einen schönen Tag noch!", "Of course. Here's your coffee. Have a lovely day!",
              "Danke, Ihnen auch!", "Thanks, you too!",
              "Ihnen auch", "Return the wish: you too!",
              ("ʃ", "“sch” sound", "“schönen” starts with sh, then a rounded ö.", "care")),
        ],
        "closing": ("Tschüss!", "Bye!", ""),
    },
    "ja": {
        "role": "店員",
        "steps": [
            S("いらっしゃいませ。ご注文は何になさいますか。", "Welcome. What would you like to order?",
              "カフェラテをお願いします。", "A café latte, please.",
              "カフェラテ", "Name the drink, then add をお願いします.",
              ("っ", "Small っ pause", "Hold a tiny silence in “irasshai”: i-ras-(pause)-shai.", "care"),
              "Irasshaimase. Gochūmon wa nani ni nasaimasu ka.", "Kafe rate o onegai shimasu."),
            S("店内でお召し上がりですか、お持ち帰りですか。", "For here, or to go?",
              "持ち帰りでお願いします。", "To go, please.",
              "持ち帰り", "Choose: 店内 (here) or 持ち帰り (to go).",
              ("♪", "Even beats", "Give every syllable about the same length.", "tone"),
              "Tennai de omeshiagari desu ka, omochikaeri desu ka.", "Mochikaeri de onegai shimasu."),
            S("ほかにご注文はありますか。クロワッサンはいかがですか。", "Anything else? Would you like a croissant?",
              "はい、クロワッサンもお願いします。", "Yes, a croissant too, please.",
              "クロワッサン", "Say yes and name the pastry, then もお願いします.",
              ("ū", "Long “ū”", "In “gochūmon” the u lasts two beats.", "care"),
              "Hoka ni gochūmon wa arimasu ka. Kurowassan wa ikaga desu ka.", "Hai, kurowassan mo onegai shimasu."),
            S("全部で五百五十円です。", "That's 550 yen in total.",
              "カードで払えますか。", "Can I pay by card?",
              "カード", "Ask whether you can pay by card.",
              ("u̥", "Whispered “u”", "The u in “desu” is nearly silent.", "silent"),
              "Zenbu de gohyaku gojū en desu.", "Kādo de haraemasu ka."),
            S("かしこまりました。ありがとうございました。", "Certainly. Thank you very much.",
              "ありがとうございます。", "Thank you very much.",
              "ありがとう", "Say thank you politely.",
              ("ō", "Long “ō”", "“Arigatō” ends on a long o: hold it.", "care"),
              "Kashikomarimashita. Arigatō gozaimashita.", "Arigatō gozaimasu."),
        ],
        "closing": ("またお越しくださいませ。", "Please come again.", "Mata okoshi kudasaimase."),
    },
    "ko": {
        "role": "점원",
        "steps": [
            S("어서 오세요. 주문하시겠어요?", "Welcome. Would you like to order?",
              "카페라테 한 잔 주세요.", "One café latte, please.",
              "카페라테", "Name the drink, then add 한 잔 주세요.",
              ("ʌ", "“eo” vs “o”", "“Eoseo” and “oseyo” use different vowels: open ㅓ, rounded ㅗ.", "care"),
              "Eoseo oseyo. Jumunhasigesseoyo?", "Kapelatte han jan juseyo."),
            S("여기에서 드시겠어요, 가져가시겠어요?", "Will you have it here or take it away?",
              "포장해 주세요.", "To go, please.",
              "포장", "Choose: 여기서 (here) or 포장 (to go).",
              ("‿", "Sound linking", "In “yeogieseo” a final sound flows into the next syllable.", "link"),
              "Yeogieseo deusigesseoyo, gajyeogasigesseoyo?", "Pojanghae juseyo."),
            S("다른 것도 필요하세요? 크루아상은 어때요?", "Anything else? How about a croissant?",
              "네, 크루아상도 하나 주세요.", "Yes, one croissant too, please.",
              "크루아상", "Say yes and name the pastry.",
              ("pʰ", "Puffed ㅍ", "“Piryo” starts with a puff of air, like p in “pie”.", "care"),
              "Dareun geotdo piryohaseyo? Keuruasangeun eottaeyo?", "Ne, keuruasangdo hana juseyo."),
            S("오천 원입니다.", "That's 5,000 won.",
              "카드로 계산해도 돼요?", "Can I pay by card?",
              "카드로", "Ask whether you can pay by card.",
              ("ㅁ", "b sounds like m", "In “imnida” the b turns into an m.", "link"),
              "Ocheon won imnida.", "Kadeuro gyesanhaedo dwaeyo?"),
            S("네, 여기 있습니다. 좋은 하루 보내세요!", "Sure, here you go. Have a nice day!",
              "감사합니다. 안녕히 계세요.", "Thank you. Goodbye.",
              "안녕히 계세요", "Thank them and say goodbye politely.",
              ("ㅅ", "Held endings", "The final sound in “itseumnida” is held, not released.", "silent"),
              "Ne, yeogi itseumnida. Joeun haru bonaeseyo!", "Gamsahamnida. Annyeonghi gyeseyo."),
        ],
        "closing": ("안녕히 가세요!", "Goodbye!", "Annyeonghi gaseyo!"),
    },
    "zh": {
        "role": "店员",
        "steps": [
            S("欢迎光临！您想喝点什么？", "Welcome! What would you like to drink?",
              "我想要一杯拿铁，谢谢。", "I'd like a latte, thank you.",
              "拿铁", "Start with “我想要”, then name the drink.",
              ("´", "Rising second tone", "“yíng” and “lín” rise like a question.", "tone"),
              "Huānyíng guānglín! Nín xiǎng hē diǎn shénme?", "Wǒ xiǎng yào yì bēi nátiě, xièxie."),
            S("在这儿喝还是带走？", "Drink here or take away?",
              "带走，谢谢。", "To go, thanks.",
              "带走", "Choose: 在这儿 (here) or 带走 (to go).",
              ("r", "Erhua “儿”", "“zhèr” ends with a curled r sound.", "care"),
              "Zài zhèr hē háishi dàizǒu?", "Dàizǒu, xièxie."),
            S("还要别的吗？要不要来个可颂？", "Anything else? Want a croissant?",
              "好的，再来一个可颂。", "Yes, one more croissant.",
              "可颂", "Say yes and name the pastry.",
              ("yí", "“一” changes tone", "Before a 4th tone or “ge”, 一 rises to yí.", "tone"),
              "Hái yào bié de ma? Yào bu yào lái ge kěsòng?", "Hǎo de, zài lái yí ge kěsòng."),
            S("一共三十五块。", "That's 35 yuan in total.",
              "可以刷卡吗？", "Can I pay by card?",
              "刷卡", "Ask whether you can pay by card.",
              ("ʂ", "Curled “sh”", "In “sān shí” the sh curls the tongue back.", "care"),
              "Yígòng sānshíwǔ kuài.", "Kěyǐ shuā kǎ ma?"),
            S("可以。这是您的拿铁，慢走！", "Sure. Here's your latte, take care!",
              "谢谢，再见！", "Thanks, goodbye!",
              "再见", "Thank them and say goodbye.",
              ("·", "Light second syllable", "In “xièxie” the second syllable is short and light.", "tone"),
              "Kěyǐ. Zhè shì nín de nátiě, màn zǒu!", "Xièxie, zàijiàn!"),
        ],
        "closing": ("再见，欢迎下次再来！", "Goodbye, come again!", "Zàijiàn, huānyíng xià cì zài lái!"),
    },
}


def _frame(answer: str, blank: str) -> str:
    return answer.replace(blank, "___", 1) if blank in answer else answer


def _norm(s: str) -> str:
    return re.sub(r"[\s.,!?¿¡。！？、，]+", "", s).lower()


def _next(step: dict) -> dict:
    return {
        "hints": [step["hint"]],
        "frame": _frame(step["a"], step["blank"]),
        "answer": step["a"],
        "reading": step["ar"],
        "meaning": step["am"],
    }


def mock_converse(language: str, turn: int, user_text: str) -> dict:
    """turn 0 = opening line; turn k = learner just finished turn k."""
    script = SCRIPTS[language]
    steps = script["steps"]
    out: dict = {"role": script["role"]}

    if turn >= 1:
        said = steps[min(turn, len(steps)) - 1]
        same = _norm(user_text) == _norm(said["a"])
        out["recast"] = {
            "text": said["a"],
            "reading": said["ar"],
            "note": "" if same else MEANING_NOTE,
            "changed": not same,
        }

    if turn >= len(steps):
        text, meaning, reading = script["closing"]
        out["reply"] = {"text": text, "meaning": meaning, "reading": reading}
        out["done"] = True
        return out

    step = steps[turn]
    out["reply"] = {"text": step["p"], "meaning": step["pm"], "reading": step["pr"]}
    out["listen"] = step["listen"]
    out["next"] = _next(step)
    out["done"] = False
    return out
