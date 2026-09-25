# Demo script

1. Start backend (`uvicorn app.main:app --reload --port 8000`)
2. Start frontend (`npm run dev`)
3. Landing → **Explore Test Lab**
4. Run **Intentionally weak RSA (ECM demo)** → expect FACTOR_FOUND
5. Open audit details → show factor evidence + timeline
6. Generate JSON report
7. Run **Normal demonstration RSA key** → typically INCONCLUSIVE
8. Say out loud: “No factor found does not mean the key is secure.”
