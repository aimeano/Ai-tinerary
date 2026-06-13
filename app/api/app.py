from fastapi import FastAPI

from app.api.auth_routes import router as auth_router
from app.api.trip_routes import router as trip_router



app = FastAPI(
    title="Ai-tinerary API"
)

app.include_router(auth_router)
app.include_router(trip_router)

@app.get("/")
def root():
    return {
        "status": "ok"
    }