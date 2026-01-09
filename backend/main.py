from fastapi import FastAPI, UploadFile, File, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
import traceback

from resume_parser import extract_text_from_pdf
from skill_extractor import extract_skills_and_topics
from query_builder_local_llm import build_search_queries  # This will use Ollama now!

# =========================
# APP SETUP
# =========================
app = FastAPI(title="Resume → LinkedIn Pipeline API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# STORAGE
# =========================
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Check if we're in backend folder, adjust path accordingly
if os.path.basename(os.getcwd()) == 'backend':
    FRONTEND_DIR = "../frontend"
else:
    FRONTEND_DIR = "frontend"

if not os.path.exists(FRONTEND_DIR):
    os.makedirs(FRONTEND_DIR)
    print(f"⚠️ Created {FRONTEND_DIR} directory. Please place your HTML, CSS, and JS files there.")

job_store = {}

# =========================
# MOUNT STATIC FILES (CSS, JS)
# =========================
if os.path.exists(FRONTEND_DIR):
    try:
        app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    except Exception as e:
        print(f"Warning: Could not mount static files: {e}")

# =========================
# SERVE FRONTEND (Root path serves HTML)
# =========================
@app.get("/", include_in_schema=False)
def serve_frontend():
    html_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    else:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Frontend not found", 
                "message": f"Please place index.html in the '{FRONTEND_DIR}' directory"
            }
        )

@app.get("/script.js", include_in_schema=False)
def serve_script():
    js_path = os.path.join(FRONTEND_DIR, "script.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    return JSONResponse(status_code=404, content={"error": "script.js not found"})

@app.get("/style.css", include_in_schema=False)
def serve_style():
    css_path = os.path.join(FRONTEND_DIR, "style.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    return JSONResponse(status_code=404, content={"error": "style.css not found"})

# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "LinkedIn Pipeline API is running",
        "jobs_count": len(job_store),
        "llm_backend": "Ollama (Local)"
    }

# =========================
# PROCESS RESUME
# =========================
@app.post("/process-resume")
async def process_resume(file: UploadFile = File(...)):
    """
    Upload resume, extract skills, generate queries using Ollama
    """
    print(f"\n📄 Processing resume: {file.filename}")
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        # Generate job ID
        job_id = str(uuid.uuid4())
        print(f"🆔 Generated Job ID: {job_id}")

        # Save resume
        file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"💾 Saved resume to: {file_path}")

        # Extract resume text
        print("📖 Extracting text from PDF...")
        resume_text = extract_text_from_pdf(file_path)

        if not resume_text or len(resume_text) < 50:
            print("❌ Could not extract enough text from resume")
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from resume. Please ensure it's a valid PDF with text content."
            )

        print(f"✅ Extracted {len(resume_text)} characters")

        # Extract skills
        print("🔍 Extracting skills...")
        extracted = extract_skills_and_topics(resume_text)
        skills = extracted.get("skills", [])

        if not skills:
            print("⚠️ No skills found, using resume text for query generation")
            skills = ["software", "developer"]  # Fallback

        print(f"✅ Found {len(skills)} skills: {skills[:5]}")

        # Build LinkedIn queries using Ollama
        print("🤖 Generating search queries with local LLM (Ollama)...")
        print("⏳ This may take 10-30 seconds for the first query...")
        
        queries = build_search_queries(
            skills=skills, 
            resume_text=resume_text, 
            max_queries=12
        )
        
        print(f"✅ Generated {len(queries)} queries")

        # Print sample queries for debugging
        if queries:
            print(f"📋 Sample queries: {queries[:3]}")

        # Store job
        job_store[job_id] = {
            "status": "waiting_for_linkedin",
            "skills": skills,
            "queries": queries,
            "results": [],
            "resume_text": resume_text
        }

        print(f"✅ Job {job_id} stored successfully\n")

        return {
            "success": True,
            "job_id": job_id,
            "skills": skills,
            "queries": queries,
            "status": "waiting_for_linkedin",
            "message": "Resume processed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing resume: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error processing resume: {str(e)}"
        )

# =========================
# GET JOB DETAILS (for local agent)
# =========================
@app.get("/api/results/{job_id}")
async def get_job_for_agent(job_id: str):
    """
    Local agent fetches job details (skills, queries)
    """
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job ID not found")
    
    job = job_store[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "skills": job.get("skills", []),
        "queries": job.get("queries", [])
    }

# =========================
# SUBMIT RESULTS (from local agent)
# =========================
@app.post("/api/submit-results/{job_id}")
async def submit_results(job_id: str, payload: dict = Body(...)):
    """
    Local agent submits scraped results
    """
    print(f"\n📥 Receiving results for job: {job_id}")
    
    try:
        if job_id not in job_store:
            raise HTTPException(status_code=404, detail="Job ID not found")

        results = payload.get("results", [])
        
        if not isinstance(results, list):
            raise HTTPException(status_code=400, detail="Results must be a list")

        job_store[job_id]["results"] = results
        job_store[job_id]["status"] = "completed"

        print(f"✅ Stored {len(results)} results for job {job_id}\n")

        return {
            "success": True,
            "status": "success",
            "message": "Results received successfully",
            "count": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error submitting results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# GET RESULTS (for frontend polling)
# =========================
@app.get("/results/{job_id}")
async def get_results(job_id: str):
    """
    Frontend polls this to get results
    """
    try:
        if job_id not in job_store:
            raise HTTPException(status_code=404, detail="Job ID not found")

        job = job_store[job_id]
        
        return {
            "success": True,
            "job_id": job_id,
            "status": job["status"],
            "skills": job.get("skills", []),
            "queries": job.get("queries", []),
            "results": job.get("results", []),
            "result_count": len(job.get("results", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# RANK RESULTS
# =========================
@app.get("/rank/{job_id}")
async def rank_results(job_id: str, top_k: int = 20):
    """
    Rank results by relevance to resume
    """
    try:
        if job_id not in job_store:
            raise HTTPException(status_code=404, detail="Job ID not found")

        job = job_store[job_id]
        
        if not job.get("results"):
            raise HTTPException(status_code=400, detail="No results to rank yet")

        resume_text = job.get("resume_text", "")
        results = job["results"]

        try:
            from ranker import rank_posts
            ranked = rank_posts(resume_text, results, top_k=top_k)
            
            return {
                "success": True,
                "ranked_results": ranked,
                "count": len(ranked)
            }
        except ImportError as ie:
            print(f"❌ Ranking import error: {ie}")
            raise HTTPException(status_code=500, detail="Ranking module not available. Install scikit-learn.")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error ranking results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# GET ALL JOBS
# =========================
@app.get("/jobs")
async def get_all_jobs():
    """
    List all jobs
    """
    try:
        return {
            "success": True,
            "total_jobs": len(job_store),
            "jobs": {
                job_id: {
                    "status": job["status"],
                    "skills": job.get("skills", []),
                    "result_count": len(job.get("results", []))
                }
                for job_id, job in job_store.items()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# STARTUP EVENT
# =========================
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*60)
    print("🚀 LinkedIn Job Finder API Starting...")
    print("="*60)
    print(f"📁 Upload directory: {UPLOAD_DIR}")
    print(f"🌐 Frontend directory: {FRONTEND_DIR}")
    print(f"🤖 LLM Backend: Ollama (Local)")
    
    # Check if Ollama is running
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]
            print(f"✅ Ollama is running")
            if model_names:
                print(f"📦 Available models: {', '.join(model_names[:3])}")
            else:
                print("⚠️  No models found. Run: ollama pull llama2")
        else:
            print("⚠️  Ollama not responding properly")
    except Exception as e:
        print("❌ Ollama not running!")
        print("   Start it with: ollama serve")
        print("   Then: ollama pull llama2")
    
    # Check if frontend files exist
    required_files = ["index.html", "script.js", "style.css"]
    missing_files = [f for f in required_files if not os.path.exists(os.path.join(FRONTEND_DIR, f))]
    
    if missing_files:
        print(f"⚠️ WARNING: Missing frontend files: {', '.join(missing_files)}")
        print(f"   Please place these files in the '{FRONTEND_DIR}' directory")
    else:
        print(f"✅ All frontend files found")
    
    print(f"✅ Server ready at: http://127.0.0.1:8000")
    print("="*60 + "\n")