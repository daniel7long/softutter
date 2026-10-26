from typing import List, Optional

from pydantic import BaseModel, Field

TAGS = {"none", "care", "silent", "link", "tone"}


class Segment(BaseModel):
    text: str
    tag: str = "none"


class Chunk(BaseModel):
    text: str
    ipa: str = ""
    reading: str = ""
    tip: str = ""
    segments: List[Segment] = []


class Sound(BaseModel):
    symbol: str = ""
    title: str
    tip: str = ""
    tag: str = "care"
    chunks: List[int] = []  # 0-based chunk indices where this sound occurs


class Frame(BaseModel):
    text: str
    note: str = ""


class Variant(BaseModel):
    label: str
    text: str


class ScaffoldRequest(BaseModel):
    language: str
    text: str = Field(min_length=1, max_length=300)
    l1: str = "en"
    context: str = "cafe"
    formality: str = "polite"
    cefr: str = "A2"


class Scaffold(BaseModel):
    language: str
    source_text: str
    l1: str
    context: str
    formality: str
    target: str
    meaning: str = ""
    reading: str = ""
    ipa: str = ""
    feedback: str = ""
    gap_filled: List[str] = []
    chunks: List[Chunk]
    sounds: List[Sound] = []
    hints: List[str] = []
    frame: Optional[Frame] = None
    variants: List[Variant] = []
    mock: bool = False


class PhraseIn(BaseModel):
    language: str
    target: str
    meaning: str = ""
    reading: str = ""
    ipa: str = ""
    payload: dict = {}


class PhraseStatus(BaseModel):
    status: str


class SoundEvent(BaseModel):
    title: str
    symbol: str = ""
    tag: str = "care"
    tip: str = ""
    outcome: str  # seen | clear | care


class SoundEventsIn(BaseModel):
    language: str
    events: List[SoundEvent]


# ---------- conversation mode ----------
class ConvTurn(BaseModel):
    role: str  # "partner" | "you"
    text: str


class ConverseRequest(BaseModel):
    language: str
    l1: str = "en"
    context: str = "cafe"
    formality: str = "polite"
    cefr: str = "A2"
    history: List[ConvTurn] = []  # everything said so far (empty at the start)
    user_text: str = Field(default="", max_length=300)  # the learner's latest turn ("" at the start)
    turn: int = 0  # number of learner turns completed including user_text (0 = opening)
    max_turns: int = 5


class ConvLine(BaseModel):
    text: str
    reading: str = ""
    meaning: str = ""


class ConvRecast(BaseModel):
    text: str
    reading: str = ""
    note: str = ""
    changed: bool = False  # False when the learner's own sentence was already fine


class ConvNext(BaseModel):
    """Help for the learner's next turn, all levels at once (1 hints, 2 frame, 3 full answer)."""

    hints: List[str] = []
    frame: str = ""
    answer: str = ""
    reading: str = ""
    meaning: str = ""


class ConvListen(BaseModel):
    symbol: str = ""
    title: str
    tip: str = ""
    tag: str = "care"


class ConverseResponse(BaseModel):
    role: str = "Barista"
    recast: Optional[ConvRecast] = None
    reply: ConvLine
    listen: Optional[ConvListen] = None
    next: Optional[ConvNext] = None
    done: bool = False
    mock: bool = False
