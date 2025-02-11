"""
Text normalization module for TTS processing.
Handles various text formats including URLs, emails, numbers, money, and special characters.
Converts them into a format suitable for text-to-speech processing.
"""

import re
from functools import lru_cache
import inflect

# Constants
VALID_TLDS = [
    "com",
    "org",
    "net",
    "edu",
    "gov",
    "mil",
    "int",
    "biz",
    "info",
    "name",
    "pro",
    "coop",
    "museum",
    "travel",
    "jobs",
    "mobi",
    "tel",
    "asia",
    "cat",
    "xxx",
    "aero",
    "arpa",
    "bg",
    "br",
    "ca",
    "cn",
    "de",
    "es",
    "eu",
    "fr",
    "in",
    "it",
    "jp",
    "mx",
    "nl",
    "ru",
    "uk",
    "us",
    "io",
]

VALID_UNITS = {
    "m":"meter", "cm":"centimeter", "mm":"millimeter", "km":"kilometer", "in":"inch", "ft":"foot", "yd":"yard", "mi":"mile",  # Length
    "g":"gram", "kg":"kilogram", "mg":"miligram",      # Mass
    "s":"second", "ms":"milisecond", "min":"minutes", "h":"hour", # Time
    "l":"liter", "ml":"mililiter", "cl":"centiliter", "dl":"deciliter",  # Volume
    "kph":"kilometer per hour", "mph":"mile per hour","mi/h":"mile per hour", "m/s":"meter per second", "km/h":"kilometer per hour", "mm/s":"milimeter per second","cm/s":"centimeter per second", "ft/s":"feet per second","cm/h":"centimeter per day", # Speed
    "°c":"degree celsius","c":"degree celsius", "°f":"degree fahrenheit","f":"degree fahrenheit", "k":"kelvin",     # Temperature
    "pa":"pascal", "kpa":"kilopascal", "mpa":"megapascal", "atm":"atmosphere",  # Pressure
    "hz":"hertz", "khz":"kilohertz", "mhz":"megahertz", "ghz":"gigahertz", # Frequency
    "v":"volt", "kv":"kilovolt", "mv":"mergavolt",      # Voltage
    "a":"amp", "ma":"megaamp", "ka":"kiloamp",      # Current
    "w":"watt", "kw":"kilowatt", "mw":"megawatt",      # Power
    "j":"joule", "kj":"kilojoule", "mj":"megajoule",      # Energy
    "Ω":"ohm", "kΩ":"kiloohm", "mΩ":"megaohm",      # Resistance (Ohm)
    "f":"farad", "µf":"microfarad", "nf":"nanofarad", "pf":"picofarad", # Capacitance
    "b":"bit", "kb":"kilobit", "mb":"megabit", "gb":"gigabit", "tb":"terabit", "pb":"petabit", # Data size
    "kbps":"kilobit per second","mbps":"megabit per second","gbps":"gigabit per second","tbps":"terabit per second",
    "px":"pixel"  # CSS units
}


# Pre-compiled regex patterns for performance
EMAIL_PATTERN = re.compile(
    r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}\b", re.IGNORECASE
)
URL_PATTERN = re.compile(
    r"(https?://|www\.|)+(localhost|[a-zA-Z0-9.-]+(\.(?:"
    + "|".join(VALID_TLDS)
    + "))+|[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})(:[0-9]+)?([/?][^\s]*)?",
    re.IGNORECASE,
)

UNIT_PATTERN = re.compile(r"((?<!\w)([+-]?)(\d{1,3}(,\d{3})*|\d+)(\.\d+)?)\s*(" + "|".join(sorted(list(VALID_UNITS.keys()),reverse=True)) + r"""){1}(?=[^\w\d]{1}|\b)""",re.IGNORECASE)

INFLECT_ENGINE=inflect.engine()

def split_num(num: re.Match[str]) -> str:
    """Handle number splitting for various formats"""
    num = num.group()
    if "." in num:
        return num
    elif ":" in num:
        h, m = [int(n) for n in num.split(":")]
        if m == 0:
            return f"{h} o'clock"
        elif m < 10:
            return f"{h} oh {m}"
        return f"{h} {m}"
    year = int(num[:4])
    if year < 1100 or year % 1000 < 10:
        return num
    left, right = num[:2], int(num[2:4])
    s = "s" if num.endswith("s") else ""
    if 100 <= year % 1000 <= 999:
        if right == 0:
            return f"{left} hundred{s}"
        elif right < 10:
            return f"{left} oh {right}{s}"
    return f"{left} {right}{s}"

def handle_units(u: re.Match[str]) -> str:
    unit_string=u.group(6).strip() 
    unit=unit_string
    
    print(unit)
    if unit_string.lower() in VALID_UNITS:
        unit=VALID_UNITS[unit_string.lower()].split(" ")
        
        # Handles the B vs b case
        if unit[0].endswith("bit"):
            b_case=unit_string[min(1,len(unit_string) - 1)]
            if b_case == "B":
                unit[0]=unit[0][:-3] + "byte"
            
        number=u.group(1).strip()
        unit[0]=INFLECT_ENGINE.no(unit[0],number)
    return " ".join(unit)

def handle_money(m: re.Match[str]) -> str:
    """Convert money expressions to spoken form"""
    m = m.group()
    bill = "dollar" if m[0] == "$" else "pound"
    if m[-1].isalpha():
        return f"{m[1:]} {bill}s"
    elif "." not in m:
        s = "" if m[1:] == "1" else "s"
        return f"{m[1:]} {bill}{s}"
    b, c = m[1:].split(".")
    s = "" if b == "1" else "s"
    c = int(c.ljust(2, "0"))
    coins = (
        f"cent{'' if c == 1 else 's'}"
        if m[0] == "$"
        else ("penny" if c == 1 else "pence")
    )
    return f"{b} {bill}{s} and {c} {coins}"


def handle_decimal(num: re.Match[str]) -> str:
    """Convert decimal numbers to spoken form"""
    a, b = num.group().split(".")
    return " point ".join([a, " ".join(b)])


def handle_email(m: re.Match[str]) -> str:
    """Convert email addresses into speakable format"""
    email = m.group(0)
    parts = email.split("@")
    if len(parts) == 2:
        user, domain = parts
        domain = domain.replace(".", " dot ")
        return f"{user} at {domain}"
    return email


def handle_url(u: re.Match[str]) -> str:
    """Make URLs speakable by converting special characters to spoken words"""
    if not u:
        return ""

    url = u.group(0).strip()

    # Handle protocol first
    url = re.sub(
        r"^https?://",
        lambda a: "https " if "https" in a.group() else "http ",
        url,
        flags=re.IGNORECASE,
    )
    url = re.sub(r"^www\.", "www ", url, flags=re.IGNORECASE)

    # Handle port numbers before other replacements
    url = re.sub(r":(\d+)(?=/|$)", lambda m: f" colon {m.group(1)}", url)

    # Split into domain and path
    parts = url.split("/", 1)
    domain = parts[0]
    path = parts[1] if len(parts) > 1 else ""

    # Handle dots in domain
    domain = domain.replace(".", " dot ")

    # Reconstruct URL
    if path:
        url = f"{domain} slash {path}"
    else:
        url = domain

    # Replace remaining symbols with words
    url = url.replace("-", " dash ")
    url = url.replace("_", " underscore ")
    url = url.replace("?", " question-mark ")
    url = url.replace("=", " equals ")
    url = url.replace("&", " ampersand ")
    url = url.replace("%", " percent ")
    url = url.replace(":", " colon ")  # Handle any remaining colons
    url = url.replace("/", " slash ")  # Handle any remaining slashes

    # Clean up extra spaces
    return re.sub(r"\s+", " ", url).strip()


def normalize_urls(text: str) -> str:
    """Pre-process URLs before other text normalization"""
    # Handle email addresses first
    text = EMAIL_PATTERN.sub(handle_email, text)

    # Handle URLs
    text = URL_PATTERN.sub(handle_url, text)

    return text


def normalize_text(text: str) -> str:
    """Normalize text for TTS processing"""
    # Pre-process URLs first
    text = normalize_urls(text)

    # Pre-process numbers with units
    text=UNIT_PATTERN.sub(handle_units,text)
    
    # Replace quotes and brackets
    text = text.replace(chr(8216), "'").replace(chr(8217), "'")
    text = text.replace("«", chr(8220)).replace("»", chr(8221))
    text = text.replace(chr(8220), '"').replace(chr(8221), '"')
    text = text.replace("(", "«").replace(")", "»")

    # Handle CJK punctuation and some non standard chars
    for a, b in zip("、。！，：；？–", ",.!,:;?-"):
        text = text.replace(a, b + " ")

    # Clean up whitespace
    text = re.sub(r"[^\S \n]", " ", text)
    text = re.sub(r"  +", " ", text)
    text = re.sub(r"(?<=\n) +(?=\n)", "", text)

    # Handle titles and abbreviations
    text = re.sub(r"\bD[Rr]\.(?= [A-Z])", "Doctor", text)
    text = re.sub(r"\b(?:Mr\.|MR\.(?= [A-Z]))", "Mister", text)
    text = re.sub(r"\b(?:Ms\.|MS\.(?= [A-Z]))", "Miss", text)
    text = re.sub(r"\b(?:Mrs\.|MRS\.(?= [A-Z]))", "Mrs", text)
    text = re.sub(r"\betc\.(?! [A-Z])", "etc", text)

    # Handle common words
    text = re.sub(r"(?i)\b(y)eah?\b", r"\1e'a", text)

    # Handle numbers and money
    text = re.sub(
        r"\d*\.\d+|\b\d{4}s?\b|(?<!:)\b(?:[1-9]|1[0-2]):[0-5]\d\b(?!:)", split_num, text
    )
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    text = re.sub(
        r"(?i)[$£]\d+(?:\.\d+)?(?: hundred| thousand| (?:[bm]|tr)illion)*\b|[$£]\d+\.\d\d?\b",
        handle_money,
        text,
    )
    text = re.sub(r"\d*\.\d+", handle_decimal, text)

    # Handle various formatting
    text = re.sub(r"(?<=\d)-(?=\d)", " to ", text)
    text = re.sub(r"(?<=\d)S", " S", text)
    text = re.sub(r"(?<=[BCDFGHJ-NP-TV-Z])'?s\b", "'S", text)
    text = re.sub(r"(?<=X')S\b", "s", text)
    text = re.sub(
        r"(?:[A-Za-z]\.){2,} [a-z]", lambda m: m.group().replace(".", "-"), text
    )
    text = re.sub(r"(?i)(?<=[A-Z])\.(?=[A-Z])", "-", text)

    return text.strip()
