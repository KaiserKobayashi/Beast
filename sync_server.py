"""
Minimal FastAPI sync server (dev/demo) — copy this into sync_server.py

Endpoints:
 - POST /upload           : single-shot file upload (multipart/form-data)
 - POST /upload_chunk     : chunked/resumable upload (upload_id + chunk_index + total_chunks)
 - GET  /list?project=... : list metadata for a project
 - GET  /download/{project}/{file_id} : download a stored file
 - WS   /ws?project=...   : WebSocket notifications for project subscribers
Auth:
 - Demo API-key header check: Authorization: Bearer <key>
Storage:
 - Files stored under ./sync_store/<project>
 - Metadata stored in ./sync_store/sync_meta.db (SQLite)

Note: This is a development/demo server. For production add TLS, secure auth, input validation and harden file handling.
"""
import os
import uuid
import time
import hashlib
import sqlite3
import shutil
from typing import Optional, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.abspath("sync_store")
DB_PATH = os.path.join(BASE_DIR, "sync_meta.db")
os.makedirs(BASE_DIR, exist_ok=True)

app = FastAPI(title="Sync Server (demo)")

# Allow local dev CORS (be careful in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple API key store for demo (replace with secure store)
API_KEYS: Dict[str, str] = {
    "dev-key-1": "desktop",
    "mobile-key-1": "mobile",
}


def require_api_key(authorization: Optional[str] = Header(None)):
    """
    Very small API key check. Supply header:
      Authorization: Bearer <key>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    key = authorization.split(" ", 1)[1]
    if key not in API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return API_KEYS[key]


# Initialize DB schema
def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            project TEXT,
            path TEXT,
            filename TEXT,
            version INTEGER,
            sha256 TEXT,
            uploaded_at REAL,
            client_id TEXT
        )
        """)
        conn.commit()
    finally:
        conn.close()


init_db()


# WebSocket manager per project
class WSManager:
    def __init__(self):
        # project -> set(WebSocket)
        self.conns: Dict[str, set] = {}

    async def connect(self, project: str, ws: WebSocket):
        await ws.accept()
        self.conns.setdefault(project, set()).add(ws)

    def disconnect(self, project: str, ws: WebSocket):
        s = self.conns.get(project)
        if s and ws in s:
            s.remove(ws)

    async def notify(self, project: str, payload: dict):
        for ws in list(self.conns.get(project, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                # remove broken sockets
                self.disconnect(project, ws)


ws_manager = WSManager()


def file_sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


@app.get("/")
def root():
    return {"ok": True, "message": "Sync server (demo). See /docs for API."}


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    project: str = Form(...),
    path: str = Form(...),
    authorization: str = Depends(require_api_key),
    client_id: str = Form(None),
):
    """
    Single-shot upload. Provide:
      - project : logical project name
      - path    : logical path inside project (e.g., subs/en/001.srt)
    Returns metadata for the uploaded file.
    """
    content = await file.read()
    sha = file_sha256_bytes(content)
    file_id = str(uuid.uuid4())
    project_dir = os.path.join(BASE_DIR, project)
    os.makedirs(project_dir, exist_ok=True)
    disk_name = f"{file_id}_{os.path.basename(path)}"
    disk_path = os.path.join(project_dir, disk_name)
    with open(disk_path, "wb") as f:
        f.write(content)

    # persist metadata
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        ts = time.time()
        cur.execute(
            "INSERT INTO files (id, project, path, filename, version, sha256, uploaded_at, client_id) VALUES (?,?,?,?,?,?,?,?)",
            (file_id, project, path, os.path.basename(path), 1, sha, ts, client_id),
        )
        conn.commit()
    finally:
        conn.close()

    payload = {"event": "uploaded", "project": project, "file_id": file_id, "path": path, "uploaded_at": ts}
    await ws_manager.notify(project, payload)

    return JSONResponse({"id": file_id, "path": path, "version": 1, "sha256": sha, "uploaded_at": ts})


@app.post("/upload_chunk")
async def upload_chunk(
    project: str = Form(...),
    path: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    chunk: UploadFile = File(...),
    upload_id: str = Form(...),
    authorization: str = Depends(require_api_key),
    client_id: str = Form(None),
):
    """
    Chunked upload. Send chunk files with same upload_id.
    When all parts received they are assembled and stored like /upload.
    """
    upload_dir = os.path.join(BASE_DIR, "chunks", upload_id)
    os.makedirs(upload_dir, exist_ok=True)
    chunk_path = os.path.join(upload_dir, f"{chunk_index:06d}.part")
    data = await chunk.read()
    with open(chunk_path, "wb") as f:
        f.write(data)

    parts = sorted([p for p in os.listdir(upload_dir) if p.endswith(".part")])
    if len(parts) == total_chunks:
        content = bytearray()
        for p in parts:
            with open(os.path.join(upload_dir, p), "rb") as pf:
                content.extend(pf.read())
        # persist assembled file same as /upload
        file_id = str(uuid.uuid4())
        project_dir = os.path.join(BASE_DIR, project)
        os.makedirs(project_dir, exist_ok=True)
        disk_name = f"{file_id}_{os.path.basename(path)}"
        disk_path = os.path.join(project_dir, disk_name)
        with open(disk_path, "wb") as f:
            f.write(content)
        sha = file_sha256_bytes(content)
        ts = time.time()
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO files (id, project, path, filename, version, sha256, uploaded_at, client_id) VALUES (?,?,?,?,?,?,?,?)",
                (file_id, project, path, os.path.basename(path), 1, sha, ts, client_id),
            )
            conn.commit()
        finally:
            conn.close()
        # cleanup chunk dir
        shutil.rmtree(upload_dir, ignore_errors=True)
        await ws_manager.notify(project, {"event": "uploaded", "project": project, "file_id": file_id, "path": path, "uploaded_at": ts})
        return JSONResponse({"id": file_id, "path": path, "version": 1, "sha256": sha, "uploaded_at": ts})

    return JSONResponse({"status": "part_received", "upload_id": upload_id, "chunk_index": chunk_index})


@app.get("/list")
def list_files(project: str, authorization: str = Depends(require_api_key)):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, path, filename, version, sha256, uploaded_at, client_id FROM files WHERE project=? ORDER BY uploaded_at DESC",
            (project,),
        )
        rows = cur.fetchall()
    finally:
        conn.close()
    items = []
    for r in rows:
        items.append({"id": r[0], "path": r[1], "filename": r[2], "version": r[3], "sha256": r[4], "uploaded_at": r[5], "client_id": r[6]})
    return items


@app.get("/download/{project}/{file_id}")
def download(project: str, file_id: str, authorization: str = Depends(require_api_key)):
    project_dir = os.path.join(BASE_DIR, project)
    if not os.path.isdir(project_dir):
        raise HTTPException(status_code=404, detail="project not found")
    for f in os.listdir(project_dir):
        if f.startswith(f"{file_id}_"):
            file_path = os.path.join(project_dir, f)
            return FileResponse(file_path, filename=f.split("_", 1)[1])
    raise HTTPException(status_code=404, detail="file not found")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, project: str):
    # Note: For production you should validate auth for the socket (token or cookie)
    await ws_manager.connect(project, websocket)
    try:
        while True:
            # keepalive: client may send pings; we ignore content
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(project, websocket)