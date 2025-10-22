import logging
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

# some fuctions we should have
from app.routes import iot
from app.config import init_config

# logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# the configuration initialization function in app.config
init_config()

# intialize FastAPI & its configuration -> return a FastAPI-type object
def create_app() -> FastAPI:

    # intialize a new instance
    app = FastAPI(
        title="IoT Security with blockchain",
        description="Secure & verifiable IoT data transmission using Blockchain & IPFS.",
        version="1.0.0"
    )

    # middleware configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # include all routes from iot.router in the main app with new prefix 
    app.include_router(iot.router, prefix="/api/iot", tags=["IoT Devices"])
   

    # api homepage (root endpoint)
    @app.get("/")
    def root():
        return {"message": "IoT Security API is running"}

    return app

app = create_app()

if __name__ == "__main__":
    logger.info("Starting Uvicorn Server...")   
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)