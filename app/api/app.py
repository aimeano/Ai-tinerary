from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from app.api.auth_routes import router as auth_router
from app.api.trip_routes import router as trip_router



app = FastAPI(
    title="Ai-tinerary API"
)

app.add_middleware(  
    CORSMiddleware,  
    allow_origins=[ 
        "http://localhost:5173",    
        "http://127.0.0.1:5173",   
        "http://localhost:8000",  
        "http://127.0.0.1:8000",
    ],  
    allow_credentials=True,  
    allow_methods=["*"],  
    allow_headers=["*"],  
)  

app.include_router(auth_router)
app.include_router(trip_router)

@app.get("/")
def root():
    return {
        "status": "ok"
    }