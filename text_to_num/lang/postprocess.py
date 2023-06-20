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

class PostProcessorES:
    MONTHS = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
    PERCENT_REGEX = re.compile(r"((\d)\s*per\s?cent\b)", re.IGNORECASE)
    # purely numeric dates e.g. 07032021 (07/03/2021), 732021 with 4 digit years 19xx-20xx
    NUMERIC_DATE_REGEX = re.compile(
        r"\b(0?[1-9]|10|11|12)"  # month
        + r" (0?[1-9]|[12]\d|30|31)"  # day
        + r"(19\d\d|20\d\d)\b"  # year 19xx, 20xx, 50-99, 10-39
    )
    # month name followed by day, year
    NUMERIC_MONTH_DATE_REGEX = re.compile(
        r"\b(0?[1-9]|[12]\d|30|31)"  # day
        + r"( del?)?\s+"
        + r"(" + "|".join(MONTHS) + r")"
        + r"( del?)?\s+"
        + r"(19\d\d|20\d\d)\b"  # year 19xx, 20xx, 50-99, 10-39
        , re.IGNORECASE
    )
    
    TIME_REGEX = re.compile(r"\b(son las|es la)\s+(2[0-4]|[01]?\d)( y ([0-5]?\d|60))?", re.IGNORECASE)
    
    def re_sub_month(self, match) -> str:
        da = match.group(1)
        mo = self.MONTHS.index(match.group(3).lower()) + 1
        ye = match.group(5)
        return fr"{da}/{mo}/{ye}"
    
    def format_date(self, text: str, month_name=False) -> str:
        """Format date into 03/05/2021"""
        if month_name:
            text = self.NUMERIC_MONTH_DATE_REGEX.sub(r"\1 \3 \5", text)
        else:
            text = self.NUMERIC_MONTH_DATE_REGEX.sub(self.re_sub_month, text)
        text = self.NUMERIC_DATE_REGEX.sub(r"\1/\2/\3", text)
        return text
    
    def re_sub_time(self, match) -> str:
        txt = match.group(1)
        hr = match.group(2)
        mn = match.group(4)
        if not mn:
            print("****", match)
        return f"{txt} {hr}:{mn.zfill(2)}"
    
    def format_time(self, text: str) -> str:
        text = self.TIME_REGEX.sub(self.re_sub_time, text) 
        return text

def test_DM():
    DM = DecimalMerger()
    tests = [
        "3.1 2 3 4 5 6 7 8 9",
        "hello 3.1 2.5 okay",
        "hi 3. 7 42 yes",
        "123456.722 1 15",
    ]
    for t in tests:
        print(t, "\n=>\t", DM.merge_decimals(t.split()))
    
def test_dates():
    PP = PostProcessorES()
    tests = [
        "Hoy es el 13 de octubre del 1999.",
    ]
    for t in tests:
        print(t, "\n=>\t", PP.format_date(t))
    
    # test on a random set of dates, print for visual check.
    print("TESTING RANDOM DATES")
    import random
    for x in range(20):
        da = random.randint(1, 30)
        mo = random.choice(PP.MONTHS)
        ye = random.randint(1900, 2030)
        co = random.choice(["del", "de"])
        t = f"Hoy es el {da} de {mo} {co} {ye}."
        print(t, "\t=>\t", PP.format_date(t))
    
    # test on all dates from given start to end. Automatic check.
    print("TESTING RANGE of DATES")
    from datetime import date, timedelta
    start_date = date(1900, 1, 1)
    end_date = date(2050, 1, 1)
    delta = timedelta(days=1)
    while start_date <= end_date:
        da = start_date.day
        mo = start_date.month
        mo_name = PP.MONTHS[mo-1]
        ye = start_date.year
        co = random.choice(["del", "de"])
        t = f"Hoy es el {da} de {mo_name} {co} {ye}."
        tf = PP.format_date(t)
        if tf != f"Hoy es el {da}/{mo}/{ye}.":
            print("????", t, "\t=>\t", tf)
        start_date += delta

def test_times():
    PP = PostProcessorES()
    tests = [
        "Son las ocho y treinta.",
    ]
    for t in tests:
        print(t, "\n=>\t", PP.format_date(t))
        
    print("TESTING RANDOM TIMES")
    import random
    for x in range(20):
        hr = random.randint(0, 24)
        mn = random.randint(0, 59)
        co = "es la" if hr==1 else "son las"
        t = f"Hey {co} {hr} y {mn}."
        print(t, "\t=>\t", PP.format_time(t))

if __name__ == "__main__":
    test_dates()
    test_times()
