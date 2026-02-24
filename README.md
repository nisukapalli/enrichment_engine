# Sixtyfour Workflow Engine

A simplified replica of Sixtyfour's Workflow Engine: configure and run workflows built from chainable blocks (Read CSV, Filter, Enrich Lead, Find Email, Save CSV). Built with **Python (FastAPI)**, **React**, and **TypeScript**.

## Quick start

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173
