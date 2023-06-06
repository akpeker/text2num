from typing import List
import re

class DecimalMerger:
    def __init__(self, decimal_sym: str = ".", max_decimal:int = 4, max_group:int = 2) -> None:
        """Initialize the parser."""
        self.decimal_sym = decimal_sym
        self.max_decimal = max_decimal
        self.dec_ptrn = re.compile(f"^\d+\{decimal_sym}\d{{1,{max_group}}}$")
        self.grp_ptrn = re.compile(f"^\d{{1,{max_group}}}$")


    def merge_decimals(self, tokens: List[str]) -> List[str]:
        """join compound ordinal cases created by a text2num 1st pass

        Example:
                20° 7° -> 27°

        Greedy pusher: push along the token stream,
                       create a new ordinal sequence if an ordinal is found
                       stop sequence when no more ordinals are found
                       sum ordinal sequence

        """
        # print("[DecMer]", "|".join([f"[{t}]" if re.match(self.dec_ptrn, t) else t for t in tokens]))
        out_tokens = []
        in_decimal = False
        decimal = ""
        for token in tokens:
            if re.match(self.dec_ptrn, token):
                # finding a new decimal while in a decimal means previous one ended
                if in_decimal:
                    out_tokens.append(decimal)
                in_decimal = True
                decimal = token
            elif in_decimal:
                if re.match(self.grp_ptrn, token) and len(token) + len(decimal.split(self.decimal_sym)[1]) <= self.max_decimal:
                    decimal += token
                else:
                    in_decimal = False
                    out_tokens.append(decimal)
                    out_tokens.append(token)
            else:
                out_tokens.append(token)
        if in_decimal:
            out_tokens.append(decimal)
        return out_tokens

if __name__ == "__main__":
    DM = DecimalMerger()
    tests = [
        "3.1 2 3 4 5 6 7 8 9",
        "hello 3.1 2.5 okay",
        "hi 3. 7 42 yes",
        "123456.722 1 15",
    ]
    for t in tests:
        print(t, "\n=>\t", DM.merge_decimals(t.split()))