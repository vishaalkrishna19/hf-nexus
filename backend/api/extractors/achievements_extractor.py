import re

class AchievementsExtractor:
    def __init__(self):
        self.achievement_keywords = ['achievement', 'award', 'winner', 'certificate', 'recognition', 'honor']
    
    def extract_achievements(self, text):
        """Extract achievements from resume text"""
        achievements = []
        lines = text.split('\n')
        
        in_achievement_section = False

        achievements.extend(self._extract_titled_achievements(lines))
        
        for line in lines:
            line = line.strip()
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in self.achievement_keywords):
                in_achievement_section = True
               
                if self._is_achievement_line(line):
                    achievement = self._clean_achievement(line)
                    if achievement and self._is_valid_achievement(achievement):
                        achievements.append(achievement)
                continue
            
            if line_lower.startswith(('education', 'skills', 'experience', 'projects')):
                if not any(ach_kw in line_lower for ach_kw in self.achievement_keywords):
                    in_achievement_section = False
                continue
            
            # If in achievement section or line contains achievement indicators
            if in_achievement_section or self._is_achievement_line(line):
                if line and not self._is_section_header(line):
                    achievement = self._clean_achievement(line)
                    if achievement and len(achievement) > 10 and self._is_valid_achievement(achievement):
                        achievements.append(achievement)
    

        return self._deduplicate_achievements(achievements)[:5] if achievements else []

    def _extract_titled_achievements(self, lines):
        """Extract achievements that have clear titles followed by descriptions"""
        achievements = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Check if this line looks like an achievement title
            if self._is_achievement_title(line):
                # Build complete achievement from title and following lines
                achievement_parts = [line]
                
                # Look for date/time info in next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if self._is_date_line(next_line):
                        achievement_parts.append(next_line)
                        i += 1
                
                # Collect description lines
                description_lines = []
                j = i + 1
                while j < len(lines) and j < i + 6:  # Look ahead max 6 lines
                    desc_line = lines[j].strip()
                    
                    # Stop if we hit another achievement title or section header
                    if (self._is_achievement_title(desc_line) or 
                        self._is_section_header(desc_line) or
                        not desc_line):
                        break
                    
                    # Add description line if it's meaningful
                    if len(desc_line) > 15 and not self._is_standalone_date(desc_line):
                        description_lines.append(desc_line)
                    
                    j += 1
                
                # Combine title and description
                if description_lines:
                    complete_achievement = achievement_parts[0]
                    if len(achievement_parts) > 1:  # Has date
                        complete_achievement += f" ({achievement_parts[1]})"
                    complete_achievement += " - " + " ".join(description_lines)
                    achievements.append(complete_achievement)
                
                i = j
            else:
                i += 1
        
        return achievements
    def _is_achievement_title(self, line):
        """Check if line looks like an achievement title"""
        line_lower = line.lower()
        
        if any(cert_word in line_lower for cert_word in ['certification', 'certificate', 'certified', 'course completion']):
            return False
        
        # Achievement title indicators
        title_indicators = [
            'google developer solution challenge', 'hackathons', 'key speaker',
            'mentor', 'bootcamp', 'challenge', 'competition', 'winner',
            'achievement', 'award', 'recognition', 'speaker', 'invited',
            'top 100', 'finalist', 'champion', 'scholarship', 'patent',
            'published', 'honor', 'coordinator', 'runner-up', 'national level'
        ]
        
        # Check for title patterns
        if any(indicator in line_lower for indicator in title_indicators):
            return True
        
        # Check for title-like formatting (Title Case, short line)
        if (line and line[0].isupper() and 
            len(line.split()) <= 15 and 
            len(line) < 100 and
            not self._is_date_line(line) and
            not line_lower.startswith(('education', 'skills', 'experience', 'projects'))):
            
            # Must contain some achievement-related words
            achievement_words = [
                'challenge', 'hackathon', 'competition', 'award', 'speaker',
                'mentor', 'winner', 'finalist', 'achievement', 'recognition',
                'honor', 'scholarship', 'patent', 'published', 'coordinator',
                'runner-up', 'national level'
            ]
            
            if any(word in line_lower for word in achievement_words):
                return True
        
        return False

    def _is_date_line(self, line):
        """Check if line contains date information"""
        date_patterns = [
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}\b',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}\b'
        ]
        
        line_lower = line.lower()
        return any(re.search(pattern, line_lower) for pattern in date_patterns)

    def _is_standalone_date(self, line):
        """Check if line is just a date with minimal other content"""
        if len(line.strip()) < 8:
            return False
        
        # Remove common date patterns and see what's left
        cleaned = re.sub(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b', '', line, flags=re.IGNORECASE)
        cleaned = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '', cleaned)
        cleaned = re.sub(r'\b\d{4}\b', '', cleaned)
        cleaned = re.sub(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}\b', '', cleaned, flags=re.IGNORECASE)
        
        return len(cleaned.strip()) < 5

    def _deduplicate_achievements(self, achievements):
        """Remove duplicate or very similar achievements"""
        unique_achievements = []
        
        for achievement in achievements:
            is_duplicate = False
            achievement_words = set(achievement.lower().split())
            
            for existing in unique_achievements:
                existing_words = set(existing.lower().split())
                
                # Calculate overlap
                overlap = len(achievement_words.intersection(existing_words))
                smaller_set_size = min(len(achievement_words), len(existing_words))
                
                # If more than 60% overlap, consider duplicate
                if smaller_set_size > 0 and overlap / smaller_set_size > 0.6:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_achievements.append(achievement)
        
        return unique_achievements

    def _clean_achievement(self, line):
        """Clean achievement line"""
        # Remove bullet points and common prefixes
        cleaned = re.sub(r'^[•\-*]\s*', '', line)
        cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
        cleaned = re.sub(r'^(achievement|award|winner|certificate):\s*', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip() if cleaned.strip() else None
    
    def _is_achievement_line(self, line):
        """Check if line contains achievement indicators"""
        line_lower = line.lower()
        achievement_indicators = [
            'winner', 'first', 'second', 'third', 'runner', 'champion', 'finalist',
            'award', 'prize', 'medal', 'certificate', 'scholarship', 'honor',
            'recognition', 'published', 'patent', 'hackathon', 'competition'
        ]
        
        return any(indicator in line_lower for indicator in achievement_indicators)
    
    def _is_section_header(self, line):
        """Check if line is a section header"""
        line_lower = line.lower().strip()
        headers = [
            'projects', 'achievements', 'awards', 'experience', 'education',
            'skills', 'personal projects', 'key projects', 'major projects'
        ]
        return line_lower in headers or (len(line.split()) <= 3 and any(header in line_lower for header in headers))
    
    def _is_valid_achievement(self, achievement):
        """Check if the text is actually an achievement and not education info"""
        achievement_lower = achievement.lower()

        certification_keywords = [
        'certification', 'certificate', 'certified', 'cert', 'course completion',
        'training completion', 'diploma', 'license', 'accreditation', 'credential',
        'professional certification', 'online course', 'coursera', 'udemy',
        'edx', 'linkedin learning', 'pluralsight', 'khan academy'
    ]
        if any(keyword in achievement_lower for keyword in certification_keywords):
            return False
        
        # Filter out education-related entries
        education_keywords = [
            'higher secondary', 'secondary school', 'high school', 'matriculation',
            'hsc', 'sslc', 'cbse', 'icse', 'state board', 'central board',
            'class 10', 'class 12', 'grade 10', 'grade 12', '10th', '12th',
            'bachelor', 'master', 'degree', 'diploma', 'b.tech', 'm.tech',
            'b.e.', 'm.e.', 'bca', 'mca', 'college', 'university', 'institute'
        ]
        
        # Filter out incomplete or non-meaningful achievements
        invalid_patterns = [
            r'^\d{4}[-\s]*\d{4}?$',  # Just years
            r'^\d+(\.\d+)?%?$',       # Just percentages
            r'^(cgpa|gpa)[:=\s]*\d+',  # CGPA entries
        ]
        
        # Check if it's education-related
        if any(keyword in achievement_lower for keyword in education_keywords):
            return False
        
        # Check if it matches invalid patterns
        if any(re.match(pattern, achievement_lower) for pattern in invalid_patterns):
            return False
        
        achievement_indicators = [
            'winner', 'first', 'second', 'third', 'runner', 'champion', 'finalist',
            'award', 'prize', 'medal', 'certificate', 'scholarship', 'honor',
            'recognition', 'published', 'patent', 'hackathon', 'competition',
            'achieved', 'secured', 'obtained', 'received', 'participated',
            'qualified', 'selected', 'ranked', 'top 100', 'speaker', 'mentor',
            'invited', 'distinguished', 'bootcamp', 'challenge', 'developed',
            'shortlisted', 'globally', 'won many', 'innovation', 'problem-solving'
        ]
        
        return any(indicator in achievement_lower for indicator in achievement_indicators)
