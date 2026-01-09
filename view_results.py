import requests
import json
from backend.ranker import rank_posts
from backend.resume_parser import extract_text_from_pdf

BACKEND_URL = "http://127.0.0.1:8000"


def view_results(job_id: str, rank_by_resume: bool = False):
    """
    Fetch and display results from backend
    """
    print(f"\n🔍 Fetching results for job_id: {job_id}\n")
    
    try:
        resp = requests.get(f"{BACKEND_URL}/results/{job_id}")
        
        if resp.status_code != 200:
            print(f"❌ Failed to fetch results (Status: {resp.status_code})")
            return
        
        data = resp.json()
        
        if data.get("status") == "not_found":
            print("❌ Job ID not found")
            return
        
        status = data.get("status")
        results = data.get("results", [])
        skills = data.get("skills", [])
        queries = data.get("queries", [])
        
        print("="*70)
        print(f"📊 JOB STATUS: {status.upper()}")
        print("="*70)
        print(f"✅ Skills Extracted: {', '.join(skills[:10])}")
        print(f"🔍 Queries Used: {len(queries)}")
        print(f"📝 Total Posts Found: {len(results)}")
        print("="*70 + "\n")
        
        if status == "waiting_for_linkedin":
            print("⏳ Waiting for LinkedIn scraping to complete...")
            print("   Run the local_agent.py to scrape LinkedIn posts")
            return
        
        if not results:
            print("❌ No results yet")
            return
        
        # Option to rank by resume
        if rank_by_resume:
            print("🎯 Ranking posts by relevance to your resume...\n")
            # Get resume text from job data (you'll need to modify this)
            # For now, we'll just display all results
        
        # Display results
        for idx, post in enumerate(results, 1):
            print(f"\n{'─'*70}")
            print(f"📌 POST #{idx}")
            print(f"{'─'*70}")
            print(f"👤 Author: {post['author']}")
            print(f"🔍 Query: {post['query']}")
            print(f"\n📝 Content:\n{post['content'][:300]}{'...' if len(post['content']) > 300 else ''}")
            
            if post.get('links'):
                print(f"\n🔗 Links:")
                for link in post['links'][:3]:
                    print(f"   • {link}")
            
            print()
        
        # Save to file
        save_option = input("\n💾 Save results to file? (y/n): ").lower()
        if save_option == 'y':
            filename = f"results_{job_id[:8]}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved to {filename}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running:")
        print("   uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")


def list_all_jobs():
    """
    List all jobs in the system
    """
    try:
        resp = requests.get(f"{BACKEND_URL}/jobs")
        
        if resp.status_code != 200:
            print(f"❌ Failed to fetch jobs (Status: {resp.status_code})")
            return
        
        data = resp.json()
        total = data.get("total_jobs", 0)
        jobs = data.get("jobs", {})
        
        print(f"\n📋 Total Jobs: {total}\n")
        print("="*70)
        
        for job_id, job_info in jobs.items():
            status = job_info.get("status", "unknown")
            result_count = job_info.get("result_count", 0)
            skills = job_info.get("skills", [])
            
            status_emoji = "✅" if status == "completed" else "⏳"
            
            print(f"\n{status_emoji} Job ID: {job_id}")
            print(f"   Status: {status}")
            print(f"   Results: {result_count} posts")
            print(f"   Skills: {', '.join(skills[:5])}")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" 📊 LinkedIn Results Viewer")
    print("="*70)
    
    print("\nOptions:")
    print("1. View results for a specific job")
    print("2. List all jobs")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        job_id = input("\n📌 Enter JOB ID: ").strip()
        if job_id:
            view_results(job_id)
        else:
            print("❌ Job ID required")
    
    elif choice == "2":
        list_all_jobs()
    
    else:
        print("❌ Invalid choice")
