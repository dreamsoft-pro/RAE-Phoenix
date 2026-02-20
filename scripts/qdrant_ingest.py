#!/usr/bin/env python3
import argparse, os, json, uuid
from tqdm import tqdm
from typing import List, Dict
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from joblib import dump, load

def load_chunks(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def build_dense_model(name: str):
    # Dobry, wielojęzyczny model do zapytań PL i treści kodu:
    # intfloat/multilingual-e5-base (sprawdza się w RAG)
    return SentenceTransformer(name)

def to_sparse_struct(vec):
    # SciKit CSR -> Qdrant SparseVector
    coo = vec.tocoo()
    return models.SparseVector(
        indices=coo.col.tolist(),
        values=coo.data.tolist()
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", required=True)
    ap.add_argument("--collection", default="frontend_feniks")
    ap.add_argument("--qdrant-url", default="http://localhost:6333")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--dense-model", default="intfloat/multilingual-e5-base")
    ap.add_argument("--batch", type=int, default=128)
    args = ap.parse_args()

    client = QdrantClient(url=args.qdrant_url)

    chunks = list(load_chunks(args.chunks))
    texts = [c["code_snippet"] or "" for c in chunks]

    # === Dense embeddings ===
    dense_model = build_dense_model(args.dense_model)
    dense_dim = dense_model.get_sentence_embedding_dimension()

    # === Sparse TF-IDF (uni+bi-gram) ===
    # Fit na całym korpusie -> zapisujemy vektoryzer dla zapytań
    tfidf = TfidfVectorizer(ngram_range=(1,2), min_df=2, token_pattern=r"(?u)\b\w+\b")
    X = tfidf.fit_transform(texts)
    os.makedirs("feniks/data", exist_ok=True)
    dump(tfidf, "feniks/data/tfidf.joblib")

    # === Kolekcja Qdrant: dense + sparse ===
    if args.reset and client.collection_exists(args.collection):
        client.delete_collection(args.collection)

    if not client.collection_exists(args.collection):
        client.create_collection(
            collection_name=args.collection,
            vectors_config={
                "dense_code": models.VectorParams(
                    size=dense_dim, distance=models.Distance.COSINE
                )
            },
            sparse_vectors_config={
                "sparse_keywords": models.SparseVectorParams()
            },
        )

        # Indeksy payloadu do szybkiego filtrowania
        for field in ["file_path","ast_node_type","chunk_name","template_url"]:
            client.create_payload_index(args.collection, field_name=field, field_schema=models.PayloadSchemaType.KEYWORD)
        for field in ["dependencies_di","tags"]:
            client.create_payload_index(args.collection, field_name=field, field_schema=models.PayloadSchemaType.KEYWORD)

    # === Upsert w partiach ===
    points = []
    for i in tqdm(range(0, len(chunks), args.batch), desc="Upsert"):
        batch = chunks[i:i+args.batch]
        dense = dense_model.encode([b["code_snippet"] or "" for b in batch], show_progress_bar=False, normalize_embeddings=True)
        sparse = X[i:i+args.batch]
        pts = []
        for j, c in enumerate(batch):
            s = to_sparse_struct(sparse[j])
            pts.append(models.PointStruct(
                id=c["chunk_id"],
                vector={
                    "dense_code": dense[j].tolist(),
                    "sparse_keywords": s
                },
                payload=c
            ))
        client.upsert(collection_name=args.collection, points=pts)

    info = client.get_collection(args.collection)
    print("Collection created:", info)

if __name__ == "__main__":
    main()
