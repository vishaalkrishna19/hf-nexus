import re
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def check_ats_compliance(parsed_resume):
    """
    Enhanced ATS compliance checker with partial scoring.
    Returns a dict: { 'score': int, 'status': 'Excellent'|'Good'|'Fair'|'Poor', 'details': [str, ...], 'breakdown': dict }
    """
    score = 0
    details = []
    breakdown = {}

    # Rule 1: Contact Information (20 points max)
    contact_score = 0
    contact_details = []
    
    if parsed_resume.get('name') and len(parsed_resume['name'].strip()) > 1:
        contact_score += 7
    else:
        contact_details.append("Missing or invalid name")
    
    email = parsed_resume.get('email', '')
    if email and re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        contact_score += 7
    elif email:
        contact_score += 3
        contact_details.append("Email format may not be ATS-friendly")
    else:
        contact_details.append("Missing email address")
    
    phone = parsed_resume.get('phone', '')
    if phone and re.search(r'\d{3}.*\d{3}.*\d{4}', phone):
        contact_score += 6
    elif phone and re.search(r'\d{7,}', phone):
        contact_score += 3
        contact_details.append("Phone format could be clearer")
    else:
        contact_details.append("Missing or invalid phone number")
    
    score += contact_score
    breakdown['Contact Information'] = {'score': contact_score, 'max': 20, 'details': contact_details}

    education_score = 0
    education_details = []
    
    school = parsed_resume.get('school', '')
    college = parsed_resume.get('college', '')
    
    if college and len(college.strip()) > 5:
        education_score += 10
        if re.search(r'\b(bachelor|master|phd|degree|b\.tech|m\.tech|bsc|msc)\b', college.lower()):
            education_score += 3
    elif school and len(school.strip()) > 5:
        education_score += 7
    else:
        education_details.append("Missing or incomplete education information")
    
    # Check for graduation year or GPA
    edu_text = f"{school} {college}".lower()
    if re.search(r'\b(20\d{2}|19\d{2})\b', edu_text):
        education_score += 2
    
    score += education_score
    breakdown['Education'] = {'score': education_score, 'max': 15, 'details': education_details}

    # Rule 3: Projects (20 points max)
    projects_score = 0
    projects_details = []
    
    projects = parsed_resume.get('personal_projects', [])
    generic_keywords = [
        "extra curricular", "personal details", "declaration", "activities", "hobbies"
    ]
    
    # Filter and score projects
    real_projects = []
    for project in projects:
        if not project or len(project.strip()) < 5:
            continue
        project_clean = project.strip().lower()
        
        # Skip generic keywords and date-only entries
        if any(gk in project_clean for gk in generic_keywords):
            continue
        if re.match(r'^[a-z]{3,9}\s+\d{4}(?:\s*-\s*[a-z]{3,9}\s+\d{4})?$', project_clean):
            continue
        if re.match(r'^\d{4}$', project.strip()):
            continue
            
        real_projects.append(project)
    
    project_count = len(real_projects)
    if project_count >= 3:
        projects_score += 15
        # Bonus for detailed projects (longer descriptions likely indicate detail)
        detailed_projects = [p for p in real_projects if len(p) > 50]
        if len(detailed_projects) >= 2:
            projects_score += 5
    elif project_count == 2:
        projects_score += 10
        projects_details.append("Consider adding more projects to strengthen profile")
    elif project_count == 1:
        projects_score += 5
        projects_details.append("Only one project found - add more to improve ATS score")
    else:
        projects_details.append("No valid projects found")
    
    score += projects_score
    breakdown['Projects'] = {'score': projects_score, 'max': 20, 'details': projects_details}

    # Rule 4: Technical Skills (15 points max)
    skills_score = 0
    skills_details = []
    
    tech_stack = parsed_resume.get('tech_stack', [])
    if tech_stack and len(tech_stack) > 0:
        skill_count = len([skill for skill in tech_stack if skill and len(skill.strip()) > 1])
        
        if skill_count >= 8:
            skills_score += 15
        elif skill_count >= 5:
            skills_score += 12
        elif skill_count >= 3:
            skills_score += 8
        elif skill_count >= 1:
            skills_score += 4
            skills_details.append("Limited technical skills listed")
        
        # Bonus for variety in skills
        skills_text = ' '.join(tech_stack).lower()
        categories = 0
        if re.search(r'\b(python|java|javascript|c\+\+|c#|php|ruby|go)\b', skills_text):
            categories += 1
        if re.search(r'\b(react|angular|vue|django|flask|spring|express)\b', skills_text):
            categories += 1
        if re.search(r'\b(mysql|postgresql|mongodb|sqlite|oracle)\b', skills_text):
            categories += 1
        if re.search(r'\b(aws|azure|gcp|docker|kubernetes)\b', skills_text):
            categories += 1
        
        if categories >= 3 and skills_score < 15:
            skills_score = min(15, skills_score + 2)
    else:
        skills_details.append("No technical skills found")
    
    score += skills_score
    breakdown['Technical Skills'] = {'score': skills_score, 'max': 15, 'details': skills_details}

    # Rule 5: Work Experience/Internships (20 points max)
    experience_score = 0
    experience_details = []
    
    internships = parsed_resume.get('internships', [])
    internship_projects = parsed_resume.get('internship_projects', [])
    
    # Filter real internships
    real_internships = []
    for internship in internships:
        if not internship or len(internship.strip()) < 10:
            continue
        internship_clean = internship.strip().lower()
        
        if any(gk in internship_clean for gk in generic_keywords):
            continue
        if re.match(r'^[a-z]{3,9}\s+\d{4}(?:\s*-\s*[a-z]{3,9}\s+\d{4})?$', internship_clean):
            continue
            
        real_internships.append(internship)
    
    total_experience = len(real_internships) + len(internship_projects or [])
    
    if total_experience >= 3:
        experience_score += 18

        detailed_exp = [exp for exp in real_internships if len(exp) > 100]
        if len(detailed_exp) >= 1:
            experience_score += 2
    elif total_experience == 2:
        experience_score += 12
        experience_details.append("Good experience base - consider adding more details")
    elif total_experience == 1:
        experience_score += 6
        experience_details.append("Limited work experience - seek more internships/projects")
    else:
        experience_details.append("No work experience or internships found")
    
    score += experience_score
    breakdown['Work Experience'] = {'score': experience_score, 'max': 20, 'details': experience_details}

    #Achievements/Certifications (10 points max)
    achievements_score = 0
    achievements_details = []
    
    achievements = parsed_resume.get('achievements', [])
    if achievements and len(achievements) > 0:
        valid_achievements = [a for a in achievements if a and len(a.strip()) > 5]
        achievement_count = len(valid_achievements)
        
        if achievement_count >= 3:
            achievements_score += 10
        elif achievement_count == 2:
            achievements_score += 7
        elif achievement_count == 1:
            achievements_score += 4
            achievements_details.append("Consider adding more achievements or certifications")
        
        # Bonus for specific types of achievements
        achievements_text = ' '.join(achievements).lower()
        if re.search(r'\b(certification|certified|award|winner|scholarship|published)\b', achievements_text):
            achievements_score = min(10, achievements_score + 2)
    else:
        achievements_details.append("No achievements or certifications found")
    
    score += achievements_score
    breakdown['Achievements'] = {'score': achievements_score, 'max': 10, 'details': achievements_details}

    # Compile overall details
    for category, data in breakdown.items():
        if data['details']:
            details.extend([f"{category}: {detail}" for detail in data['details']])

    # Determine status based on score ranges
    if score >= 85:
        status = "Excellent"
    elif score >= 70:
        status = "Good"
    elif score >= 50:
        status = "Fair"
    else:
        status = "Poor"

    return {
        "score": score,
        "status": status,
        "details": details if details else ["Resume meets ATS compliance standards"],
        "breakdown": breakdown,
        "recommendations": generate_recommendations(breakdown, score)
    }

def generate_recommendations(breakdown, total_score):
    """Generate specific recommendations based on scoring breakdown"""
    recommendations = []
    
    for category, data in breakdown.items():
        score_percentage = (data['score'] / data['max']) * 100
        
        if score_percentage < 50:
            if category == "Contact Information":
                recommendations.append("Ensure all contact details are complete and properly formatted")
            elif category == "Education":
                recommendations.append("Add complete education details including degree type and graduation year")
            elif category == "Projects":
                recommendations.append("Add 2-3 detailed personal projects with clear descriptions")
            elif category == "Technical Skills":
                recommendations.append("Expand technical skills section with relevant technologies")
            elif category == "Work Experience":
                recommendations.append("Include internships or work experience with detailed descriptions")
            elif category == "Achievements":
                recommendations.append("Add achievements, certifications, or notable accomplishments")
    
    if total_score < 70:
        recommendations.append("Consider using standard section headers (Experience, Education, Skills, etc.)")
        recommendations.append("Use bullet points for better readability and ATS parsing")
    
    return recommendations

@csrf_exempt
def check_ats_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            resume = data.get('resume', {})
            result = check_ats_compliance(resume)
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({
                'score': 0, 
                'status': 'Poor', 
                'details': [f'Error processing resume: {str(e)}'],
                'breakdown': {},
                'recommendations': ['Please check resume format and try again']
            })
    return JsonResponse({
        'score': 0, 
        'status': 'Poor', 
        'details': ['Invalid request method'], 
        'breakdown': {},
        'recommendations': ['Use POST method with resume data']
    })