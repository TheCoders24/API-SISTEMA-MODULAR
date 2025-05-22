from fastapi import FastAPI

app = FastAPI()


@app.get("/hola")
async def root():
    return {"message": "Hello World"}