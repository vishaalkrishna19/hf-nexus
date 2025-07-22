import re
import requests
from bs4 import BeautifulSoup
import time

class LinkedInExtractor:
    def __init__(self):
        self.linkedin_patterns = [
            r'linkedin\.com/in/([a-zA-Z0-9\-_.]+)',
            r'www\.linkedin\.com/in/([a-zA-Z0-9\-_.]+)',
            r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-_.]+)',
        ]
    
    def extract_linkedin_url(self, text):
        """Extract LinkedIn profile URL from resume text"""
        print(f"Searching for LinkedIn URL in text...")
        
        for i, pattern in enumerate(self.linkedin_patterns):
            print(f"Trying pattern {i+1}: {pattern}")
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                username = match
                print(f"Found potential LinkedIn username: {username}")
                
                if self._is_valid_linkedin_username(username):
                    linkedin_url = f"https://www.linkedin.com/in/{username}"
                    print(f"Valid LinkedIn URL: {linkedin_url}")
                    return linkedin_url
                else:
                    print(f"Invalid LinkedIn username rejected: {username}")
        
        print("No valid LinkedIn URL found")
        return None
    
    def _is_valid_linkedin_username(self, username):
        """Validate if the username is a valid LinkedIn username"""
        
        
        if not username or len(username) < 3 or len(username) > 100:
            return False
        if not re.match(r'^[a-zA-Z0-9\-_.]+$', username):
            return False
        
        digit_count = sum(1 for char in username if char.isdigit())
        if len(username) > 0 and (digit_count / len(username)) > 0.7:
            print(f"Rejecting {username}: too many numbers ({digit_count}/{len(username)})")
            return False
        
        # Reject if it contains common words that suggest it's not a username
        invalid_words = [
            'nationality', 'address', 'contact', 'phone', 'email', 'website',
            'summary', 'objective', 'experience', 'education', 'skills',
            'projects', 'achievements', 'references', 'languages', 'interests'
        ]
        
        username_lower = username.lower()
        for word in invalid_words:
            if word in username_lower:
                print(f"Rejecting {username}: contains invalid word '{word}'")
                return False
        
        # Reject if it's too long and contains suspicious patterns
        if len(username) > 30:
            # Long usernames with lots of numbers are suspicious
            if digit_count > 10:
                print(f"Rejecting {username}: too long with too many numbers")
                return False
        
        return True
    
    def extract_name_from_linkedin_url(self, text):
        """Extract name from LinkedIn URL username"""
        print("Starting LinkedIn name extraction...")
        linkedin_url = self.extract_linkedin_url(text)
        if linkedin_url:
            # Extract username from URL
            username_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9\-_.]+)', linkedin_url)
            if username_match:
                username = username_match.group(1).lower()
                print(f"Analyzing LinkedIn username: {username}")
                
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
                    print(f"LinkedIn extracted name: {potential_name}")
                    return potential_name
                elif len(valid_parts) == 1 and len(valid_parts[0]) >= 4:
                    # Single name from LinkedIn username
                    single_name = valid_parts[0]
                    print(f"LinkedIn extracted name (single): {single_name}")
                    return single_name
        else:
            print("No LinkedIn URL found, cannot extract name")
        
        return None
    
    def scrape_linkedin_profile(self, linkedin_url):
        """
        Attempt to scrape basic information from LinkedIn profile
        Note: This is limited due to LinkedIn's anti-scraping measures
        """
        try:
            print(f"Attempting to scrape LinkedIn profile: {linkedin_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Add delay to be respectful
            time.sleep(2)
            
            response = requests.get(linkedin_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                profile_data = {}
                
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.get_text()
     
                    if '|' in title_text:
                        name_part = title_text.split('|')[0].strip()
                        if name_part and not name_part.lower().startswith('linkedin'):
                            profile_data['name'] = name_part
                
                description_tag = soup.find('meta', attrs={'name': 'description'})
                if description_tag:
                    description = description_tag.get('content', '')
                    profile_data['description'] = description
                
                og_title = soup.find('meta', attrs={'property': 'og:title'})
                if og_title:
                    og_title_content = og_title.get('content', '')
                    if og_title_content and not profile_data.get('name'):
                        profile_data['name'] = og_title_content
                
                return profile_data
            else:
                print(f"Failed to access LinkedIn profile. Status code: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"Error scraping LinkedIn profile: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error scraping LinkedIn: {str(e)}")
            return None
    
    def extract_professional_info_from_url(self, linkedin_url):
        """
        Extract professional information hints from LinkedIn URL structure
        """
        try:
            # Some LinkedIn URLs contain hints about the person
            username_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9\-_.]+)', linkedin_url)
            if username_match:
                username = username_match.group(1)
                
                # Common patterns in professional LinkedIn usernames
                professional_indicators = {
                    'engineer': ['engineer', 'dev', 'developer', 'tech', 'software'],
                    'manager': ['manager', 'mgr', 'lead', 'director'],
                    'analyst': ['analyst', 'data', 'business'],
                    'consultant': ['consultant', 'advisor', 'expert'],
                    'student': ['student', 'intern', 'graduate', 'undergrad']
                }
                
                username_lower = username.lower()
                detected_roles = []
                
                for role, indicators in professional_indicators.items():
                    if any(indicator in username_lower for indicator in indicators):
                        detected_roles.append(role)
                
                if detected_roles:
                    print(f"Detected professional roles from LinkedIn username: {detected_roles}")
                    return detected_roles
                
        except Exception as e:
            print(f"Error analyzing LinkedIn URL: {str(e)}")
        
        return []
    
    def get_linkedin_insights(self, text):
        """
        Get all possible insights from LinkedIn profile mentioned in resume
        """
        linkedin_url = self.extract_linkedin_url(text)
        if not linkedin_url:
            return None
        
        insights = {
            'linkedin_url': linkedin_url,
            'name_from_url': self.extract_name_from_linkedin_url(text),
            'professional_hints': self.extract_professional_info_from_url(linkedin_url),
            'scraped_data': None
        }
        
        # Attempt to scrape (may not work due to LinkedIn's restrictions)
        try:
            scraped_data = self.scrape_linkedin_profile(linkedin_url)
            if scraped_data:
                insights['scraped_data'] = scraped_data
        except Exception as e:
            print(f"Could not scrape LinkedIn profile: {str(e)}")
        
        return insights
    
    def extract_additional_contact_info(self, text):
        """
        Extract additional contact information that might be related to LinkedIn
        """
 
        additional_links = {
            'twitter': re.findall(r'twitter\.com/([a-zA-Z0-9_]+)', text, re.IGNORECASE),
            'portfolio': re.findall(r'((?:https?://)?(?:www\.)?[a-zA-Z0-9\-_.]+\.(?:com|org|net|io|dev)/?[a-zA-Z0-9\-_./]*)', text),
            'medium': re.findall(r'medium\.com/@?([a-zA-Z0-9\-_.]+)', text, re.IGNORECASE),
        }
        
        filtered_links = {k: v for k, v in additional_links.items() if v}
        
        if filtered_links:
            print(f"Found additional professional links: {filtered_links}")
        
        return filtered_links
    
    def extract_linkedin_link(self, text):
        """Extract LinkedIn link from the given text"""
        linkedin_pattern = r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-_/]+)'
        match = re.search(linkedin_pattern, text)
        return match.group(0) if match else None
