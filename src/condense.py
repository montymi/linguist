import re
from enum import Enum


class InputShape(Enum):
    DEBATE = "debate"
    LIST = "list"
    CHECKLIST = "checklist"
    TABLE = "table"
    CODE_BLOCK = "code_block"
    SHORT = "short"
    PROSE = "prose"


DEBATE_MARKERS = [
    "verdict", "one-line:", "where they agreed", "where all three agreed",
    "top 3 fixes", "where they disagreed",
]
DEBATE_AGENTS = [
    "linus", "sid", "lamport", "vogels", "kleppmann",
    "vonnegut", "asimov", "white", "shakespeare", "tupac",
]


def detect_shape(text: str) -> InputShape:
    lower = text.lower()
    lines = text.strip().split("\n")

    if any(marker in lower for marker in DEBATE_MARKERS):
        agent_hits = sum(1 for a in DEBATE_AGENTS if a in lower)
        if agent_hits >= 2:
            return InputShape.DEBATE

    checkbox_lines = [l for l in lines if re.match(r'\s*[-*]\s*\[[ x]\]', l)]
    if len(checkbox_lines) >= 2:
        return InputShape.CHECKLIST

    bullet_lines = [l for l in lines if re.match(r'\s*[-*]\s+\S', l) or re.match(r'\s*\d+\.\s+\S', l)]
    if len(bullet_lines) >= 3:
        return InputShape.LIST

    table_lines = [l for l in lines if l.strip().startswith("|") and l.strip().endswith("|")]
    if len(table_lines) >= 3:
        return InputShape.TABLE

    if "```" in text:
        return InputShape.CODE_BLOCK

    clean = _strip_markdown(text)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 5]
    if len(sentences) <= 2:
        return InputShape.SHORT

    return InputShape.PROSE


_AGENT_LABEL = re.compile(
    r"\*{0,2}(?:Linus|Sid|Vonnegut|Asimov|White|Shakespeare|Tupac|"
    r"Lamport|Vogels|Kleppmann|Agent [A-C])"
    r"(?:'s)?\s*(?:one-line|says|rewrite|verdict)?:?\*{0,2}\s*",
    re.IGNORECASE,
)
_FILE_PATH = re.compile(r'\S+/\S+\.\w{1,5}(?::\d+)?')
_EMOJI = re.compile(
    r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0000FE00-\U0000FE0F'
    r'\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0]+',
)


def _strip_markdown(text: str) -> str:
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = _AGENT_LABEL.sub('', text)
    text = _FILE_PATH.sub('', text)
    text = _EMOJI.sub('', text)
    text = re.sub(r'[#*`\[\]\(\)|>]', '', text)
    # underscores between word chars are identifiers — replace with spaces
    text = re.sub(r'(?<=\w)_(?=\w)', ' ', text)
    text = re.sub(r'_', '', text)
    text = re.sub(r'\n+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _cap(text: str, max_chars: int = 500) -> str:
    if len(text) > max_chars:
        return text[:max_chars - 3] + "..."
    return text


def _condense_debate(text: str) -> str:
    lines = text.split("\n")
    one_liners = []
    for line in lines:
        if "one-line:" in line.lower():
            part = line.split(":", 2)[-1].strip()
            part = re.sub(r'[*_]', '', part)
            part = _AGENT_LABEL.sub('', part).strip()
            if part:
                one_liners.append(part)

    top_fix = ""
    in_fixes = False
    for line in lines:
        if re.match(r'#+\s*top\s+\d+\s+fix', line, re.IGNORECASE):
            in_fixes = True
            continue
        if in_fixes and re.match(r'\s*1[.)]\s+', line):
            top_fix = re.sub(r'\s*1[.)]\s+', '', line).strip()
            top_fix = re.sub(r'\*\*([^*]+)\*\*', r'\1', top_fix)
            break

    parts = []
    if one_liners:
        parts.extend(one_liners[:3])
    if top_fix:
        parts.append(f"Top fix: {top_fix}")

    if parts:
        joined = ". ".join(p.rstrip(".") for p in parts) + "."
        return _cap(re.sub(r'[#*_`\[\]\(\)>]', '', joined))

    return _condense_prose(text)


def _condense_list(text: str) -> str:
    lines = text.strip().split("\n")
    items = []
    for line in lines:
        m = re.match(r'\s*(?:[-*]|\d+\.)\s+(.*)', line)
        if m:
            item = re.sub(r'[*_`]', '', m.group(1)).strip()
            if item:
                items.append(item)

    if not items:
        return _condense_prose(text)

    count = len(items)
    top = items[:3]
    result = f"{count} items. " + ". ".join(top)
    return _cap(_strip_markdown(result))


def _condense_checklist(text: str) -> str:
    lines = text.strip().split("\n")
    done = 0
    total = 0
    next_incomplete = ""
    for line in lines:
        m = re.match(r'\s*[-*]\s*\[([ x])\]\s*(.*)', line)
        if m:
            total += 1
            if m.group(1) == 'x':
                done += 1
            elif not next_incomplete:
                next_incomplete = re.sub(r'[*_`]', '', m.group(2)).strip()

    result = f"{done} of {total} complete."
    if next_incomplete:
        result += f" Next: {next_incomplete}"
    return _cap(result)


def _condense_table(text: str) -> str:
    lines = text.strip().split("\n")
    table_lines = [l for l in lines if l.strip().startswith("|") and l.strip().endswith("|")]
    if len(table_lines) < 2:
        return _condense_prose(text)

    header_cells = [c.strip() for c in table_lines[0].strip("|").split("|")]

    data_rows = []
    for line in table_lines[1:]:
        if re.match(r'\s*\|[\s-]+\|', line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        data_rows.append(cells)

    parts = []
    for row in data_rows[:3]:
        pairs = []
        for i, cell in enumerate(row):
            label = header_cells[i] if i < len(header_cells) else ""
            cell_clean = re.sub(r'[*_`]', '', cell).strip()
            if cell_clean:
                if label:
                    pairs.append(f"{label}: {cell_clean}")
                else:
                    pairs.append(cell_clean)
        if pairs:
            parts.append(", ".join(pairs))

    return _cap(". ".join(parts)) if parts else _condense_prose(text)


def _condense_code_block(text: str) -> str:
    stripped = re.sub(r'```[\s\S]*?```', '', text)
    return _condense_prose(stripped)


_CONCLUSION_SIGNAL = re.compile(
    r'\b(?:done|fixed|created|updated|added|removed|changed|moved|installed|'
    r'linked|built|deployed|merged|shipped|complete|ready|next step|'
    r'summary|in short|bottom line|takeaway|result|conclusion|'
    r'what changed|what\'s next)\b',
    re.IGNORECASE,
)


def _condense_prose(text: str) -> str:
    clean = _strip_markdown(text)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 10]
    if not sentences:
        return _cap(clean)

    conclusion = [s for s in sentences if _CONCLUSION_SIGNAL.search(s)]
    if conclusion:
        result = " ".join(conclusion[-3:])
    else:
        result = " ".join(sentences[-3:])
    return _cap(result)


def condense(text: str, verbatim: bool = False) -> str:
    if not text or not text.strip():
        return ""

    if verbatim:
        return _cap(_strip_markdown(text))

    shape = detect_shape(text)

    if shape == InputShape.SHORT:
        return _cap(_strip_markdown(text))

    condensers = {
        InputShape.DEBATE: _condense_debate,
        InputShape.LIST: _condense_list,
        InputShape.CHECKLIST: _condense_checklist,
        InputShape.TABLE: _condense_table,
        InputShape.CODE_BLOCK: _condense_code_block,
        InputShape.PROSE: _condense_prose,
    }

    return condensers[shape](text)
