import uvicorn

from app.core import config

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=config.PORT,
        lifespan="on",
        reload=True
    )
