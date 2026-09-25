# API

Base: `/api/v1` · OpenAPI: `/docs`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| POST | `/keys/pem` | Ingest PEM public key |
| POST | `/keys/raw` | Ingest n,e |
| GET | `/keys` | Inventory |
| GET | `/keys/{key_id}` | Key detail |
| POST | `/audits` | Run audit |
| GET | `/audits` | List audits |
| GET | `/audits/{audit_id}` | Audit detail |
| GET | `/dashboard/summary` | Dashboard metrics |
| GET | `/test-lab/fixtures` | Lab fixtures |
| POST | `/test-lab/run` | Run fixture audit |
| POST | `/reports/{audit_id}` | Generate JSON report |
