"""
03_indexer.py — Embedding + indexácia do ChromaDB

Čo robí:
  - Načíta chunks.json
  - Embedding každého chunku pomocou BGE-M3 (lokálne, bez API)
  - Uloží do ChromaDB (perzistentná vektorová DB na disku)

Spustenie (po 02_chunker.py):
  python 03_indexer.py

Čas: 10-20 minút (prvé spustenie stiahne BGE-M3 model ~2 GB)
     Pri opakovanom spustení: model je cached, trvá ~2-5 min

Expected output:
  chroma_db/  — priečinok s ChromaDB dátami
  "Hotovo. X dokumentov v kolekcii."
"""

import json
import os
import sys
import chromadb
from sentence_transformers import SentenceTransformer
from config import (
    EMBED_MODEL, CHROMA_DB_PATH, COLLECTION_NAME,
    CHUNKS_FILE, N_RESULTS
)

BATCH_SIZE = 50  # Spracovávame po dávkach — šetrí RAM


def main():
    print("=" * 60)
    print("Indexer — embedding + ChromaDB import")
    print("=" * 60)
    print()

    # ── Načítanie chunkov ──────────────────────────────────────────────────────
    if not os.path.exists(CHUNKS_FILE):
        print(f"✗ Nenájdený: {CHUNKS_FILE}")
        print("  Spusti najprv: python 02_chunker.py")
        sys.exit(1)

    with open(CHUNKS_FILE, encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"✓ Načítaných {len(chunks)} chunkov z {CHUNKS_FILE}")
    print()

    # ── Embedding model ────────────────────────────────────────────────────────
    print(f"Načítavam embedding model: {EMBED_MODEL}")
    print("  (prvé spustenie stiahne ~2 GB — čakaj...)")
    model = SentenceTransformer(EMBED_MODEL)
    print(f"✓ Model načítaný. Dimenzia embeddingov: {model.get_sentence_embedding_dimension()}")
    print()

    # ── ChromaDB ───────────────────────────────────────────────────────────────
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Ak kolekcia existuje, opýtame sa či ju prepísať
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        print(f"Kolekcia '{COLLECTION_NAME}' už existuje "
              f"({client.get_collection(COLLECTION_NAME).count()} dokumentov).")
        ans = input("Prepísať? [y/N]: ").strip().lower()
        if ans == "y":
            client.delete_collection(COLLECTION_NAME)
            print("  Stará kolekcia vymazaná.")
        else:
            print("  Indexácia zrušená.")
            sys.exit(0)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine similarity pre BGE-M3
    )
    print(f"✓ Kolekcia '{COLLECTION_NAME}' vytvorená.")
    print()

    # ── Batch embedding + insert ───────────────────────────────────────────────
    total = len(chunks)
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        texts     = [c["text"] for c in batch]
        ids       = [c["id"]   for c in batch]
        metadatas = [
            {
                "zakon":           c["zakon"],
                "zakon_cislo":     c["zakon_cislo"],
                "paragraf":        c["paragraf"],
                "url":             c["url"],
                "datum_ucinnosti": c["datum_ucinnosti"],
            }
            for c in batch
        ]

        # Embedding — hlavný výpočet
        embeddings = model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,   # dôležité pre cosine similarity
        ).tolist()

        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        pct = (i + len(batch)) / total * 100
        print(f"  Batch {batch_num}/{total_batches} [{pct:.0f}%] — "
              f"vložených {len(batch)} chunkov")

    final_count = collection.count()
    print()
    print(f"✓ Hotovo! {final_count} dokumentov v kolekcii '{COLLECTION_NAME}'")
    print(f"  Uložené v: {CHROMA_DB_PATH}/")
    print()
    print("ĎALŠÍ KROK — Smoke test (krok 1.9):")
    print("  python 03_indexer.py --test")
    print("  alebo: python -c \"from rag import retrieve; "
          "[print(r['metadata']['paragraf'],r['distance']) "
          "for r in retrieve('výpovedná doba')]\"")


def smoke_test():
    """Rýchly test retrieval — zavolaj cez: python 03_indexer.py --test"""
    print("Smoke test — retrieval test")
    print()

    model = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    test_queries = [
        "výpovedná doba",
        "registrácia na úrade práce",
        "dávka v nezamestnanosti",
    ]

    for query in test_queries:
        embedding = model.encode([query], normalize_embeddings=True).tolist()
        results = collection.query(
            query_embeddings=embedding,
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )
        print(f"Dotaz: '{query}'")
        for j in range(len(results["ids"][0])):
            meta = results["metadatas"][0][j]
            dist = results["distances"][0][j]
            sim  = 1 - dist
            preview = results["documents"][0][j][:80].replace("\n", " ")
            print(f"  [{sim:.2f}] § {meta['paragraf']} {meta['zakon']} | {preview}...")
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        smoke_test()
    else:
        main()
