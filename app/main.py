from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Market Coach API",
    description="Educational-only stock learning API (no investment advice).",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "name": "ai-market-coach",
        "status": "ok",
        "health": "/health",
        "docs": "/docs",
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# Register API routes
try:
    from app.api.routes import router as api_router
    app.include_router(api_router)
except Exception as e:
    @app.get("/debug/routes-import")
    def routes_import_debug():
        return {"routes_import_error": str(e)}
