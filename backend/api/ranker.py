from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os
import google.generativeai as genai
import logging
import json
import re
import asyncio

router = APIRouter()

def clean_and_parse_json(text):
    """
    More robust JSON parsing with proper error handling
    """
    try:
        # First, try to parse as-is
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON array from the response
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if not json_match:
        print("No JSON array found in response")
        return []
    
    json_str = json_match.group(0)
    
    # Try parsing the extracted JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        print(f"Problematic JSON: {json_str[:500]}...")
        
        # Last resort: try to parse individual objects
        return parse_individual_objects(json_str)

def parse_individual_objects(json_str):
    """
    Parse individual JSON objects from a malformed array
    """
    objects = []
    
    # Find individual objects using regex
    object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(object_pattern, json_str)
    
    for match in matches:
        try:
            # Clean up common issues
            cleaned = match.strip()
            
            # Remove trailing commas before closing braces
            cleaned = re.sub(r',(\s*})', r'\1', cleaned)
            
            # Parse the object
            obj = json.loads(cleaned)
            
            # Validate that it has required fields
            if isinstance(obj, dict) and obj:
                objects.append(obj)
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse individual object: {e}")
            print(f"Object: {match}")
            continue
    
    return objects

def validate_resume_object(resume):
    """
    Validate and clean a resume object
    """
    if not isinstance(resume, dict):
        return None
    
    # Ensure required fields exist
    required_fields = ['score']
    for field in required_fields:
        if field not in resume:
            resume[field] = 0
    
    try:
        resume['score'] = float(resume['score'])
    except (ValueError, TypeError):
        resume['score'] = 0
    
    if 'company_fit' not in resume:
        resume['company_fit'] = "Analysis not available"
    
    if 'score_split_up' not in resume or not isinstance(resume['score_split_up'], dict):
        resume['score_split_up'] = {
            "project_tech": 0,
            "project_innovation": 0,
            "achievements": 0,
            "other": 0
        }
    
    return resume

async def gemini_rank_resumes(resumes):
    
    api_key = os.getenv("GOOGLE_API_KEY") or 'AIzaSyBf_FexIh3jQP69UA0ymeCP7Gaodl5Wlgg'
    if not api_key:
        raise Exception("GOOGLE_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
    except Exception:
        model = genai.GenerativeModel("gemini-pro")

    prompt = (
    "You are an expert resume ranker for HappyFox company. "
    "Given the following list of resumes in JSON, rank them from best to worst for a software engineering role at HappyFox.\n\n"
    "At HappyFox, we are looking for:\n"
    "- Frontend engineers with React.js, Ember.js, or HTML/CSS/JS skills\n"
    "- Backend engineers with Python and Django skills\n"
    "- Full stack engineers (MERN stack is also good)\n\n"
    "For each resume, analyze the candidate's tech stack, projects, and skills, and determine if they are a good fit for HappyFox. "
    "If they fit, specify the most suitable role: 'Frontend Engineer', 'Backend Engineer', or 'Full Stack Engineer'. "
    "If they do not fit, state clearly that they are not a fit and briefly explain why.\n\n"
    "IMPORTANT: Return ONLY a valid JSON array. Do not include any text before or after the JSON. "
    "Each resume object must have these exact fields:\n"
    "- All original fields from the input resume\n"
    "- 'score': number between 0-100 (higher is better)\n"
    "- 'company_fit': string with your analysis and fit/role decision\n"
    "- 'score_split_up': object with keys 'Project Tech', 'Project Innovation', 'Achievements', 'Other'. "
    "Each key must have an object with 'score' (number) and 'reason' (string) explaining why that score was given. "
    "For 'project_innovation', the 'reason' must clearly state why the project is innovative and how it demonstrates innovation. "
    "For example: 'project_tech': {'score': 20, 'reason': 'Candidate used React and Django in multiple projects.'}\n\n"
    f"Input resumes:\n{json.dumps(resumes, indent=2)}\n\n"
    "Output only the JSON array:"
)

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, lambda: model.generate_content(prompt)
    )
    
    try:
        text = response.text.strip()
        print("Gemini response text:", text[:500] + "..." if len(text) > 500 else text)
        
        # Clean and parse the JSON
        ranked_raw = clean_and_parse_json(text)
        
        if not isinstance(ranked_raw, list):
            print("Response is not a list")
            return []
        
        # Validate and clean each resume object
        ranked = []
        for resume in ranked_raw:
            validated_resume = validate_resume_object(resume)
            if validated_resume:
                ranked.append(validated_resume)
        
        # Sort by score (highest first)
        ranked.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return ranked
        
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        import traceback
        print(traceback.format_exc())
        return []

@router.post("/api/rank-resumes/")
async def rank_resumes(request: Request):
    try:
        data = await request.json()
        resumes = data.get('resumes', [])
        
        if not resumes:
            return JSONResponse({"error": "No resumes provided"}, status_code=400)
        
        ranked = await gemini_rank_resumes(resumes)
        print(f"Successfully ranked {len(ranked)} resumes")
        
        if not ranked:
            return JSONResponse({
                "error": "Gemini did not return a valid ranked list. Please check the logs for details."
            }, status_code=500)
            
        return JSONResponse({"ranked_resumes": ranked})
        
    except Exception as e:
        import traceback
        print("Rank resumes error:", traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=500)