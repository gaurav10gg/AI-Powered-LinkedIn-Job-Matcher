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


def generate_queries_with_ollama(skills, locations=None, country=None, max_queries=12):
    """
    Use Ollama to generate smart LinkedIn search queries with location AND country
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
    
    # Build location context
    location_context = ""
    if country:
        location_context = f"Country: {country}"
        if locations:
            location_context += f" (cities: {', '.join(locations[:2])})"
    elif locations:
        location_context = f"Location: {locations[0]}"
    
    prompt = f"""Given these technical skills: {skills_str}
{location_context}

Create {max_queries} LinkedIn search queries for job postings.

Rules:
- Mix internships and full-time jobs
- Include country in queries: "{country if country else 'India'}"
- 3-6 words each
- Include variations like "hiring", "looking for", "seeking", "opening"
- Focus on RECENT job posts
- Make queries specific to finding actual job openings in {country if country else 'India'}

Respond with ONLY a JSON array. No explanation, no markdown, just the array.

Example for India: ["python developer hiring India", "react intern opening Bangalore", "ml engineer India remote", "hiring backend developer India"]

JSON array:"""

    try:
        print(f"🤖 Querying Ollama with location context: {location_context}...")
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 250,
                }
            },
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"⚠️  Ollama returned status {response.status_code}")
            return None
        
        data = response.json()
        ollama_text = data.get("response", "").strip()
        
        print(f"📄 Ollama raw response:\n{ollama_text[:200]}...\n")
       
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
            return None
        
        json_str = ollama_text[start_idx:end_idx + 1]
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
        return None
    except requests.exceptions.Timeout:
        print("⚠️  Ollama request timed out")
        return None
    except Exception as e:
        print(f"⚠️  Ollama error: {e}")
        return None


def build_fallback_queries(skills, locations=None, country=None, max_queries=12):
    """
    Fallback query generation without AI - now with country support!
    """
    queries = []
    seen = set()
    
    # Determine country to use
    target_country = country if country else "India"
    primary_location = locations[0] if locations else None
    
    # Templates with country and location
    if primary_location:
        templates = [
            "{skill} internship {country}",
            "{skill} developer hiring {location}",
            "hiring {skill} engineer {country}",
            "{skill} job opening {location}",
            "{skill} position {country}",
            "looking for {skill} {country}",
            "{skill} remote {country}",
            "{skill} developer {location} {country}",
        ]
    else:
        templates = [
            "{skill} internship {country}",
            "{skill} developer hiring {country}",
            "hiring {skill} engineer {country}",
            "{skill} job opening {country}",
            "{skill} position available {country}",
            "looking for {skill} developer {country}",
            "{skill} remote {country}",
            "{skill} jobs {country}",
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
            
            if primary_location:
                query = template.format(
                    skill=clean, 
                    location=primary_location,
                    country=target_country
                )
            else:
                query = template.format(skill=clean, country=target_country)
            
            if query not in seen:
                seen.add(query)
                queries.append(query)
    
    # Add generic queries with country
    if len(queries) < max_queries:
        if primary_location:
            generic = [
                f"software engineer internship {primary_location}",
                f"developer hiring {target_country}",
                f"tech job opening {primary_location}",
                f"engineer position {target_country}",
                f"startup hiring {target_country}",
                f"remote job {target_country}",
            ]
        else:
            generic = [
                f"software engineer internship {target_country}",
                f"developer hiring {target_country}",
                f"tech job opening {target_country}",
                f"engineer position {target_country}",
                f"startup hiring {target_country}",
                f"remote job {target_country}",
            ]
        
        for query in generic:
            if len(queries) >= max_queries:
                break
            if query not in seen:
                seen.add(query)
                queries.append(query)
    
    return queries[:max_queries]


def build_search_queries(skills, locations=None, country=None, resume_text=None, max_queries=12):
    """
    Main function: Try Ollama first, fallback to templates
    Now includes country support!
    
    Args:
        skills: List of technical skills
        locations: List of cities/states
        country: Country name (e.g., "India", "USA", "UK")
        resume_text: Full resume text (optional)
        max_queries: Number of queries to generate
    
    Returns:
        List of search queries
    """
    print("🔎 Building search queries...")
    
    if country:
        print(f"🌍 Target Country: {country}")
    if locations:
        print(f"📍 Using locations: {', '.join(locations[:3])}")
    
    # Try Ollama first
    ollama_queries = generate_queries_with_ollama(skills, locations, country, max_queries)
    
    if ollama_queries and len(ollama_queries) >= 3:
        print("✅ Using Ollama-generated queries")
        return ollama_queries
    
    print("⚠️  Using fallback query generation...")
    fallback_queries = build_fallback_queries(skills, locations, country, max_queries)
    
    return fallback_queries