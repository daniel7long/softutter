"""Offline logic checks (demo mode, no API keys needed). Run from backend/:  python tests/test_logic.py"""
import os, sys
os.environ["SOFTUTTER_MOCK"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from app.schemas import ScaffoldRequest
from app.llm import generate_scaffold, normalize
from app.languages import LANGUAGES
from app import assess, speech, store

# 1. all six languages scaffold, chunks survive validation, segments reassemble
for code in LANGUAGES:
    s = generate_scaffold(ScaffoldRequest(language=code, text="x"))
    join = LANGUAGES[code]["join"]
    assert len(s.chunks) == 3, (code, len(s.chunks))
    assert join.join(c.text for c in s.chunks).replace(" ","") == s.target.replace(" ",""), code
    for c in s.chunks:
        assert "".join(x.text for x in c.segments).strip() == c.text, (code, c.text)
    assert s.sounds and s.hints and s.frame and s.variants, code
    print("ok scaffold", code, s.target, [c.text for c in s.chunks])

# 2. normalize repairs bad model output
bad = {"target":"Hello there friend","chunks":[{"text":"Hello","segments":[{"text":"Hxllo","tag":"care"}]},{"text":"zzz"}],"sounds":[{"title":"t","tag":"weird"}]}
n = normalize(bad, ScaffoldRequest(language="fr", text="hi"))
assert len(n.chunks)==1 and n.chunks[0].text=="Hello there friend" and n.sounds[0].tag=="none"
try: normalize({}, ScaffoldRequest(language="fr", text="hi")); raise SystemExit("should fail")
except ValueError: pass
print("ok normalize repair")

# 3. compare: exact, slip, CJK
fr=["Je voudrais","un café au lait,","s'il vous plaît."]
r=assess.compare(fr,"je voudrais un café au lait s'il vous plait",  "fr")
assert all(c["status"]=="good" for c in r["chunks"]), r
r=assess.compare(fr,"Je voudrais un thé au lait, s'il vous plaît.","fr")
assert r["chunks"][1]["status"]=="care" and r["chunks"][0]["status"]=="good" and r["chunks"][2]["status"]=="good", r
print("fr wrong word ->", r["issues"])
zh=["请给我","一杯","加牛奶的咖啡。"]
r=assess.compare(zh,"请给我一杯加牛奶的咖啡","zh"); assert all(c["status"]=="good" for c in r["chunks"]), r
r=assess.compare(zh,"请给我一杯加牛奶的可乐","zh"); assert r["chunks"][2]["status"]=="care", r
ko=["우유를 넣은","커피 한 잔","주세요."]
r=assess.compare(ko,"우유를 넣은 커피 한잔 주세요","ko"); assert all(c["status"]=="good" for c in r["chunks"]), r
ja=["ミルク入りの","コーヒーを","お願いします。"]
r=assess.compare(ja,"ミルク入りのコーヒーをお願いします","ja"); assert all(c["status"]=="good" for c in r["chunks"]), r
print("ok compare zh/ko/ja")

# 4. demo assess alternates focus / clean
a1=assess.assess(b"x","a.wav","fr",fr,"en"); a2=assess.assess(b"x","a.wav","fr",fr,"en")
assert a1["focus"] and not a2["focus"], (a1, a2)
print("ok demo assess:", a1["focus"], "|", a2["wins"])

# 5. uncertain words from logprobs
import math
lp=[{"token":"Je","logprob":-0.01},{"token":" voudrais","logprob":-0.02},{"token":" un","logprob":-0.9},{"token":" café","logprob":-0.01}]
print("uncertain:", speech.uncertain_words(lp," "))
assert speech.uncertain_words(lp," ")==["un"]
lp2=[{"token":"请","logprob":-0.01},{"token":"给","logprob":-1.2},{"token":"我","logprob":-0.01}]
assert speech.uncertain_words(lp2,"")==["给"]
print("ok uncertain words")

# 6. transcribe/tts in demo mode
assert speech.transcribe(b"x","a.wav","ja")["mock"] and speech.synthesize("hi","fr",1.0) is None
print("ok demo speech")

# 7. phrasebook store
store.init()
p=store.add_phrase({"language":"fr","target":"TEST-PHRASE","payload":{"a":1}})
assert store.add_phrase({"language":"fr","target":"TEST-PHRASE"})["id"]==p["id"]
assert store.set_status(p["id"],"own")["status"]=="own"
store.delete_phrase(p["id"]); assert not [x for x in store.list_phrases() if x["target"]=="TEST-PHRASE"]
print("ok store")

# 8. My sounds: demo sounds link to chunks; events aggregate into statuses
for code in LANGUAGES:
    s = generate_scaffold(ScaffoldRequest(language=code, text="x"))
    assert all(snd.chunks for snd in s.sounds), code
    assert all(i < len(s.chunks) for snd in s.sounds for i in snd.chunks), code
assert store.sound_status([]) == "new"
assert store.sound_status(["care"]) == "working"
assert store.sound_status(["clear"]) == "new"
assert store.sound_status(["care", "clear", "clear"]) == "working"
assert store.sound_status(["care", "clear", "clear", "clear"]) == "steady"
T = "ZZ test sound"
store.add_sound_events("fr", [{"title": T, "symbol": "z", "tag": "care", "tip": "t", "outcome": "seen"}])
store.add_sound_events("fr", [{"title": T, "symbol": "z", "tag": "care", "tip": "t", "outcome": "care"}])
row = [x for x in store.list_sounds("fr") if x["key"] == "zz test sound"][0]
assert (row["seen"], row["attempts"], row["care"], row["status"]) == (1, 1, 1, "working"), row
for _ in range(3):
    store.add_sound_events("fr", [{"title": T, "outcome": "clear"}])
row = [x for x in store.list_sounds("fr") if x["key"] == "zz test sound"][0]
assert row["status"] == "steady" and row["history"] == ["care", "clear", "clear", "clear"], row
assert not [x for x in store.list_sounds("es") if x["key"] == "zz test sound"]
with store.db() as c:
    c.execute("DELETE FROM sound_events WHERE key='zz test sound'")
print("ok my sounds")

# 9. Conversation mode: five-turn scripts in all six languages, plus model-output repair
from app.schemas import ConverseRequest
from app.llm import generate_converse, normalize_converse
from app.mock_convo import SCRIPTS
for code in LANGUAGES:
    first = generate_converse(ConverseRequest(language=code))
    assert first.reply.text and first.next and first.next.answer and not first.done and first.recast is None, code
    assert "___" in first.next.frame and first.listen and first.listen.tag in ("care", "silent", "link", "tone"), code
    if LANGUAGES[code]["reading_label"]:
        assert first.reply.reading and first.next.reading, code
    spoken = []
    for t in range(1, 6):
        r = generate_converse(ConverseRequest(language=code, turn=t, user_text=first.next.answer if t == 1 else "x"))
        assert r.recast and r.recast.text == SCRIPTS[code]["steps"][t - 1]["a"], (code, t)
        assert r.done == (t == 5), (code, t)
        assert (r.next is None) == (t == 5), (code, t)
        spoken.append(r.reply.text)
    # the learner repeated the model answer on turn 1, so no correction was needed there
    assert generate_converse(ConverseRequest(language=code, turn=1, user_text=first.next.answer)).recast.changed is False
    assert generate_converse(ConverseRequest(language=code, turn=1, user_text="zzz")).recast.changed is True
    print("ok conversation", code, "|", first.reply.text, "->", spoken[-1])
try:
    generate_converse(ConverseRequest(language="fr", turn=2, user_text="  "))
    raise SystemExit("should reject empty learner turn")
except Exception as e:
    assert "Say or type" in str(getattr(e, "detail", e)), e
# a model reply with junk fields is repaired, a missing reply is rejected
req = ConverseRequest(language="fr", turn=2, user_text="x")
ok = normalize_converse({"reply": {"text": "Bonjour"}, "recast": {"text": "Salut", "note": "n"},
                         "listen": {"title": "t", "tag": "weird"}, "next": {"answer": "Oui", "hints": ["a", "b", "c", "d"]}}, req)
assert ok.recast.changed and ok.listen.tag == "care" and len(ok.next.hints) == 3 and ok.role == "Barista", ok
assert normalize_converse({"reply": {"text": "Au revoir"}, "next": {"answer": "x"}}, ConverseRequest(language="fr", turn=5, user_text="x")).next is None
try: normalize_converse({"reply": {"text": " "}}, req); raise SystemExit("should fail")
except ValueError: pass
print("ok conversation repair")
