import requests
from linkedin_scraper import scrape_posts
import json

BACKEND_URL = "http://127.0.0.1:8000"
JOB_ENDPOINT = "/api/results"
SUBMIT_ENDPOINT = "/api/submit-results"

LIMIT_PER_QUERY = 5


def run_agent(job_id: str):
    print(f"\n🔗 Fetching job details for job_id: {job_id}")

    try:
        resp = requests.get(f"{BACKEND_URL}{JOB_ENDPOINT}/{job_id}")
        
        if resp.status_code != 200:
            print(f"❌ Failed to fetch job from backend (Status: {resp.status_code})")
            print(f"Response: {resp.text}")
            return

        job_data = resp.json()
        queries = job_data.get("queries", [])

        if not queries:
            print("❌ No queries found in job data")
            return

        print(f"✅ Received {len(queries)} queries")
        print(f"📋 Queries: {queries[:3]}..." if len(queries) > 3 else f"📋 Queries: {queries}")

        # Scrape LinkedIn
        print("\n" + "="*60)
        print("🚀 Starting LinkedIn scraper...")
        print("="*60)
        
        results = scrape_posts(
            queries=queries,
            limit_per_query=LIMIT_PER_QUERY
        )

        if not results:
            print("❌ No results scraped")
            return

        print(f"\n📤 Sending {len(results)} posts to backend")

        # Submit results
        payload = {"results": results}
        
        submit = requests.post(
            f"{BACKEND_URL}{SUBMIT_ENDPOINT}/{job_id}",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if submit.status_code == 200:
            response_data = submit.json()
            print("\n" + "="*60)
            print("✅ SUCCESS: Results submitted")
            print("="*60)
            print(f"   Backend confirmed: {response_data.get('count', 0)} posts received")
            print(f"\n🌐 View results at: http://127.0.0.1:8000")
            print("\n💡 Tip: Go to the web interface and click 'I've Started the Agent - Check for Results'")
        else:
            print(f"❌ Failed to submit results (Status: {submit.status_code})")
            print(f"Response: {submit.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend. Make sure it's running:")
        print("   1. Open another terminal")
        print("   2. cd backend")
        print("   3. uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "="*60)
    print(" 🔵 LinkedIn Local Agent")
    print("="*60)
    
    print("\n⚠️  IMPORTANT: Make sure the backend server is running!")
    print("   (In another terminal: cd backend && uvicorn main:app --reload)")
    
    print("\n" + "-"*60)
    
    job_id = input("📌 Paste JOB ID: ").strip()

    if job_id:
        run_agent(job_id)
    else:
        print("❌ Job ID required")
        print("\n💡 How to get a Job ID:")
        print("   1. Go to http://127.0.0.1:8000")
        print("   2. Upload your resume")
        print("   3. Copy the Job ID shown on screen")