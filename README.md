# 🔵 LinkedIn Job Finder

**AI-Powered Resume Matcher for LinkedIn Job Posts**

An intelligent full-stack application that analyzes your resume, generates targeted search queries, scrapes LinkedIn for relevant job postings, and ranks them by relevance to your skills and experience.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🌟 Features

### 🤖 **AI-Powered Resume Analysis**
- **NLP-based skill extraction** using spaCy
- **Location & country detection** from resume
- **Smart query generation** using Ollama (local LLM) or template-based fallback
- Supports PDF resume parsing with pdfplumber

### 🔍 **Intelligent LinkedIn Scraping**
- **Automated LinkedIn post scraping** with Playwright
- **Job keyword filtering** to ensure posts are actually job-related
- **Time-based filtering** (past 24h, week, month)
- **Post deduplication** and link extraction
- Handles LinkedIn's authentication flow

### 📊 **Relevance Ranking**
- **TF-IDF based similarity scoring** between resume and job posts
- Ranks posts by relevance to your skills
- Configurable top-K results

### 🎨 **Modern Web Interface**
- **Drag-and-drop resume upload**
- Real-time processing status
- Interactive results display
- Export results to JSON
- Responsive design with gradient UI

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │  (HTML/CSS/JS)
│   Web UI        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │  (Backend Server)
│   Backend       │  - Resume processing
└────────┬────────┘  - Job store
         │            - Results API
         ▼
┌─────────────────┐
│  Local Agent    │  (Playwright Scraper)
│  Scraper        │  - LinkedIn automation
└────────┬────────┘  - Post collection
         │
         ▼
┌─────────────────┐
│   Ollama LLM    │  (Local AI)
│   (Optional)    │  - Query generation
└─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js** (for Playwright)
- **Ollama** (optional, for AI query generation)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/linkedin-job-finder.git
cd linkedin-job-finder
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Download spaCy language model**
```bash
python -m spacy download en_core_web_sm
```

4. **Install Playwright browsers**
```bash
playwright install chromium
```

5. **(Optional) Install Ollama for AI query generation**
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull llama3.1:8b
```

6. **Run setup script** (organizes files)
```bash
python setup.py
```

---

## 📖 Usage

### Step 1: Start the Backend Server

```bash
cd backend
uvicorn main:app --reload
```

The server will start at `http://127.0.0.1:8000`

### Step 2: Upload Resume

1. Open your browser and go to `http://127.0.0.1:8000`
2. Drag and drop your resume (PDF only) or click to browse
3. Click **"Process Resume"**
4. Copy the **Job ID** displayed on screen

### Step 3: Run the LinkedIn Scraper

In a **new terminal window**:

```bash
cd backend
python local_agent.py
```

- Paste the Job ID when prompted
- **Log in to LinkedIn** in the browser window that opens
- Wait for the scraper to collect posts
- Results are automatically sent to the backend

### Step 4: View Results

1. Return to the web interface
2. Click **"I've Started the Agent - Check for Results"**
3. View, export, or rank the collected job posts

### Alternative: Command-Line Results Viewer

```bash
python view_results.py
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **FastAPI** | REST API server |
| **Uvicorn** | ASGI server |
| **spaCy** | NLP for skill extraction |
| **pdfplumber** | PDF text extraction |
| **scikit-learn** | TF-IDF ranking |
| **Playwright** | Browser automation |
| **Ollama** | Local LLM (optional) |

### Frontend
- **Vanilla JavaScript** - No frameworks
- **Modern CSS** - Gradients, animations, responsive design
- **Font Awesome** - Icons

---

## 📁 Project Structure

```
linkedin-job-finder/
│
├── backend/
│   ├── main.py                    # FastAPI server
│   ├── linkedin_scraper.py        # Playwright scraper
│   ├── local_agent.py             # Agent runner
│   ├── resume_parser.py           # PDF extraction
│   ├── skill_extractor.py         # NLP skill extraction
│   ├── query_builder_local_llm.py # AI query generation
│   ├── ranker.py                  # TF-IDF ranking
│   └── uploads/                   # Resume storage
│
├── frontend/
│   ├── index.html                 # Web interface
│   ├── script.js                  # Frontend logic
│   └── style.css                  # Styling
│
├── requirements.txt               # Python dependencies
├── setup.py                       # Setup script
├── view_results.py                # CLI results viewer
└── README.md                      # This file
```

---

## 🎯 Key Features Breakdown

### 1️⃣ **Resume Processing**

The system extracts:
- **Technical skills** (Python, React, ML, etc.)
- **Topics** (web development, data science, etc.)
- **Locations** (cities, states)
- **Country** (India, USA, UK, etc.)

**Example:**
```python
{
  "skills": ["python", "react", "machine learning"],
  "topics": ["web development", "data analysis"],
  "locations": ["Bangalore", "Karnataka"],
  "country": "India"
}
```

### 2️⃣ **Smart Query Generation**

**With Ollama (AI-powered):**
```
- "python developer hiring India"
- "react intern opening Bangalore"
- "ml engineer India remote"
```

**Without Ollama (Template-based):**
```
- "python internship India"
- "react job opening Bangalore"
- "machine learning position India"
```

### 3️⃣ **Job Post Filtering**

Only posts containing hiring keywords are collected:
- ✅ "We're hiring Python developers"
- ✅ "Looking for React interns"
- ✅ "Join our ML team - apply now"
- ❌ "Proud to announce our new product launch"
- ❌ "Congratulations to our team"

### 4️⃣ **Relevance Ranking**

Uses **TF-IDF cosine similarity** to match:
- Resume skills → Job post content
- Resume experience → Job requirements
- Returns top K most relevant posts

---

## 🔧 Configuration

### Time Filters

Modify in `linkedin_scraper.py`:

```python
scrape_posts(
    queries=queries,
    limit_per_query=5,
    time_filter="past-week"  # Options: past-24h, past-week, past-month
)
```

### Query Limits

Modify in `query_builder_local_llm.py`:

```python
build_search_queries(
    skills=skills,
    locations=locations,
    country=country,
    max_queries=12  # Adjust number of queries
)
```

### Ranking Configuration

Modify in `ranker.py`:

```python
rank_posts(
    resume_text=resume_text,
    posts=posts,
    top_k=20  # Number of top results
)
```

---

## 🌍 Location & Country Detection

The system automatically detects your target job market:

**Supported Countries:**
- 🇮🇳 India
- 🇺🇸 USA
- 🇬🇧 UK
- 🇨🇦 Canada
- 🇦🇺 Australia
- 🇸🇬 Singapore
- 🇦🇪 UAE
- 🇩🇪 Germany
- And more...

**Example:**
```
Resume mentions: "Bangalore, Karnataka"
→ Detected Country: India
→ Query: "python developer hiring India"
```

---

## 🐛 Troubleshooting

### Issue: "Ollama not running"

**Solution:**
```bash
# Start Ollama service
ollama serve

# Pull the model
ollama pull llama3.1:8b
```

### Issue: "Login verification failed"

**Solution:**
- Ensure you're fully logged in to LinkedIn
- Complete any security checkpoints
- Wait for the feed to load before pressing ENTER

### Issue: "No posts found"

**Possible causes:**
- LinkedIn rate limiting (wait 24 hours)
- Invalid search queries
- Time filter too restrictive

**Solution:**
- Try broader search terms
- Change `time_filter` to "past-month"
- Reduce `limit_per_query`

### Issue: "Cannot connect to backend"

**Solution:**
```bash
# Make sure backend is running
cd backend
uvicorn main:app --reload
```

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve web interface |
| `/health` | GET | Server health check |
| `/process-resume` | POST | Upload and process resume |
| `/api/results/{job_id}` | GET | Get job details for agent |
| `/api/submit-results/{job_id}` | POST | Submit scraped posts |
| `/results/{job_id}` | GET | Get results for frontend |
| `/rank/{job_id}` | GET | Get ranked results |
| `/jobs` | GET | List all jobs |

---

## 🔐 Privacy & Security

- ✅ All processing happens **locally** on your machine
- ✅ Resume data is stored **only in your `/uploads` folder**
- ✅ No data is sent to external servers (except LinkedIn)
- ✅ LinkedIn credentials are **never stored**
- ⚠️ You must log in to LinkedIn manually (no credential handling)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 Roadmap

- [ ] Add support for Google Drive resume storage
- [ ] Implement email notifications when jobs are found
- [ ] Add job post deduplication across sessions
- [ ] Support for multiple resume formats (DOCX, TXT)
- [ ] Integration with job boards (Indeed, Glassdoor)
- [ ] Chrome extension for one-click scraping
- [ ] Docker containerization
- [ ] Cloud deployment guide

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **spaCy** for NLP capabilities
- **Playwright** for browser automation
- **FastAPI** for the excellent framework
- **Ollama** for local LLM support
- **LinkedIn** for the platform (use responsibly!)

---

## ⚠️ Disclaimer

This tool is for **educational and personal use only**. Please respect LinkedIn's Terms of Service and use responsibly:

- ✅ Use for personal job searching
- ✅ Reasonable scraping limits (5-10 posts per query)
- ❌ Do not use for commercial purposes
- ❌ Do not scrape at high frequency
- ❌ Do not violate LinkedIn's rate limits

**The authors are not responsible for any misuse of this tool.**


<div align="center">

**⭐ If you found this project helpful, please give it a star!**

Made with ❤️ for job seekers

</div>
