import os
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database import db, create_document, get_documents
from schemas import ContactMessage, ChatMessage, VideoItem

app = FastAPI(title="Ivan Noskovič - Profil politika API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Nastavenie adresára pre uploady
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads" / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# Sprístupni statické súbory
app.mount("/uploads", StaticFiles(directory=BASE_DIR / "uploads"), name="uploads")

@app.get("/")
def read_root():
    return {"message": "API beží", "name": "Ivan Noskovič"}

# Schémy pre tabuľky reforiem (športové mzdy a dôchodková reforma)
class WageRow(BaseModel):
    liga: int
    min_mzda: float
    max_mzda: float

class PensionStep(BaseModel):
    bod: int
    opis: str

# Statické dáta reforiem (môžu sa neskôr presunúť do DB)
SPORT_WAGES: List[WageRow] = [
    WageRow(liga=1, min_mzda=3500, max_mzda=9000),
    WageRow(liga=2, min_mzda=2200, max_mzda=5000),
    WageRow(liga=3, min_mzda=1500, max_mzda=3200),
    WageRow(liga=4, min_mzda=900, max_mzda=2000),
    WageRow(liga=5, min_mzda=600, max_mzda=1200),
]

PENSION_REFORM: List[PensionStep] = [
    PensionStep(bod=1, opis="Stabilizácia II. piliera s vyššou transparentnosťou"),
    PensionStep(bod=2, opis="Automatický vstup mladých s možnosťou opt-out"),
    PensionStep(bod=3, opis="Indexové fondy ako predvolená voľba"),
    PensionStep(bod=4, opis="Motivačné príspevky pre dlhodobé sporenie"),
    PensionStep(bod=5, opis="Daňové zvýhodnenie dobrovoľných príspevkov"),
    PensionStep(bod=6, opis="Zavedenie dlhopisov pre infra projekty v dôchodkových fondoch"),
    PensionStep(bod=7, opis="Spravodlivejšie valorizácie pre nízkopríjmové skupiny"),
    PensionStep(bod=8, opis="Silnejšie zásluhové prvky – prepojenie na celoživotný príjem"),
    PensionStep(bod=9, opis="Digitalizácia Sociálnej poisťovne a zníženie byrokracie"),
    PensionStep(bod=10, opis="Zjednodušenie predčasného dôchodku s jasnými pravidlami"),
    PensionStep(bod=11, opis="Podpora aktívnej staroby – práca popri dôchodku bez penalizácie"),
    PensionStep(bod=12, opis="Lepšia ochrana dôchodkov pred infláciou"),
    PensionStep(bod=13, opis="Medzigeneračná solidarita: bonusy za výchovu detí"),
]

# Verejné API na čítanie reforiem
@app.get("/api/sport-wages", response_model=List[WageRow])
def get_sport_wages():
    return SPORT_WAGES

@app.get("/api/pension-reform", response_model=List[PensionStep])
def get_pension_reform():
    return PENSION_REFORM

# Kontakt: uloženie správy do DB
@app.post("/api/contact")
def post_contact(msg: ContactMessage):
    try:
        doc_id = create_document("contactmessage", msg)
        return {"status": "ok", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Jednoduchý verejný chat (bez auth) – ukladá do DB a vracia posledné správy
@app.get("/api/chat", response_model=List[ChatMessage])
def get_chat_messages(limit: int = 30):
    try:
        docs = get_documents("chatmessage", {}, limit)
        cleaned = []
        for d in docs:
            cleaned.append({
                "name": d.get("name", "Anonym"),
                "content": d.get("content", ""),
            })
        return cleaned
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def post_chat_message(msg: ChatMessage):
    try:
        _id = create_document("chatmessage", msg)
        return {"status": "ok", "id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Videá: jednoduché CRUD (bez auth) – ukladá URL, názov, popis a thumbnail
@app.get("/api/videos", response_model=List[VideoItem])
def list_videos(limit: int = 50):
    try:
        docs = get_documents("videoitem", {}, limit)
        items: List[VideoItem] = []
        for d in docs:
            created_at = d.get("created_at")
            if isinstance(created_at, datetime):
                created_iso = created_at.isoformat()
            else:
                created_iso = str(created_at) if created_at else None
            items.append(VideoItem(
                title=d.get("title", ""),
                url=d.get("url", ""),
                thumbnail=d.get("thumbnail"),
                description=d.get("description"),
                created_at=created_iso
            ))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/videos")
def create_video(item: VideoItem):
    try:
        vid = create_document("videoitem", item)
        return {"status": "ok", "id": vid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Upload videa (multipart/form-data)
@app.post("/api/videos/upload")
def upload_video(title: str = Form(...), description: Optional[str] = Form(None), file: UploadFile = File(...)):
    try:
        # Bezpečný názov súboru
        ext = Path(file.filename).suffix.lower()
        if ext not in {".mp4", ".mov", ".webm", ".mkv", ".avi"}:
            raise HTTPException(status_code=400, detail="Podporované formáty: mp4, mov, webm, mkv, avi")
        safe_name = f"{uuid.uuid4().hex}{ext}"
        dest_path = UPLOAD_DIR / safe_name
        with dest_path.open("wb") as f:
            f.write(file.file.read())
        # URL cestu vraciame relatívne voči backendu
        url_path = f"/uploads/videos/{safe_name}"
        # Ulož do DB
        payload = {
            "title": title,
            "url": url_path,
            "description": description or "",
            "thumbnail": None,
        }
        _id = create_document("videoitem", payload)
        return {"status": "ok", "id": _id, "item": payload}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    """Test endpoint na dostupnosť databázy"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
