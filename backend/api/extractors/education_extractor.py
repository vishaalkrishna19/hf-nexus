import re

class EducationExtractor:
    def __init__(self):
        self.school_keywords = [
            'school', 'high school', 'higher secondary', 'senior secondary', 
            'secondary school', 'matriculation', 'hsc', 'sslc', 'hssc',
            'higher sec', 'sr sec', 'sr. sec', 'senior sec', 'vidyalaya',
            'vidyamandir', 'academy', 'convent', 'public school', 'govt school',
            'government school', 'kendriya vidyalaya', 'navodaya', 'cbse', 'icse'
        ]
        self.college_keywords = ['college', 'university', 'institute', 'engineering', 'technology']
    
    def extract_school(self, text):
        """Extract school name from resume text"""
        lines = text.split('\n')
        
        # Look for education section first
        education_sections = self._identify_education_sections(lines)
        
        # Look within education sections for school patterns
        for start_idx, end_idx in education_sections:
            for i in range(start_idx, min(end_idx, len(lines))):
                line = lines[i].strip()
                if not line:
                    continue
                
                # Check if this line has SSLC/10th indicators
                if any(keyword in line.lower() for keyword in ['sslc', '10th', 'tenth', 'matriculation']):
                    # Look for school name in previous lines within the section
                    for j in range(max(start_idx, i-3), i):
                        prev_line = lines[j].strip()
                        if prev_line and self._looks_like_school_name(prev_line):
                            return prev_line
                    
                    # Also check if current line contains school name
                    school_name = self._extract_school_name_from_line(line)
                    if school_name:
                        return school_name
        
 
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Check if this line contains school indicators (vidyalaya, school, etc.)
            if any(keyword in line_clean.lower() for keyword in ['vidyalaya', 'school', 'academy', 'convent']):
                # Check if next line has SSLC/HSLC patterns
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if any(pattern in next_line.upper() for pattern in ['SSLC', 'HSLC', '10TH']):
                        return line_clean
    
        # Fallback: Look for school patterns with improved matching
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_lower = line_clean.lower()
            
            # Skip empty lines and lines with just years/percentages
            if not line_clean or re.match(r'^\d{4}[-\s]*\d{4}?$', line_clean) or re.match(r'^\d+(\.\d+)?%?$', line_clean):
                continue
            
            # Look for school indicators
            if any(keyword in line_lower for keyword in self.school_keywords):
                school_name = self._extract_school_name_from_line(line_clean)
                if school_name:
                    return school_name
                
                # Check surrounding lines for school name
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    if j != i:  # Don't check the same line again
                        candidate_line = lines[j].strip()
                        if candidate_line and not self._is_grade_or_year_line(candidate_line):
                            school_name = self._extract_school_name_from_line(candidate_line)
                            if school_name and any(kw in school_name.lower() for kw in self.school_keywords):
                                return school_name
    
        # Look for specific school name patterns
        school_patterns = [
            r'([A-Z][A-Za-z\s&.]+(?:SCHOOL|VIDYALAYA|ACADEMY|CONVENT|HSS|HSSS|SR\.?\s*SEC\.?)[A-Za-z\s]*)',
            r'([A-Z][A-Za-z\s&.]*(?:HIGHER|SENIOR)\s+SECONDARY[A-Za-z\s]*)',
            r'([A-Z][A-Za-z\s&.]*HSC[A-Za-z\s]*)',
            r'([A-Z][A-Za-z\s&.]*SSLC[A-ZaEzA-z\s]*)',
            r'(KENDRIYA\s+VIDYALAYA[A-Za-z\s]*)',
            r'([A-Z][A-Za-z\s&.]*PUBLIC\s+SCHOOL[A-Za-z\s]*)',
            r'([A-Z][A-Za-z\s&.]*GOVERNMENT\s+SCHOOL[A-Za-z\s]*)',
        ]
        
        for pattern in school_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                school_name = matches[0].strip()
                if len(school_name) > 5:  # Avoid too short matches
                    return school_name
        
        return None

    def _looks_like_school_name(self, line):
        """Check if a line looks like a school name"""
        line_lower = line.lower()
        
        # Skip lines that are clearly not school names
        if self._is_grade_or_year_line(line) or self._is_degree_or_achievement_line(line):
            return False
        
        school_indicators = ['vidyalaya', 'school', 'academy', 'convent']
        if any(indicator in line_lower for indicator in school_indicators):
            return True
        
        if line and line[0].isupper() and len(line) > 5:
          
            tech_words = ['html', 'css', 'javascript', 'python', 'java', 'react', 'angular']
            if not any(tech in line_lower for tech in tech_words):
                return True
        
        return False

    def extract_college(self, text):
        """Extract college name from resume text"""
        lines = text.split('\n')
        
        education_sections = self._identify_education_sections(lines)
        
        for start_idx, end_idx in education_sections:
            for i in range(start_idx, end_idx):
                if i >= len(lines):
                    break
                    
                line = lines[i].strip()
                
                if not line:
                    continue
                
                # IMPROVED: First check if this line itself is a college name
                if self._looks_like_college_name(line):
                    college_name = self._clean_college_name(line)
                    if college_name and not self._is_degree_subjects_line(college_name):
                        return college_name
                
                # Look for degree indicators and find college name in surrounding lines
                if any(keyword in line.lower() for keyword in ['bachelor', 'b.tech', 'be', 'engineering', 'computer science']):
                    # Look for college name in previous lines within the section
                    for j in range(max(start_idx, i-3), i):
                        prev_line = lines[j].strip()
                        if prev_line and self._looks_like_college_name(prev_line):
                            college_name = self._clean_college_name(prev_line)
                            if college_name and not self._is_degree_subjects_line(college_name):
                                return college_name
        
        # Direct pattern matching for format without section headers
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Check if this line contains college indicators
            if any(keyword in line_clean.lower() for keyword in ['engineering college', 'college', 'university', 'institute']):
                # Verify it's actually a college name, not a degree subject line
                if self._looks_like_college_name(line_clean) and not self._is_degree_subjects_line(line_clean):
                    return self._clean_college_name(line_clean)
                
                # Check if next line has degree patterns
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if any(pattern in next_line.lower() for pattern in ['bachelor', 'b.tech', 'engineering', 'computer science']):
                        return line_clean
        
        return None
    
    def _is_degree_subjects_line(self, line):
        """Check if line contains degree subjects rather than college name"""
        line_lower = line.lower()
        
        # Common degree subjects that shouldn't be considered college names
        subject_keywords = [
            'software engineering', 'business information systems', 'data structures',
            'algorithms', 'database', 'networking', 'programming', 'mathematics',
            'physics', 'chemistry', 'electronics', 'mechanical', 'civil',
            'electrical', 'computer networks', 'operating systems', 'web development',
            'artificial intelligence', 'machine learning', 'data science',
            'information technology', 'computer applications', 'digital marketing',
            'structures', 'systems', 'management', 'analysis', 'design'
        ]
        
        # Check if line contains primarily subject names
        subject_count = sum(1 for keyword in subject_keywords if keyword in line_lower)
        
        # If line contains multiple subject keywords and no clear college indicators, it's likely subjects
        if subject_count >= 2:
            return True
        
        # Check for comma-separated list pattern (like "Structures , Software Engineering , Business Information Systems.")
        if ',' in line and subject_count >= 1:
            # Split by comma and check if most parts are subjects
            parts = [part.strip() for part in line.split(',')]
            if len(parts) >= 2:
                subject_parts = sum(1 for part in parts if any(keyword in part.lower() for keyword in subject_keywords))
                if subject_parts >= len(parts) * 0.7:  # 70% or more are subjects
                    return True
        
        return False

    def _extract_school_name_from_line(self, line):
        """Extract school name from a single line"""
        # Remove common prefixes and suffixes that aren't part of the school name
        prefixes_to_remove = [
            r'^(education|academic|qualification|school|college):\s*',
            r'^\d{4}[-\s]*\d{4}?\s*[-:]\s*',
            r'^(hsc|sslc|higher\s+secondary|senior\s+secondary)[-:\s]*',
        ]
        
        cleaned_line = line
        for prefix in prefixes_to_remove:
            cleaned_line = re.sub(prefix, '', cleaned_line, flags=re.IGNORECASE).strip()
        
        # If line is too short after cleaning, it's probably not a school name
        if len(cleaned_line) < 5:
            return None
        
        # Check if it contains school-related keywords
        if any(keyword in cleaned_line.lower() for keyword in self.school_keywords):
            return cleaned_line
        
        return None

    def _clean_college_name(self, line):
        """Clean and extract college name from a line"""
        # Remove common prefixes that might appear with college names
        prefixes_to_remove = [
            r'^\d{4}\s*[-–]\s*\d{4}?\s*',  # Remove year ranges at start
            r'^(present|current)\s*',       # Remove "Present" or "Current"
            r'^\w{3}\s+\d{4}\s*[-–]\s*',   # Remove date patterns like "Nov 2022 -"
        ]
        
        cleaned = line
        for prefix in prefixes_to_remove:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE).strip()
        
        # Remove degree information that might be on the same line
        degree_suffixes = [
            r'\s+(b\.?tech|b\.?e|bachelor|master|m\.?tech|m\.?e|diploma).*$',
            r'\s+(artificial intelligence|machine learning|computer science|information technology).*$',
        ]
        
        for suffix in degree_suffixes:
            cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE).strip()
        
        # If the cleaned name is too short, it's probably not a valid college name
        if len(cleaned) < 5:
            return None
        
        return cleaned

    def _looks_like_college_name(self, line):
        line_lower = line.lower()
    
        # Skip lines that are clearly not college names
        if self._is_grade_or_year_line(line) or self._is_degree_or_achievement_line(line):
            return False
        
        # IMPROVED: Skip degree subjects lines
        if self._is_degree_subjects_line(line):
            return False
        
        # Skip lines that are too short
        if len(line.strip()) < 5:
            return False
        
        # Check for college-related keywords
        college_indicators = [
            'college', 'university', 'institute', 'engineering', 'technology',
            'polytechnic', 'academy', 'campus', 'educational', 'technical'
        ]
        
        if any(indicator in line_lower for indicator in college_indicators):
            return True
        
        # Check if line starts with capital letter and contains multiple words (typical college name format)
        if line and line[0].isupper() and len(line.split()) >= 2:
            # Exclude technical skills or programming languages
            tech_words = [
                'html', 'css', 'javascript', 'python', 'java', 'react', 'angular',
                'node', 'mongodb', 'mysql', 'sql', 'php', 'programming', 'coding'
            ]
            if not any(tech in line_lower for tech in tech_words):
                # Check if it's not a degree name
                degree_words = ['bachelor', 'master', 'diploma', 'certificate', 'course']
                if not any(degree in line_lower for degree in degree_words):
                    return True
        
        return False
        

    def extract_tenth_marks(self, text):
        """Extract 10th marks from resume text"""
        # Clean up spaces in text for better pattern matching
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "SSLC - 88.4" format (your specific data format)
            r'SSLC\s*[-–]\s*(\d{1,2}(?:\.\d+)?)',
            
            # Patterns with "Percentage :" format (like in Vishaal's resume)
            r'(?:10th|SSLC|Secondary|Class\s*10|X)\s*[-–]?\s*\d{4}.*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            
            # Direct percentage patterns (like "SSLC 2020 - 98%")
            r'(?:10th|SSLC|Secondary|Class\s*10|X)(?:\s*[-–]\s*\d{4})?\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%',
            
            # NEW: Handle cases where SSLC is on one line and percentage on next lines
            r'SSLC.*?(?:\n.*?)*?(\d{2})\s*%(?=.*HSC|.*12th|.*Higher|$)',
            
            # Patterns with spaces (like "9 7 .4")
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d\s*\d\s*\.\s*\d+)\s*(?:%|$)',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d\s*\d)\s*(?:%|$)',
            
            # Standard patterns - require at least 2 digits
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(?:percentage|marks?|score).*?(\d{2}(?:\.\d+)?)\s*%?',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d{2}(?:\.\d+)?)\s*(?:%|percentage|marks?|score)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                mark_str = matches[0]
               
                mark_str = re.sub(r'\s+', '', mark_str)
                try:
                    mark = float(mark_str)
                    if 30 <= mark <= 100:  
                        print(f"Found 10th marks: {mark}% using pattern: {pattern}")
                        return mark
                except ValueError:
                    continue

        sslc_hsc_pattern = r'SSLC.*?(\d{2})%.*?HSC.*?(\d{2})%'
        match = re.search(sslc_hsc_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sslc_marks = float(match.group(1))
            if 30 <= sslc_marks <= 100:
                print(f"Found 10th marks from SSLC/HSC table: {sslc_marks}%")
                return sslc_marks
        
        return None

    def extract_twelfth_marks(self, text):
        """Extract 12th marks from resume text"""
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "HSLC - 92.8" format (your specific data format)
            r'HSLC\s*[-–]\s*(\d{1,2}(?:\.\d+)?)',

            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two)(?:\s*[-–]\s*\d{4})?\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%?(?:\s|$)',

            r'HSC.*?(?:\n.*?)*?(\d{2})\s*%(?=.*SSLC|.*10th|.*Secondary|$)',
            
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?(?:percentage|marks?|score).*?(\d{2}(?:\.\d+)?)\s*%?',
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?(\d{2}(?:\.\d+)?)\s*(?:%|percentage|marks?|score)',
            
            r'HSC\s*(?:[-–]\s*)?\d{4}\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%?',
            r'Higher\s*Secondary.*?(\d{2}(?:\.\d+)?)\s*%',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                mark_str = matches[0]
                # Handle spaced numbers
                mark_str = re.sub(r'\s+', '', mark_str)
                try:
                    mark = float(mark_str)
                    if 30 <= mark <= 100:  # More realistic range for 12th marks
                        print(f"Found 12th marks: {mark}% using pattern: {pattern}")
                        return mark
                except ValueError:
                    continue
        
        # NEW: Fallback pattern for educational table format
        # Look for HSC followed by SSLC and extract the first percentage
        hsc_sslc_pattern = r'HSC.*?(\d{2})%.*?SSLC.*?(\d{2})%'
        match = re.search(hsc_sslc_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            hsc_marks = float(match.group(1))
            if 30 <= hsc_marks <= 100:
                print(f"Found 12th marks from HSC/SSLC table: {hsc_marks}%")
                return hsc_marks
        
        return None
    
    def extract_cgpa(self, text):
        """Extract CGPA from resume text"""
        # Clean up spaces in text for better pattern matching
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "Bachelor of Engineering in Computer Science - 8.46" format
            r'Bachelor.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'Bachelor.*?Engineering.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'B\.?E.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'B\.?Tech.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            
            # NEW: Pattern for standalone CGPA values near college/education context
            r'(?:B\.?E|B\.?Tech|Bachelor|Engineering|College).*?(\d+\.\d{2})\s*(?:CGPA|GPA|till|semester|out\s*of)',
            r'(?:Rajalakshmi|Engineering|College).*?(\d+\.\d{2})\s*(?:CGPA|GPA|till|semester)',
            r'(\d+\.\d{2})\s*CGPA\s*\(till',
            r'(\d+\.\d{2})\s*(?:CGPA|GPA)\s*\(',
            
            # Patterns with spaces (like "CGP A : 8.38")
            r'CGP\s*A\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'C\s*G\s*P\s*A\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Standard CGPA patterns
            r'CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'GPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Cumulative\s*GPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Cumulative\s*Grade\s*Point\s*Average\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Grade\s*Point\s*Average\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Current\s*CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Overall\s*CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Academic\s*Grade\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Patterns with context
            r'(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A).*?(\d+(?:\.\d+)?)\s*(?:/\s*10|\s*out\s*of\s*10)?',
            
            # Reverse patterns
            r'(\d+(?:\.\d+)?)\s*/\s*10\s*(?:CGPA|GPA|Grade)',
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*10\s*(?:CGPA|GPA|Grade)',
            
            # College context patterns (like "CGPA - 8.41")
            r'(?:B\.?Tech|B\.?E|Bachelor|Engineering|College).*?(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A)\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Dash patterns (like "CGPA - 8.41")
            r'(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A)\s*[-–]\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                cgpa_str = matches[0]
                # Handle spaced numbers
                cgpa_str = re.sub(r'\s+', '', cgpa_str)
                try:
                    cgpa = float(cgpa_str)
                    if 0 <= cgpa <= 10:
                        print(f"Found CGPA: {cgpa} using pattern: {pattern}")
                        return cgpa
                except ValueError:
                    continue
        
        return None

    def _identify_education_sections(self, lines):
        """Identify sections that contain education information"""
        education_headers = [
            'education', 'academic', 'qualification', 'educational background',
            'academic background', 'academic qualification', 'educational details',
            'academics', 'schooling', 'studies', 'degrees'
        ]
        
        # Section headers that should NOT contain college extraction
        non_education_headers = [
            'achievements', 'awards', 'honors', 'recognition', 'publications',
            'projects', 'experience', 'work', 'internship', 'training',
            'certification', 'skills', 'activities', 'volunteer', 'extracurricular'
        ]
        
        education_sections = []
        current_section_start = None
        current_section_type = None
        
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            
            # Check if this line is a section header
            if self._is_section_header(line_clean):
                # End previous section if it was education-related
                if current_section_start is not None and current_section_type == 'education':
                    education_sections.append((current_section_start, i))
                
                # Check if this is an education section
                if any(header in line_clean for header in education_headers):
                    current_section_start = i + 1
                    current_section_type = 'education'
                elif any(header in line_clean for header in non_education_headers):
                    current_section_start = None
                    current_section_type = 'other'
                else:
                    current_section_start = None
                    current_section_type = None
        
        # Add the last education section if it exists
        if current_section_start is not None and current_section_type == 'education':
            education_sections.append((current_section_start, len(lines)))
        
        # If no clear education sections found, consider first part of resume as potential education
        if not education_sections:
            # Look for education content in first 50% of resume
            mid_point = len(lines) // 2
            education_sections.append((0, mid_point))
        
        return education_sections

    def _is_section_header(self, line):
        """Check if a line looks like a section header"""
        # Remove common formatting
        clean_line = line.strip()
        
        # Skip empty lines
        if not clean_line:
            return False
        
        # Check if line is all uppercase (common for section headers)
        if clean_line.isupper() and len(clean_line.split()) <= 4:
            return True
        
        # Check for common section header patterns
        section_words = [
            'education', 'experience', 'skills', 'projects', 'achievements', 
            'awards', 'certification', 'training', 'summary', 'objective',
            'organizations', 'languages', 'certificates', 'qualifications'
        ]
        
        line_lower = clean_line.lower()
        
        # Exact match for single-word headers
        if line_lower in section_words:
            return True
        
        # Headers with colons or formatting
        if any(word in line_lower for word in section_words):
            if ':' in line_lower or line_lower.endswith(':'):
                return True
            # Check if it's a standalone section word (not part of a sentence)
            if len(clean_line.split()) <= 3:
                return True
        
        return False

    def _is_degree_or_achievement_line(self, line):
        """Check if line is just a degree name or achievement rather than college name"""
        line_lower = line.lower()
        
        # Common degree patterns that shouldn't be considered college names
        degree_patterns = [
            r'\b(b\.?tech|b\.?e|bachelor|master|m\.?tech|m\.?e|phd|diploma)\b',
            r'\b(bca|mca|bba|mba|bcom|mcom|ba|ma|bsc|msc)\b',
            r'\b(degree|graduation|post.?graduation)\b'
        ]
        
        # Achievement/award patterns
        achievement_patterns = [
            r'\b(prize|award|winner|champion|competition|contest|rank|position)\b',
            r'\b(first|second|third|1st|2nd|3rd|gold|silver|bronze)\b'
        ]
        
        for pattern in degree_patterns + achievement_patterns:
            if re.search(pattern, line_lower):
                return True
        
        return False

    def _is_grade_or_year_line(self, line):
        """Check if line contains only grades, years, or percentages"""
        line = line.strip()
        # Check for patterns like "2020-2022", "95.5%", "CGPA: 8.5", etc.
        grade_patterns = [
            r'^\d{4}[-\s]*\d{4}?$',  # Years like "2020-2022"
            r'^\d+(\.\d+)?%?$',       # Percentages like "95.5%" or "95"
            r'^(cgpa|gpa|percentage|marks?)[:=\s]*\d+(\.\d+)?%?$',  # Grade indicators
            r'^grade\s*[a-f]$',       # Letter grades
        ]
        
        return any(re.match(pattern, line, re.IGNORECASE) for pattern in grade_patterns)

    def _extract_school_name_from_line(self, line):
        """Extract school name from a single line"""
        # Remove common prefixes and suffixes that aren't part of the school name
        prefixes_to_remove = [
            r'^(education|academic|qualification|school|college):\s*',
            r'^\d{4}[-\s]*\d{4}?\s*[-:]\s*',
            r'^(hsc|sslc|higher\s+secondary|senior\s+secondary)[-:\s]*',
        ]
        
        cleaned_line = line
        for prefix in prefixes_to_remove:
            cleaned_line = re.sub(prefix, '', cleaned_line, flags=re.IGNORECASE).strip()
        
        # If line is too short after cleaning, it's probably not a school name
        if len(cleaned_line) < 5:
            return None
        
        # Check if it contains school-related keywords
        if any(keyword in cleaned_line.lower() for keyword in self.school_keywords):
            return cleaned_line
        
        return None

    def _clean_college_name(self, line):
        """Clean and extract college name from a line"""
        # Remove common prefixes that might appear with college names
        prefixes_to_remove = [
            r'^\d{4}\s*[-–]\s*\d{4}?\s*',  # Remove year ranges at start
            r'^(present|current)\s*',       # Remove "Present" or "Current"
            r'^\w{3}\s+\d{4}\s*[-–]\s*',   # Remove date patterns like "Nov 2022 -"
        ]
        
        cleaned = line
        for prefix in prefixes_to_remove:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE).strip()
        
        # Remove degree information that might be on the same line
        degree_suffixes = [
            r'\s+(b\.?tech|b\.?e|bachelor|master|m\.?tech|m\.?e|diploma).*$',
            r'\s+(artificial intelligence|machine learning|computer science|information technology).*$',
        ]
        
        for suffix in degree_suffixes:
            cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE).strip()
        
        # If the cleaned name is too short, it's probably not a valid college name
        if len(cleaned) < 5:
            return None
        
        return cleaned

    def _looks_like_college_name(self, line):
        line_lower = line.lower()
    
        # Skip lines that are clearly not college names
        if self._is_grade_or_year_line(line) or self._is_degree_or_achievement_line(line):
            return False
        
        # IMPROVED: Skip degree subjects lines
        if self._is_degree_subjects_line(line):
            return False
        
        # Skip lines that are too short
        if len(line.strip()) < 5:
            return False
        
        # Check for college-related keywords
        college_indicators = [
            'college', 'university', 'institute', 'engineering', 'technology',
            'polytechnic', 'academy', 'campus', 'educational', 'technical'
        ]
        
        if any(indicator in line_lower for indicator in college_indicators):
            return True
        
        # Check if line starts with capital letter and contains multiple words (typical college name format)
        if line and line[0].isupper() and len(line.split()) >= 2:
            # Exclude technical skills or programming languages
            tech_words = [
                'html', 'css', 'javascript', 'python', 'java', 'react', 'angular',
                'node', 'mongodb', 'mysql', 'sql', 'php', 'programming', 'coding'
            ]
            if not any(tech in line_lower for tech in tech_words):
                # Check if it's not a degree name
                degree_words = ['bachelor', 'master', 'diploma', 'certificate', 'course']
                if not any(degree in line_lower for degree in degree_words):
                    return True
        
        return False
        

    def extract_tenth_marks(self, text):
        """Extract 10th marks from resume text"""
        # Clean up spaces in text for better pattern matching
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "SSLC - 88.4" format (your specific data format)
            r'SSLC\s*[-–]\s*(\d{1,2}(?:\.\d+)?)',
            
            # Patterns with "Percentage :" format (like in Vishaal's resume)
            r'(?:10th|SSLC|Secondary|Class\s*10|X)\s*[-–]?\s*\d{4}.*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            
            # Direct percentage patterns (like "SSLC 2020 - 98%")
            r'(?:10th|SSLC|Secondary|Class\s*10|X)(?:\s*[-–]\s*\d{4})?\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%',
            
            # NEW: Handle cases where SSLC is on one line and percentage on next lines
            r'SSLC.*?(?:\n.*?)*?(\d{2})\s*%(?=.*HSC|.*12th|.*Higher|$)',
            
            # Patterns with spaces (like "9 7 .4")
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d\s*\d\s*\.\s*\d+)\s*(?:%|$)',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d\s*\d)\s*(?:%|$)',
            
            # Standard patterns - require at least 2 digits
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(?:percentage|marks?|score).*?(\d{2}(?:\.\d+)?)\s*%?',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d{2}(?:\.\d+)?)\s*(?:%|percentage|marks?|score)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                mark_str = matches[0]
               
                mark_str = re.sub(r'\s+', '', mark_str)
                try:
                    mark = float(mark_str)
                    if 30 <= mark <= 100:  
                        print(f"Found 10th marks: {mark}% using pattern: {pattern}")
                        return mark
                except ValueError:
                    continue

        sslc_hsc_pattern = r'SSLC.*?(\d{2})%.*?HSC.*?(\d{2})%'
        match = re.search(sslc_hsc_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sslc_marks = float(match.group(1))
            if 30 <= sslc_marks <= 100:
                print(f"Found 10th marks from SSLC/HSC table: {sslc_marks}%")
                return sslc_marks
        
        return None

    def extract_twelfth_marks(self, text):
        """Extract 12th marks from resume text"""
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "HSLC - 92.8" format (your specific data format)
            r'HSLC\s*[-–]\s*(\d{1,2}(?:\.\d+)?)',

            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two)(?:\s*[-–]\s*\d{4})?\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%?(?:\s|$)',

            r'HSC.*?(?:\n.*?)*?(\d{2})\s*%(?=.*SSLC|.*10th|.*Secondary|$)',
            
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?(?:percentage|marks?|score).*?(\d{2}(?:\.\d+)?)\s*%?',
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?(\d{2}(?:\.\d+)?)\s*(?:%|percentage|marks?|score)',
            
            r'HSC\s*(?:[-–]\s*)?\d{4}\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%?',
            r'Higher\s*Secondary.*?(\d{2}(?:\.\d+)?)\s*%',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                mark_str = matches[0]
                # Handle spaced numbers
                mark_str = re.sub(r'\s+', '', mark_str)
                try:
                    mark = float(mark_str)
                    if 30 <= mark <= 100:  # More realistic range for 12th marks
                        print(f"Found 12th marks: {mark}% using pattern: {pattern}")
                        return mark
                except ValueError:
                    continue
        
        # NEW: Fallback pattern for educational table format
        # Look for HSC followed by SSLC and extract the first percentage
        hsc_sslc_pattern = r'HSC.*?(\d{2})%.*?SSLC.*?(\d{2})%'
        match = re.search(hsc_sslc_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            hsc_marks = float(match.group(1))
            if 30 <= hsc_marks <= 100:
                print(f"Found 12th marks from HSC/SSLC table: {hsc_marks}%")
                return hsc_marks
        
        return None
    
    def extract_cgpa(self, text):
        """Extract CGPA from resume text"""
        # Clean up spaces in text for better pattern matching
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "Bachelor of Engineering in Computer Science - 8.46" format
            r'Bachelor.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'Bachelor.*?Engineering.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'B\.?E.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'B\.?Tech.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            
            # NEW: Pattern for standalone CGPA values near college/education context
            r'(?:B\.?E|B\.?Tech|Bachelor|Engineering|College).*?(\d+\.\d{2})\s*(?:CGPA|GPA|till|semester|out\s*of)',
            r'(?:Rajalakshmi|Engineering|College).*?(\d+\.\d{2})\s*(?:CGPA|GPA|till|semester)',
            r'(\d+\.\d{2})\s*CGPA\s*\(till',
            r'(\d+\.\d{2})\s*(?:CGPA|GPA)\s*\(',
            
            # Patterns with spaces (like "CGP A : 8.38")
            r'CGP\s*A\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'C\s*G\s*P\s*A\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Standard CGPA patterns
            r'CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'GPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Cumulative\s*GPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Cumulative\s*Grade\s*Point\s*Average\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Grade\s*Point\s*Average\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Current\s*CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Overall\s*CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Academic\s*Grade\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Patterns with context
            r'(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A).*?(\d+(?:\.\d+)?)\s*(?:/\s*10|\s*out\s*of\s*10)?',
            
            # Reverse patterns
            r'(\d+(?:\.\d+)?)\s*/\s*10\s*(?:CGPA|GPA|Grade)',
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*10\s*(?:CGPA|GPA|Grade)',
            
            # College context patterns (like "CGPA - 8.41")
            r'(?:B\.?Tech|B\.?E|Bachelor|Engineering|College).*?(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A)\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Dash patterns (like "CGPA - 8.41")
            r'(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A)\s*[-–]\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                cgpa_str = matches[0]
                # Handle spaced numbers
                cgpa_str = re.sub(r'\s+', '', cgpa_str)
                try:
                    cgpa = float(cgpa_str)
                    if 0 <= cgpa <= 10:
                        print(f"Found CGPA: {cgpa} using pattern: {pattern}")
                        return cgpa
                except ValueError:
                    continue
        
        return None

    def _identify_education_sections(self, lines):
        """Identify sections that contain education information"""
        education_headers = [
            'education', 'academic', 'qualification', 'educational background',
            'academic background', 'academic qualification', 'educational details',
            'academics', 'schooling', 'studies', 'degrees'
        ]
        
        # Section headers that should NOT contain college extraction
        non_education_headers = [
            'achievements', 'awards', 'honors', 'recognition', 'publications',
            'projects', 'experience', 'work', 'internship', 'training',
            'certification', 'skills', 'activities', 'volunteer', 'extracurricular'
        ]
        
        education_sections = []
        current_section_start = None
        current_section_type = None
        
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            
            # Check if this line is a section header
            if self._is_section_header(line_clean):
                # End previous section if it was education-related
                if current_section_start is not None and current_section_type == 'education':
                    education_sections.append((current_section_start, i))
                
                # Check if this is an education section
                if any(header in line_clean for header in education_headers):
                    current_section_start = i + 1
                    current_section_type = 'education'
                elif any(header in line_clean for header in non_education_headers):
                    current_section_start = None
                    current_section_type = 'other'
                else:
                    current_section_start = None
                    current_section_type = None
        
        # Add the last education section if it exists
        if current_section_start is not None and current_section_type == 'education':
            education_sections.append((current_section_start, len(lines)))
        
        # If no clear education sections found, consider first part of resume as potential education
        if not education_sections:
            # Look for education content in first 50% of resume
            mid_point = len(lines) // 2
            education_sections.append((0, mid_point))
        
        return education_sections

    def _is_section_header(self, line):
        """Check if a line looks like a section header"""
        # Remove common formatting
        clean_line = line.strip()
        
        # Skip empty lines
        if not clean_line:
            return False
        
        # Check if line is all uppercase (common for section headers)
        if clean_line.isupper() and len(clean_line.split()) <= 4:
            return True
        
        # Check for common section header patterns
        section_words = [
            'education', 'experience', 'skills', 'projects', 'achievements', 
            'awards', 'certification', 'training', 'summary', 'objective',
            'organizations', 'languages', 'certificates', 'qualifications'
        ]
        
        line_lower = clean_line.lower()
        
        # Exact match for single-word headers
        if line_lower in section_words:
            return True
        
        # Headers with colons or formatting
        if any(word in line_lower for word in section_words):
            if ':' in line_lower or line_lower.endswith(':'):
                return True
            # Check if it's a standalone section word (not part of a sentence)
            if len(clean_line.split()) <= 3:
                return True
        
        return False

    def _is_degree_or_achievement_line(self, line):
        """Check if line is just a degree name or achievement rather than college name"""
        line_lower = line.lower()
        
        # Common degree patterns that shouldn't be considered college names
        degree_patterns = [
            r'\b(b\.?tech|b\.?e|bachelor|master|m\.?tech|m\.?e|phd|diploma)\b',
            r'\b(bca|mca|bba|mba|bcom|mcom|ba|ma|bsc|msc)\b',
            r'\b(degree|graduation|post.?graduation)\b'
        ]
        
        # Achievement/award patterns
        achievement_patterns = [
            r'\b(prize|award|winner|champion|competition|contest|rank|position)\b',
            r'\b(first|second|third|1st|2nd|3rd|gold|silver|bronze)\b'
        ]
        
        for pattern in degree_patterns + achievement_patterns:
            if re.search(pattern, line_lower):
                return True
        
        return False

    def _is_grade_or_year_line(self, line):
        """Check if line contains only grades, years, or percentages"""
        line = line.strip()
        # Check for patterns like "2020-2022", "95.5%", "CGPA: 8.5", etc.
        grade_patterns = [
            r'^\d{4}[-\s]*\d{4}?$',  # Years like "2020-2022"
            r'^\d+(\.\d+)?%?$',       # Percentages like "95.5%" or "95"
            r'^(cgpa|gpa|percentage|marks?)[:=\s]*\d+(\.\d+)?%?$',  # Grade indicators
            r'^grade\s*[a-f]$',       # Letter grades
        ]
        
        return any(re.match(pattern, line, re.IGNORECASE) for pattern in grade_patterns)

    def _extract_school_name_from_line(self, line):
        """Extract school name from a single line"""
        # Remove common prefixes and suffixes that aren't part of the school name
        prefixes_to_remove = [
            r'^(education|academic|qualification|school|college):\s*',
            r'^\d{4}[-\s]*\d{4}?\s*[-:]\s*',
            r'^(hsc|sslc|higher\s+secondary|senior\s+secondary)[-:\s]*',
        ]
        
        cleaned_line = line
        for prefix in prefixes_to_remove:
            cleaned_line = re.sub(prefix, '', cleaned_line, flags=re.IGNORECASE).strip()
        
        # If line is too short after cleaning, it's probably not a school name
        if len(cleaned_line) < 5:
            return None
        
        # Check if it contains school-related keywords
        if any(keyword in cleaned_line.lower() for keyword in self.school_keywords):
            return cleaned_line
        
        return None

    def _clean_college_name(self, line):
        """Clean and extract college name from a line"""
        # Remove common prefixes that might appear with college names
        prefixes_to_remove = [
            r'^\d{4}\s*[-–]\s*\d{4}?\s*',  # Remove year ranges at start
            r'^(present|current)\s*',       # Remove "Present" or "Current"
            r'^\w{3}\s+\d{4}\s*[-–]\s*',   # Remove date patterns like "Nov 2022 -"
        ]
        
        cleaned = line
        for prefix in prefixes_to_remove:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE).strip()
        
        # Remove degree information that might be on the same line
        degree_suffixes = [
            r'\s+(b\.?tech|b\.?e|bachelor|master|m\.?tech|m\.?e|diploma).*$',
            r'\s+(artificial intelligence|machine learning|computer science|information technology).*$',
        ]
        
        for suffix in degree_suffixes:
            cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE).strip()
        
        # If the cleaned name is too short, it's probably not a valid college name
        if len(cleaned) < 5:
            return None
        
        return cleaned

    def _looks_like_college_name(self, line):
        line_lower = line.lower()
    
        # Skip lines that are clearly not college names
        if self._is_grade_or_year_line(line) or self._is_degree_or_achievement_line(line):
            return False
        
        # IMPROVED: Skip degree subjects lines
        if self._is_degree_subjects_line(line):
            return False
        
        # Skip lines that are too short
        if len(line.strip()) < 5:
            return False
        
        # Check for college-related keywords
        college_indicators = [
            'college', 'university', 'institute', 'engineering', 'technology',
            'polytechnic', 'academy', 'campus', 'educational', 'technical'
        ]
        
        if any(indicator in line_lower for indicator in college_indicators):
            return True
        
        # Check if line starts with capital letter and contains multiple words (typical college name format)
        if line and line[0].isupper() and len(line.split()) >= 2:
            # Exclude technical skills or programming languages
            tech_words = [
                'html', 'css', 'javascript', 'python', 'java', 'react', 'angular',
                'node', 'mongodb', 'mysql', 'sql', 'php', 'programming', 'coding'
            ]
            if not any(tech in line_lower for tech in tech_words):
                # Check if it's not a degree name
                degree_words = ['bachelor', 'master', 'diploma', 'certificate', 'course']
                if not any(degree in line_lower for degree in degree_words):
                    return True
        
        return False
        

    def extract_tenth_marks(self, text):
        """Extract 10th marks from resume text"""
        # Clean up spaces in text for better pattern matching
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "SSLC - 88.4" format (your specific data format)
            r'SSLC\s*[-–]\s*(\d{1,2}(?:\.\d+)?)',
            
            # Patterns with "Percentage :" format (like in Vishaal's resume)
            r'(?:10th|SSLC|Secondary|Class\s*10|X)\s*[-–]?\s*\d{4}.*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            
            # Direct percentage patterns (like "SSLC 2020 - 98%")
            r'(?:10th|SSLC|Secondary|Class\s*10|X)(?:\s*[-–]\s*\d{4})?\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%',
            
            # NEW: Handle cases where SSLC is on one line and percentage on next lines
            r'SSLC.*?(?:\n.*?)*?(\d{2})\s*%(?=.*HSC|.*12th|.*Higher|$)',
            
            # Patterns with spaces (like "9 7 .4")
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d\s*\d\s*\.\s*\d+)\s*(?:%|$)',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d\s*\d)\s*(?:%|$)',
            
            # Standard patterns - require at least 2 digits
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(?:percentage|marks?|score).*?(\d{2}(?:\.\d+)?)\s*%?',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d{2}(?:\.\d+)?)\s*(?:%|percentage|marks?|score)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                mark_str = matches[0]
               
                mark_str = re.sub(r'\s+', '', mark_str)
                try:
                    mark = float(mark_str)
                    if 30 <= mark <= 100:  
                        print(f"Found 10th marks: {mark}% using pattern: {pattern}")
                        return mark
                except ValueError:
                    continue

        sslc_hsc_pattern = r'SSLC.*?(\d{2})%.*?HSC.*?(\d{2})%'
        match = re.search(sslc_hsc_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sslc_marks = float(match.group(1))
            if 30 <= sslc_marks <= 100:
                print(f"Found 10th marks from SSLC/HSC table: {sslc_marks}%")
                return sslc_marks
        
        return None

    def extract_twelfth_marks(self, text):
        """Extract 12th marks from resume text"""
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "HSLC - 92.8" format (your specific data format)
            r'HSLC\s*[-–]\s*(\d{1,2}(?:\.\d+)?)',

            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two)(?:\s*[-–]\s*\d{4})?\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%?(?:\s|$)',

            r'HSC.*?(?:\n.*?)*?(\d{2})\s*%(?=.*SSLC|.*10th|.*Secondary|$)',
            
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?(?:percentage|marks?|score).*?(\d{2}(?:\.\d+)?)\s*%?',
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?(\d{2}(?:\.\d+)?)\s*(?:%|percentage|marks?|score)',
            
            r'HSC\s*(?:[-–]\s*)?\d{4}\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%?',
            r'Higher\s*Secondary.*?(\d{2}(?:\.\d+)?)\s*%',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                mark_str = matches[0]
                # Handle spaced numbers
                mark_str = re.sub(r'\s+', '', mark_str)
                try:
                    mark = float(mark_str)
                    if 30 <= mark <= 100:  # More realistic range for 12th marks
                        print(f"Found 12th marks: {mark}% using pattern: {pattern}")
                        return mark
                except ValueError:
                    continue
        
        # NEW: Fallback pattern for educational table format
        # Look for HSC followed by SSLC and extract the first percentage
        hsc_sslc_pattern = r'HSC.*?(\d{2})%.*?SSLC.*?(\d{2})%'
        match = re.search(hsc_sslc_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            hsc_marks = float(match.group(1))
            if 30 <= hsc_marks <= 100:
                print(f"Found 12th marks from HSC/SSLC table: {hsc_marks}%")
                return hsc_marks
        
        return None
    
    def extract_cgpa(self, text):
        """Extract CGPA from resume text"""
        # Clean up spaces in text for better pattern matching
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "Bachelor of Engineering in Computer Science - 8.46" format
            r'Bachelor.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'Bachelor.*?Engineering.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'B\.?E.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'B\.?Tech.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            
            # NEW: Pattern for standalone CGPA values near college/education context
            r'(?:B\.?E|B\.?Tech|Bachelor|Engineering|College).*?(\d+\.\d{2})\s*(?:CGPA|GPA|till|semester|out\s*of)',
            r'(?:Rajalakshmi|Engineering|College).*?(\d+\.\d{2})\s*(?:CGPA|GPA|till|semester)',
            r'(\d+\.\d{2})\s*CGPA\s*\(till',
            r'(\d+\.\d{2})\s*(?:CGPA|GPA)\s*\(',
            
            # Patterns with spaces (like "CGP A : 8.38")
            r'CGP\s*A\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'C\s*G\s*P\s*A\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Standard CGPA patterns
            r'CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'GPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Cumulative\s*GPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Cumulative\s*Grade\s*Point\s*Average\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Grade\s*Point\s*Average\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Current\s*CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Overall\s*CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Academic\s*Grade\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Patterns with context
            r'(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A).*?(\d+(?:\.\d+)?)\s*(?:/\s*10|\s*out\s*of\s*10)?',
            
            # Reverse patterns
            r'(\d+(?:\.\d+)?)\s*/\s*10\s*(?:CGPA|GPA|Grade)',
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*10\s*(?:CGPA|GPA|Grade)',
            
            # College context patterns (like "CGPA - 8.41")
            r'(?:B\.?Tech|B\.?E|Bachelor|Engineering|College).*?(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A)\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Dash patterns (like "CGPA - 8.41")
            r'(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A)\s*[-–]\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                cgpa_str = matches[0]
                # Handle spaced numbers
                cgpa_str = re.sub(r'\s+', '', cgpa_str)
                try:
                    cgpa = float(cgpa_str)
                    if 0 <= cgpa <= 10:
                        print(f"Found CGPA: {cgpa} using pattern: {pattern}")
                        return cgpa
                except ValueError:
                    continue
        
        return None

    def _identify_education_sections(self, lines):
        """Identify sections that contain education information"""
        education_headers = [
            'education', 'academic', 'qualification', 'educational background',
            'academic background', 'academic qualification', 'educational details',
            'academics', 'schooling', 'studies', 'degrees'
        ]
        
        # Section headers that should NOT contain college extraction
        non_education_headers = [
            'achievements', 'awards', 'honors', 'recognition', 'publications',
            'projects', 'experience', 'work', 'internship', 'training',
            'certification', 'skills', 'activities', 'volunteer', 'extracurricular'
        ]
        
        education_sections = []
        current_section_start = None
        current_section_type = None
        
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            
            # Check if this line is a section header
            if self._is_section_header(line_clean):
                # End previous section if it was education-related
                if current_section_start is not None and current_section_type == 'education':
                    education_sections.append((current_section_start, i))
                
                # Check if this is an education section
                if any(header in line_clean for header in education_headers):
                    current_section_start = i + 1
                    current_section_type = 'education'
                elif any(header in line_clean for header in non_education_headers):
                    current_section_start = None
                    current_section_type = 'other'
                else:
                    current_section_start = None
                    current_section_type = None
        
        # Add the last education section if it exists
        if current_section_start is not None and current_section_type == 'education':
            education_sections.append((current_section_start, len(lines)))
        
        # If no clear education sections found, consider first part of resume as potential education
        if not education_sections:
            # Look for education content in first 50% of resume
            mid_point = len(lines) // 2
            education_sections.append((0, mid_point))
        
        return education_sections

    def _is_section_header(self, line):
        """Check if a line looks like a section header"""
        # Remove common formatting
        clean_line = line.strip()
        
        # Skip empty lines
        if not clean_line:
            return False
        
        # Check if line is all uppercase (common for section headers)
        if clean_line.isupper() and len(clean_line.split()) <= 4:
            return True
        
        # Check for common section header patterns
        section_words = [
            'education', 'experience', 'skills', 'projects', 'achievements', 
            'awards', 'certification', 'training', 'summary', 'objective',
            'organizations', 'languages', 'certificates', 'qualifications'
        ]
        
        line_lower = clean_line.lower()
        
        # Exact match for single-word headers
        if line_lower in section_words:
            return True
        
        # Headers with colons or formatting
        if any(word in line_lower for word in section_words):
            if ':' in line_lower or line_lower.endswith(':'):
                return True
            # Check if it's a standalone section word (not part of a sentence)
            if len(clean_line.split()) <= 3:
                return True
        
        return False

    def _is_degree_or_achievement_line(self, line):
        """Check if line is just a degree name or achievement rather than college name"""
        line_lower = line.lower()
        
        # Common degree patterns that shouldn't be considered college names
        degree_patterns = [
            r'\b(b\.?tech|b\.?e|bachelor|master|m\.?tech|m\.?e|phd|diploma)\b',
            r'\b(bca|mca|bba|mba|bcom|mcom|ba|ma|bsc|msc)\b',
            r'\b(degree|graduation|post.?graduation)\b'
        ]
        
        # Achievement/award patterns
        achievement_patterns = [
            r'\b(prize|award|winner|champion|competition|contest|rank|position)\b',
            r'\b(first|second|third|1st|2nd|3rd|gold|silver|bronze)\b'
        ]
        
        for pattern in degree_patterns + achievement_patterns:
            if re.search(pattern, line_lower):
                return True
        
        return False

    def _is_grade_or_year_line(self, line):
        """Check if line contains only grades, years, or percentages"""
        line = line.strip()
        # Check for patterns like "2020-2022", "95.5%", "CGPA: 8.5", etc.
        grade_patterns = [
            r'^\d{4}[-\s]*\d{4}?$',  # Years like "2020-2022"
            r'^\d+(\.\d+)?%?$',       # Percentages like "95.5%" or "95"
            r'^(cgpa|gpa|percentage|marks?)[:=\s]*\d+(\.\d+)?%?$',  # Grade indicators
            r'^grade\s*[a-f]$',       # Letter grades
        ]
        
        return any(re.match(pattern, line, re.IGNORECASE) for pattern in grade_patterns)

    def _extract_school_name_from_line(self, line):
        """Extract school name from a single line"""
        # Remove common prefixes and suffixes that aren't part of the school name
        prefixes_to_remove = [
            r'^(education|academic|qualification|school|college):\s*',
            r'^\d{4}[-\s]*\d{4}?\s*[-:]\s*',
            r'^(hsc|sslc|higher\s+secondary|senior\s+secondary)[-:\s]*',
        ]
        
        cleaned_line = line
        for prefix in prefixes_to_remove:
            cleaned_line = re.sub(prefix, '', cleaned_line, flags=re.IGNORECASE).strip()
        
        # If line is too short after cleaning, it's probably not a school name
        if len(cleaned_line) < 5:
            return None
        
        # Check if it contains school-related keywords
        if any(keyword in cleaned_line.lower() for keyword in self.school_keywords):
            return cleaned_line
        
        return None

    def _clean_college_name(self, line):
        """Clean and extract college name from a line"""
        # Remove common prefixes that might appear with college names
        prefixes_to_remove = [
            r'^\d{4}\s*[-–]\s*\d{4}?\s*',  # Remove year ranges at start
            r'^(present|current)\s*',       # Remove "Present" or "Current"
            r'^\w{3}\s+\d{4}\s*[-–]\s*',   # Remove date patterns like "Nov 2022 -"
        ]
        
        cleaned = line
        for prefix in prefixes_to_remove:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE).strip()
        
        # Remove degree information that might be on the same line
        degree_suffixes = [
            r'\s+(b\.?tech|b\.?e|bachelor|master|m\.?tech|m\.?e|diploma).*$',
            r'\s+(artificial intelligence|machine learning|computer science|information technology).*$',
        ]
        
        for suffix in degree_suffixes:
            cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE).strip()
        
        # If the cleaned name is too short, it's probably not a valid college name
        if len(cleaned) < 5:
            return None
        
        return cleaned

    def _looks_like_college_name(self, line):
        line_lower = line.lower()
    
        # Skip lines that are clearly not college names
        if self._is_grade_or_year_line(line) or self._is_degree_or_achievement_line(line):
            return False
        
        # IMPROVED: Skip degree subjects lines
        if self._is_degree_subjects_line(line):
            return False
        
        # Skip lines that are too short
        if len(line.strip()) < 5:
            return False
        
        # Check for college-related keywords
        college_indicators = [
            'college', 'university', 'institute', 'engineering', 'technology',
            'polytechnic', 'academy', 'campus', 'educational', 'technical'
        ]
        
        if any(indicator in line_lower for indicator in college_indicators):
            return True
        
        # Check if line starts with capital letter and contains multiple words (typical college name format)
        if line and line[0].isupper() and len(line.split()) >= 2:
            # Exclude technical skills or programming languages
            tech_words = [
                'html', 'css', 'javascript', 'python', 'java', 'react', 'angular',
                'node', 'mongodb', 'mysql', 'sql', 'php', 'programming', 'coding'
            ]
            if not any(tech in line_lower for tech in tech_words):
                # Check if it's not a degree name
                degree_words = ['bachelor', 'master', 'diploma', 'certificate', 'course']
                if not any(degree in line_lower for degree in degree_words):
                    return True
        
        return False
        

    def extract_tenth_marks(self, text):
        """Extract 10th marks from resume text"""
        # Clean up spaces in text for better pattern matching
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "SSLC - 88.4" format (your specific data format)
            r'SSLC\s*[-–]\s*(\d{1,2}(?:\.\d+)?)',
            
            # Patterns with "Percentage :" format (like in Vishaal's resume)
            r'(?:10th|SSLC|Secondary|Class\s*10|X)\s*[-–]?\s*\d{4}.*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            
            # Direct percentage patterns (like "SSLC 2020 - 98%")
            r'(?:10th|SSLC|Secondary|Class\s*10|X)(?:\s*[-–]\s*\d{4})?\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%',
            
            # NEW: Handle cases where SSLC is on one line and percentage on next lines
            r'SSLC.*?(?:\n.*?)*?(\d{2})\s*%(?=.*HSC|.*12th|.*Higher|$)',
            
            # Patterns with spaces (like "9 7 .4")
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d\s*\d\s*\.\s*\d+)\s*(?:%|$)',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d\s*\d)\s*(?:%|$)',
            
            # Standard patterns - require at least 2 digits
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(?:percentage|marks?|score).*?(\d{2}(?:\.\d+)?)\s*%?',
            r'(?:10th|SSLC|Secondary|Class\s*10|X).*?(\d{2}(?:\.\d+)?)\s*(?:%|percentage|marks?|score)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                mark_str = matches[0]
               
                mark_str = re.sub(r'\s+', '', mark_str)
                try:
                    mark = float(mark_str)
                    if 30 <= mark <= 100:  
                        print(f"Found 10th marks: {mark}% using pattern: {pattern}")
                        return mark
                except ValueError:
                    continue

        sslc_hsc_pattern = r'SSLC.*?(\d{2})%.*?HSC.*?(\d{2})%'
        match = re.search(sslc_hsc_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sslc_marks = float(match.group(1))
            if 30 <= sslc_marks <= 100:
                print(f"Found 10th marks from SSLC/HSC table: {sslc_marks}%")
                return sslc_marks
        
        return None

    def extract_twelfth_marks(self, text):
        """Extract 12th marks from resume text"""
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "HSLC - 92.8" format (your specific data format)
            r'HSLC\s*[-–]\s*(\d{1,2}(?:\.\d+)?)',

            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?Percen\s*tage\s*:\s*(\d{2}(?:\.\d+)?)',
            
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two)(?:\s*[-–]\s*\d{4})?\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%?(?:\s|$)',

            r'HSC.*?(?:\n.*?)*?(\d{2})\s*%(?=.*SSLC|.*10th|.*Secondary|$)',
            
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?(?:percentage|marks?|score).*?(\d{2}(?:\.\d+)?)\s*%?',
            r'(?:12th|HSC|Higher\s*Secondary|Senior\s*Secondary|Class\s*12|XII|\+2|Plus\s*Two).*?(\d{2}(?:\.\d+)?)\s*(?:%|percentage|marks?|score)',
            
            r'HSC\s*(?:[-–]\s*)?\d{4}\s*[-–]?\s*(\d{2}(?:\.\d+)?)\s*%?',
            r'Higher\s*Secondary.*?(\d{2}(?:\.\d+)?)\s*%',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                mark_str = matches[0]
                # Handle spaced numbers
                mark_str = re.sub(r'\s+', '', mark_str)
                try:
                    mark = float(mark_str)
                    if 30 <= mark <= 100:  # More realistic range for 12th marks
                        print(f"Found 12th marks: {mark}% using pattern: {pattern}")
                        return mark
                except ValueError:
                    continue
        
        # NEW: Fallback pattern for educational table format
        # Look for HSC followed by SSLC and extract the first percentage
        hsc_sslc_pattern = r'HSC.*?(\d{2})%.*?SSLC.*?(\d{2})%'
        match = re.search(hsc_sslc_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            hsc_marks = float(match.group(1))
            if 30 <= hsc_marks <= 100:
                print(f"Found 12th marks from HSC/SSLC table: {hsc_marks}%")
                return hsc_marks
        
        return None
    
    def extract_cgpa(self, text):
        """Extract CGPA from resume text"""
        # Clean up spaces in text for better pattern matching
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # ADDED CODE: Pattern for "Bachelor of Engineering in Computer Science - 8.46" format
            r'Bachelor.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'Bachelor.*?Engineering.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'B\.?E.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            r'B\.?Tech.*?Computer Science\s*[-–]\s*(\d+\.\d+)',
            
            # NEW: Pattern for standalone CGPA values near college/education context
            r'(?:B\.?E|B\.?Tech|Bachelor|Engineering|College).*?(\d+\.\d{2})\s*(?:CGPA|GPA|till|semester|out\s*of)',
            r'(?:Rajalakshmi|Engineering|College).*?(\d+\.\d{2})\s*(?:CGPA|GPA|till|semester)',
            r'(\d+\.\d{2})\s*CGPA\s*\(till',
            r'(\d+\.\d{2})\s*(?:CGPA|GPA)\s*\(',
            
            # Patterns with spaces (like "CGP A : 8.38")
            r'CGP\s*A\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'C\s*G\s*P\s*A\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Standard CGPA patterns
            r'CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'GPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Cumulative\s*GPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Cumulative\s*Grade\s*Point\s*Average\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Grade\s*Point\s*Average\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Current\s*CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Overall\s*CGPA\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            r'Academic\s*Grade\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Patterns with context
            r'(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A).*?(\d+(?:\.\d+)?)\s*(?:/\s*10|\s*out\s*of\s*10)?',
            
            # Reverse patterns
            r'(\d+(?:\.\d+)?)\s*/\s*10\s*(?:CGPA|GPA|Grade)',
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*10\s*(?:CGPA|GPA|Grade)',
            
            # College context patterns (like "CGPA - 8.41")
            r'(?:B\.?Tech|B\.?E|Bachelor|Engineering|College).*?(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A)\s*[-:=]?\s*(\d+(?:\.\d+)?)',
            
            # Dash patterns (like "CGPA - 8.41")
            r'(?:CGPA|GPA|C\s*G\s*P\s*A|CGP\s*A)\s*[-–]\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                cgpa_str = matches[0]
                # Handle spaced numbers
                cgpa_str = re.sub(r'\s+', '', cgpa_str)
                try:
                    cgpa = float(cgpa_str)
                    if 0 <= cgpa <= 10:
                        print(f"Found CGPA: {cgpa} using pattern: {pattern}")
                        return cgpa
                except ValueError:
                    continue
        
        return None

    def _identify_education_sections(self, lines):
        """Identify sections that contain education information"""
        education_headers = [
            'education', 'academic', 'qualification', 'educational background',
            'academic background', 'academic qualification', 'educational details',
            'academics', 'schooling', 'studies', 'degrees'
        ]
        
        # Section headers that should NOT contain college extraction
        non_education_headers = [
            'achievements', 'awards', 'honors', 'recognition', 'publications',
            'projects', 'experience', 'work', 'internship', 'training',
            'certification', 'skills', 'activities', 'volunteer', 'extracurricular'
        ]
        
        education_sections = []
        current_section_start = None
        current_section_type = None
        
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            
            # Check if this line is a section header
            if self._is_section_header(line_clean):
                # End previous section if it was education-related
                if current_section_start is not None and current_section_type == 'education':
                    education_sections.append((current_section_start, i))
                
                # Check if this is an education section
                if any(header in line_clean for header in education_headers):
                    current_section_start = i + 1
                    current_section_type = 'education'
                elif any(header in line_clean for header in non_education_headers):
                    current_section_start = None
                    current_section_type = 'other'
                else:
                    current_section_start = None
                    current_section_type = None
        
        # Add the last education section if it exists
        if current_section_start is not None and current_section_type == 'education':
            education_sections.append((current_section_start, len(lines)))
        
        # If no clear education sections found, consider first part of resume as potential education
        if not education_sections:
            # Look for education content in first 50% of resume
            mid_point = len(lines) // 2
            education_sections.append((0, mid_point))
        
        return education_sections

    def _is_section_header(self, line):
        """Check if a line looks like a section header"""
        # Remove common formatting
        clean_line = line.strip()
        
        # Skip empty lines
        if not clean_line:
            return False
        
        # Check if line is all uppercase (common for section headers)
        if clean_line.isupper() and len(clean_line.split()) <= 4:
            return True
        
        # Check for common section header patterns
        section_words = [
            'education', 'experience', 'skills', 'projects', 'achievements', 
            'awards', 'certification', 'training', 'summary', 'objective',
            'organizations', 'languages', 'certificates', 'qualifications'
        ]
        
        line_lower = clean_line.lower()
        
        # Exact match for single-word headers
        if line_lower in section_words:
            return True
        
        # Headers with colons or formatting
        if any(word in line_lower for word in section_words):
            if ':' in line_lower or line_lower.endswith(':'):
                return True
            # Check if it's a standalone section word (not part of a sentence)
            if len(clean_line.split()) <= 3:
                return True
        
        return False

    def _is_degree_or_achievement_line(self, line):
        """Check if line is just a degree name or achievement rather than college name"""
        line_lower = line.lower()
        
        # Common degree patterns that shouldn't be considered college names
        degree_patterns = [
            r'\b(b\.?tech|b\.?e|bachelor|master|m\.?tech|m\.?e|phd|diploma)\b',
            r'\b(bca|mca|bba|mba|bcom|mcom|ba|ma|bsc|msc)\b',
            r'\b(degree|graduation|post.?graduation)\b'
        ]
        
        # Achievement/award patterns
        achievement_patterns = [
            r'\b(prize|award|winner|champion|competition|contest|rank|position)\b',
            r'\b(first|second|third|1st|2nd|3rd|gold|silver|bronze)\b'
        ]
        
        for pattern in degree_patterns + achievement_patterns:
            if re.search(pattern, line_lower):
                return True
        
        return False

    def _is_grade_or_year_line(self, line):
        """Check if line contains only grades, years, or percentages"""
        line = line.strip()
        # Check for patterns like "2020-2022", "95.5%", "CGPA: 8.5", etc.
        grade_patterns = [
            r'^\d{4}[-\s]*\d{4}?$',  # Years like "2020-2022"
            r'^\d+(\.\d+)?%?$',       # Percentages like "95.5%" or "95"
            r'^(cgpa|gpa|percentage|marks?)[:=\s]*\d+(\.\d+)?%?$',  # Grade indicators
            r'^grade\s*[a-f]$',       # Letter grades
        ]
        
        return any(re.match(pattern, line, re.IGNORECASE) for pattern in grade_patterns)

    def _extract_school_name_from_line(self, line):
        """Extract school name from a single line"""
        # Remove common prefixes and suffixes that aren't part of the school name
        prefixes_to_remove = [
            r'^(education|academic|qualification|school|college):\s*',
            r'^\d{4}[-\s]*\d{4}?\s*[-:]\s*',
            r'^(hsc|sslc|higher\s+secondary|senior\s+secondary)[-:\s]*',
        ]
        
        cleaned_line = line
        for prefix in prefixes_to_remove:
            cleaned_line = re.sub(prefix, '', cleaned_line, flags=re.IGNORECASE).strip()
        
        # If line is too short after cleaning, it's probably not a school name
        if len(cleaned_line) < 5:
            return None
        
        # Check if it contains school-related keywords
        if any(keyword in cleaned_line.lower() for keyword in self.school_keywords):
            return cleaned_line
        
        return None

    def _clean_college_name(self, line):
        """Clean and extract college name from a line"""
        # Remove common prefixes that might appear with college names
        prefixes_to_remove = [
            r'^\d{4}\s*[-–]\s*\d{4}?\s*',  # Remove year ranges at start
            r'^(present|current)\s*',       # Remove "Present" or "Current"
            r'^\w{3}\s+\d{4}\s*[-–]\s*',   # Remove date patterns like "Nov 2022 -"
        ]
        
        cleaned = line
        for prefix in prefixes_to_remove:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE).strip()
        
        # Remove degree information that might be on the same line
        degree_suffixes = [
            r'\s+(b\.?tech|b\.?e|bachelor|master|m\.?tech|m\.?e|diploma).*$',
            r'\s+(artificial intelligence|machine learning|computer science|information technology).*$',
        ]
        
        for suffix in degree_suffixes:
            cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE).strip()
        
        # If the cleaned name is too short, it's probably not a valid college name
        if len(cleaned) < 5:
            return None
        
        return cleaned

    def _looks_like_college_name(self, line):
        line_lower = line.lower()
    
        # Skip lines that are clearly not college names
        if self._is_grade_or_year_line(line) or self._is_degree_or_achievement_line(line):
            return False
        
        # IMPROVED: Skip degree subjects lines
        if self._is_degree_subjects_line(line):
            return False
        
        # Skip lines that are too short
        if len(line.strip()) < 5:
            return False
        
        # Check for college-related keywords
        college_indicators = [
            'college', 'university', 'institute', 'engineering', 'technology',
            'polytechnic', 'academy', 'campus', 'educational', 'technical'
        ]
        
        if any(indicator in line_lower for indicator in college_indicators):
            return True
        
        # Check if line starts with capital letter and contains multiple words (typical college name format)
        if line and line[0].isupper() and len(line.split()) >= 2:
            # Exclude technical skills or programming languages
            tech_words = [
                'html', 'css', 'javascript', 'python', 'java', 'react', 'angular',
                'node', 'mongodb', 'mysql', 'sql', 'php', 'programming', 'coding'
            ]
            if not any(tech in line_lower for tech in tech_words):
                # Check if it's not a degree name
                degree_words = ['bachelor', 'master', 'diploma', 'certificate', 'course']
                if not any(degree in line_lower for degree in degree_words):
                    return True
        
        return False
