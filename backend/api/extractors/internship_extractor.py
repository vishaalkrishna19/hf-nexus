import re
import spacy
from datetime import datetime
from dateutil import parser
import calendar

class InternshipExtractor:
    def __init__(self):
        self.internship_keywords = ['intern', 'internship', 'trainee', 'apprentice']
        
        self.duration_patterns = [
            r'(\d{1,2})\s*(?:months?|mon|mos?)\b',
            r'(\w+\s*\d{4})\s*[-–—]\s*(\w+\s*\d{4})',
            r'(\d{1,2}/\d{2,4})\s*[-–—]\s*(\d{1,2}/\d{2,4})',
            r'(\d{4})\s*[-–—]\s*(\d{4})',
            r'(\w+)\s*(\d{4})\s*[-–—]\s*(\w+)\s*(\d{4})',
            r'(\d{1,2}\s*weeks?)\b',
            r'(summer\s*\d{4}|winter\s*\d{4}|spring\s*\d{4}|fall\s*\d{4})',
            r'(\d{1,2}\.\d{4})\s*[-–—]\s*(\d{1,2}\.\d{4})',
        ]
        
        self.role_keywords = [
            'software engineer', 'data scientist', 'data analyst', 'web developer',
            'frontend developer', 'backend developer', 'full stack developer',
            'machine learning engineer', 'ai engineer', 'devops engineer',
            'product manager', 'business analyst', 'research assistant',
            'marketing intern', 'finance intern', 'hr intern', 'sales intern',
            'designer', 'ux designer', 'ui designer', 'content creator',
            'quality assurance', 'qa engineer', 'test engineer', 'scrum master'
        ]
        
        self.company_suffixes = [
            'ltd', 'inc', 'corp', 'company', 'pvt', 'technologies', 'tech', 'systems', 
            'solutions', 'enterprises', 'group', 'corporation', 'llc', 'llp', 'co',
            'labs', 'works', 'soft', 'ware', 'services', 'consulting', 'digital',
            'media', 'studios', 'ventures', 'partners', 'holdings', 'international',
            'limited', 'incorporated', 'associates', 'industries', 'foundation'
        ]
        
        self.non_company_words = [
            'work', 'experience', 'internship', 'training', 'project', 'development', 
            'software', 'application', 'system', 'platform', 'engineer', 'developer', 
            'analyst', 'manager', 'lead', 'senior', 'junior', 'intern', 'trainee', 
            'apprentice', 'student', 'graduate', 'role', 'position', 'job', 'career',
            'skills', 'education', 'university', 'college', 'school', 'institute',
            'department', 'team', 'division', 'section', 'branch', 'office', 'summer',
            'winter', 'spring', 'fall', 'january', 'february', 'march', 'april',
            'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'
        ]
        
        self.month_names = list(calendar.month_name[1:]) + list(calendar.month_abbr[1:])
    
        self.nlp = None
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            print("spaCy English model not found. Run: python -m spacy download en_core_web_sm")
    
    def extract_internships(self, text):
        """Extract internship details from resume text"""
        internships = []
        lines = text.split('\n')

        section_start = None
        section_end = None
        section_headers = [
            'experience', 'work experience', 'professional experience', 'internships'
        ]
        for idx, line in enumerate(lines):
            l = line.lower().strip()
            if any(h in l for h in section_headers) and len(l.split()) <= 4:
                section_start = idx + 1
                break
        if section_start is None:
            section_lines = lines
        else:
            section_end = len(lines)
            for idx in range(section_start, len(lines)):
                l = lines[idx].lower().strip()
                if any(h in l for h in ['education', 'skills', 'projects', 'achievements', 'awards', 'certifications', 'languages', 'interests', 'hobbies']) and len(l.split()) <= 4:
                    section_end = idx
                    break
            section_lines = lines[section_start:section_end]

        i = 0
        while i < len(section_lines):
            line = section_lines[i].strip()
            if not line:
                i += 1
                continue
            
            if "," in line and any(kw in line.lower() for kw in self.internship_keywords):
                parts = [p.strip() for p in line.split(",", 1)]
                if len(parts) == 2:
                    role, company = parts
                    if self._is_valid_company_name(company) and any(kw in role.lower() for kw in self.internship_keywords):
                        internships.append(f"{company} - {role}")
                i += 1
                continue
            
            if " - " in line:
                parts = [p.strip() for p in line.split(" - ", 1)]
                if len(parts) == 2:
                    company, role = parts
                    if self._is_valid_company_name(company):
                        internships.append(f"{company} - {role}")
                i += 1
                continue
            
            if "," in line and any(kw in line.lower() for kw in self.internship_keywords + [role.lower() for role in self.role_keywords]):
                parts = [p.strip() for p in line.split(",", 1)]
                if len(parts) == 2:
                    role, company = parts
                    
                    if self._is_valid_company_name(company) and (any(kw in role.lower() for kw in self.internship_keywords)):
                        internships.append(f"{company} - {role}")
                i += 1
                continue

            if any(kw in line.lower() for kw in self.internship_keywords):
                role = line
          
                company = None
       
                if i > 0:
                    prev_line = section_lines[i-1].strip()
                    if prev_line and self._is_valid_company_name(prev_line):
                        company = prev_line
     
                if not company and i+1 < len(section_lines):
                    next_line = section_lines[i+1].strip()
                    if next_line and self._is_valid_company_name(next_line):
                        company = next_line
                if company:
                    internships.append(f"{company} - {role}")
                i += 1
                continue
            i += 1

        return self._clean_and_deduplicate_internships(internships)

    def _has_intern_keyword(self, text):
        """Check if text contains intern-related keywords using enhanced POS tagging"""
        text_lower = text.lower()
        
        # Use spaCy for precise POS tagging
        if self.nlp:
            doc = self.nlp(text)
            for token in doc:
                # Check for internship keywords as nouns, proper nouns, or adjectives
                if token.lemma_.lower() in self.internship_keywords and token.pos_ in {"NOUN", "PROPN", "ADJ"}:
                    # Additional context checking
                    if self._is_valid_intern_context(token, doc):
                        return True
            return False
        
        # Enhanced fallback regex if spaCy not available
        for keyword in self.internship_keywords:
            pattern = rf'\b{re.escape(keyword)}(?:s|ship|ships)?\b'
            if re.search(pattern, text_lower):
                # More comprehensive false match avoidance
                false_matches = ['internet', 'international', 'internal', 'interned', 
                               'determine', 'winter', 'printer', 'painter', 'entertainer']
                if not any(false_match in text_lower for false_match in false_matches):
                    return True
        return False
    
    def _is_valid_intern_context(self, token, doc):
        """Validate intern keyword context using POS tagging"""
        token_text = token.text.lower()
        
        # Exclude false matches
        false_matches = ['internet', 'international', 'internal', 'interned', 
                        'determine', 'winter', 'printer', 'painter', 'entertainer']
        if token_text in false_matches:
            return False
        
        # Check surrounding context for additional validation
        token_idx = token.i
        
        # Look for role-related words nearby
        for i in range(max(0, token_idx-3), min(len(doc), token_idx+4)):
            nearby_token = doc[i]
            if nearby_token.pos_ in {"NOUN", "PROPN", "ADJ"} and nearby_token.lemma_.lower() in self.role_keywords:
                return True
            # Check for company indicators
            if nearby_token.lemma_.lower() in self.company_suffixes:
                return True
        
        # Check if token is followed by typical role words
        if token_idx < len(doc) - 1:
            next_token = doc[token_idx + 1]
            if next_token.pos_ in {"NOUN", "PROPN"} and next_token.text.lower() not in self.non_company_words:
                return True
        
        return True
    
    def _clean_and_deduplicate_internships(self, internships):
        """Clean and deduplicate internships, keeping only the most informative entries"""
        if not internships:
            return []
        
        # First, filter out non-internship entries with enhanced validation
        valid_internships = []
        for internship in internships:
            if self._is_valid_internship_entry_enhanced(internship):
                company = self._extract_company_name_from_internship(internship)
                if company and self._is_valid_company_name(company):
                    valid_internships.append(internship)
        

        company_groups = {}
        for internship in valid_internships:
            company = self._extract_company_name_from_internship(internship)
            if company:
                company_lower = company.lower()
                if company_lower not in company_groups:
                    company_groups[company_lower] = []
                company_groups[company_lower].append(internship)
        
        # For each company, select the most informative internship entry
        unique_internships = []
        for company_lower, entries in company_groups.items():
            best_entry = self._select_best_internship_entry(entries)
            if best_entry:
                unique_internships.append(best_entry)
        return unique_internships

    def _is_valid_internship_entry_enhanced(self, entry):
        """Enhanced validation to filter out hackathons, certifications, and invalid entries"""
        entry_lower = entry.lower().strip()
        
        # Exclude hackathons and competitions
        hackathon_indicators = [
            'hackathon', 'hackfest', 'competition', 'contest', 'winner', 'prize', 'place',
            '1st', '2nd', '3rd', 'first', 'second', 'third', 'finalist', 'lakhs', 'lakh',
            'smart india hackathon', 'national hackathon', 'mit hackathon'
        ]
        if any(indicator in entry_lower for indicator in hackathon_indicators):
            return False
        
        # Exclude certifications and courses
        certification_indicators = [
            'certification', 'certificate', 'course', 'nptel', 'coursera', 'udemy',
            'edx', 'mooc', 'training program', 'workshop', 'python for data science'
        ]
        if any(indicator in entry_lower for indicator in certification_indicators):
            return False
        
        # Exclude standalone dates without context
        standalone_date_patterns = [
            r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}\s*-\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}$',
            r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}\s*-\s*present$',
            r'^\d{4}\s*-\s*\d{4}$',
            r'^\d{4}\s*-\s*present$'
        ]
        for pattern in standalone_date_patterns:
            if re.match(pattern, entry_lower):
                return False
        
        # Exclude domain/role titles without company context
        role_only_patterns = [
            r'^domain\s+head\s*-\s*.*$',
            r'^head\s+of\s+.*$',
            r'^coordinator\s*-\s*.*$',
            r'^volunteer\s*-\s*.*$',
            r'^member\s*-\s*.*$'
        ]
        for pattern in role_only_patterns:
            if re.match(pattern, entry_lower):
                return False
        
        # Must have either intern keyword or valid company-role structure
        has_intern_keyword = any(keyword in entry_lower for keyword in self.internship_keywords)
        has_company_role_structure = ' - ' in entry and self._extract_company_name_from_internship(entry)

        # If it has company-role structure, check if company is valid
        if has_company_role_structure:
            company = self._extract_company_name_from_internship(entry)
            if company and self._is_valid_company_name(company):
                return True

        # If it has intern keywords, additional validation
        if has_intern_keyword:
            # Must have meaningful length
            if len(entry.strip()) < 10:
                return False
            return True

        # NEW: Allow company-only internship if company is valid and not excluded
        company = entry.strip()
        if self._is_valid_company_name(company):
            return True

        return False
    
    def _extract_company_name_from_internship(self, internship):
        """Extract company name from an internship entry"""
        # Look for pattern: "CompanyName - Position"
        company_split = internship.split(' - ', 1)
        if len(company_split) > 1:
            return company_split[0].strip()
        
        # If no dash found, try extracting using existing method
        return self._extract_company_from_line(internship)
    
    def _select_best_internship_entry(self, entries):
        """Select the most informative entry from a list of internship entries for the same company"""
        if not entries:
            return None
            
        # Prioritize entries with:
        # 1. Both company name and role (contains a dash)
        # 2. Most descriptive role (most words after the dash)
        # 3. Contains duration info
        
        # First look for entries with company - role format
        entries_with_role = [e for e in entries if ' - ' in e]
        if entries_with_role:
            # Find the one with the most descriptive role
            best_entry = max(entries_with_role, 
                            key=lambda e: (len(e.split(' - ')[1].split()),  # Number of words in role
                                          len(e)))  # Total length as tie-breaker
            return best_entry
        
        # If no entries have roles, use the longest entry that has proper intern keywords
        valid_entries = [e for e in entries if self._has_intern_keyword(e)]
        if valid_entries:
            return max(valid_entries, key=len)
        
        return max(entries, key=len) if entries else None
    
    def _is_generic_phrase(self, text):
        """Check if the text is a generic phrase rather than a real internship"""
        generic_phrases = [
            'electricity or internet', 'internet connection', 'international students',
            'international programs', 'internal processes', 'internal systems',
            'and/or', 'either/or', 'as needed', 'on request', 'please see',
            'available', 'this is', 'i am', 'currently', 'requirements',
            'specifications', 'documentation', 'presentation', 'meeting'
        ]
        
        text_lower = text.lower().strip()
        
        # Check if it's a generic phrase
        for phrase in generic_phrases:
            if phrase in text_lower:
                return True
        
        # Check if it contains words that look like "intern" but aren't
        words_in_text = re.findall(r'\b\w*intern\w*\b', text_lower)
        non_intern_words = ['internet', 'international', 'internal', 'interned', 'determine', 'winter']
        
        # If we find intern-like words, check if any are actually intern-related
        if words_in_text:
            valid_intern_words = []
            for word in words_in_text:
                if not any(non_word in word for non_word in non_intern_words):
                    # Check if it's a valid intern word
                    if any(keyword in word for keyword in self.internship_keywords):
                        valid_intern_words.append(word)
            
            # If no valid intern words found, it's likely generic
            if not valid_intern_words:
                return True
                
        # Check if it looks like a sentence fragment rather than internship info
        words = text_lower.split()
        if len(words) >= 3:
            common_words = ['the', 'a', 'an', 'in', 'on', 'at', 'for', 'with', 'and', 'or', 'of', 'to', 'from']
            common_word_count = sum(1 for word in words[:4] if word in common_words)
            if common_word_count >= 2:
                return True  # Likely a sentence fragment
                
        return False
    
    def _extract_from_work_section(self, lines):
        """Extract internships from work experience section with enhanced accuracy"""
        internships = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            line_lower = line.lower()
            
            # Check if line contains internship keywords using enhanced matching
            if self._has_intern_keyword(line):
                internship_data = self._extract_complete_internship_info(lines, i)
                if internship_data:
                    internships.append(self._format_internship_entry(internship_data))
        
        return internships
    
    def _extract_complete_internship_info(self, lines, center_idx):
        """Extract complete internship information from surrounding context"""
        internship_info = {
            'company': None,
            'role': None,
            'duration': None,
            'confidence': 0
        }
        
        # Search in a wider context window
        search_range = range(max(0, center_idx-3), min(len(lines), center_idx+5))
        
        for j in search_range:
            current_line = lines[j].strip()
            if not current_line:
                continue
            
            # Extract company using enhanced method
            if not internship_info['company']:
                company = self._extract_company_from_line(current_line)
                if company:
                    internship_info['company'] = company
                    internship_info['confidence'] += 30
            
            # Extract role using enhanced method  
            if not internship_info['role']:
                role = self._extract_role_from_line(current_line)
                if role:
                    internship_info['role'] = role
                    internship_info['confidence'] += 25
            
            # Extract duration using enhanced method
            if not internship_info['duration']:
                duration = self._extract_duration(current_line)
                if duration:
                    internship_info['duration'] = duration
                    internship_info['confidence'] += 20
        
        # Validate extracted information
        if internship_info['company'] or internship_info['role']:
            if internship_info['confidence'] >= 30:  # Minimum confidence threshold
                return internship_info
        
        return None
    
    def _format_internship_entry(self, internship_data):
        """Format internship data into a standardized entry"""
        entry_parts = []
        

        if internship_data['company']:
            entry_parts.append(internship_data['company'])
     
        if internship_data['role']:
            if entry_parts:
                entry_parts.append(f" - {internship_data['role']}")
            else:
                entry_parts.append(internship_data['role'])
        
        # Add duration in parentheses
        if internship_data['duration']:
            entry_parts.append(f" ({internship_data['duration']})")
        
        return "".join(entry_parts)
    
    def _extract_from_organizations_section(self, lines):
        """Extract internships from organizations/organisations section with enhanced detection"""
        internships = []
        in_org_section = False
        current_org = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            line_lower = line.lower()
            
            if not line:
                continue
            
            # Enhanced section detection using POS tagging
            if self._is_organization_section_header(line):
                in_org_section = True
                continue
            elif self._is_different_section_header(line) and 'organization' not in line_lower:
                in_org_section = False
                current_org = None
                continue
            
            if in_org_section and line:
                if self._has_intern_keyword(line):
                    # Extract complete internship information
                    org_internship = self._extract_organization_internship_complete(lines, i, current_org)
                    if org_internship:
                        internships.append(org_internship)
                else:
                    # Check if this is an organization name
                    potential_org = self._extract_company_from_line(line)
                    if potential_org and self._is_valid_organization_name(potential_org, line_lower):
                        current_org = potential_org
        
        return internships
    
    def _is_organization_section_header(self, line):
        """Enhanced detection of organization section headers"""
        line_lower = line.lower().strip()
        org_keywords = ['organization', 'organisations', 'organizations', 'affiliations', 'memberships']
        
        # Check if it's a section header (short line with organization keywords)
        if any(keyword in line_lower for keyword in org_keywords) and len(line.split()) <= 3:
            return True
        
        return False
    
    def _is_different_section_header(self, line):
        """Check if line is a different section header"""
        section_headers = [
            'education', 'skills', 'projects', 'achievements', 'experience', 
            'certifications', 'awards', 'languages', 'interests', 'hobbies'
        ]
        line_lower = line.lower().strip()
        
        return any(header in line_lower for header in section_headers) and len(line.split()) <= 3
    
    def _extract_organization_internship_complete(self, lines, center_idx, current_org):
        """Extract complete internship information from organization context"""
        # Get role from current line
        role = self._extract_role_from_line(lines[center_idx])
        
        # Look for organization in nearby lines if not already set
        organization = current_org
        if not organization:
            organization = self._find_nearby_organization(lines, center_idx)
        
        # Look for duration
        duration = None
        for j in range(max(0, center_idx-2), min(len(lines), center_idx+3)):
            duration = self._extract_duration(lines[j])
            if duration:
                break
        
        # Format the internship entry
        if organization and role:
            entry = f"{organization} - {role}"
        elif organization:
            entry = f"{organization} - Intern"
        elif role:
            entry = role
        else:
            return None
        
        # Add duration if found
        if duration:
            entry += f" ({duration})"
        
        return entry
    
    def _is_valid_organization_name(self, org_name, line_lower):
        """Validate if the extracted text is a valid organization name"""
        # Skip lines that contain role-related keywords
        role_indicators = ['domain', 'head', 'chapter', 'student', 'member', 'volunteer', 'participant']
        
        if any(indicator in line_lower for indicator in role_indicators):
            return False
        
        return self._is_valid_company_name(org_name)
    
    def _find_nearby_organization(self, lines, current_idx):
        """Find organization name in nearby lines"""
        # Look backwards first (more common pattern)
        for offset in [-1, -2, 1, 2]:
            idx = current_idx + offset
            if 0 <= idx < len(lines):
                line = lines[idx].strip()
                if line:
                    org = self._extract_company_from_line(line)
                    if org and not self._has_intern_keyword(line):
                        return org
        return None

    def _extract_from_anywhere(self, lines):
        """Extract internships from anywhere in the text using enhanced pattern recognition"""
        internships = []
        
        # Enhanced role keywords with categories
        entry_level_roles = [
            'intern', 'internship', 'trainee', 'apprentice',
            'junior', 'graduate', 'fresher', 'entry level', 'assistant', 'associate'
        ]
        
        tech_roles = [
            'developer', 'engineer', 'analyst', 'tester', 'qa', 'support', 
            'consultant', 'programmer', 'administrator', 'designer'
        ]

        for i, line in enumerate(lines):
            line = line.strip()
            line_lower = line.lower()

            # Skip section headers and processed sections
            if self._should_skip_line_for_anywhere_extraction(line_lower):
                continue

            # Enhanced role detection using POS tagging
            if self._contains_relevant_role(line, entry_level_roles, tech_roles):
                internship_info = self._extract_enhanced_standalone_internship(lines, i)
                if internship_info and self._validate_standalone_internship(internship_info):
                    internships.append(internship_info)

        return internships
    
    def _should_skip_line_for_anywhere_extraction(self, line_lower):
        """Determine if line should be skipped in anywhere extraction"""
        skip_phrases = [
            'work experience', 'organization', 'organisations', 'organizations',
            'education', 'skills', 'projects', 'achievements', 'awards'
        ]
        return any(phrase in line_lower for phrase in skip_phrases)
    
    def _contains_relevant_role(self, line, entry_level_roles, tech_roles):
        """Check if line contains relevant role keywords using enhanced matching"""
        # Primary check with enhanced intern keyword detection
        if self._has_intern_keyword(line):
            return True
        
        # Secondary check for other entry-level roles
        line_lower = line.lower()
        
        # Use POS tagging for better role detection if available
        if self.nlp:
            doc = self.nlp(line)
            for token in doc:
                if token.pos_ in {"NOUN", "PROPN", "ADJ"}:
                    lemma = token.lemma_.lower()
                    if lemma in entry_level_roles[4:] + tech_roles:  # Skip intern keywords
                        return True
            return False
        
        # Fallback to regex for role detection
        for role in entry_level_roles[4:] + tech_roles:
            if re.search(rf'\b{re.escape(role)}\b', line_lower):
                return True
        
        return False
    
    def _extract_enhanced_standalone_internship(self, lines, center_idx):
        """Extract internship information with enhanced context analysis"""
        internship_data = {
            'company': None,
            'role': None,
            'duration': None,
            'source_line': lines[center_idx].strip()
        }
        
        # Enhanced context window
        context_range = range(max(0, center_idx-2), min(len(lines), center_idx+4))
        
        for j in context_range:
            current_line = lines[j].strip()
            if not current_line:
                continue
            
            # Try to extract each component
            if not internship_data['company']:
                company = self._extract_company_from_line(current_line)
                if company:
                    internship_data['company'] = company
            
            if not internship_data['role']:
                role = self._extract_role_from_line(current_line)
                if role:
                    internship_data['role'] = role
            
            if not internship_data['duration']:
                duration = self._extract_duration(current_line)
                if duration:
                    internship_data['duration'] = duration
        
        # Format the result
        return self._format_standalone_internship(internship_data)
    
    def _format_standalone_internship(self, internship_data):
        """Format standalone internship data into entry"""
        if not internship_data['company'] and not internship_data['role']:
            return None
        
        entry_parts = []
        
        if internship_data['company']:
            entry_parts.append(internship_data['company'])
        
        if internship_data['role']:
            if entry_parts:
                entry_parts.append(f" - {internship_data['role']}")
            else:
                entry_parts.append(internship_data['role'])
        
        if internship_data['duration']:
            entry_parts.append(f" ({internship_data['duration']})")
        
        return "".join(entry_parts) if entry_parts else None
    
    def _extract_organization_internship(self, lines, current_idx):
        """Extract internship details from organizations section"""
        current_line = lines[current_idx].strip()
        
        # Look for company name in current or nearby lines
        company = None
        role = None
        
        # Check current line and nearby lines for company and role
        for offset in range(-2, 3):
            idx = current_idx + offset
            if 0 <= idx < len(lines):
                line = lines[idx].strip()
                if not line:
                    continue
                
                # Extract role if it contains intern using precise matching
                if self._has_intern_keyword(line) and not role:
                    role = self._extract_role_from_line(line)
                
                # Extract company if it looks like a company name
                if not company:
                    potential_company = self._extract_company_from_line(line)
                    if potential_company and not self._has_intern_keyword(potential_company):
                        company = potential_company
        
        # Construct internship entry
        if company or role:
            if company and role:
                return f"{company} - {role}"
            elif company:
                return f"{company} - Intern"
            elif role:
                return role
        
        return None
    
    def _extract_standalone_internship(self, lines, current_idx):
        """Extract internship from standalone mentions - legacy method for compatibility"""
        # Redirect to enhanced method
        return self._extract_enhanced_standalone_internship(lines, current_idx)
    
    def _extract_role_from_line(self, line):
        """Extract role information from a line using enhanced POS tagging"""
        # Clean the line
        role = line.strip()
        
        # Remove bullet points and numbering
        role = re.sub(r'^[•\-*]\s*', '', role)
        role = re.sub(r'^\d+\.\s*', '', role)
        
        # Remove common prefixes
        role = re.sub(r'^(position|role|as|job):\s*', '', role, flags=re.IGNORECASE)
        
        # Use spaCy for better role extraction
        if self.nlp:
            extracted_role = self._extract_role_with_pos(role)
            if extracted_role:
                return extracted_role
        
        # Fallback to pattern-based extraction
        return self._extract_role_with_patterns(role)
    
    def _extract_role_with_pos(self, text):
        """Extract role using POS tagging for better accuracy"""
        doc = self.nlp(text)
        
        # Look for role patterns in the parsed text
        role_phrases = []
        current_phrase = []
        
        for token in doc:
            # Look for adjectives and nouns that could form role descriptions
            if token.pos_ in {"ADJ", "NOUN", "PROPN"} and token.is_alpha:
                # Skip common non-role words
                if token.lemma_.lower() not in self.non_company_words:
                    current_phrase.append(token.text)
                else:
                    if current_phrase:
                        role_phrases.append(" ".join(current_phrase))
                        current_phrase = []
            else:
                if current_phrase:
                    role_phrases.append(" ".join(current_phrase))
                    current_phrase = []
        
        # Add final phrase if exists
        if current_phrase:
            role_phrases.append(" ".join(current_phrase))
        
        # Find the best role phrase
        for phrase in role_phrases:
            if self._is_valid_role_phrase(phrase):
                return phrase.title()
        
        return None
    
    def _extract_role_with_patterns(self, role):
        """Extract role using regex patterns as fallback"""
        if self._has_intern_keyword(role):
            # Look for patterns like "Data Analytics Intern", "Software Development Intern", etc.
            intern_patterns = [
                r'([A-Za-z\s]+)\s+Intern(?:ship)?',
                r'Intern(?:ship)?\s*-?\s*([A-Za-z\s]+)',
                r'([A-Za-z\s]*Intern(?:ship)?[A-Za-z\s]*)',
            ]
            
            for pattern in intern_patterns:
                match = re.search(pattern, role, re.IGNORECASE)
                if match:
                    extracted_role = match.group(1).strip() if match.group(1) else match.group(0).strip()
                    if self._is_valid_role_phrase(extracted_role):
                        return extracted_role.title()
        
        # Look for specific role keywords
        for role_keyword in self.role_keywords:
            if role_keyword.lower() in role.lower():
                return role_keyword.title()
        
        return None
    
    def _is_valid_role_phrase(self, phrase):
        """Validate if the extracted phrase is a valid role description"""
        phrase_lower = phrase.lower().strip()
        
        # Must be at least 3 characters
        if len(phrase) < 3:
            return False
        
        # Should not be common false matches
        false_matches = ['internet', 'international', 'internal', 'interned', 'determine', 'winter']
        if any(false_match in phrase_lower for false_match in false_matches):
            return False
        
        # Should contain meaningful role indicators
        role_indicators = ['intern', 'engineer', 'developer', 'analyst', 'designer', 'manager', 
                          'assistant', 'specialist', 'coordinator', 'associate', 'trainee']
        
        # Either contains role indicators or is from predefined role keywords
        has_role_indicator = any(indicator in phrase_lower for indicator in role_indicators)
        is_predefined_role = any(role.lower() in phrase_lower for role in self.role_keywords)
        
        return has_role_indicator or is_predefined_role
    
    def _is_section_header(self, line):
        """Check if line is a section header"""
        section_headers = [
            'education', 'experience', 'skills', 'projects', 'achievements',
            'certifications', 'awards', 'organizations', 'organisations',
            'languages', 'interests', 'hobbies', 'references'
        ]
        
        return any(header in line.lower() for header in section_headers) and len(line.split()) <= 3

    def _extract_company_from_line(self, line):
        """Extract company name from a line with enhanced POS tagging accuracy"""
        # Skip lines that are obviously not company names
        line_lower = line.lower()
        if any(skip in line_lower for skip in ['work experience', 'internship projects', 'trainee position', 'apprentice role']):
            return None

        # Enhanced spaCy-based extraction using entity recognition and POS tagging
        if self.nlp:
            doc = self.nlp(line)
            
            # First try: Named Entity Recognition for organizations
            for ent in doc.ents:
                if ent.label_ in {"ORG", "PERSON"} and ent.label_ == "ORG":
                    if self._is_valid_company_name(ent.text):
                        return ent.text.strip()
            
            # Second try: Look for proper nouns that could be company names
            company_candidates = []
            current_company = []
            
            for i, token in enumerate(doc):
                # Collect sequences of proper nouns, nouns that could be company names
                if token.pos_ in {"PROPN", "NOUN"} and token.is_alpha:
                    # Skip if it's an internship keyword or non-company word
                    if token.lemma_.lower() not in self.internship_keywords and token.lemma_.lower() not in self.non_company_words:
                        current_company.append(token.text)
                    else:
                        # If we hit an internship keyword, finalize current company if it exists
                        if current_company and token.lemma_.lower() in self.internship_keywords:
                            company_candidates.append(" ".join(current_company))
                        current_company = []
                else:
                    # End of potential company name sequence
                    if current_company:
                        company_candidates.append(" ".join(current_company))
                        current_company = []
            
            # Add any remaining company name
            if current_company:
                company_candidates.append(" ".join(current_company))
            
            # Find the best company candidate
            for candidate in company_candidates:
                if self._is_valid_company_name(candidate) and len(candidate) >= 3:
                    return candidate.strip()
            
            # Third try: Look for capitalized words that follow company patterns
            return self._extract_company_with_patterns(doc)
        # Fallback to enhanced regex-based extraction
        return self._extract_company_with_regex_fallback(line)
    
    def _extract_company_with_patterns(self, doc):
        """Extract company using POS-based patterns"""
        # Look for sequences that could be company names
        for i in range(len(doc)):
            token = doc[i]
            if token.pos_ == "PROPN" and token.is_alpha:
                # Check if followed by company suffixes
                company_phrase = [token.text]
                j = i + 1
                while j < len(doc) and (doc[j].pos_ in {"PROPN", "NOUN"} or doc[j].lemma_.lower() in self.company_suffixes):
                    company_phrase.append(doc[j].text)
                    j += 1
                
                company_candidate = " ".join(company_phrase).strip()
                if len(company_candidate) >= 3 and self._is_valid_company_name(company_candidate):
                    return company_candidate
        return None
    
    def _extract_company_with_regex_fallback(self, line):
        """Fallback regex-based company extraction"""
        company_line = line
        # Remove internship keywords
        for keyword in self.internship_keywords:
            company_line = re.sub(rf'\b{re.escape(keyword)}(?:s|ship|ships)?\b', '', company_line, flags=re.IGNORECASE)
        
        # Remove role words
        role_words = ['developer', 'engineer', 'analyst', 'position', 'role', 'job', 'at', 'in', 'with', 'for']
        for word in role_words:
            company_line = re.sub(rf'\b{re.escape(word)}\b', '', company_line, flags=re.IGNORECASE)
        
        company_line = company_line.strip(' |-•()[]')
        if len(company_line) < 2:
            return None
            
        company_patterns = [
            # Companies with common suffixes
            rf'\b([A-Z][a-zA-Z\s&.-]+(?:{"|".join(self.company_suffixes)}))\b',
            # Multi-word capitalized company names 
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b',
            # Single word companies with specific suffixes
            rf'\b([A-Z][a-z]{{3,}}(?:{"|".join(self.company_suffixes[:10])}))\b',
            # Well-known tech companies
            r'\b(Google|Microsoft|Amazon|Apple|Meta|Facebook|Netflix|Tesla|Uber|Spotify|Adobe|Oracle|IBM|Intel|NVIDIA|Salesforce|GitHub|GitLab|Atlassian|Shopify|Stripe|PayPal|LinkedIn|Twitter|TCS|Infosys|Wipro|HCL|Accenture|Capgemini|Cognizant|Tech Mahindra)\b'
        ]

        # Check patterns in order of preference
        for pattern in company_patterns:
            matches = re.findall(pattern, company_line, re.IGNORECASE)
            for match in matches:
                company = match.strip() if isinstance(match, str) else match
                # Additional validation
                if self._is_valid_company_name(company):
                    return company

        return None
    


    
    def _is_valid_company_name(self, company):
        """Validate if the extracted text is a valid company name"""
        company_lower = company.lower().strip()
        
        # Reject common non-company words
        invalid_companies = [
            'work experience', 'experience', 'internship', 'training', 'project',
            'projects', 'development', 'software', 'application', 'system', 'platform',
            'engineer', 'developer', 'analyst', 'manager', 'lead', 'senior',
            'junior', 'intern', 'trainee', 'apprentice', 'student', 'graduate',
            'role', 'position', 'job', 'career', 'skills', 'education', 'school',
            'college', 'institute', 'department', 'team', 'division', 'section',
            'branch', 'office', 'summer', 'winter', 'spring', 'fall', 'hackathon',
            'dam', 'chennai'
        ]
        # Remove generic city names and generic project/competition words
        city_names = [
            'chennai', 'bangalore', 'mumbai', 'delhi', 'pune', 'hyderabad', 'kolkata', 'ahmedabad', 'surat', 'jaipur', 'lucknow', 'kanpur', 'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'patna', 'vadodara', 'ghaziabad', 'ludhiana', 'agra', 'nashik', 'faridabad', 'meerut', 'rajkot', 'kalyan', 'vasai', 'varanasi', 'srinagar', 'aurangabad', 'dhanbad', 'amritsar', 'navi mumbai', 'allahabad', 'howrah', 'ranchi', 'gwalior', 'jabalpur', 'coimbatore', 'vijayawada', 'jodhpur', 'madurai', 'raipur', 'kota', 'guwahati', 'chandigarh', 'solapur', 'hubli', 'mysore', 'tiruchirappalli', 'bareilly', 'aligarh', 'tiruppur', 'moradabad', 'jalandhar', 'bhubaneswar', 'salem', 'warangal', 'guntur', 'bhiwandi', 'saharanpur', 'gorakhpur', 'bikaner', 'amravati', 'noida', 'jamshedpur', 'bhilai', 'cuttack', 'kochi', 'udaipur', 'bhavnagar', 'dehradun', 'asansol', 'nellore', 'ajmer', 'kolhapur', 'akola', 'gulbarga', 'jamnagar', 'bokaro', 'belgaum', 'satna', 'kurnool', 'ulhasnagar', 'malegaon', 'mangalore', 'gaya', 'tirunelveli', 'rohtak', 'panipat', 'durgapur', 'kozhikode'
        ]
        generic_words = [
            'hackathon', 'competition', 'contest', 'event', 'projects', 'project', 'dam'
        ]
        # Remove if company is a city name or generic word
        if company_lower in city_names or company_lower in generic_words:
            return False

        if company_lower in invalid_companies:
            return False
        
        # Must be at least 3 characters
        if len(company) < 3:
            return False
        
        # Should contain alphabetic characters
        if not any(c.isalpha() for c in company):
            return False
        
        # Should not be all uppercase and a generic word
        if company.isupper() and company_lower in invalid_companies:
            return False

        # Should not be all uppercase and a generic word
        if company.isupper() and company_lower in generic_words:
            return False

        # Should not be all uppercase and a city name
        if company.isupper() and company_lower in city_names:
            return False

        return True
    
    def _is_date_or_duration_line(self, line):
        """Check if line contains only dates or duration info"""
        line_lower = line.lower().strip()
        
        # Date patterns
        date_patterns = [
            r'^\d{1,2}/\d{4}\s*-\s*\d{1,2}/\d{4}$',  # MM/YYYY - MM/YYYY
            r'^\d{4}\s*-\s*\d{4}$',                    # YYYY - YYYY
            r'^\w{3}\s+\d{4}\s*-\s*\w{3}\s+\d{4}$',   # Mon YYYY - Mon YYYY
            r'^\(\d{2}/\d{4}\s*-\s*\d{2}/\d{4}\)$',   # (MM/YYYY - MM/YYYY)
            r'^\d{1,2}\s*months?$',                     # X months
        ]
        
        return any(re.match(pattern, line_lower) for pattern in date_patterns)
    
    def _extract_duration(self, text):
        """Extract duration from text with enhanced pattern matching"""
        text_lower = text.lower().strip()
        
        # Enhanced duration extraction with POS tagging if available
        if self.nlp:
            duration = self._extract_duration_with_pos(text)
            if duration:
                return duration
        
        # Fallback to pattern matching
        for pattern in self.duration_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                duration_text = match.group(0)
                # Validate and clean duration
                cleaned_duration = self._clean_duration_text(duration_text)
                if cleaned_duration:
                    return cleaned_duration
        return None
    
    def _extract_duration_with_pos(self, text):
        """Extract duration using POS tagging for better accuracy"""
        doc = self.nlp(text)
        
        # Look for duration patterns in the parsed text
        for i, token in enumerate(doc):
            # Look for numbers followed by time units
            if token.like_num:
                if i + 1 < len(doc):
                    next_token = doc[i + 1]
                    time_units = ['month', 'months', 'week', 'weeks', 'year', 'years', 'mon', 'mos']
                    if next_token.lemma_.lower() in time_units:
                        return f"{token.text} {next_token.text}"
            
            # Look for month names followed by years
            if token.text.lower() in [month.lower() for month in self.month_names]:
                if i + 1 < len(doc) and doc[i + 1].like_num and len(doc[i + 1].text) == 4:
                    # Look for end date
                    for j in range(i + 2, min(i + 6, len(doc))):
                        if doc[j].text.lower() in [month.lower() for month in self.month_names]:
                            if j + 1 < len(doc) and doc[j + 1].like_num and len(doc[j + 1].text) == 4:
                                return f"{token.text} {doc[i + 1].text} - {doc[j].text} {doc[j + 1].text}"
        
        return None
    
    def _clean_duration_text(self, duration_text):
        """Clean and validate duration text"""
        duration_text = duration_text.strip()
        
        # Remove parentheses if present
        duration_text = re.sub(r'^[(\[]|[)\]]$', '', duration_text)
        
        # Validate that it's a meaningful duration
        if len(duration_text) < 3:
            return None
            
        # Check if it contains valid duration indicators
        valid_indicators = ['month', 'week', 'year', 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                           'jul', 'aug', 'sep', 'oct', 'nov', 'dec', '20', '19']
        
        if any(indicator in duration_text.lower() for indicator in valid_indicators):
            return duration_text
            
        return None
    
    def _clean_project_title(self, title):
        """Clean and extract main project title"""
        # Remove bullet points and common prefixes
        title = re.sub(r'^[•\-*]\s*', '', title)
        title = re.sub(r'^\d+\.\s*', '', title)
        
        # Remove links and extra formatting
        title = re.sub(r'\[\s*link\s*\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'https?://[^\s]+', '', title)
        
        # Extract the main title (usually the first sentence or before colon)
        if ':' in title:
            title = title.split(':')[0]
        
        # Split by periods but keep the main sentence
        sentences = title.split('.')
        if sentences:
            title = sentences[0]
        
        return title.strip()
    
    def extract_internship_projects(self, text):
        """Extract projects specifically done during internships using enhanced context analysis"""
        projects = []
        lines = text.split('\n')
        
        # Find Experience/Internship section
        section_start = None
        section_end = None
        section_headers = [
            'experience', 'work experience', 'professional experience', 'internships'
        ]
        for idx, line in enumerate(lines):
            l = line.lower().strip()
            if any(h in l for h in section_headers) and len(l.split()) <= 4:
                section_start = idx + 1
                break
        if section_start is None:
            section_lines = lines
        else:
            section_end = len(lines)
            for idx in range(section_start, len(lines)):
                l = lines[idx].lower().strip()
                if any(h in l for h in ['education', 'skills', 'projects', 'achievements', 'awards', 'certifications', 'languages', 'interests', 'hobbies']) and len(l.split()) <= 4:
                    section_end = idx
                    break
            section_lines = lines[section_start:section_end]

        # For each internship, find its block and collect following description lines as projects
        i = 0
        while i < len(section_lines):
            line = section_lines[i].strip()
            if not line:
                i += 1
                continue
            
            # NEW PATTERN: COMPANY - ROLE (DATE) format (e.g., "Nexilo Tech - Java Developer (03/2024 - 05/2024)")
            company_role_date_pattern = r'^(.+?)\s*-\s*(.+?)\s*\(([^)]+)\)\s*$'
            match = re.match(company_role_date_pattern, line)
            if match:
                company = match.group(1).strip()
                role = match.group(2).strip()
                if self._is_valid_company_name(company):
                    # Collect following project description lines
                    j = i + 1
                    while j < len(section_lines):
                        proj_line = section_lines[j].strip()
                        if not proj_line:
                            j += 1
                            continue
                        # Stop if we hit another internship or section
                        if (any(kw in proj_line.lower() for kw in self.internship_keywords) and 
                            any(suffix in proj_line.lower() for suffix in self.company_suffixes)) or \
                           self._is_section_header(proj_line) or \
                           re.match(company_role_date_pattern, proj_line):
                            break
                        # Collect project description lines
                        if len(proj_line) > 15 and not self._is_date_or_duration_line(proj_line):
                            projects.append(proj_line)
                        j += 1
                    i = j
                    continue
            
            # NEW PATTERN: ROLE, COMPANY (e.g., "Software Development Intern, ZakApps pvt. ltd.")
            if "," in line and any(kw in line.lower() for kw in self.internship_keywords):
                parts = [p.strip() for p in line.split(",", 1)]
                if len(parts) == 2:
                    role, company = parts
                    if self._is_valid_company_name(company) and any(kw in role.lower() for kw in self.internship_keywords):
                        # Skip date line and collect project descriptions
                        j = i + 1
                        # Skip date line if present
                        if j < len(section_lines) and self._is_date_or_duration_line(section_lines[j]):
                            j += 1
                        # Collect following project description lines
                        while j < len(section_lines):
                            proj_line = section_lines[j].strip()
                            if not proj_line:
                                j += 1
                                continue
                            # Stop if we hit another internship or section
                            if (any(kw in proj_line.lower() for kw in self.internship_keywords) and 
                                any(suffix in proj_line.lower() for suffix in self.company_suffixes)) or \
                               self._is_section_header(proj_line):
                                break
                            # Collect project description lines
                            if len(proj_line) > 15:
                                projects.append(proj_line)
                            j += 1
                        i = j
                        continue

            # If line looks like an internship role
            if any(kw in line.lower() for kw in self.internship_keywords):
                # Look for company in previous or next non-empty line
                company = None
                if i > 0:
                    prev_line = section_lines[i-1].strip()
                    if prev_line and self._is_valid_company_name(prev_line):
                        company = prev_line.lower()
                if not company and i+1 < len(section_lines):
                    next_line = section_lines[i+1].strip()
                    if next_line and self._is_valid_company_name(next_line):
                        company = next_line.lower()
                # Collect following bullet/indented lines as projects
                j = i + 1
                while j < len(section_lines):
                    proj_line = section_lines[j]
                    if not proj_line.strip():
                        break
                    if proj_line.lstrip().startswith(('-', '*', '•')) or (len(proj_line) - len(proj_line.lstrip()) >= 2):
                        project = proj_line.lstrip('-*• ').strip()
                        if len(project) > 10:
                            projects.append(project)
                    else:
                        # If line contains "interning" or "intern" and company name, treat as project
                        if company and any(kw in proj_line.lower() for kw in self.internship_keywords) and company in proj_line.lower():
                            projects.append(proj_line.strip())
                    j += 1
                i += 1
                continue
            i += 1
        return projects
    
    def extract_comprehensive_internship_data(self, text):
        """Extract comprehensive internship data including projects"""
        result = {
            'internships': self.extract_internships(text),
            'internship_projects': self.extract_internship_projects(text),
            'summary': {}
        }
        
        # Add summary statistics
        result['summary'] = {
            'total_internships': len(result['internships']),
            'total_projects': len(result['internship_projects']),
            'companies': list(set([
                internship.split(' - ')[0] if ' - ' in internship else internship.split(' (')[0]
                for internship in result['internships']
            ])),
            'roles': list(set([
                internship.split(' - ')[1].split(' (')[0] if ' - ' in internship 
                else 'Intern' for internship in result['internships'] if ' - ' in internship
            ]))
        }
        
        return result
        """Extract detailed project information for internship projects"""
        project_text = lines[start_idx].strip()
        
        # Clean up bullet points and numbering
        project_text = re.sub(r'^[•\-*]\s*', '', project_text)
        project_text = re.sub(r'^\d+\.\s*', '', project_text)
        
        # Add context from internship if helpful
        context_info = ""
        if internship_context and " - " in internship_context:
            company = internship_context.split(" - ")[0].strip()
            context_info = f" (at {company})"
        
        # Get complete project description
        complete_description = self._build_complete_project_description(lines, start_idx)
        
        # Extract meaningful project title with enhanced patterns
        if self.nlp:
            project_title = self._extract_project_title_with_nlp(complete_description)
        else:
            project_title = self._extract_meaningful_title(complete_description)
        
        if project_title:
            return project_title + context_info
        
        return None
    
    def _build_complete_project_description(self, lines, start_idx):
        """Build complete project description from multiple lines"""
        description_lines = [lines[start_idx].strip()]
        
        # Look ahead for continuation lines
        for next_idx in range(start_idx + 1, min(start_idx + 4, len(lines))):
            next_line = lines[next_idx].strip()
            
            # Stop conditions
            if not next_line:
                break
            if self._is_new_project_or_section(next_line):
                break
            if self._is_date_or_duration_line(next_line):
                break
                
            # Add continuation line
            if len(next_line) > 10 and not next_line.startswith('•'):
                description_lines.append(next_line)
            
            # Stop if we have enough content
            if len(" ".join(description_lines)) > 150:
                break
        
        return " ".join(description_lines)
    
    def _extract_project_title_with_nlp(self, text):
        """Extract project title using NLP for better accuracy"""
        doc = self.nlp(text)
        
        # Look for noun phrases that could be project titles
        project_phrases = []
        
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            # Skip if it's just common words or very short
            if len(chunk_text) > 10 and not chunk_text.lower().startswith(('a ', 'an ', 'the ')):
                # Check if it contains technical terms
                if any(token.lemma_ in ['application', 'system', 'platform', 'website', 'tool', 'dashboard'] 
                       for token in chunk):
                    project_phrases.append(chunk_text)
        
        # Return the most descriptive phrase
        if project_phrases:
            return max(project_phrases, key=len)
        
        # Fallback to pattern-based extraction
        return self._extract_meaningful_title(text)
    
    def _is_new_project_or_section(self, line):
        """Check if line indicates start of new project or section"""
        line_lower = line.lower()
        new_project_indicators = [
            'built', 'developed', 'created', 'designed', 'implemented',
            'education', 'skills', 'achievements', 'awards'
        ]
        return any(indicator in line_lower for indicator in new_project_indicators)
    
    def _filter_and_deduplicate_projects(self, projects):
        """Enhanced filtering and deduplication of projects"""
        if not projects:
            return []
        
        # Remove projects that are too generic or short
        filtered_projects = []
        for project in projects:
            if len(project) >= 25 and not self._is_generic_project_description(project):
                filtered_projects.append(project)
        
        # Enhanced deduplication
        unique_projects = []
        for project in filtered_projects:
            if not any(self._are_similar_projects(project, existing) for existing in unique_projects):
                unique_projects.append(project)
        
        # Sort by descriptiveness (length and technical content)
        unique_projects.sort(key=lambda p: self._calculate_project_score(p), reverse=True)
        
        return unique_projects
    
    def _is_generic_project_description(self, description):
        """Check if project description is too generic"""
        generic_phrases = [
            'worked on various', 'assisted with', 'helped develop', 'participated in',
            'was responsible for', 'contributed to team', 'supported the team'
        ]
        
        description_lower = description.lower()
        return any(phrase in description_lower for phrase in generic_phrases)
    
    def _calculate_project_score(self, project):
        """Calculate a score for project based on descriptiveness and technical content"""
        score = len(project)  # Base score from length
        
        # Bonus for technical terms
        technical_terms = [
            'application', 'system', 'platform', 'api', 'database', 'algorithm',
            'machine learning', 'ai', 'web', 'mobile', 'frontend', 'backend'
        ]
        
        project_lower = project.lower()
        tech_bonus = sum(10 for term in technical_terms if term in project_lower)
        
        return score + tech_bonus
    
    def _extract_complete_project_title(self, lines, start_idx):
        """Extract complete project title from multiple lines if needed"""
        project_text = lines[start_idx].strip()
        
        # Clean up bullet points and numbering
        project_text = re.sub(r'^[•\-*]\s*', '', project_text)
        project_text = re.sub(r'^\d+\.\s*', '', project_text)
        
        # Get the complete project description by reading multiple lines
        current_line = project_text
        
        # Continue reading lines until we get a complete thought
        for next_idx in range(start_idx + 1, min(start_idx + 5, len(lines))):
            next_line = lines[next_idx].strip()
            
            # Stop if we hit another project start
            if any(keyword in next_line.lower() for keyword in ['built', 'developed', 'created', 'designed', 'implemented']):
                break
            
            # Stop if we hit a section header
            if any(section in next_line.lower() for section in ['education', 'skills', 'achievements', 'personal projects']):
                break
            
            # Stop if we hit a new company/position
            if any(indicator in next_line for indicator in ['Ltd', 'Inc', 'Corp', 'Company', 'Pvt', 'Tech', 'Technologies']):
                break
            
            # Continue if the line is part of the description
            if next_line and not re.match(r'^\([0-9/\s-]+\)$', next_line):  # Skip date lines
                current_line += " " + next_line
            
            # Stop if we have enough content (more than 100 characters)
            if len(current_line) > 100:
                break
        
        # Extract the main project title
        project_title = self._extract_meaningful_title(current_line)
        return project_title if project_title and len(project_title) > 20 else None
    
    def _extract_meaningful_title(self, text):
        """Extract meaningful project title from text"""
        # Clean up the text first
        text = text.strip()
        
        # Remove common action words at the beginning
        text = re.sub(r'^(developed|built|created|designed|implemented|worked on)\s+', '', text, flags=re.IGNORECASE)
        
        # Look for complete project descriptions
        project_patterns = [
            # Pattern: "a suite of X applications (details)"
            r'a\s+suite\s+of\s+([^.]+?applications?[^.]*?)(?:\s+that|\s+which|\.|$)',
            # Pattern: "a X system/platform/application that does Y"
            r'a\s+([^.]+?(?:system|platform|application|tool|app|software|solution)[^.]*?)(?:\s+that|\s+which|\.|$)',
            # Pattern: "ProjectName - description"
            r'^([A-Z][A-Za-z\s\-]+?)\s*[-–]\s*([^.]+)',
            # Pattern: Applications in parentheses
            r'([^(]+)\s*\(([^)]+)\)',
            # Pattern: Complete sentence ending with improvement metrics
            r'^([^.]+?(?:system|platform|application|tool|app|software|solution)[^.]*?)(?:\s+(?:that|which)\s+improved|by\s+\d+%|\.|$)',
            # Pattern: Just take the complete first sentence
            r'^([^.!?]+)',
        ]
        
        for i, pattern in enumerate(project_patterns):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if i == 0:  
                    title = f"Suite of {match.group(1)}"
                elif i == 3: 
                    main_part = match.group(1).strip()
                    details = match.group(2).strip()
                    title = f"{main_part} ({details})"
                elif i == 2:  # Dash pattern
                    title = f"{match.group(1)} - {match.group(2)}"
                else:
                    title = match.group(1).strip()
                
                # Clean up the title
                title = self._clean_extracted_title(title)
                if len(title) > 15:
                    return title
        
        return None
    
    def _clean_extracted_title(self, title):
        """Clean and format the extracted title"""
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Remove leading articles if title starts with them
        title = re.sub(r'^(a|an|the)\s+', '', title, flags=re.IGNORECASE)
        
        # Remove trailing improvement metrics
        title = re.sub(r'\s+(?:that|which)\s+improved.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+by\s+\d+%.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+through.*$', '', title, flags=re.IGNORECASE)
        
        if title.isupper():
            title = title.title()
        elif title.islower():
            title = title.capitalize()
        
        # Remove trailing prepositions and conjunctions
        title = re.sub(r'\s+(for|with|using|in|on|at|and|or|by)$', '', title, flags=re.IGNORECASE)
        
        return title.strip()

    def _are_similar_projects(self, project1, project2):
        """Check if two projects are similar to avoid duplicates"""
        # Simple similarity check based on common words
        words1 = set(project1.lower().split())
        words2 = set(project2.lower().split())
        
        # Remove common words
        common_words = {'a', 'an', 'the', 'and', 'or', 'but', 'with', 'using', 'for', 'to', 'of', 'in', 'on'}
        words1 -= common_words
        words2 -= common_words
        
        # If more than 50% words overlap, consider similar
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        overlap = len(words1.intersection(words2))
        similarity = overlap / min(len(words1), len(words2))
        
        return similarity > 0.5
    
    def extract_comprehensive_internship_data(self, text):
        """Extract comprehensive internship data including projects"""
        result = {
            'internships': self.extract_internships(text),
            'internship_projects': self.extract_internship_projects(text),
            'summary': {}
        }
        
        result['summary'] = {
            'total_internships': len(result['internships']),
            'total_projects': len(result['internship_projects']),
            'companies': list(set([
                internship.split(' - ')[0] if ' - ' in internship else internship.split(' (')[0]
                for internship in result['internships']
            ])),
            'roles': list(set([
                internship.split(' - ')[1].split(' (')[0] if ' - ' in internship 
                else 'Intern' for internship in result['internships'] if ' - ' in internship
            ]))
        }
        
        return result

