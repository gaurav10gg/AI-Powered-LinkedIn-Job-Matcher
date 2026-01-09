import requests
import json


def normalize_skill(skill):
    """Normalize skill names for better search"""
    return (
        skill.lower()
        .replace(".js", "")
        .replace(".", "")
        .strip()
    )


def generate_queries_with_ollama(skills, max_queries=12):
    """
    Use Ollama to generate smart LinkedIn search queries
    """
    try:
        # Check if Ollama is running
        health_check = requests.get("http://localhost:11434/api/tags", timeout=2)
        if health_check.status_code != 200:
            print("⚠️  Ollama is not responding")
            return None
    except Exception:
        print("⚠️  Cannot connect to Ollama (is it running?)")
        return None
    
    # Create prompt for Ollama
    skills_str = ", ".join(skills[:10])  # Use top 10 skills
    
    prompt = f"""Given these technical skills: {skills_str}

Create {max_queries} LinkedIn search queries for job postings.

Rules:
- Mix internships and full-time jobs
- 2-4 words each
- Include variations like "hiring", "looking for", "seeking"

Respond with ONLY a JSON array. No explanation, no markdown, just the array.

Example: ["python internship", "react developer job", "hiring ml engineer"]

JSON array:"""

    try:
        print("🤖 Querying Ollama (llama3.1:8b)...")
        
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.1:8b",  # Using your available model
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower for more focused output
                    "top_p": 0.9,
                    "num_predict": 200,  # Limit response length
                }
            },
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"⚠️  Ollama returned status {response.status_code}")
            return None
        
        data = response.json()
        ollama_text = data.get("response", "").strip()
        
        print(f"📄 Ollama raw response:\n{ollama_text}\n")
       
        if "```json" in ollama_text:
            ollama_text = ollama_text.split("```json")[1].split("```")[0].strip()
        elif "```" in ollama_text:
            parts = ollama_text.split("```")
            if len(parts) >= 3:
                ollama_text = parts[1].strip()
        
       
        if ollama_text.startswith("json"):
            ollama_text = ollama_text[4:].strip()
        
        
        start_idx = ollama_text.find("[")
        end_idx = ollama_text.rfind("]")
        
        if start_idx == -1 or end_idx == -1:
            print("⚠️  Could not find JSON array in response")
            print(f"Full response: {ollama_text}")
            return None
        
        json_str = ollama_text[start_idx:end_idx + 1]
        print(f"📄 Extracted JSON: {json_str[:200]}...")
        
        
        queries = json.loads(json_str)
        
        if not isinstance(queries, list):
            print("⚠️  Response is not a list")
            return None
        
        
        valid_queries = []
        for q in queries:
            if isinstance(q, str) and len(q.strip()) > 0:
                valid_queries.append(q.strip().lower())
        
        if len(valid_queries) < 3:
            print(f"⚠️  Only got {len(valid_queries)} valid queries")
            return None
        
        print(f"✅ Generated {len(valid_queries)} queries with Ollama")
        return valid_queries[:max_queries]
        
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse JSON: {e}")
        print(f"Response was: {ollama_text[:200]}")
        return None
    except requests.exceptions.Timeout:
        print("⚠️  Ollama request timed out")
        return None
    except Exception as e:
        print(f"⚠️  Ollama error: {e}")
        return None


def build_fallback_queries(skills, max_queries=12):
    """
    Fallback query generation without AI
    """
    queries = []
    seen = set()
    
    templates = [
        "{skill} internship",
        "{skill} developer job",
        "hiring {skill} developer",
        "{skill} engineer opening",
        "looking for {skill} intern",
        "{skill} job opportunity",
    ]
    
    for skill in skills:
        if len(queries) >= max_queries:
            break
        
        clean = normalize_skill(skill)
        
        if len(clean) < 2:
            continue
        
        for template in templates:
            if len(queries) >= max_queries:
                break
            
            query = template.format(skill=clean)
            
            if query not in seen:
                seen.add(query)
                queries.append(query)
    
    
    if len(queries) < max_queries:
        generic = [
            "software engineer internship",
            "full stack developer hiring",
            "backend developer job",
            "frontend developer opening",
        ]
        
        for query in generic:
            if len(queries) >= max_queries:
                break
            if query not in seen:
                seen.add(query)
                queries.append(query)
    
    return queries[:max_queries]


def build_search_queries(skills, resume_text=None, max_queries=12):
    """
    Main function: Try Ollama first, fallback to templates
    resume_text parameter is optional (for future enhancements)
    """
    print("🔎 Building search queries...")
    
    
    ollama_queries = generate_queries_with_ollama(skills, max_queries)
    
    if ollama_queries and len(ollama_queries) >= 3:
        print("✅ Using Ollama-generated queries")
        return ollama_queries
    
    print("⚠️  Using fallback query generation...")
    fallback_queries = build_fallback_queries(skills, max_queries)
    
    return fallback_queries