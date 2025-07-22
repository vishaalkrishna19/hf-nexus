import re
import spacy
from .details_extractor import DetailsExtractor
from .linkedin_extractor import LinkedInExtractor

class NameExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except IOError:
            print("Please install the English model: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        self.details_extractor = DetailsExtractor()
        self.linkedin_extractor = LinkedInExtractor()
    
    def extract_name(self, text, filename=None):
        """Extract name from resume text with multiple strategies"""
        # Clean the text
        text = text.strip()
        lines = text.split('\n')
        
        print(f"Starting name extraction with filename: {filename}")
        
        filename_name = self._extract_name_from_filename(filename) if filename else None
        print(f"Filename strategy result: {filename_name}")
        
        email_name = self._extract_name_from_email(text)
        print(f"Email strategy result: {email_name}")
        
        github_name = self._extract_name_from_github(text)
        print(f"GitHub strategy result: {github_name}")
        
        linkedin_name = self._extract_name_from_linkedin(text)
        print(f"LinkedIn strategy result: {linkedin_name}")
        
        header_name = self._extract_name_from_header(lines)
        print(f"Header strategy result: {header_name}")
        
        nlp_name = self._extract_name_using_nlp(lines) if self.nlp else None
        print(f"NLP strategy result: {nlp_name}")
        
        priority_candidates = [filename_name, email_name, github_name, linkedin_name]
        secondary_candidates = [header_name, nlp_name]
        
        print(f"Priority candidates: {priority_candidates}")
        print(f"Secondary candidates: {secondary_candidates}")
        
        # First check high-priority sources - prefer complete names
        complete_name_candidates = []
        single_name_candidates = []
        
        for candidate in priority_candidates:
            if candidate and self._is_valid_name(candidate) and not self._is_institution_name(candidate):
                if len(candidate.split()) >= 2:
                    complete_name_candidates.append(candidate)
                else:
                    single_name_candidates.append(candidate)
        
        # Calculate frequency for all candidates
        all_candidates = priority_candidates + secondary_candidates
        name_frequency = {}
        for candidate in all_candidates:
            if candidate:
                name_frequency[candidate] = name_frequency.get(candidate, 0) + 1
        
        print(f"All name frequency count: {name_frequency}")
        
        if complete_name_candidates:
            complete_name_candidates.sort(key=lambda x: (
                name_frequency.get(x, 0),  
                self._calculate_name_naturalness_score(x)  
            ), reverse=True)
            
            best_complete = complete_name_candidates[0]
            best_complete_score = self._calculate_name_naturalness_score(best_complete)
            best_complete_frequency = name_frequency.get(best_complete, 0)
            
            if (best_complete_score > 0 or best_complete_frequency >= 2):
                print(f"Name extracted from high-priority source (complete): {best_complete} (frequency: {best_complete_frequency}, score: {best_complete_score})")
                return best_complete
            else:
                print(f"Rejecting complete name '{best_complete}' due to negative naturalness score and low frequency")
        
        if single_name_candidates:
            single_name_candidates.sort(key=lambda x: (
                name_frequency.get(x, 0),  
                self._calculate_name_naturalness_score(x), 
                len(x) 
            ), reverse=True)
            
            best_single = single_name_candidates[0]
            best_single_frequency = name_frequency.get(best_single, 0)
            
            # Check if there's a complete name in secondary candidates with same or higher frequency
            for candidate in secondary_candidates:
                if candidate and self._is_valid_name(candidate) and not self._is_institution_name(candidate):
                    if len(candidate.split()) >= 2:
                        candidate_frequency = name_frequency.get(candidate, 0)
                        if candidate_frequency >= best_single_frequency and self._calculate_name_naturalness_score(candidate) > 0:
                            print(f"Name extracted from secondary source (complete, same/higher frequency): {candidate} (frequency: {candidate_frequency})")
                            return candidate
            
            if (self._calculate_name_naturalness_score(best_single) > 0 or 
                name_frequency.get(best_single, 0) > 1):
                print(f"Name extracted from high-priority source (single): {best_single} (frequency: {name_frequency.get(best_single, 0)})")
                return best_single
            else:
                print(f"Best single name '{best_single}' has poor naturalness score and low frequency")

        for candidate in secondary_candidates:
            if candidate and self._is_valid_name(candidate) and not self._is_institution_name(candidate):
                if len(candidate.split()) >= 2:
                    if self._calculate_name_naturalness_score(candidate) > 0:
                        print(f"Name extracted from secondary source (complete): {candidate}")
                        return candidate
                    else:
                        print(f"Rejecting secondary candidate '{candidate}' due to poor naturalness score")
        
        if single_name_candidates:
            best_name = single_name_candidates[0]
            print(f"Falling back to single name from priority source: {best_name}")
            return best_name
        
        for candidate in secondary_candidates:
            if candidate and self._is_valid_name(candidate) and not self._is_institution_name(candidate):
                if self._calculate_name_naturalness_score(candidate) > 0:
                    print(f"Name extracted from secondary source (single): {candidate}")
                    return candidate

        print("No valid name found")
        return None
    
    def _extract_name_from_filename(self, filename):
        """Extract name from filename"""
        if not filename:
            return None
        
        print(f"Analyzing filename: {filename}")
        
        # Remove file extension first
        name = re.sub(r'\.(pdf|docx?|txt)$', '', filename, flags=re.IGNORECASE)
        
        name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        
        non_name_words = [
            'resume', 'cv', 'curriculum', 'vitae', 'updated?', 'final', 'latest', 'new',
            'hardcopy', 'soft', 'copy', 'document', 'doc', 'file', 'scan', 'scanned',
            'original', 'origninal', 'modified', 'edited', 'version', 'v\d+', 'draft', 'backup',
            'temp', 'temporary', 'old', 'archive', 'archived', 'submission', 'upload',
            'download', 'print', 'printed', 'digital', 'format', 'formatted'
        ]
        
        pattern = r'\b(' + '|'.join(non_name_words) + r')\b'
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        name = name.lower()
        name = re.sub(r'[_-]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        print(f"Processed filename: '{name}'")
        
        words = name.split()
        valid_words = []
        
        invalid_patterns = [
            r'^[a-z]{1,3}$',  # Very short words like "hss"
            r'^\d+$',          # Pure numbers
            r'^[a-z]+\d+$',    # Words ending with numbers
            r'^\(\d+\)$',      # Parentheses with numbers like "(1)"
        ]
        
        for word in words:
            # FIXED: Initialize is_valid at the start of the loop
            is_valid = False
            
            if len(word) >= 2 and word.isalpha():
                is_valid = True
                
                # Check against invalid patterns
                for invalid_pattern in invalid_patterns:
                    if re.match(invalid_pattern, word.lower()):
                        print(f"Rejecting word '{word}' - matches invalid pattern: {invalid_pattern}")
                        is_valid = False
                        break
            
                # ENHANCED: Check if it's a common non-name word (including misspellings)
                if is_valid: 
                    common_non_names = [
                        'pdf', 'doc', 'docx', 'txt', 'file', 'copy', 'scan', 'page',
                        'part', 'section', 'chapter', 'appendix', 'attachment',
                        'original', 'origninal', 'orginal'  # Common misspellings
                    ]
                    
                    if word.lower() in common_non_names:
                        print(f"Rejecting word '{word}' - common non-name word")
                        is_valid = False
            
            # ENHANCED: Also reject words that are just numbers or symbols in parentheses
            elif re.match(r'^\(\d+\)$', word):  # Matches "(1)", "(2)", etc.
                print(f"Rejecting word '{word}' - parentheses with numbers")
                is_valid = False
            
            if is_valid:
                valid_words.append(word.capitalize())
    
        print(f"Valid words from filename: {valid_words}")
        
        # Only return if we have meaningful name words
        if len(valid_words) >= 1 and not all(len(word) <= 3 for word in valid_words):
            formatted_name = ' '.join(valid_words[:4])  # Max 4 words
            print(f"Filename extracted name: {formatted_name}")
            return formatted_name
        
        print("No valid name words found in filename")
        return None
    
    def _extract_name_from_email(self, text):
        """Extract name from email address"""
        # Use details_extractor to get the email
        email = self.details_extractor.extract_email(text)
        
        if email:
            print(f"Found email: {email}")
            # Extract username part before @
            username = email.split('@')[0]
            print(f"Analyzing email username: {username}")
            
            # Handle different username patterns
            # Split by common separators and numbers
            parts = re.split(r'[._-]', username)
            name_parts = []
            
            for part in parts:
                # Remove numbers but keep alphabetic parts
                clean_part = re.sub(r'\d+$', '', part)  # Remove trailing numbers
                if len(clean_part) >= 2 and clean_part.isalpha():
                    name_parts.append(clean_part.capitalize())
            
            if name_parts:
                if len(name_parts) >= 2:
                    # Multiple parts found
                    potential_name = ' '.join(name_parts[:3])  # Max 3 parts
                    print(f"Email extracted name (multi-part): {potential_name}")
                    return potential_name
                else:
                    # Single part - could still be a valid name
                    single_name = name_parts[0]
                    if len(single_name) >= 4:  # At least 4 characters for single names
                        print(f"Email extracted name (single): {single_name}")
                        return single_name
        
        return None
    
    def _extract_name_from_github(self, text):
        """Extract name from GitHub username"""
        # Use details_extractor to get the GitHub URL
        github_url = self.details_extractor.extract_github(text)
        
        if github_url:
            print(f"Found GitHub URL: {github_url}")
            # Extract username from GitHub URL
            github_match = re.search(r'github\.com/([a-zA-Z][a-zA-Z0-9\-_.]*)', github_url, re.IGNORECASE)
            if github_match:
                username = github_match.group(1).lower()
                print(f"Analyzing GitHub username: {username}")
                
                # Split by common separators
                parts = re.split(r'[._-]', username)
                valid_parts = []
                
                for part in parts:
                    # Remove numbers but keep alphabetic parts
                    clean_part = re.sub(r'\d+', '', part)
                    if len(clean_part) >= 2 and clean_part.isalpha():
                        valid_parts.append(clean_part.capitalize())
                
                if len(valid_parts) >= 2:
                    potential_name = ' '.join(valid_parts[:3])
                    print(f"GitHub extracted name: {potential_name}")
                    return potential_name
                elif len(valid_parts) == 1 and len(valid_parts[0]) >= 4:
                    # Single name from GitHub username
                    single_name = valid_parts[0]
                    print(f"GitHub extracted name (single): {single_name}")
                    return single_name
        
        return None
    
    def _extract_name_from_linkedin(self, text):
        """Extract name from LinkedIn profile"""
        return self.linkedin_extractor.extract_name_from_linkedin_url(text)
    
    def _extract_name_from_header(self, lines):
        """Extract name from first few lines of resume with enhanced NER and POS tagging"""
        for i, line in enumerate(lines[:5]):  # Check first 5 lines
            line = line.strip()
            if not line:
                continue
            
            skip_patterns = [
                r'@.*\.',  # Email addresses
                r'www\.|http|\.com|\.org|\.in|\.edu',  # URLs
                r'^\+?\d{10,}',  # Phone numbers at start of line
            ]
            
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
                continue
            
            # ENHANCED: Use NLP for better name detection
            if self.nlp:
                doc = self.nlp(line)
                
                # Check for PERSON entities
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        name = ent.text.strip()
                        if (not self._is_institution_name(name) and 
                            self._is_valid_name(name) and 
                            self._calculate_name_naturalness_score(name) > 0):
                            print(f"NER found name in header line {i}: {name}")
                            return self._format_name(name)
                
                # ENHANCED: Use POS tagging to find proper nouns that could be names
                proper_nouns = []
                for token in doc:
                    if (token.pos_ == "PROPN" and 
                        token.is_alpha and 
                        len(token.text) >= 2 and
                        not token.text.lower() in ['original', 'origninal']):  
                            proper_nouns.append(token.text)
                
                if len(proper_nouns) >= 2:
                    potential_name = ' '.join(proper_nouns[:4]) 
                    if (self._is_valid_name(potential_name) and 
                        not self._is_institution_name(potential_name) and
                        self._calculate_name_naturalness_score(potential_name) > 0):
                        print(f"POS tagging found name in header line {i}: {potential_name}")
                        return self._format_name(potential_name)
            
            # Original pattern matching as fallback
            if i == 0:
                # All caps pattern (like "DHANUSH T S")
                if re.match(r'^[A-Z\s]{3,50}$', line):
                    words = line.split()
                    if 2 <= len(words) <= 4 and all(len(word) >= 1 and word.isalpha() for word in words):
                        potential_name = ' '.join(words)
                        if (not self._is_institution_name(potential_name) and 
                            not self._is_resume_section(potential_name) and 
                            not self._is_technical_term(potential_name) and
                            self._calculate_name_naturalness_score(potential_name) > 0):
                            print(f"All caps pattern found name: {potential_name}")
                            return self._format_name(potential_name)
                
                # Title case pattern
                if re.match(r'^[A-Z][a-zA-Z\s]{2,40}$', line):
                    words = line.split()
                    if 2 <= len(words) <= 4 and all(len(word) >= 2 and word.isalpha() for word in words):
                        potential_name = ' '.join(words)
                        if (not self._is_institution_name(potential_name) and 
                            not self._is_resume_section(potential_name) and 
                            not self._is_technical_term(potential_name) and
                            self._calculate_name_naturalness_score(potential_name) > 0):
                            print(f"Title case pattern found name: {potential_name}")
                            return self._format_name(potential_name)
            
            else:
                if re.match(r'^[A-Z][a-zA-Z\s]{2,40}$', line):
                    words = line.split()
                    if 2 <= len(words) <= 4 and all(len(word) >= 2 and word.isalpha() for word in words):
                        potential_name = ' '.join(words)
                        if (not self._is_institution_name(potential_name) and 
                            not self._is_resume_section(potential_name) and 
                            not self._is_technical_term(potential_name) and
                            self._calculate_name_naturalness_score(potential_name) > 0):
                            print(f"Non-first line pattern found name: {potential_name}")
                            return self._format_name(potential_name)
    
        return None

    def _is_resume_section(self, text):
        """Check if the text is a resume section header"""
        section_headers = [
            'professional experience', 'work experience', 'experience', 'employment',
            'education', 'academic background', 'qualifications', 'skills',
            'technical skills', 'projects', 'personal projects', 'achievements',
            'certifications', 'awards', 'honors', 'publications', 'references',
            'objective', 'career objective', 'summary', 'profile summary',
            'professional summary', 'contact information', 'personal details', 
            'about me', 'languages', 'interests', 'hobbies', 'volunteer experience', 
            'internships'
        ]
        
        text_lower = text.lower().strip()
        # Exact match for common single words that might be confused
        single_word_sections = ['experience', 'education', 'skills', 'projects', 'summary']
        if text_lower in single_word_sections:
            return True
            
        return any(header in text_lower for header in section_headers)

    def _is_technical_term(self, text):
        """Check if the text contains technical terms or programming languages"""
        technical_terms = [
            'java', 'python', 'javascript', 'html', 'css', 'react', 'node', 'angular',
            'spring', 'boot', 'hibernate', 'mysql', 'mongodb', 'sql', 'nosql',
            'git', 'github', 'docker', 'kubernetes', 'aws', 'azure', 'cloud',
            'android', 'ios', 'flutter', 'react native', 'swift', 'kotlin',
            'c++', 'c#', 'php', 'ruby', 'golang', 'rust', 'scala', 'perl',
            'tools', 'technologies', 'frameworks', 'libraries', 'databases',
            'frontend', 'backend', 'fullstack', 'devops', 'machine learning',
            'artificial intelligence', 'data science', 'web development'
        ]
        
        text_lower = text.lower()
        words = text_lower.split()
        
        for word in words:
            if word in technical_terms:
                return True
        
        for term in technical_terms:
            if term in text_lower:
                return True
                
        return False

    def _extract_name_using_nlp(self, lines):
        """Use NLP to extract person names with enhanced validation"""
        if not self.nlp:
            return None
        
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if not line:
                continue
                
            print(f"NLP analyzing line {i}: '{line}'")
            doc = self.nlp(line)
            
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text.strip()
                    print(f"NLP found PERSON entity: '{name}'")
                    
                    if (not self._is_institution_name(name) and 
                        self._is_valid_name(name) and
                        self._calculate_name_naturalness_score(name) > 0):
                        print(f"NLP validated name: {name}")
                        return self._format_name(name)
                    else:
                        print(f"NLP rejected name: {name}")
        
            proper_nouns = []
            for token in doc:
                if (token.pos_ == "PROPN" and 
                    token.is_alpha and 
                    len(token.text) >= 2):
                    proper_nouns.append(token.text)
            
            if len(proper_nouns) >= 2:
                potential_name = ' '.join(proper_nouns[:4])
                print(f"NLP found proper noun sequence: '{potential_name}'")
                
                if (self._is_valid_name(potential_name) and 
                    not self._is_institution_name(potential_name) and
                    self._calculate_name_naturalness_score(potential_name) > 0):
                    print(f"NLP validated proper noun name: {potential_name}")
                    return self._format_name(potential_name)
        
        return None

    def _calculate_name_naturalness_score(self, name):
        """Calculate how natural/realistic a name looks"""
        if not name:
            return 0
        
        words = name.split()
        score = 0
        
        score += len(words) * 10
        
        # ENHANCED: Heavy penalty for obvious resume sections first
        resume_section_words = [
            'final', 'year', 'student', 'graduate', 'intern', 'candidate',
            'professional', 'experience', 'work', 'education', 'skills',
            'projects', 'summary', 'objective', 'profile'
        ]
        
        # Check if this looks like a resume section
        if any(word.lower() in resume_section_words for word in words):
            score -= 200  # Heavy penalty for resume section words
            print(f"Heavy penalty for '{name}' - contains resume section words")
        
        document_words = ['original', 'origninal', 'orginal', 'copy', 'hardcopy', 'softcopy', 'file', 'document']
        if any(doc_word in name.lower() for doc_word in document_words):
            score -= 100
            print(f"Heavy penalty for '{name}' - contains document word")
        
        if any(prefix in name.lower() for prefix in ['environment', 'system', 'application', 'software', 'platform']):
            score -= 50
            print(f"Heavy penalty for '{name}' - contains technical prefix")
        
        unusual_combinations = [
            ['happy', 'sad', 'good', 'bad', 'nice', 'great', 'awesome'],  # Adjectives
            ['area', 'expertise', 'skill', 'knowledge', 'experience'],     # Professional terms
            ['developer', 'engineer', 'manager'],               # Job titles (removed 'student' as it's handled above)
            ['resume', 'cv', 'profile', 'document'],                       # Document terms
            ['generative', 'artificial', 'intelligence', 'machine', 'learning'],  # AI/Tech terms
            ['environment', 'system', 'application', 'software', 'platform'],  # Tech prefixes
            ['original', 'origninal', 'copy', 'file']  # Document words
        ]
        
        for word in words:
            word_lower = word.lower()
            
            # Penalty for unusual words in names
            for unusual_group in unusual_combinations:
                if word_lower in unusual_group:
                    score -= 20
                    print(f"Penalizing '{name}' for unusual word: {word}")
            
            # Bonus for typical name characteristics
            if word_lower.isalpha() and len(word) >= 2:  # Changed from 3 to 2 for initials
                score += 5
            
            # Bonus for proper capitalization
            if word[0].isupper() and (len(word) == 1 or word[1:].islower()):  # Allow single letter initials
                score += 3
            
            # FIXED: Reduce penalty for all caps names - they could be valid names like "SHAKITHIYAN K V"
            if len(word) > 1 and word.isupper():
                # Only small penalty for all caps, don't heavily penalize valid names
                score -= 1  # Reduced from -2 to -1
        
        # Bonus for common name patterns
        if len(words) == 2:
            score += 10
        elif len(words) == 3:  # Names like "DHANUSH T S" or "SHAKITHIYAN K V"
            score += 15  # Increased bonus for 3-word names with initials
        elif len(words) == 1:
            score += 5
        
        # ENHANCED: Heavy penalty for obvious resume sections
        name_lower = name.lower()
        obvious_sections = [
            'final year', 'work experience', 'professional experience',
            'technical skills', 'personal projects', 'career objective'
        ]
        if any(section in name_lower for section in obvious_sections):
            score -= 150
            print(f"Heavy penalty for '{name}' - obvious resume section")
        
        # ENHANCED: Penalty for very unusual combinations
        bad_combinations = ['happy', 'area of', 'expertise', 'skill set', 'generative ai', 'environment', 'original', 'origninal']
        if any(combo in name_lower for combo in bad_combinations):
            score -= 30
            print(f"Heavy penalty for '{name}' - contains unusual name combination")
        
        print(f"Name naturalness score for '{name}': {score}")
        return score

    def _is_valid_name(self, name):
        """Validate if the extracted text is a valid person name"""
        if not name or len(name.strip()) < 2:  # Changed from 3 to 2
            return False
        
        words = name.strip().split()
        
        # ENHANCED: Reject obvious resume sections first
        obvious_resume_sections = [
            'final year', 'work experience', 'professional experience',
            'technical skills', 'personal projects', 'career objective',
            'final year student', 'computer science', 'software engineer'
        ]
        
        if name.lower().strip() in obvious_resume_sections:
            print(f"Rejecting '{name}' - obvious resume section")
            return False

        # REJECT: Names that are just a list of platform names (like "Linkedin Github Leetcode")
        platform_words = {'linkedin', 'github', 'leetcode', 'hackerrank', 'codechef', 'codesignal', 'codeforces', 'portfolio', 'website', 'blog'}
        platform_word_count = sum(1 for word in words if word.lower() in platform_words)
        if all(word.lower() in platform_words for word in words):
            print(f"Rejecting '{name}' - all words are platform names")
            return False
        # NEW: Reject if name contains 2 or more platform words, or starts/ends with a platform word
        if platform_word_count >= 2:
            print(f"Rejecting '{name}' - contains multiple platform names")
            return False
        if words and (words[0].lower() in platform_words or words[-1].lower() in platform_words):
            print(f"Rejecting '{name}' - starts or ends with a platform name")
            return False

        # REJECT: Names that are just a list of institution names
        # institution_words = {'university', 'college', 'institute', 'school', 'academy'}
        # if all(word.lower() in institution_words for word in words):
        #     print(f"Rejecting '{name}' - all words are institution names")
        #     return False
        
        # ENHANCED: Reject if contains multiple resume-related words
        resume_words = ['final', 'year', 'student', 'experience', 'professional', 'technical', 'skills', 'projects']
        resume_word_count = sum(1 for word in words if word.lower() in resume_words)
        if resume_word_count >= 2:
            print(f"Rejecting '{name}' - contains {resume_word_count} resume-related words")
            return False
        
        # ENHANCED: Reject document-related combinations
        non_name_combinations = [
            'hss hardcopy', 'soft copy', 'hard copy', 'resume file', 'cv file',
            'document file', 'scan copy', 'original copy', 'final version',
            'dhanush original', 'dhanush origninal'  # Specific bad combinations
        ]
        
        if name.lower() in non_name_combinations:
            print(f"Rejecting '{name}' - obvious non-name combination")
            return False
        
        # Allow single word names if they're from high-priority sources and long enough
        if len(words) == 1:
            word = words[0]
            # Single words should be at least 3 characters (changed from 4) and not abbreviations
            if len(word) >= 3 and word.isalpha():
                invalid_single_words = [
                    'student', 'engineer', 'developer', 'graduate', 'intern', 
                    'candidate', 'applicant', 'software', 'computer', 'science', 
                    'resume', 'profile', 'summary', 'document', 'hardcopy',
                    'original', 'origninal', 'copy', 'file', 'final', 'year'  # Added resume words
                ]
                if word.lower() not in invalid_single_words:
                    return True
            return False
    
        # Allow names with initials (like "DHANUSH T S" or "SHAKITHIYAN K V")
        if len(words) >= 2:
            for word in words:
                if len(word) < 1 or len(word) > 20:  # Allow single letter initials
                    return False
                if not word.isalpha():
                    return False
        
            # ENHANCED: Check against invalid word combinations
            invalid_words = [
                'student', 'engineer', 'developer', 'graduate', 'intern', 
                'candidate', 'applicant', 'software', 'computer', 'science',
                'resume', 'cv', 'profile', 'summary', 'work', 'experience',
                'education', 'skills', 'projects', 'technical', 'professional',
                'java', 'python', 'javascript', 'tools', 'technologies',
                'hardcopy', 'copy', 'document', 'file', 'scan',
                'original', 'origninal', 'orginal', 'final', 'year'  # Added more resume words
            ]
            
            # FIXED: Only reject if it contains obvious invalid words, not just any invalid word
            # Allow names that might have one borderline word if other words are clearly name-like
            critical_invalid_words = ['student', 'experience', 'professional', 'technical', 'resume', 'final', 'year']
            critical_count = sum(1 for word in words if word.lower() in critical_invalid_words)
            
            if critical_count > 0:
                print(f"Rejecting '{name}' - contains {critical_count} critical invalid words")
                return False
            
            return True
    
        # For multi-word names (more than 4 words is unusual)
        if len(words) > 4:
            return False
        
        # Check if it's a resume section or technical term
        if self._is_resume_section(name) or self._is_technical_term(name):
            return False
        
        return True

    def _is_institution_name(self, name):
        """Check if the name looks like an institution rather than a person name"""
        if not name:
            return False
        
        name_lower = name.lower()
        
        # Common institution indicators
        institution_keywords = [
            'university', 'college', 'institute', 'school', 'academy', 'corporation',
            'company', 'ltd', 'limited', 'inc', 'incorporated', 'llc', 'pvt',
            'private', 'public', 'government', 'govt', 'department', 'ministry',
            'organization', 'foundation', 'trust', 'society', 'association',
            'technology', 'technologies', 'solutions', 'systems', 'services',
            'consulting', 'consultancy', 'group', 'holdings', 'enterprises',
            'international', 'global', 'national', 'regional', 'local',
            'engineering', 'medical', 'hospital', 'clinic', 'center', 'centre'
        ]
        
        # Check if name contains institution keywords
        if any(keyword in name_lower for keyword in institution_keywords):
            return True
        
        # Check for common institution name patterns
        institution_patterns = [
            r'\b(dr|prof|professor|mr|mrs|ms|miss)\b',  # Titles (though these could be in person names too)
            r'\b(and|&)\b',  # Names with "and" are often institutions
            r'\b(the)\s+[a-z]+',  # "The Something" format
            r'\b[a-z]+\s+(ltd|inc|llc|pvt|corp)\b',  # Corporate suffixes
            r'\b[a-z]+\s+(university|college|institute|school)\b',  # Educational institutions
        ]
        
        for pattern in institution_patterns:
            if re.search(pattern, name_lower):
                return True
        
        # Check for very long names (institutions tend to have longer names)
        words = name.split()
        if len(words) > 4:
            return True
        
        # Check for all caps institutional names
        if name.isupper() and len(words) > 2:
            # Could be an acronym like "MIT" or institutional name
            return True
        
        return False

    def _format_name(self, name):
        """Format the extracted name properly"""
        if not name:
            return None
        
        # Clean up extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Handle all caps names (like "DHANUSH T S")
        if name.isupper():
            words = name.split()
            formatted_words = []
            for word in words:
                if len(word) == 1:
                    # Keep single letters as uppercase (initials)
                    formatted_words.append(word.upper())
                else:
                    # Capitalize first letter, lowercase the rest
                    formatted_words.append(word.capitalize())
            return ' '.join(formatted_words)
        
        # Handle mixed case - ensure proper capitalization
        words = name.split()
        formatted_words = []
        for word in words:
            if len(word) == 1:
                # Single letters should be uppercase (initials)
                formatted_words.append(word.upper())
            elif word.islower():
                # All lowercase should be capitalized
                formatted_words.append(word.capitalize())
            else:
                # Keep existing capitalization if it looks correct
                formatted_words.append(word)
        
        return ' '.join(formatted_words)
