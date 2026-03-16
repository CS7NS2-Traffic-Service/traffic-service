from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount(
    "/assets", StaticFiles(directory="traffic-frontend/dist/assets"), name="assets"
)


@app.get("/")
async def serve_index():
    return FileResponse("traffic-frontend/dist/index.html")


@app.get("/{full_path:path}")
async def serve_frontend(_: str):
    return FileResponse("traffic-frontend/dist/index.html")
