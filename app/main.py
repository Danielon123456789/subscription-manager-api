from fastapi import FastAPI

from app.modules.auth.router import router as auth_router
from app.modules.subscriptions.router import router as subscriptions_router
from app.modules.groups.router import router as groups_router
from app.modules.invitations.router import router as invitations_router
from app.modules.dashboard.router import router as dashboard_router

app = FastAPI(title="Subscription Manager API", version="1.0.0")

app.include_router(auth_router)
app.include_router(subscriptions_router)
app.include_router(groups_router)
app.include_router(invitations_router)
app.include_router(dashboard_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
