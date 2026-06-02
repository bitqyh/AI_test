import logging
import os
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models import AnalysisResult, MatchScore
from app.pdf_loader import load_pdf_text, compute_file_md5
from app.ai_parser import parse_resume
from app.scorer import score_resume
from app.cache import cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("服务启动，预热中...")
    yield
    await cache_manager.close()
    logger.info("服务关闭")


app = FastAPI(
    title="AI Resume Analysis API",
    description="AI简历智能解析与评分系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/system/health")
async def health_check():
    return {"status": "ok", "service": "AI Resume Analysis API"}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
def _invoke_score_resume(resume_json: str, job_description: str) -> MatchScore:
    return score_resume(resume_json, job_description)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
def _invoke_parse_resume(resume_text: str, job_description: str | None) -> dict:
    parsed = parse_resume(resume_text, job_description)
    return parsed.model_dump()


@app.post("/api/v1/resume/analyze")
async def analyze_resume(
    file: UploadFile = File(description="简历PDF文件"),
    job_description: str = Form(default="", description="岗位描述"),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持PDF格式的简历文件")

    try:
        content = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="无法读取上传的文件")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(content)

    try:
        resume_md5 = compute_file_md5(tmp_path)
        jd_md5 = cache_manager.compute_md5(job_description) if job_description else "no_jd"

        cached_result = await cache_manager.get(resume_md5, jd_md5)
        if cached_result:
            logger.info(f"缓存命中: {resume_md5}:{jd_md5}")
            cached_result.from_cache = True
            return cached_result.model_dump()

        logger.info("开始解析PDF文本...")
        resume_text = load_pdf_text(tmp_path)

        logger.info("开始AI解析简历...")
        parsed_dict = _invoke_parse_resume(
            resume_text, job_description if job_description else None
        )

        match_result = None
        if job_description:
            logger.info("开始岗位匹配评分...")
            resume_json_str = str(parsed_dict)
            match_result = _invoke_score_resume(resume_json_str, job_description)

        result = AnalysisResult(
            resume=parsed_dict,
            match=match_result.model_dump() if match_result else None,
            from_cache=False,
        )

        await cache_manager.set(resume_md5, jd_md5, result)
        logger.info(f"分析完成并缓存: {resume_md5}:{jd_md5}")

        return result.model_dump()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("分析过程出错")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    index_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "static", "index.html"
    )
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI Resume Analysis API", "docs": "/docs"}
