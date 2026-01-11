import spacy
from collections import Counter
import re


# Load spaCy model
nlp = spacy.load("en_core_web_sm")


TECH_SKILLS = {
    "python", "java", "javascript", "c", "sql",
    "react", "react.js", "next.js",
    "node", "node.js", "express", "mongodb",
    "machine learning", "deep learning",
    "data science", "artificial intelligence",
    "ai", "ml",
    "git", "github",
    "docker", "aws"
}


# Geographic database for country detection
# Format: {location_name: country_name}
LOCATION_TO_COUNTRY = {
    # Indian cities
    'bangalore': 'India', 'bengaluru': 'India', 'mumbai': 'India', 'bombay': 'India',
    'delhi': 'India', 'new delhi': 'India', 'hyderabad': 'India', 'pune': 'India',
    'chennai': 'India', 'madras': 'India', 'kolkata': 'India', 'calcutta': 'India',
    'ahmedabad': 'India', 'gurgaon': 'India', 'gurugram': 'India', 'noida': 'India',
    'jaipur': 'India', 'lucknow': 'India', 'indore': 'India', 'bhopal': 'India',
    'nagpur': 'India', 'vadodara': 'India', 'surat': 'India', 'coimbatore': 'India',
    'kochi': 'India', 'cochin': 'India', 'trivandrum': 'India', 'thiruvananthapuram': 'India',
    'chandigarh': 'India', 'madurai': 'India', 'mysore': 'India', 'mangalore': 'India',
    'visakhapatnam': 'India', 'vijayawada': 'India', 'bhubaneswar': 'India',
    'pondicherry': 'India', 'puducherry': 'India', 'gangtok': 'India', 'shimla': 'India',
    'patna': 'India', 'ranchi': 'India', 'guwahati': 'India', 'dehradun': 'India',
    
    # Indian states/territories
    'karnataka': 'India', 'maharashtra': 'India', 'tamil nadu': 'India', 
    'telangana': 'India', 'west bengal': 'India', 'kerala': 'India',
    'rajasthan': 'India', 'gujarat': 'India', 'punjab': 'India', 'haryana': 'India',
    'uttar pradesh': 'India', 'madhya pradesh': 'India', 'andhra pradesh': 'India',
    'odisha': 'India', 'assam': 'India', 'jharkhand': 'India', 'bihar': 'India',
    'chhattisgarh': 'India', 'himachal pradesh': 'India', 'uttarakhand': 'India',
    'goa': 'India', 'sikkim': 'India', 'manipur': 'India', 'meghalaya': 'India',
    
    # US cities (for international students)
    'new york': 'USA', 'los angeles': 'USA', 'chicago': 'USA', 'houston': 'USA',
    'san francisco': 'USA', 'boston': 'USA', 'seattle': 'USA', 'austin': 'USA',
    'san jose': 'USA', 'dallas': 'USA', 'denver': 'USA', 'atlanta': 'USA',
    'miami': 'USA', 'philadelphia': 'USA', 'phoenix': 'USA', 'portland': 'USA',
    
    # US states
    'california': 'USA', 'texas': 'USA', 'florida': 'USA', 'new york': 'USA',
    'massachusetts': 'USA', 'washington': 'USA', 'colorado': 'USA', 'georgia': 'USA',
    
    # UK cities
    'london': 'UK', 'manchester': 'UK', 'birmingham': 'UK', 'edinburgh': 'UK',
    'glasgow': 'UK', 'cambridge': 'UK', 'oxford': 'UK', 'bristol': 'UK',
    
    # Canada
    'toronto': 'Canada', 'vancouver': 'Canada', 'montreal': 'Canada', 'ottawa': 'Canada',
    'calgary': 'Canada', 'ontario': 'Canada', 'quebec': 'Canada', 'british columbia': 'Canada',
    
    # Australia
    'sydney': 'Australia', 'melbourne': 'Australia', 'brisbane': 'Australia',
    'perth': 'Australia', 'adelaide': 'Australia', 'canberra': 'Australia',
    
    # Singapore
    'singapore': 'Singapore',
    
    # UAE
    'dubai': 'UAE', 'abu dhabi': 'UAE', 'sharjah': 'UAE',
    
    # Germany
    'berlin': 'Germany', 'munich': 'Germany', 'frankfurt': 'Germany', 'hamburg': 'Germany',
    
    # Other countries that are commonly mentioned
    'china': 'China', 'japan': 'Japan', 'south korea': 'South Korea', 
    'france': 'France', 'spain': 'Spain', 'italy': 'Italy',
    'netherlands': 'Netherlands', 'switzerland': 'Switzerland',
}


def detect_country_from_location(location: str) -> str:
    """
    Detect which country a location belongs to.
    
    Args:
        location: City or state name
    
    Returns:
        Country name (e.g., "India", "USA", "UK")
        Returns None if country cannot be determined
    """
    if not location:
        return None
    
    location_lower = location.lower().strip()
    
    # Direct lookup
    if location_lower in LOCATION_TO_COUNTRY:
        return LOCATION_TO_COUNTRY[location_lower]
    
    # Partial match (for "Bangalore, Karnataka" → matches "bangalore")
    for loc_key, country in LOCATION_TO_COUNTRY.items():
        if loc_key in location_lower or location_lower in loc_key:
            return country
    
    # If location IS a country name
    if location_lower in ['india', 'usa', 'united states', 'america', 'uk', 
                          'united kingdom', 'canada', 'australia', 'singapore',
                          'uae', 'germany', 'france', 'japan', 'china']:
        return location.title()
    
    return None


def extract_locations_with_nlp(text: str, top_k: int = 3):
    """
    Extract locations using spaCy's Named Entity Recognition (NER).
    This automatically detects GPE (Geo-Political Entity) and LOC (Location) entities.
    """
    if not text:
        return []
    
    # Process with spaCy
    doc = nlp(text)
    
    locations = []
    location_counts = Counter()
    
    # Extract all GPE (cities, states, countries) and LOC
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            location = ent.text.strip()
            
            # Filter out very short or generic words
            if len(location) < 3:
                continue
            
            # Skip common non-location words
            skip_words = {
                'university', 'institute', 'college', 'school', 'company',
                'indian', 'american', 'european', 'asian',
                'online', 'remote', 'virtual', 'digital'
            }
            
            if location.lower() in skip_words:
                continue
            
            # Count occurrences
            location_counts[location] += 1
    
    # Get most frequently mentioned locations
    for location, count in location_counts.most_common(top_k * 2):
        if location not in locations:
            locations.append(location)
        
        if len(locations) >= top_k:
            break
    
    return locations


def extract_locations_and_country(text: str, top_k: int = 3):
    """
    Extract locations AND determine the country.
    
    Returns:
        dict with 'locations' (list) and 'country' (str)
    
    Example:
        Input: "Studied at IIT Madras, Chennai, Tamil Nadu"
        Output: {
            'locations': ['Chennai', 'Tamil Nadu'],
            'country': 'India'
        }
    """
    if not text:
        return {'locations': [], 'country': None}
    
    # Extract locations using NLP
    locations = extract_locations_with_nlp(text, top_k=top_k)
    
    # Detect country from locations
    country = None
    country_votes = Counter()
    
    for location in locations:
        detected_country = detect_country_from_location(location)
        if detected_country:
            country_votes[detected_country] += 1
    
    # Most common country wins
    if country_votes:
        country = country_votes.most_common(1)[0][0]
    
    # If no country detected from locations, check if "India" appears in text
    if not country:
        text_lower = text.lower()
        if 'india' in text_lower or 'indian' in text_lower:
            country = 'India'
        elif 'usa' in text_lower or 'united states' in text_lower or 'america' in text_lower:
            country = 'USA'
        elif 'uk' in text_lower or 'united kingdom' in text_lower:
            country = 'UK'
    
    return {
        'locations': locations,
        'country': country
    }


def extract_skills_and_topics(resume_text: str, top_k: int = 15):
    """
    Extract skills and topics from resume using spaCy NLP.
    """
    doc = nlp(resume_text)

    phrases = []

    # Extract noun phrases
    for chunk in doc.noun_chunks:
        phrase = chunk.text.lower().strip()
        if len(phrase) > 2:
            phrases.append(phrase)

    # Extract tech skills
    for token in doc:
        if token.text.lower() in TECH_SKILLS:
            phrases.append(token.text.lower())

    freq = Counter(phrases)

    skills = []
    topics = []

    for phrase, _ in freq.most_common():
        if phrase in TECH_SKILLS:
            skills.append(phrase)
        elif any(word in phrase for word in ["ai", "ml", "analytics", "backend", "frontend", "full stack"]):
            topics.append(phrase)

    return {
        "skills": skills[:top_k],
        "topics": topics[:top_k]
    }


def extract_skills_topics_and_locations(resume_text: str, raw_text: str = None, top_k: int = 15):
    """
    Extract skills, topics, locations, AND country in one go using NLP.
    
    Args:
        resume_text: Cleaned resume text (for skills)
        raw_text: Original resume text with proper capitalization (for locations)
        top_k: Number of top items to return
    
    Returns:
        dict with 'skills', 'topics', 'locations', and 'country'
        
    Example:
        {
            "skills": ["python", "react", "machine learning"],
            "topics": ["web development", "data analysis"],
            "locations": ["Pondicherry", "Tamil Nadu"],
            "country": "India"
        }
    """
    text_for_locations = raw_text if raw_text else resume_text
    
    # Extract skills and topics
    skills_data = extract_skills_and_topics(resume_text, top_k=top_k)
    
    # Extract locations and detect country
    location_data = extract_locations_and_country(text_for_locations, top_k=3)
    
    return {
        "skills": skills_data["skills"],
        "topics": skills_data["topics"],
        "locations": location_data["locations"],
        "country": location_data["country"]
    }


if __name__ == "__main__":
    from resume_parser import extract_text_and_metadata

    # Test with sample resume
    try:
        result = extract_text_and_metadata("Gaurav-G-FlowCV-Resume-20251212.pdf")
        resume_text = result["text"]
        raw_text = result["raw_text"]

        # Extract everything together
        extracted = extract_skills_topics_and_locations(resume_text, raw_text)

        print("\n" + "="*60)
        print("📊 EXTRACTION RESULTS")
        print("="*60)
        
        print("\n🔧 Skills:")
        for s in extracted["skills"]:
            print(f"  • {s}")

        print("\n📚 Topics:")
        for t in extracted["topics"]:
            print(f"  • {t}")
        
        print("\n📍 Locations:")
        for loc in extracted["locations"]:
            country = detect_country_from_location(loc)
            country_str = f" ({country})" if country else ""
            print(f"  • {loc}{country_str}")
        
        print(f"\n🌍 Detected Country: {extracted['country'] or 'Unknown'}")
        
        print("\n" + "="*60)
        
        # Test country detection
        print("\n🔬 COUNTRY DETECTION TEST")
        print("="*60)
        
        test_locations = [
            "Pondicherry", "Chennai", "Tamil Nadu", "Bangalore",
            "San Francisco", "California", "London", "Toronto"
        ]
        
        print("\nLocation → Country Mapping:")
        for loc in test_locations:
            country = detect_country_from_location(loc)
            print(f"  {loc:20} → {country or 'Unknown'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 TIP: Make sure you have a resume PDF in the current directory")