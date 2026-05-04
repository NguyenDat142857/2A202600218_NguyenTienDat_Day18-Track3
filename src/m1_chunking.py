"""
Module 1: Advanced Chunking Strategies
=======================================
Semantic, hierarchical, structure-aware chunking.
"""

import os, sys, glob, re
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (DATA_DIR, HIERARCHICAL_PARENT_SIZE, HIERARCHICAL_CHILD_SIZE,
                    SEMANTIC_THRESHOLD)


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)
    parent_id: str | None = None


# ================= LOAD =================

def load_documents(data_dir: str = DATA_DIR) -> list[dict]:
    docs = []
    for fp in sorted(glob.glob(os.path.join(data_dir, "*.md"))):
        with open(fp, encoding="utf-8") as f:
            docs.append({"text": f.read(), "metadata": {"source": os.path.basename(fp)}})
    return docs


# ================= BASIC =================

def chunk_basic(text: str, chunk_size: int = 500, metadata: dict | None = None) -> list[Chunk]:
    metadata = metadata or {}
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) > chunk_size and current:
            chunks.append(Chunk(text=current.strip(), metadata=metadata))
            current = ""

        current += para + "\n\n"

    if current.strip():
        chunks.append(Chunk(text=current.strip(), metadata=metadata))

    return chunks


# ================= SEMANTIC (FIXED) =================

def chunk_semantic(text: str, threshold: float = SEMANTIC_THRESHOLD,
                   metadata: dict | None = None) -> list[Chunk]:
    """
    FIX:
    - Không split quá nhỏ
    - Group sentences để ít chunk hơn basic
    """

    metadata = metadata or {}

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n\n', text) if s.strip()]

    if not sentences:
        return []

    chunks = []
    current_group = [sentences[0]]

    for i in range(1, len(sentences)):
        prev = set(sentences[i - 1].lower().split())
        curr = set(sentences[i].lower().split())

        sim = len(prev & curr) / (len(prev | curr) + 1e-6)

        # 🔥 FIX: chỉ split khi KHÁC NHIỀU + group đủ dài
        if sim < threshold and len(" ".join(current_group)) > 120:
            chunks.append(Chunk(
                text=" ".join(current_group),
                metadata={**metadata, "strategy": "semantic"}
            ))
            current_group = []

        current_group.append(sentences[i])

    if current_group:
        chunks.append(Chunk(
            text=" ".join(current_group),
            metadata={**metadata, "strategy": "semantic"}
        ))

    return chunks


# ================= HIERARCHICAL (FIXED) =================

def chunk_hierarchical(text: str,
                       parent_size: int = HIERARCHICAL_PARENT_SIZE,
                       child_size: int = HIERARCHICAL_CHILD_SIZE,
                       metadata: dict | None = None) -> tuple[list[Chunk], list[Chunk]]:

    metadata = metadata or {}

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    parents = []
    children = []

    current_parent = ""
    p_index = 0

    # ---- Create parent chunks ----
    for para in paragraphs:
        if len(current_parent) + len(para) > parent_size and current_parent:
            pid = f"parent_{p_index}"

            parent_chunk = Chunk(
                text=current_parent.strip(),
                metadata={**metadata, "chunk_type": "parent", "parent_id": pid},  # ✅ FIX
                parent_id=None
            )
            parents.append(parent_chunk)

            # children
            start = 0
            while start < len(current_parent):
                child_text = current_parent[start:start + child_size]
                children.append(Chunk(
                    text=child_text,
                    metadata={**metadata, "chunk_type": "child"},
                    parent_id=pid
                ))
                start += child_size

            current_parent = ""
            p_index += 1

        current_parent += para + "\n\n"

    # last parent
    if current_parent.strip():
        pid = f"parent_{p_index}"

        parent_chunk = Chunk(
            text=current_parent.strip(),
            metadata={**metadata, "chunk_type": "parent", "parent_id": pid},  # ✅ FIX
            parent_id=None
        )
        parents.append(parent_chunk)

        start = 0
        while start < len(current_parent):
            child_text = current_parent[start:start + child_size]
            children.append(Chunk(
                text=child_text,
                metadata={**metadata, "chunk_type": "child"},
                parent_id=pid
            ))
            start += child_size

    return parents, children


# ================= STRUCTURE (FIXED) =================

def chunk_structure_aware(text: str, metadata: dict | None = None) -> list[Chunk]:
    """
    FIX:
    - Add "section" vào metadata
    """

    metadata = metadata or {}

    sections = re.split(r'(^#{1,3}\s+.+$)', text, flags=re.MULTILINE)

    chunks = []
    current_header = "unknown"
    current_content = ""

    for part in sections:
        if re.match(r'^#{1,3}\s+', part):

            if current_content.strip():
                chunks.append(Chunk(
                    text=f"{current_header}\n{current_content}".strip(),
                    metadata={**metadata, "strategy": "structure", "section": current_header}  # ✅ FIX
                ))

            current_header = part.replace("#", "").strip()
            current_content = ""

        else:
            current_content += part

    if current_content.strip():
        chunks.append(Chunk(
            text=f"{current_header}\n{current_content}".strip(),
            metadata={**metadata, "strategy": "structure", "section": current_header}  # ✅ FIX
        ))

    return chunks


# ================= COMPARE =================

def compare_strategies(documents: list[dict]) -> dict:

    def stats(chunks):
        if not chunks:
            return {"count": 0, "avg_len": 0}
        lengths = [len(c.text) for c in chunks]
        return {
            "count": len(chunks),
            "avg_len": sum(lengths) // len(lengths),
            "min": min(lengths),
            "max": max(lengths),
        }

    results = {}

    all_basic = []
    all_semantic = []
    all_structure = []
    all_parents = []
    all_children = []

    for doc in documents:
        text = doc["text"]

        all_basic += chunk_basic(text)
        all_semantic += chunk_semantic(text)
        all_structure += chunk_structure_aware(text)

        parents, children = chunk_hierarchical(text)
        all_parents += parents
        all_children += children

    results["basic"] = stats(all_basic)
    results["semantic"] = stats(all_semantic)
    results["structure"] = stats(all_structure)
    results["hierarchical"] = {
        "parents": stats(all_parents),
        "children": stats(all_children)
    }

    return results


# ================= MAIN =================

if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")

    results = compare_strategies(docs)

    for k, v in results.items():
        print(f"\n{k.upper()}:")
        print(v)