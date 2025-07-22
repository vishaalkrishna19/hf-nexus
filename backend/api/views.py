from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from .resume_parser import ResumeParser
from .utils.excel_exporter import ExcelExporter
from .ranker import gemini_rank_resumes  # Import Gemini logic
from .extractors.details_extractor import DetailsExtractor
from .utils.github_details_viewer import get_github_details
from .shortlist_ranker import shortlist_candidates_with_gemini
from .utils.drive_downloader import DriveDownloader
import json
import asyncio
import tempfile
import os
import openpyxl

@api_view(['GET'])
def hello_world(request):
    return Response({'message': 'Hii hello from django!'})

@csrf_exempt
@api_view(['POST'])
def parse_resume(request):
    """Parse uploaded resume and extract information"""
    try:
        if 'resume_file' not in request.FILES:
            return Response({
                'success': False,
                'error': 'No resume file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        resume_file = request.FILES['resume_file']
        
        # Validate file type
        if not resume_file.name.lower().endswith(('.pdf', '.docx', '.doc')):
            return Response({
                'success': False,
                'error': 'Invalid file format. Please upload PDF or DOCX file.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse the resume
        parser = ResumeParser()
        parsed_data = parser.parse_resume(resume_file)
        
        # Log the parsed data to console
        print("=== RESUME PARSING RESULTS ===")
        print(json.dumps(parsed_data, indent=2, default=str))
        print("==============================")
        
        return Response({
            'success': True,
            'parsed_data': parsed_data
        })
        
    except Exception as e:
        print(f"Error parsing resume: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
def shortlist_candidates(request):
    """Shortlist candidates based on criteria using dedicated Gemini analysis"""
    try:
        data = json.loads(request.body)
        candidates_data = data.get('candidates_data', [])
        criteria = data.get('criteria', {})
        num_candidates = data.get('num_candidates', 10)

        print(f"DEBUG: Received {len(candidates_data)} candidates for shortlisting")
        print(f"DEBUG: Criteria: {criteria}")
        print(f"DEBUG: Num candidates requested: {num_candidates}")

        if candidates_data:
            from .extractors.details_extractor import DetailsExtractor
            from .extractors.name_extractor import NameExtractor
            from .extractors.education_extractor import EducationExtractor
            from .extractors.internship_extractor import InternshipExtractor
            from .extractors.project_details import ProjectDetailsExtractor
            from .extractors.achievements_extractor import AchievementsExtractor
            from .extractors.linkedin_extractor import LinkedInExtractor
            from .extractors.language_extractor import LanguageExtractor
            from .extractors.github_crawler import GithubCrawler

            enriched_candidates = []
            for candidate in candidates_data:
                try:
                    # Use the available fields or empty string if not present
                    text = " ".join(str(candidate.get(field, "")) for field in candidate.keys())
                    
                    # Extract fields using backend extractors with fallback to original data
                    name = candidate.get('name') or candidate.get('Name') or NameExtractor().extract_name(text) or 'Unknown'
                    email = candidate.get('email') or candidate.get('Email') or DetailsExtractor().extract_email(text) or 'Not provided'
                    phone = candidate.get('phone') or candidate.get('Phone') or DetailsExtractor().extract_phone(text) or 'Not provided'
                    github = candidate.get('github') or candidate.get('GitHub') or DetailsExtractor().extract_github(text) or 'Not provided'
                    linkedin = candidate.get('linkedin') or candidate.get('LinkedIn') or LinkedInExtractor().extract_linkedin_url(text) or 'Not provided'
                    school = candidate.get('school') or candidate.get('School') or EducationExtractor().extract_school(text) or 'Not provided'
                    college = candidate.get('college') or candidate.get('College') or EducationExtractor().extract_college(text) or 'Not provided'
                    
                    # Handle numeric fields with proper conversion
                    tenth_marks = candidate.get('tenth_marks') or candidate.get('10th Marks (%)') or candidate.get('10th (%)') or candidate.get('10th') or 'Not provided'
                    twelfth_marks = candidate.get('twelfth_marks') or candidate.get('12th Marks (%)') or candidate.get('12th (%)') or candidate.get('12th') or 'Not provided'
                    cgpa = candidate.get('cgpa') or candidate.get('CGPA') or EducationExtractor().extract_cgpa(text) or 'Not provided'
                    
                    # Handle array fields
                    internships = candidate.get('internships') or candidate.get('Internships') or InternshipExtractor().extract_internships(text) or []
                    internship_projects = candidate.get('internship_projects') or candidate.get('Internship Projects') or InternshipExtractor().extract_internship_projects(text) or []
                    personal_projects = candidate.get('personal_projects') or candidate.get('Personal Projects') or candidate.get('Projects') or ProjectDetailsExtractor().extract_personal_projects(text) or []
                    achievements = candidate.get('achievements') or candidate.get('Achievements') or AchievementsExtractor().extract_achievements(text) or []
                    
                    # Tech stack handling
                    tech_stack = candidate.get('tech_stack') or candidate.get('Tech Stack') or candidate.get('TechStack') or []
                    if isinstance(tech_stack, str):
                        tech_stack = [t.strip() for t in tech_stack.split(',') if t.strip()]
                    elif not isinstance(tech_stack, list):
                        tech_stack = []
                    
                    # Languages handling
                    languages = candidate.get('languages') or candidate.get('Languages') or LanguageExtractor().extract_languages(text) or []

                    # Handle projects - combine internship and personal projects
                    projects = []
                    if internship_projects:
                        if isinstance(internship_projects, list):
                            projects.extend(internship_projects)
                        else:
                            projects.append(str(internship_projects))
                    
                    if personal_projects:
                        if isinstance(personal_projects, list):
                            projects.extend(personal_projects)
                        else:
                            projects.append(str(personal_projects))
                    
                    # Fix: Add missing github_summary variable
                    github_summary = "No GitHub profile"
                    
                    # GitHub profile analysis
                    github_profile_analysis = "No GitHub profile analysis available"
                    if github and isinstance(github, str) and "github.com" in github:
                        try:
                            crawler = GithubCrawler(github)
                            github_data = crawler.get_profile_data()
                            if github_data:
                                # Create detailed analysis
                                analysis_parts = []
                                if github_data.get("public_repos"):
                                    analysis_parts.append(f"Has {github_data['public_repos']} public repositories")
                                if github_data.get("followers"):
                                    analysis_parts.append(f"{github_data['followers']} followers")
                                if github_data.get("total_commits"):
                                    analysis_parts.append(f"~{github_data['total_commits']} total commits")
                                if github_data.get("most_used_languages"):
                                    top_langs = [f"{l['language']} ({l['percentage']}%)" for l in github_data["most_used_languages"][:3]]
                                    analysis_parts.append(f"Top languages: {', '.join(top_langs)}")
                                if github_data.get("top_repos"):
                                    top_repo = github_data["top_repos"][0]
                                    analysis_parts.append(f"Top repository: {top_repo['name']} (⭐{top_repo['stargazers_count']})")
                                
                                github_profile_analysis = " | ".join(analysis_parts)
                                github_summary = f"GitHub: {github_data.get('public_repos', 0)} repos, {github_data.get('followers', 0)} followers"
                            else:
                                github_profile_analysis = "GitHub profile found but no data available"
                        except Exception as e:
                            github_profile_analysis = f"Error analyzing GitHub profile: {str(e)}"
                            print(f"DEBUG: GitHub analysis error for {github}: {e}")

                    # Create enriched candidate object
                    enriched_candidate = {
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "github": github,
                        "linkedin": linkedin,
                        "school": school,
                        "college": college,
                        "tenth_marks": tenth_marks,
                        "twelfth_marks": twelfth_marks,
                        "cgpa": cgpa,
                        "internships": internships,
                        "internship_projects": internship_projects,
                        "personal_projects": personal_projects,
                        "projects": projects,  # Combined projects
                        "achievements": achievements,
                        "tech_stack": tech_stack,
                        "languages": languages,
                        "github_summary": github_summary,
                        "github_profile_analysis": github_profile_analysis,
                        "filename": candidate.get('filename', candidate.get('Name', name) + '.pdf'),
                        # Preserve any original fields that might be useful
                        **{k: v for k, v in candidate.items() if k not in [
                            'name', 'Name', 'email', 'Email', 'phone', 'Phone', 
                            'github', 'GitHub', 'linkedin', 'LinkedIn', 'school', 'School',
                            'college', 'College', 'tenth_marks', '10th Marks (%)', '10th (%)', '10th',
                            'twelfth_marks', '12th Marks (%)', '12th (%)', '12th', 'cgpa', 'CGPA',
                            'internships', 'Internships', 'internship_projects', 'Internship Projects',
                            'personal_projects', 'Personal Projects', 'Projects', 'achievements', 'Achievements',
                            'tech_stack', 'Tech Stack', 'TechStack', 'languages', 'Languages'
                        ]}
                    }
                    
                    enriched_candidates.append(enriched_candidate)
                    
                except Exception as e:
                    print(f"DEBUG: Error processing candidate {candidate.get('name', 'unknown')}: {e}")
                    # Still add the candidate with basic fields
                    enriched_candidates.append({
                        "name": candidate.get('name', candidate.get('Name', 'Unknown')),
                        "email": candidate.get('email', candidate.get('Email', 'Not provided')),
                        "phone": candidate.get('phone', candidate.get('Phone', 'Not provided')),
                        "github": candidate.get('github', candidate.get('GitHub', 'Not provided')),
                        "linkedin": candidate.get('linkedin', candidate.get('LinkedIn', 'Not provided')),
                        "school": candidate.get('school', candidate.get('School', 'Not provided')),
                        "college": candidate.get('college', candidate.get('College', 'Not provided')),
                        "tenth_marks": candidate.get('tenth_marks', candidate.get('10th Marks (%)', candidate.get('10th (%)', 'Not provided'))),
                        "twelfth_marks": candidate.get('twelfth_marks', candidate.get('12th Marks (%)', candidate.get('12th (%)', 'Not provided'))),
                        "cgpa": candidate.get('cgpa', candidate.get('CGPA', 'Not provided')),
                        "internships": candidate.get('internships', candidate.get('Internships', [])),
                        "internship_projects": candidate.get('internship_projects', candidate.get('Internship Projects', [])),
                        "personal_projects": candidate.get('personal_projects', candidate.get('Personal Projects', candidate.get('Projects', []))),
                        "achievements": candidate.get('achievements', candidate.get('Achievements', [])),
                        "tech_stack": candidate.get('tech_stack', candidate.get('Tech Stack', [])),
                        "languages": candidate.get('languages', candidate.get('Languages', [])),
                        "github_summary": "No GitHub profile",
                        "filename": candidate.get('filename', candidate.get('Name', 'Unknown') + '.pdf'),
                        "error": str(e)
                    })

            print(f"DEBUG: Enriched {len(enriched_candidates)} candidates")
            if enriched_candidates:
                print(f"DEBUG: Sample enriched candidate keys: {list(enriched_candidates[0].keys())}")
                print(f"DEBUG: Sample enriched candidate: {enriched_candidates[0]}")

            # Use dedicated shortlist ranker
            import asyncio
            shortlisted = asyncio.run(shortlist_candidates_with_gemini(enriched_candidates, criteria))
            
            print(f"DEBUG: Shortlisted {len(shortlisted)} candidates")
            if shortlisted:
                print(f"DEBUG: Sample shortlisted candidate keys: {list(shortlisted[0].keys())}")
                print(f"DEBUG: Sample shortlisted candidate: {shortlisted[0]}")
            
            # Add rank field and ensure all necessary fields are present
            for idx, candidate in enumerate(shortlisted):
                candidate['Rank'] = idx + 1
                
                # Ensure all expected fields are present with fallbacks
                required_fields = {
                    'name': 'Unknown',
                    'email': 'Not provided',
                    'phone': 'Not provided',
                    'github': 'Not provided',
                    'linkedin': 'Not provided',
                    'school': 'Not provided',
                    'college': 'Not provided',
                    'tenth_marks': 'Not provided',
                    'twelfth_marks': 'Not provided',
                    'cgpa': 'Not provided',
                    'internships': [],
                    'internship_projects': [],
                    'personal_projects': [],
                    'achievements': [],
                    'tech_stack': [],
                    'languages': [],
                    'github_summary': 'No GitHub profile',
                    'filename': 'Unknown.pdf',
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
            
            # Limit to requested number
            final_shortlisted = shortlisted[:num_candidates]
            
            print(f"DEBUG: Final shortlisted count: {len(final_shortlisted)}")
            if final_shortlisted:
                print(f"DEBUG: Final candidate keys: {list(final_shortlisted[0].keys())}")
        else:
            print("DEBUG: No candidates data received")
            final_shortlisted = []

        return Response({
            'success': True,
            'shortlisted_candidates': final_shortlisted,
            'total_processed': len(candidates_data),
            'total_shortlisted': len(final_shortlisted)
        })

    except Exception as e:
        print(f"DEBUG: Error in shortlist_candidates: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
def export_to_excel(request):
    """Export parsed resume data to Excel file"""
    try:
        data = json.loads(request.body)
        
        # Check if it's multiple resumes or single resume
        if 'multiple_resumes' in data:
            multiple_resumes_data = data.get('multiple_resumes', [])
            filename = data.get('filename', 'multiple_resumes')
            
            if not multiple_resumes_data:
                return Response({
                    'success': False,
                    'error': 'No resume data provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create Excel file for multiple resumes
            exporter = ExcelExporter()
            workbook = exporter.create_multiple_resumes_sheet(multiple_resumes_data)
            excel_data = exporter.save_to_bytes()
            
            # Create HTTP response with Excel file
            response = HttpResponse(
                excel_data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="resume_data_extracted.xlsx"'
            
            return response
        else:
            # Handle single resume (existing functionality)
            parsed_data = data.get('parsed_data', {})
            filename = data.get('filename', 'resume')
            
            if not parsed_data:
                return Response({
                    'success': False,
                    'error': 'No parsed data provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create Excel file
            exporter = ExcelExporter()
            workbook = exporter.create_resume_sheet(parsed_data, filename)
            excel_data = exporter.save_to_bytes()
            
            # Create HTTP response with Excel file
            response = HttpResponse(
                excel_data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}_analysis.xlsx"'
            
            return response
        
    except Exception as e:
        print(f"Error exporting to Excel: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
def rank_resumes(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            resumes = data.get('resumes', [])
            # Run the async Gemini logic in Django sync context
            ranked = asyncio.run(gemini_rank_resumes(resumes))
            return JsonResponse({"ranked_resumes": ranked}, safe=False)
        except Exception as e:
            # Log the error for debugging
            import traceback
            print("Rank resumes error:", traceback.format_exc())
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid method"}, status=405)

@csrf_exempt
@api_view(['GET'])
def github_details(request):
    """
    Extract GitHub details from a given GitHub profile URL.
    Usage: /api/github-details?url=https://github.com/username
    """
    url = request.GET.get('url')
    if not url:
        return Response({'success': False, 'error': 'No GitHub URL provided.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        print(f"Fetching GitHub details for URL: {url}")
        details = get_github_details(url)
        
        if not details:
            return Response({'success': False, 'error': 'Could not extract GitHub details.'}, status=status.HTTP_404_NOT_FOUND)
        
        print(f"Successfully fetched GitHub details: {details}")
        return Response(details)
        
    except Exception as e:
        print(f"Error in github_details view: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
def process_excel_drive_links(request):
    """Process Excel file containing Google Drive links to PDF resumes"""
    try:
        if 'excel_file' not in request.FILES:
            return Response({
                'success': False,
                'error': 'No Excel file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        excel_file = request.FILES['excel_file']
        
        # Validate file type
        if not excel_file.name.lower().endswith(('.xlsx', '.xls')):
            return Response({
                'success': False,
                'error': 'Invalid file format. Please upload Excel file (.xlsx or .xls).'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print("=== PROCESSING EXCEL WITH GOOGLE DRIVE LINKS ===")
        
        # Parse Excel file to extract Google Drive links
        drive_links = []
        try:
            # Read Excel file
            workbook = openpyxl.load_workbook(excel_file, data_only=True)
            worksheet = workbook.active
            
            for row_idx, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                candidate_name = None
                drive_link = None
                
                # Look for name and Google Drive link in the row
                for cell_idx, cell_value in enumerate(row):
                    if cell_value and isinstance(cell_value, str):
                        # Check if this looks like a name (first non-link string)
                        if not candidate_name and not ('drive.google.com' in cell_value or 'docs.google.com' in cell_value):
                            candidate_name = cell_value.strip()
                        
                        # Check if this is a Google Drive link
                        if 'drive.google.com' in cell_value or 'docs.google.com' in cell_value:
                            drive_link = cell_value.strip()
                
                if drive_link:
                    drive_links.append({
                        'name': candidate_name or f'Candidate_{row_idx}',
                        'url': drive_link,
                        'row': row_idx
                    })
            
            print(f"Found {len(drive_links)} Google Drive links in Excel")
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error reading Excel file: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not drive_links:
            return Response({
                'success': False,
                'error': 'No Google Drive links found in Excel file'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Test accessibility of Google Drive links first
        print("=== TESTING GOOGLE DRIVE LINK ACCESSIBILITY ===")
        drive_downloader = DriveDownloader()
        
        accessible_links = []
        inaccessible_links = []
        
        for link_info in drive_links:
            print(f"Testing accessibility for {link_info['name']}: {link_info['url']}")
            is_accessible, status_msg = drive_downloader.test_download(link_info['url'])
            
            if is_accessible:
                accessible_links.append(link_info)
                print(f"✅ {link_info['name']}: {status_msg}")
            else:
                inaccessible_links.append({**link_info, 'error': status_msg})
                print(f"❌ {link_info['name']}: {status_msg}")
        
        print(f"Accessible: {len(accessible_links)}, Inaccessible: {len(inaccessible_links)}")
        
        if not accessible_links:
            error_details = []
            for link in inaccessible_links:
                error_details.append(f"• {link['name']}: {link['error']}")
            
            return Response({
                'success': False,
                'error': 'No accessible Google Drive links found. Common issues:\n' + 
                        '\n'.join(error_details) + 
                        '\n\nPlease ensure:\n' +
                        '• Files are set to "Anyone with the link can view"\n' +
                        '• Files are PDF format\n' +
                        '• Links are not expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Download PDFs from accessible Google Drive links and parse them
        parser = ResumeParser()
        parsed_resumes = []
        
        # Add inaccessible files to results with error info
        for link_info in inaccessible_links:
            parsed_resumes.append({
                'name': link_info['name'],
                'filename': f"{link_info['name']}.pdf",
                'error': f"Google Drive access error: {link_info['error']}",
                'drive_url': link_info['url']
            })
        
        # Process accessible files
        for idx, link_info in enumerate(accessible_links):
            try:
                print(f"Downloading and parsing {idx + 1}/{len(accessible_links)}: {link_info['name']}")
                
                # Get file info first
                # file_info = drive_downloader.get_file_info(link_info['url'])
                # if file_info:
                #     print(f"File info: {file_info}")
                
                # Download PDF from Google Drive
                pdf_content = drive_downloader.download_pdf(link_info['url'])
                
                if not pdf_content:
                    print(f"Failed to download PDF for {link_info['name']}")
                    parsed_resumes.append({
                        'name': link_info['name'],
                        'filename': f"{link_info['name']}.pdf",
                        'error': 'Failed to download PDF from Google Drive - file may not be publicly accessible',
                        'drive_url': link_info['url']
                    })
                    continue
                
                print(f"Successfully downloaded {len(pdf_content)} bytes for {link_info['name']}")
                
                # Create temporary file for parsing
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(pdf_content)
                    temp_file_path = temp_file.name
                
                try:
                    # Parse the downloaded PDF
                    class TempFile:
                        def __init__(self, path, name):
                            self.path = path
                            self.name = name
                        
                        def read(self):
                            with open(self.path, 'rb') as f:
                                return f.read()
                        
                        def seek(self, pos):
                            pass  # Not needed for this use case
                    
                    temp_file_obj = TempFile(temp_file_path, f"{link_info['name']}.pdf")
                    parsed_data = parser.parse_resume(temp_file_obj)
                    
                    # Add metadata
                    parsed_data['filename'] = f"{link_info['name']}.pdf"
                    parsed_data['drive_url'] = link_info['url']
                    parsed_data['excel_row'] = link_info['row']
                    
                    parsed_resumes.append(parsed_data)
                    
                    print(f"✅ Successfully parsed resume for {link_info['name']}")
                
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                
            except Exception as e:
                print(f"Error processing {link_info['name']}: {str(e)}")
                parsed_resumes.append({
                    'name': link_info['name'],
                    'filename': f"{link_info['name']}.pdf",
                    'error': f"Parsing error: {str(e)}",
                    'drive_url': link_info['url']
                })
        
        successful_parses = len([r for r in parsed_resumes if 'error' not in r])
        print(f"=== FINAL RESULTS ===")
        print(f"Total links: {len(drive_links)}")
        print(f"Accessible links: {len(accessible_links)}")
        print(f"Successful parses: {successful_parses}")
        print(f"Failed parses: {len(parsed_resumes) - successful_parses}")
        
        return Response({
            'success': True,
            'parsed_resumes': parsed_resumes,
            'total_links': len(drive_links),
            'accessible_links': len(accessible_links),
            'successful_parses': successful_parses,
            'accessibility_report': {
                'accessible': len(accessible_links),
                'inaccessible': len(inaccessible_links),
                'inaccessible_details': [
                    {'name': link['name'], 'error': link['error']} 
                    for link in inaccessible_links
                ]
            }
        })
        
    except Exception as e:
        print(f"Error in process_excel_drive_links: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

