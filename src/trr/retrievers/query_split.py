"""Query segmentation: split a benchmark query into its identity part and its content part.

IR idea: a LegalBench-RAG query does two jobs at once. The header ("Consider the NDA between
CEII and ...") says WHICH document; the question ("Does the document allow ...?") says WHICH
clause. Scoring whole documents with the full query lets ~15 generic question words, shared by
every NDA, outvote the one or two rare party names (results/notes/failure_analysis_docfirst.md).
Giving each job its own part of the query keeps the identity signal clean.
"""

from __future__ import annotations


def split_query(text: str) -> tuple[str, str]:
    """(header, question): the text before the first ';' and the text after it.

    Every benchmark query has a header; without a ';' both parts are the whole text, so a
    method using either part falls back to the full query.
    """
    if ";" not in text:
        return text, text
    header, question = text.split(";", 1)
    return header.strip(), question.strip()
