from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, File
import uuid
import fitz
from datetime import datetime

from app.schemas.chat_schema import ChatRequest, ChatResponse, HealthResponse
from app.services.chat_service import process_message
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        model=settings.model_name,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    try:
        from app.db.vector_store import add_documents

        contents = await file.read()

        pdf = fitz.open(stream=contents, filetype="pdf")
        full_text = ""
        for page in pdf:
            full_text += page.get_text()
        pdf.close()

        if not full_text.strip():
            raise HTTPException(status_code=400, detail="PDF is empty or scanned")

        words = full_text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunks.append(" ".join(words[i:i + 500]))
            i += 450

        metadatas = [
            {
                "policy_name": file.filename.replace(".pdf", ""),
                "section": f"chunk_{idx}",
                "source": file.filename,
            }
            for idx in range(len(chunks))
        ]
        ids = [f"{file.filename}_chunk_{idx}_{uuid.uuid4().hex[:8]}" for idx in range(len(chunks))]

        add_documents(documents=chunks, metadatas=metadatas, ids=ids)

        return {
            "message": "PDF uploaded successfully",
            "filename": file.filename,
            "chunks_created": len(chunks),
            "status": "ready to query",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request, response: Response):
    try:
        session_id = http_request.cookies.get("session_id")

        if not session_id:
            session_id = str(uuid.uuid4())
            response.set_cookie(key="session_id", value=session_id)

        employee_id = request.employee_id or "guest"

        text = process_message(
            employee_id=employee_id,
            message=request.message,
            session_id=session_id,
        )

        return ChatResponse(
            response=text,
            session_id=session_id,
            employee_id=employee_id,
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))