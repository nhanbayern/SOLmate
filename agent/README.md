# Vietnamese Loan Advisory RAG Skeleton

Project skeleton for a hybrid Retrieval-Augmented Generation (RAG) system focused on Vietnamese loan advisory.
The structure is aligned to this concrete stack:

- LLM: `Qwen`
- Dense embedding: `bkai-foundation-models/vietnamese-bi-encoder`
- Vector database: `Milvus`
- Preprocessing: section-aware chunking, overlap chunking, RDR word segmentation

## Structure

```text
.
|-- app/
|   |-- core/
|   |-- embeddings/
|   |-- ingestion/
|   |-- llm/
|   |-- preprocessing/
|   |-- retrieval/
|   |-- schemas/
|   |-- services/
|   |-- utils/
|   |-- vectorstores/
|   |-- config.py
|   `-- pipeline.py
|-- tests/
|-- main.py
`-- requirements.txt
```

## Pipeline

1. Build an advisory query from enterprise profile, score rules, and CIC metrics.
2. Segment Vietnamese text with RDR-compatible word segmentation.
3. Build a dense retrieval view for the BKAI encoder.
4. Chunk legal articles by section first, otherwise use overlap chunking under 256 tokens.
5. Store chunk text, dense vectors, and metadata in Milvus.
6. Retrieve dense candidates from Milvus.
7. Group chunks back to original legal articles.
8. Generate a loan advisory report using the risk assessment and retrieved legal basis.

## Run

```bash
python main.py
```

Run the API locally:

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000
```

## Docker

Build the app image:

```bash
docker compose build app
```

Start the Milvus stack:

```bash
docker compose --profile milvus up -d
```

Ingest legal data into Milvus:

```bash
docker compose run --rm app python -m app.ingestion.milvus_ingest --dataset dataset/vietnamese-bank-legal.json --drop-existing
```

Start the API server:

```bash
docker compose up app
```

Check health:

```bash
curl http://localhost:8000/health
```

Call the advisory API with Milvus dense-only retrieval:

```bash
curl -X POST http://localhost:8000/advisory \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"milvus-dense\",\"customer_id\":\"CUST_70314034\"}"
```

Call the advisory API in demo mode:

```bash
curl -X POST http://localhost:8000/advisory \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"demo\",\"customer_id\":\"CUST_70314034\"}"
```

Notes:

- The `app` container now serves a FastAPI application on port `8000`.
- `mode=demo` uses the in-memory demo pipeline.
- `mode=milvus-dense` uses Milvus retrieval with dense-only search.
- `customer_id` is optional. If omitted, the first record in the dataset is used.
- `dataset_dir` can be sent in the request body if you want to read from a different dataset directory.
- `MILVUS_URI` is read from environment variables, so the app can talk to `milvus-standalone` inside Docker Compose.
- Re-run the ingest command with `--drop-existing` whenever you want to recreate the collection.
- The first run may take longer because the Qwen model and embedding model may need to be downloaded.

Response shape:

```json
{
  "customer_id": "CUST_70314034",
  "mode": "milvus-dense",
  "report_text": "...",
  "recommendation": "...",
  "summary": "..."
}
```
