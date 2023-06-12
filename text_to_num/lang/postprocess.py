from typing import List
import re


class DecimalMerger:
    def __init__(
        self, decimal_sym: str = ".", max_decimal: int = 40, max_group: int = 2
    ) -> None:
        """Initialize the merger."""
        self.decimal_sym = decimal_sym
        self.max_decimal = max_decimal
        self.dec_ptrn = re.compile(rf"\b\d+\{decimal_sym}\d{{1,{max_group}}}\b")
        self.grp_ptrn = re.compile(rf"\b\d{{1,{max_group}}}\b")

    def merge_decimals(self, tokens: List[str]) -> List[str]:
        """join decimal parts created by a text2num 1st pass,
        when the decimal digits are spoken one-by-one of in groups.

        Example:
                3.2 5 7 -> 3.257,  18.24 42 -> 18.2442
        Can limit the max number of decimal digits that can be merged this way,
        to also consider cases where a person actually is saying a different cardinal number (or a sequence) after a decimal.
        Also can limit max number of groups spoken at a time (usually 1 or 2 digits at a time in real life)
        """
        out_tokens = []
        in_decimal = False
        decimal = ""
        for token in tokens:
            if re.search(self.dec_ptrn, token):
                # finding a new decimal while in a decimal means previous one ended
                if in_decimal:
                    out_tokens.append(decimal)
                in_decimal = True
                decimal = token
            elif in_decimal:
                if (
                    re.search(self.grp_ptrn, token)
                    and len(token) + len(decimal.split(self.decimal_sym)[1])
                    <= self.max_decimal
                ):
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


class CurrencyFormatter:
    def __init__(self) -> None:
        """Initialize the formatter."""
        self.curr_whole = (
            "euros? dollars? dólare?s? dolare?s? con".split()
        )
        self.curr_fraction = (
            "céntimos? centimos? centavos?".split()
        )
        ptrn = (
            r"\b(\d+|un[oa]?) ("
            + "|".join(self.curr_whole)
            + r")( con| y con| y)?( \d{1,3}| un[oa]?)?("
            + "|".join([" " + x for x in self.curr_fraction])
            + ")?"
        )
        self.re_ptrn = re.compile(ptrn, re.IGNORECASE)

    def re_sub(self, match) -> str:
        num_maps = {"un":1, "uno":1, "una":1}
        whole = match.group(1).lower().strip()
        if whole in num_maps:
            whole = num_maps[whole]
        fract = match.group(4).lower().strip() if match.group(4) else "00"
        curr = "€" if match.group(2).startswith("eu") else "$"
        return f"{curr}{whole}.{fract.zfill(2)}"

    def format_currency(self, text: str) -> str:
        # x = re.findall(self.ptrn, text)
        x = re.sub(self.re_ptrn, self.re_sub, text)
        if x != text:
            print("\t", text, "==>", x)
        return text


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

    """
    1.50€ | un euro 0.50 céntimos | un euro con cincuenta céntimos
    1.50€ | un euro 50 céntimos | un euro cincuenta céntimos
    1.50€ | un euro 0.50 | un euro con cincuenta
    1.50€ | un euro 50 | un euro cincuenta
    1.50€ | 1.50 | uno con cincuenta
    1.50€ | 1 50 | uno cincuenta
    56.78€ | 56 euros 0.78 céntimos | cincuenta y seis euros con setenta y ocho céntimos
    56.78€ | 56 euros 78 céntimos | cincuenta y seis euros setenta y ocho céntimos
    56.78€ | 56 euros 0.78 | cincuenta y seis euros con setenta y ocho
    56.78€ | 56 euros 78 | cincuenta y seis euros setenta y ocho
    56.78€ | 56.78 | cincuenta y seis con setenta y ocho
    56.78€ | 56 78 | cincuenta y seis setenta y ocho
    $1.10 | Un dólar 10 céntimos | Un dólar diez céntimos
    $1.10 | Un dólar 10 | Un dólar diez
    $1.10 | 1 10 | Uno diez
    $1.10 | Un dollar y 10 centavos | Un dollar y diez centavos
    $3.16 | 3 dolares y 16 centavos | tres dolares y dieciseis centavos
    $3.16 | 3 dólares y 0.106 centavos | tres dólares y con diez y seis centavos
    $3.16 | 3 dólares y 10 6 centavos | tres dólares y diez y seis centavos
    """
