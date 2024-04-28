import os

if __name__ == "__main__":
    import uvicorn

    port = os.getenv("PORT", 8999)

    uvicorn.run("src.api:app", host="0.0.0.0", port=port)
