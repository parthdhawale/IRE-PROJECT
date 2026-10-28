"""Section segmentation: heading regexes + a stack that turns headings into a tree.

IR idea: contracts are hierarchical (ARTICLE > Section 4.2 > (a) > (i)), and that structure is
a better unit for comparing documents and for retrieval than fixed 500-char windows.

1. Find heading candidates at line starts, or after 3+ spaces (MAUD files have almost no
   line breaks, so headings appear mid-line after runs of spaces).
2. Classify each heading by kind (article, section-with-depth, numbered-with-depth, (a), (i),
   (1), I., ALL-CAPS line) and place it with a stack: a kind already on the stack closes
   everything below it (sibling); numbered kinds also close deeper numbered kinds; any other
   kind opens a child.
3. Leaves: every node's own text (heading up to its first child) becomes a leaf. Leaves above
   max_leaf_chars are split on paragraph / line / sentence breaks; leaves below
   min_leaf_chars merge into an adjacent sibling leaf.
4. Documents with too few headings (e.g. privacy policies) fall back to paragraph splitting.

Every node stores (start, end) in ORIGINAL offsets; end is exclusive.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from trr.chunking.recursive import split_recursive

LEAF_SEPARATORS = ("\n\n", "\n", ". ", "; ", " ", "")
_ROMAN = r"(?:i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii|xiii|xiv|xv)"

# (kind, regex). Order matters: the first pattern that matches at a position wins.
_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("article", re.compile(r"(?:ARTICLE|Article|PART|Part)\s+(?:[IVXLC]+|\d+)\b")),
    ("sec", re.compile(r"(?:SECTION|Section)\s+(\d{1,2}(?:\.\d{1,2}){0,3})\.?(?=\s)")),
    ("num", re.compile(r"(\d{1,2}(?:\.\d{1,2}){1,3})\.?\s+(?=[A-Z“\"(])")),   # 4.2 / 4.2.1
    ("num", re.compile(r"(\d{1,2})\.\s+(?=[A-Z“\"(])")),                       # 4.
    ("paren_roman", re.compile(rf"\(({_ROMAN})\)\s")),
    ("paren_alpha", re.compile(r"\(([a-z]{1,2})\)\s")),
    ("paren_num", re.compile(r"\((\d{1,2})\)\s")),
    ("roman_dot", re.compile(r"((?:[IVX]{1,4})|(?:" + _ROMAN + r"))\.\s+(?=\S)")),
]
_CANDIDATE = re.compile(r"(?:^|(?<=\n)|(?<=[ \t]{3}))[ \t]*(?=\S)", re.M)
_CAPS_LINE = re.compile(r"[^\na-z]{4,80}(?=\n|$)")


@dataclass
class Node:
    start: int
    end: int
    level: int
    heading: str
    kind: str
    parent: "Node | None" = None
    children: list["Node"] = field(default_factory=list)

    @property
    def rank(self) -> float:
        """Depth for ordered kinds (article 0, sec2/num2 = 2, ...); unordered kinds rank inf."""
        if self.kind == "article":
            return 0
        if self.kind[:3] in ("sec", "num") and self.kind[3:].isdigit():
            return int(self.kind[3:])
        return float("inf")


def detect_headings(text: str) -> list[tuple[int, str, str]]:
    """(position, kind, heading text) for every heading candidate, in document order."""
    out: list[tuple[int, str, str]] = []
    last_alpha = ""
    for m in _CANDIDATE.finditer(text):
        pos = m.end()
        if out and pos < out[-1][0] + 2:
            continue
        kind = None
        for name, pat in _PATTERNS:
            hm = pat.match(text, pos)
            if not hm:
                continue
            if name in ("sec", "num"):
                kind = f"{name}{hm.group(1).count('.') + 1}"
            elif name == "paren_roman" and last_alpha and ord(hm.group(1)[0]) == ord(last_alpha[-1]) + 1:
                continue  # "(i)" right after "(h)" is a letter, not a roman numeral
            else:
                kind = name
            if name == "paren_alpha":
                last_alpha = hm.group(1)
            break
        if kind is None:
            line_start = pos == 0 or text[pos - 1] == "\n" or text[:pos].rstrip(" \t").endswith("\n")
            cm = _CAPS_LINE.match(text, pos) if line_start else None
            if cm and sum(ch.isalpha() for ch in cm.group(0)) >= 4:
                kind = "caps"
        if kind:
            line_end = text.find("\n", pos)
            line_end = len(text) if line_end == -1 else line_end
            out.append((pos, kind, text[pos:min(line_end, pos + 80)].strip()))
    return out


def _build_tree(text: str, headings: list[tuple[int, str, str]]) -> Node:
    root = Node(0, len(text), -1, "", "root")
    if headings and text[:headings[0][0]].strip():
        root.children.append(Node(0, headings[0][0], 0, "PREAMBLE", "preamble", root))
    stack: list[Node] = [root]

    def close(node: Node, at: int) -> None:
        node.end = at

    for pos, kind, heading in headings:
        new = Node(pos, len(text), 0, heading, kind)
        kinds = [n.kind for n in stack]
        if kind in kinds:                       # sibling of an open heading of the same kind
            while stack[-1].kind != kind:
                close(stack.pop(), pos)
            close(stack.pop(), pos)
        elif new.rank != float("inf"):          # numbered: close deeper or equal numbered nodes
            while len(stack) > 1 and stack[-1].rank >= new.rank:
                close(stack.pop(), pos)
        parent = stack[-1]
        new.parent, new.level = parent, parent.level + 1
        parent.children.append(new)
        stack.append(new)
    for n in stack[1:]:
        close(n, len(text))
    return root


def _make_leaves(text: str, node: Node, max_chars: int, min_chars: int) -> None:
    """Give every internal node an 'intro' leaf for its own text, split big leaves, merge tiny ones."""
    for child in list(node.children):
        _make_leaves(text, child, max_chars, min_chars)
    if node.children and node.kind != "root":
        own_end = node.children[0].start
        if text[node.start:own_end].strip():
            intro = Node(node.start, own_end, node.level + 1, node.heading, "intro", node)
            node.children.insert(0, intro)
    # merge tiny leaf children into the previous (else next) adjacent leaf sibling,
    # as long as the merged leaf stays within max_chars
    kids = node.children
    i = 0
    while i < len(kids):
        k = kids[i]
        if not k.children and len(text[k.start:k.end].strip()) < min_chars and len(kids) > 1:
            prev = kids[i - 1] if i > 0 else None
            nxt = kids[i + 1] if i + 1 < len(kids) else None
            if prev is not None and not prev.children and prev.end == k.start \
                    and k.end - prev.start <= max_chars:
                prev.end = k.end
                kids.pop(i)
                continue
            if nxt is not None and not nxt.children and nxt.start == k.end \
                    and nxt.end - k.start <= max_chars:
                nxt.start = k.start
                nxt.heading = nxt.heading or k.heading
                kids.pop(i)
                continue
        i += 1
    # split leaf children above max_chars on paragraph / line / sentence breaks
    for k in kids:
        if not k.children and k.end - k.start > max_chars:
            for s, e in split_recursive(text, max_chars, LEAF_SEPARATORS, k.start, k.end):
                k.children.append(Node(s, e, k.level + 1, "", "piece", k))


def segment(text: str, max_leaf_chars: int = 1500, min_leaf_chars: int = 100,
            min_headings: int = 3) -> tuple[Node, bool]:
    """Return (root, used_fallback). Leaves of the tree partition the non-whitespace text."""
    headings = detect_headings(text)
    if len(headings) < min_headings:
        root = Node(0, len(text), -1, "", "root")
        for s, e in split_recursive(text, max_leaf_chars, LEAF_SEPARATORS):
            root.children.append(Node(s, e, 0, "", "paragraph", root))
        _make_leaves(text, root, max_leaf_chars, min_leaf_chars)
        return root, True
    root = _build_tree(text, headings)
    _make_leaves(text, root, max_leaf_chars, min_leaf_chars)
    return root, False


def iter_nodes(root: Node):
    """Pre-order walk yielding (node, breadcrumb), skipping the virtual root."""
    def walk(n: Node, crumbs: list[str]):
        for c in n.children:
            path = crumbs + ([c.heading] if c.heading and c.kind not in ("intro", "piece") else [])
            yield c, " > ".join(path)
            yield from walk(c, path)
    yield from walk(root, [])


def leaves(root: Node) -> list[Node]:
    return [n for n, _ in iter_nodes(root) if not n.children]
