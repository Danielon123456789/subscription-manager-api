from fastapi import FastAPI

from app.modules.auth.router import router as auth_router
from app.modules.subscriptions.router import router as subscriptions_router

app = FastAPI(title="Subscription Manager API", version="1.0.0")

app.include_router(auth_router)
app.include_router(subscriptions_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
