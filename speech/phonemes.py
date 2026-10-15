"""English grapheme-to-phoneme boundary with an offline, explainable fallback."""

import re
from typing import Protocol

from speech.types import Phoneme


class PhonemeAdapter(Protocol):
    def phonemize(self, text: str) -> list[Phoneme]: ...


# A deliberately small lexicon covers the shipped lesson and test fixtures. A production provider
# can replace this adapter with CMUdict, phonemizer/espeak, or a hosted G2P model without touching
# alignment, scoring, or persistence.
LEXICON: dict[str, tuple[str, ...]] = {
    "i": ("AY",),
    "really": ("R", "IH", "L", "IY"),
    "like": ("L", "AY", "K"),
    "led": ("L", "EH", "D"),
    "load": ("L", "OW", "D"),
    "rye": ("R", "AY"),
    "working": ("W", "ER", "K", "IH", "NG"),
    "remotely": ("R", "IH", "M", "OW", "T", "L", "IY"),
    "remote": ("R", "IH", "M", "OW", "T"),
    "red": ("R", "EH", "D"),
    "light": ("L", "AY", "T"),
    "right": ("R", "AY", "T"),
    "road": ("R", "OW", "D"),
}

LETTER_FALLBACK = {
    "a": "AE", "b": "B", "c": "K", "d": "D", "e": "EH", "f": "F", "g": "G",
    "h": "HH", "i": "IH", "j": "JH", "k": "K", "l": "L", "m": "M", "n": "N",
    "o": "OW", "p": "P", "q": "K", "r": "R", "s": "S", "t": "T", "u": "UH",
    "v": "V", "w": "W", "x": "K", "y": "Y", "z": "Z",
}


class LexiconPhonemeAdapter:
    """Map normalized English words to ARPAbet-like symbols."""

    def phonemize(self, text: str) -> list[Phoneme]:
        words = re.findall(r"[a-z']+", text.lower())
        result: list[Phoneme] = []
        for word in words:
            symbols = LEXICON.get(word) or tuple(
                LETTER_FALLBACK[letter]
                for letter in word
                if letter in LETTER_FALLBACK
            )
            result.extend(Phoneme(symbol=symbol, word=word) for symbol in symbols)
        return result
