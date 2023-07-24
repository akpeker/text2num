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
STENS: Dict[str, int] = {
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

for w10, v10 in MTENS.items():
    for w1, v1 in UNITS.items():
        STENS[w1 + "en" + w10] = v10 + v1
        if w1[-1] == "e":
            STENS[w1 + "ën" + w10] = v10 + v1

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

# Sort all numbers by length and start with the longest (we keep dict structure)
ALL_WORDS_SORTED_REVERSE = dict(sorted(
    # add "und" and "null" to NUMBERS
    {"en": None, "nul": 0, **NUMBERS}.items(),
    # take reverse length of keys to sort
    key=lambda kv: len(kv[0]),
    reverse=True
))


class Dutch(Language):

    # TODO: can this be replaced entirely?
    # Currently it has to be imported into 'parsers' as well ...
    NUMBER_DICT_NL = {"nul": 0, **NUMBERS}

    ORDINALS_FIXED_NL = {w:w+"de" for w in UNITS}
    ORDINALS_FIXED_NL = {w:w+"de" for w in STENS}
    ORDINALS_FIXED_NL["nul"] = "nulde"
    ORDINALS_FIXED_NL["één"] = "eerste"
    ORDINALS_FIXED_NL["drie"] = "derde"
    ORDINALS_FIXED_NL["acht"] = "achtste"
    
    LARGE_ORDINAL_SUFFIXES_NL = r"^(ster|stes|sten|ste)(\s|$)"  # RegEx for ord. > 19 ???????????????????????????????????????????????????

    MULTIPLIERS = MULTIPLIERS
    UNITS = UNITS
    STENS = STENS
    MTENS = MTENS
    # MTENS_WSTENS = MTENS_WSTENS
    HUNDRED = HUNDRED
    NUMBERS = NUMBERS

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
            word_base = None
            # example transf.: zwanzigster -> zwanzigste -> zwanzigs -> zwanzig
            if word.endswith("ter") or word.endswith("tes") or word.endswith("ten"):
                word_base = word[:-1].lower()       # e.g. erster -> erste
            elif word.endswith("te"):
                word_base = word.lower()
            if word_base:
                if word_base in self.ORDINALS_FIXED_NL:
                    return self.ORDINALS_FIXED_NL[word_base]
                else:
                    word_base = word_base[:-2]      # e.g. vierte -> vier
                    if word_base.endswith("s"):
                        word_base = word_base[:-1]  # e.g. zwanzigs -> zwanzig
                    if word_base in self.NUMBER_DICT_NL:
                        return word_base
                    # here we could still have e.g: "zweiundzwanzig"
                    if word_base.endswith(tuple(self.NUMBER_DICT_NL)):
                        # once again split - TODO: we should try to reduce split calls
                        word_base_split = self.split_number_word(word_base).split()
                        wbs_length = len(word_base_split)
                        if (
                            wbs_length > 0
                            and word_base_split[wbs_length - 1] in self.NUMBER_DICT_NL
                        ):
                            return "".join(word_base_split)
                    return None
            else:
                return None
        else:
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
        result = ""
        while len(text) > 0:
            # start with the longest
            found = False
            for sw, int_num in ALL_WORDS_SORTED_REVERSE.items():
                # Check at the beginning of the current sentence for the longest word in ALL_WORDS
                if text.startswith(sw):
                    if len(invalid_word) > 0:
                        result += invalid_word + " "
                        invalid_word = ""
                    result += sw + " "
                    text = text[len(sw):]
                    found = True
                    break
            # current beginning could not be assigned to a word:
            if not found:
                # is (large) ordinal ending?
                ord_match = None
                if len(result) > 3 and text.startswith("ste"):
                    ord_match = re.search(self.LARGE_ORDINAL_SUFFIXES_NL, text)

                if ord_match:
                    # add ordinal ending
                    end = ord_match.span()[1]
                    # result = result[:-1] + text[start:end]   # drop last space and add suffix
                    text = text[end:]
                    invalid_word = ""
                elif not text[0] == " ":
                    # move one index
                    invalid_word += text[0:1]
                    text = text[1:]
                else:
                    if len(invalid_word) > 0:
                        result += invalid_word + " "
                        invalid_word = ""
                    text = text[1:]
        if len(invalid_word) > 0:
            result += invalid_word + " "
        return result
