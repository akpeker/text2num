# MIT License

# Copyright (c) 2018-2019 Groupe Allo-Media

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Dict, Tuple, Set, Optional
import re

from .base import Language

#
# CONSTANTS
# Built once on import.
#

# Those words multiplies lesser numbers (see Rules)
# Special case: "hundred" is processed apart.
MULTIPLIERS = {
    "duizend": 1_000,
    "miljoen": 1_000_000,
    "miljard": 1_000_000_000,
    "biljoen": 1_000_000_000_000,
    "biljard": 1_000_000_000_000_000,
    "triljoen": 1_000_000_000_000_000_000,
    "triljard": 1_000_000_000_000_000_000_000,
}

# Units are terminals (see Rules)
# Special case: "zero/O" is processed apart.
UNITS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "één twee drie vier vijf zes zeven acht negen".split(), 1
    )
}
# Unit variants
UNITS["een"] = 1    # TODO: use that this can be followed only by "100", "1000", "en"

# Single tens are terminals (see Rules)
STENS_19: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "tien elf twaalf dertien veertien vijftien zestien zeventien achttien negentien".split(),
        10,
    )
}

# Ten multiples
# Ten multiples may be followed by a unit only;
MTENS: Dict[str, int] = {
    word: value * 10
    for value, word in enumerate(
        "twintig dertig veertig vijftig zestig zeventig tachtig negentig".split(), 2
    )
}

# Single tens that are from 20 to 99. In Dutch, consider these as atomic units
#    so that we don't have to deal with the reversed order of tens & units.
STENS_99 = dict()
for w10, v10 in MTENS.items():
    for w1, v1 in UNITS.items():
        STENS_99[w1 + "en" + w10] = v10 + v1
        if w1[-1] == "e":
            STENS_99[w1 + "ën" + w10] = v10 + v1

STENS = STENS_19.copy()
STENS.update(STENS_99)

# Ten multiples that can be combined with STENS
# MTENS_WSTENS: Set[str] = set()

# "hundred" has a special status (see Rules)
HUNDRED = {"honderd": 100}  # einhundert?

# All number words

NUMBERS = MULTIPLIERS.copy()
NUMBERS.update(UNITS)
NUMBERS.update(STENS)
NUMBERS.update(MTENS)
NUMBERS.update(HUNDRED)
# NUMBERS.update(COMPOSITES) # COMPOSITES are already in STENS for the German language

AND = "en"
ZERO = {"nul"}



class Dutch(Language):
    NUMBERS_SET = set(NUMBERS.keys())
    NUMBERS_SET.add("nul")
    
    # Irregular ordinals
    ORDINALS_IR = {"eerste":"één", "derde":"drie"}
    # Ordinals that are made by appending -de
    ORDINALS_DE = set("tien elf twaalf dertien veertien vijftien zestien zeventien achttien negentien".split())
    ORDINALS_DE.update(set("nul twee vier vijf zes zeven negen".split()))
    # Ordinals that are made by appending -ste
    ORDINALS_STE = set([*MULTIPLIERS, *MTENS, *STENS_99, *HUNDRED, "acht"])

    MULTIPLIERS = MULTIPLIERS
    UNITS = UNITS
    STENS = STENS
    MTENS = MTENS
    # MTENS_WSTENS = MTENS_WSTENS
    HUNDRED = HUNDRED
    NUMBERS = NUMBERS

    # Sort all numbers by length and start with the longest. For splitting merged words.
    ALL_WORDS_SORTED_REVERSE = sorted(
        # add "und" and "null" to NUMBERS
        ["en", "nul", *NUMBERS, *ORDINALS_IR],
        # take reverse length of keys to sort
        key=lambda x: len(x),
        reverse=True
    )

    SIGN = {"plus": "+", "minus": "-"}
    ZERO = ZERO
    DECIMAL_SEP = "komma"
    DECIMAL_SYM = ","

    # AND_NUMS = set(UNITS.keys()).union(set(STENS.keys()).union(set(MTENS.keys())))
    AND_NUMS: Set[str] = set()
    AND = AND

    NEVER_IF_ALONE = {"één"}
    NEVER_CONNECTS_WITH_AND = {"één"}

    # Relaxed composed numbers (two-words only)
    # start => (next, target)
    RELAXED: Dict[str, Tuple[str, str]] = {}  # TODO: not supported yet

    def ord2card(self, word: str) -> Optional[str]:
        """Convert ordinal number to cardinal.
        Return None if word is not an ordinal or is better left in letters.
        """
        if len(word) > 4:
            if word in self.ORDINALS_IR:
                return self.ORDINALS_IR[word]
            if word.endswith("ste") and word[:-3].lower() in self.ORDINALS_STE:
                return word[:-3]
            if word.endswith("de") and word[:-2].lower() in self.ORDINALS_DE:
                return word[:-2]
        return None

    def num_ord(self, digits: str, original_word: str) -> str:
        """Add suffix to number in digits to make an ordinal"""
        return f"{digits}e."

    def normalize(self, word: str) -> str:
        return word

    def split_number_word(self, word: str) -> str:
        """Splits number words into separate words, e.g.
        "zevenhonderdtweeëndertigduizendvijfhonderdtweeënzeventig" -> 'zeven honderd tweeëndertig duizend vijf honderd tweeënzeventig '
        """
        text = word.lower()  # NOTE: if we want to use this outside it should keep case
        invalid_word = ""
        result = []
        while len(text) > 0:
            # start with the longest
            found = False
            for sw in self.ALL_WORDS_SORTED_REVERSE:
                # Check at the beginning of the current sentence for the longest word in ALL_WORDS
                if text.startswith(sw):
                    if len(invalid_word) > 0:
                        result += invalid_word + " "
                        invalid_word = ""
                    # If this is a regular ordinal, expand word accordingly
                    if text[len(sw):].startswith("ste") and sw in self.ORDINALS_STE:
                        sw += "ste"
                    result.append(sw)
                    text = text[len(sw):]
                    found = True
                    break
            # current beginning could not be assigned to a word:
            if not found:
                if not text[0] == " ":
                    # move one index
                    invalid_word += text[0:1]
                    text = text[1:]
                else:
                    if len(invalid_word) > 0:
                        result.append(invalid_word)
                        invalid_word = ""
                    text = text[1:]
        if len(invalid_word) > 0:
            # for now, assume regular-"de"-ordinal (e.g. negende) can occur only at the end
            if invalid_word == "de" and result and result[-1] in self.ORDINALS_DE:
                result[-1] += "de"
            else:
                result.append(invalid_word)
        return " ".join(result)
