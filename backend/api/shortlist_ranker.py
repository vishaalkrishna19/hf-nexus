import google.generativeai as genai
import os
import json
import re
import asyncio
from typing import List, Dict, Any

def clean_and_parse_json(text):
    """More robust JSON parsing with proper error handling"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if not json_match:
        print("No JSON array found in response")
        return []
    
    json_str = json_match.group(0)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        return parse_individual_objects(json_str)

def parse_individual_objects(json_str):
    """Parse individual JSON objects from a malformed array"""
    objects = []
    object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(object_pattern, json_str)
    
    for match in matches:
        try:
            cleaned = match.strip()
            cleaned = re.sub(r',(\s*})', r'\1', cleaned)
            obj = json.loads(cleaned)
            
            if isinstance(obj, dict) and obj:
                objects.append(obj)
        except json.JSONDecodeError as e:
            print(f"Failed to parse individual object: {e}")
            continue
    
    return objects

def validate_candidate_object(candidate):
    """Validate and clean a candidate object"""
    if not isinstance(candidate, dict):
        return None
    
    # Ensure required fields exist with proper defaults
    required_fields = {
        'shortlist_score': 0,
        'criteria_match': 'Analysis not available',
        'criteria_analysis': {
            'academic_performance': {'score': 0, 'reason': 'Not analyzed'},
            'technical_skills': {'score': 0, 'reason': 'Not analyzed'},
            'practical_experience': {'score': 0, 'reason': 'Not analyzed'},
            'achievements': {'score': 0, 'reason': 'Not analyzed'}
        }
    }
    
    for field, default_value in required_fields.items():
        if field not in candidate or candidate[field] is None:
            candidate[field] = default_value
    
    # Validate and convert shortlist_score
    try:
        candidate['shortlist_score'] = float(candidate['shortlist_score'])
    except (ValueError, TypeError):
        candidate['shortlist_score'] = 0
    
    # Validate criteria_analysis structure
    if not isinstance(candidate['criteria_analysis'], dict):
        candidate['criteria_analysis'] = required_fields['criteria_analysis']
    else:
        # Ensure all required analysis fields exist
        for key, default_analysis in required_fields['criteria_analysis'].items():
            if key not in candidate['criteria_analysis']:
                candidate['criteria_analysis'][key] = default_analysis
            elif not isinstance(candidate['criteria_analysis'][key], dict):
                candidate['criteria_analysis'][key] = default_analysis
            else:
                # Ensure score and reason exist
                if 'score' not in candidate['criteria_analysis'][key]:
                    candidate['criteria_analysis'][key]['score'] = 0
                if 'reason' not in candidate['criteria_analysis'][key]:
                    candidate['criteria_analysis'][key]['reason'] = 'Not analyzed'
                
                # Validate score is numeric
                try:
                    candidate['criteria_analysis'][key]['score'] = float(candidate['criteria_analysis'][key]['score'])
                except (ValueError, TypeError):
                    candidate['criteria_analysis'][key]['score'] = 0
    
    return candidate

def filter_shortlist_fields(candidate):
    """Return only the static fields required for shortlist page."""
    return {
        "Rank": candidate.get("Rank"),
        "name": candidate.get("name"),
        "email": candidate.get("email"),
        "phone": candidate.get("phone"),
        "github": candidate.get("github"),
        "internships": candidate.get("internships"),
        "projects": candidate.get("projects"),
        "github_profile_analysis": candidate.get("github_profile_analysis"),
        "achievements": candidate.get("achievements"),
        "shortlist_score": candidate.get("shortlist_score"),
        "criteria_match": candidate.get("criteria_match"),
        "criteria_analysis": candidate.get("criteria_analysis"),
    }

async def shortlist_candidates_with_gemini(candidates: List[Dict[Any, Any]], criteria: Dict[Any, Any]) -> List[Dict[Any, Any]]:
    """Shortlist candidates using Gemini based on specific criteria"""

    print(f"DEBUG: Starting shortlist analysis for {len(candidates)} candidates")
    print(f"DEBUG: Criteria received: {criteria}")

    # Build comprehensive prompt for shortlisting
    prompt = f"""
You are an expert HR recruiter analyzing candidates for shortlisting based on specific criteria.

SHORTLISTING CRITERIA:
- CGPA: Min {criteria.get('cgpa', {}).get('min', 6.0)}, Max {criteria.get('cgpa', {}).get('max', 10.0)}, Weight: {criteria.get('cgpa', {}).get('weight', 25)}%
- 10th Marks: Min {criteria.get('tenthMarks', {}).get('min', 60)}%, Weight: {criteria.get('tenthMarks', {}).get('weight', 10)}%
- 12th Marks: Min {criteria.get('twelfthMarks', {}).get('min', 60)}%, Weight: {criteria.get('twelfthMarks', {}).get('weight', 10)}%
- Internships: Min {criteria.get('internships', {}).get('min', 0)}, Weight: {criteria.get('internships', {}).get('weight', 15)}%
- Projects: Min {criteria.get('projects', {}).get('min', 1)}, Weight: {criteria.get('projects', {}).get('weight', 15)}%
- Required Tech Stack: {criteria.get('techStack', {}).get('required', [])}
- Preferred Tech Stack: {criteria.get('techStack', {}).get('preferred', [])}
- Tech Stack Weight: {criteria.get('techStack', {}).get('weight', 20)}%
- Achievement Keywords: {criteria.get('achievements', {}).get('keywords', [])}
- Achievement Weight: {criteria.get('achievements', {}).get('weight', 5)}%

For each candidate, analyze their fit against these criteria and provide:
1. A shortlist_score (0-100) based on how well they meet the criteria
2. A criteria_match explanation of their strengths and gaps
3. A detailed criteria_analysis with scores and reasons for each category

IMPORTANT:
- Return ONLY a valid JSON array.
- Each candidate object must have:
  - All original fields from the input
  - 'shortlist_score': number between 0-100
  - 'criteria_match': string explaining their fit against criteria
  - 'criteria_analysis': object with keys 'academic_performance', 'technical_skills', 'practical_experience', 'achievements'
    Each key must have an object with 'score' (number) and 'reason' (string)

Example output:
[
  {{
    "name": "Rahul Sharma",
    "shortlist_score": 92,
    "criteria_match": "Strong academic and technical background, meets all criteria.",
    "criteria_analysis": {{
      "academic_performance": {{"score": 90, "reason": "CGPA and board marks are excellent."}},
      "technical_skills": {{"score": 95, "reason": "Has all required and preferred tech stack."}},
      "practical_experience": {{"score": 85, "reason": "Internships and projects above minimum."}},
      "achievements": {{"score": 80, "reason": "Relevant achievements found."}}
    }},
    ...other original fields...
  }},
  ...more candidates...
]

Candidates to analyze:
{json.dumps(candidates, indent=2)}

Output only the JSON array, no explanation or markdown:
"""

    def gemini_call():
        api_key = os.getenv("GOOGLE_API_KEY") or 'AIzaSyBf_FexIh3jQP69UA0ymeCP7Gaodl5Wlgg'
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
        except Exception:
            model = genai.GenerativeModel("gemini-pro")
        return model.generate_content(prompt)

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, gemini_call)
        text = response.text.strip()
        print("DEBUG: Gemini shortlist response text:", text[:500] + "..." if len(text) > 500 else text)

        shortlisted_raw = clean_and_parse_json(text)
        print(f"DEBUG: Parsed candidates count: {len(shortlisted_raw)}")

        if not isinstance(shortlisted_raw, list):
            print("DEBUG: Response is not a list")
            return []

        shortlisted = []
        for candidate in shortlisted_raw:
            validated_candidate = validate_candidate_object(candidate)
            if validated_candidate:
                shortlisted.append(validated_candidate)
            else:
                print(f"DEBUG: Failed to validate candidate: {candidate}")

        print(f"DEBUG: Final shortlisted count: {len(shortlisted)}")

        shortlisted.sort(key=lambda x: x.get('shortlist_score', 0), reverse=True)
        # Only return static fields for each candidate
        return [filter_shortlist_fields(c) for c in shortlisted]

    except Exception as e:
        print(f"DEBUG: Error in shortlist analysis: {e}")
        import traceback
        print(traceback.format_exc())
        return []
