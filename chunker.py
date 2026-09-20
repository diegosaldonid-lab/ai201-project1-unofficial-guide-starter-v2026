"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document

# The advice_threads files separate replies with a line like
#   --- reply 3 (8 votes) ---
# The numbers change from reply to reply, so match them as digits.
REPLY_HEADER = re.compile(
    r"^[ \t]*-{2,}[ \t]*reply[ \t]+\d+[ \t]*\([ \t]*\d+[ \t]*votes?[ \t]*\)[ \t]*-{2,}[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def _windows(text: str) -> list[str]:
    """Last resort for a piece that is still too long: fixed-size windows."""
    chunk_size = config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP

    if len(text) <= chunk_size:
        return [text]

    print(len(text))
    pieces: list[str] = []
    start = 0
    while start < len(text):
        piece = text[start : start + chunk_size].strip()
        if piece:
            pieces.append(piece)
        start += chunk_size - overlap
    return pieces


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split each thread on its reply markers, one chunk per reply.

    The advice_threads documents are short posts with a question on the first
    line and a handful of answers under it, each introduced by a line like
    `--- reply 3 (8 votes) ---`. That line is structure, not content: it tells
    the splitter where one answer ends and the next begins, and it is noise
    once the answer is on its own. So the marker decides the cut and is then
    dropped from the text.

    The thread question stays at the top of every chunk from that thread.
    A reply on its own ("West lots sell out in about three days in August")
    does not say what it is answering; with the question above it, the chunk
    reads as a complete thought and matches a question-shaped query.

    A document with no reply markers — anything in campus_life or city_guides —
    comes through as one chunk, cut into windows only if it runs past
    config.CHUNK_SIZE.
    """
    chunks: list[Chunk] = []

    for doc in documents:
        sections = [s.strip() for s in REPLY_HEADER.split(doc.text)]
        sections = [s for s in sections if s]

        if len(sections) > 1:
            # First section is the thread question; it prefixes every reply.
            header, replies = sections[0], sections[1:]
            pieces = [f"{header}\n\n{reply}" for reply in replies]
        else:
            pieces = sections

        index = 0
        for piece in pieces:
            for text in _windows(piece):
                chunks.append(
                    Chunk(
                        text=text,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
