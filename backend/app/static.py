from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


class SPAStaticFiles(StaticFiles):
    """Serve built frontend assets and fall back to index.html for client routes."""

    async def get_response(self, path: str, scope):  # type: ignore[override]
        response = await super().get_response(path, scope)
        if response.status_code != 404:
            return response

        index_path = Path(self.directory or "") / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return response


def attach_frontend(app, dist_dir: Path) -> None:
    app.mount("/assets", StaticFiles(directory=dist_dir / "assets"), name="assets")

    router = APIRouter(include_in_schema=False)

    @router.get("/")
    async def frontend_index() -> FileResponse:
        return FileResponse(dist_dir / "index.html")

    app.include_router(router)
    app.mount("/", SPAStaticFiles(directory=dist_dir, html=True), name="frontend")
