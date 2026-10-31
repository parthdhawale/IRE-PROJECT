"""CUAD contract type parsed from the file name (evaluation only, never a method input).

CUAD file names encode an exhibit number and a title, e.g. "...-EX-10.1-LICENSE AGREEMENT.txt",
or sometimes a qualified title like "...Trademark License Agreement.txt" or "...License and
Hosting Agreement.txt". `cuad_type` picks whichever known CUAD contract-type keyword appears
EARLIEST in the title -- the first one a human reading left to right would call it -- and is
used only to score family clustering (NMI/ARI) against ground truth, never as a method input.
"""

from __future__ import annotations

import re

# exhibit numbers: EX-10.1, EX-10.D2, EX-10.(D), EX-99.(K)(1), EX-4.(B)(II).3
_EX_MARKER = re.compile(r"(?<![A-Za-z])EX-\d[\dA-Z.]*(?:\([^)]*\)[\dA-Z.]*)*[-_]")

# type name -> regexes (checked in order, case-insensitive) that identify it in a title
_KEYWORDS: dict[str, list[str]] = {
    "Joint Venture": [r"JOINT VENTURE"],
    "Strategic Alliance": [r"STRATEGIC ALLIANCE"],
    "Co-Branding": [r"CO-?BRANDING"],
    "Non-Compete": [r"NON[- ]?COMPET\w*"],
    "IP": [r"INTELLECTUAL PROPERTY", r"\bIP\b"],
    "Affiliate": [r"AFFILIATE"],
    "Agency": [r"AGENCY"],
    "Collaboration": [r"COLLABORAT\w*", r"COOPERAT\w*"],
    "Consulting": [r"CONSULT\w*"],
    "Development": [r"DEVELOPMENT"],
    "Distributor": [r"DISTRIBUT\w*"],
    "Endorsement": [r"ENDORSEMENT"],
    "Franchise": [r"FRANCHISE"],
    "Hosting": [r"HOSTING"],
    "License": [r"LICEN[CS]\w*"],  # LICENSE and British LICENCE
    "Maintenance": [r"MAINTENANCE"],
    "Manufacturing": [r"MANUFACTUR\w*"],
    "Marketing": [r"MARKETING"],
    "Outsourcing": [r"OUTSOURCING"],
    "Promotion": [r"PROMOTION\w*"],
    "Reseller": [r"RESELL\w*"],
    "Service": [r"SERVIC\w*"],
    "Sponsorship": [r"SPONSOR\w*"],
    "Supply": [r"SUPPLY"],
    "Transportation": [r"TRANSPORTATION"],
}


def exhibit_title(doc_id: str) -> str:
    """Text after the last EX-<number>- marker in the file name, extension stripped."""
    name = doc_id.rsplit("/", 1)[-1]
    if name.lower().endswith(".txt"):
        name = name[:-4]
    matches = list(_EX_MARKER.finditer(name))
    return name[matches[-1].end():] if matches else name


def cuad_type(doc_id: str) -> str:
    """The CUAD contract type implied by the exhibit title, or "Other" if unrecognised."""
    title = exhibit_title(doc_id)
    if not title:
        return "Other"
    best_type, best_pos = None, None
    for type_name, patterns in _KEYWORDS.items():
        for pat in patterns:
            m = re.search(pat, title, re.IGNORECASE)
            if m and (best_pos is None or m.start() < best_pos):
                best_type, best_pos = type_name, m.start()
    return best_type or "Other"
