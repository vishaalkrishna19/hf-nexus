import re

class ProjectDetailsExtractor:
    def __init__(self):
        self.project_keywords = ['project', 'developed', 'built', 'created', 'designed', 'implemented']
    
    def extract_personal_projects(self, text):
        projects = []
        lines = text.split('\n')

        in_project_section = False
        skip_work_experience = False

        company_keywords = [
            'pvt', 'private', 'ltd', 'llp', 'inc', 'corporation', 'company', 'solutions', 'technologies', 'systems',
            'consultancy', 'services', 'labs', 'group', 'enterprises', 'industries', 'institute', 'university', 'college'
        ]

        for i, line in enumerate(lines):
            line = line.strip()
            line_lower = line.lower()

            if any(keyword in line_lower for keyword in ['work experience', 'internship', 'experience']):
                if 'project' not in line_lower:
                    skip_work_experience = True
                    in_project_section = False
                continue
            
            if any(keyword in line_lower for keyword in ['projects', 'personal project', 'key projects', 'major projects']):
                in_project_section = True
                skip_work_experience = False
                continue
            
            if line_lower.startswith(('education', 'skills', 'achievements', 'certifications')):
                in_project_section = False
                skip_work_experience = False
                continue
            
            if in_project_section and not skip_work_experience:
                if line and not self._is_section_header(line):
                    if any(kw in line_lower for kw in company_keywords):
                        continue
                    if self._looks_like_project_title(line):
                        project_title = self._extract_complete_project_title(lines, i)
                        if project_title and len(project_title) > 10:
                            if not any(self._are_similar_projects(project_title, existing) for existing in projects):
                                projects.append(project_title)

        return projects[:5] if projects else []
    
    def _extract_project_title(self, line):
        cleaned = re.sub(r'^[•\-*]\s*', '', line)
        cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
        
        if ':' in cleaned:
            title = cleaned.split(':')[0].strip()
        elif '-' in cleaned and len(cleaned.split('-')) > 1:
            parts = cleaned.split('-')
            title = parts[0].strip()
            if len(title) < 10 and len(parts) > 1:
                title = f"{parts[0].strip()} - {parts[1].strip()}"
        else:
            sentences = cleaned.split('.')
            title = sentences[0].strip()
        
        return title if len(title) > 5 else None
    
    def _is_section_header(self, line):
        line_lower = line.lower().strip()
        headers = [
            'projects', 'achievements', 'awards', 'experience', 'education',
            'skills', 'personal projects', 'key projects', 'major projects'
        ]
        return line_lower in headers or (len(line.split()) <= 3 and any(header in line_lower for header in headers))
    
    def _is_internship_related(self, text):
        return any(keyword in text.lower() for keyword in ['intern', 'internship', 'trainee'])
    
    def _extract_complete_project_title(self, lines, start_idx):
        project_line = lines[start_idx].strip()
        project_line = re.sub(r'^[•\-*]\s*', '', project_line)
        project_line = re.sub(r'^\d+\.\s*', '', project_line)
        
        project_patterns = [
            r'^([A-Z][A-Za-z\s\-&]+?)\s*[-–]\s*([A-Z][^-]*?)(?:\s*\n|$)',
            r'^([A-Z\s\-&]+)$',
            r'^([A-Z][a-zA-Z\s\-&]+?)(?:\s*\n|$)',
        ]
        
        for pattern in project_patterns:
            match = re.search(pattern, project_line)
            if match:
                if len(match.groups()) > 1:
                    title = f"{match.group(1).strip()} - {match.group(2).strip()}"
                else:
                    title = match.group(1).strip()
                title = self._clean_project_title(title)
                if len(title) > 10:
                    return title
        
        title = self._clean_project_title(project_line)
        return title if len(title) > 10 else None
    
    def _clean_project_title(self, title):
        title = re.sub(r'\s+', ' ', title).strip()
        title = re.sub(r'\[\s*link\s*\].*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'https?://[^\s]+', '', title)
        title = re.sub(r'\s*(?:personal project|project|hackathon)\s*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\d{2}/\d{4}\s*-\s*(?:present|\d{2}/\d{4})\s*$', '', title, flags=re.IGNORECASE)
        if title.isupper() and len(title) > 10:
            title = title.title()
        return title.strip()

    def _looks_like_project_title(self, line):
        line_lower = line.lower()
        if any(skip in line_lower for skip in ['developed', 'implemented', 'achieved', 'utilized', 'contributed']):
            return False
        if re.match(r'^\d{2}/\d{4}\s*-\s*(?:present|\d{2}/\d{4})', line):
            return False
        title_indicators = [
            re.match(r'^[A-Z\s\-:&]+$', line) and len(line) > 5,
            ' - ' in line and not line_lower.startswith(('developed', 'implemented')),
            any(keyword in line_lower for keyword in ['app', 'system', 'platform', 'tool', 'website', 'application']) and not line_lower.startswith(('developed', 'built')),
            any(tech in line_lower for tech in ['ai', 'smart', 'bank', 'management']) and not line_lower.startswith(('developed', 'implemented')),
        ]
        return any(title_indicators)
    
    def _are_similar_projects(self, project1, project2):
        words1 = set(project1.lower().split())
        words2 = set(project2.lower().split())
        common_words = {'a', 'an', 'the', 'and', 'or', 'but', 'with', 'using', 'for', 'to', 'of', 'in', 'on', 'app', 'system'}
        words1 -= common_words
        words2 -= common_words
        if len(words1) == 0 or len(words2) == 0:
            return False
        overlap = len(words1.intersection(words2))
        similarity = overlap / min(len(words1), len(words2))
        return similarity > 0.6
