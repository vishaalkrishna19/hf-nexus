import re
from .github_crawler import GithubCrawler

class DetailsExtractor:
    def __init__(self):
        # Updated email pattern to handle spaces
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'(?:\+91|91)?[-.\s]?[6-9]\d{9}|\b\d{10}\b'
        self.github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w.-]+/?'
    
    def extract_email(self, text):
        """Extract email from resume text"""
        print(f"Searching for email in text: {text[:200]}...")
        
        # Multiple patterns to handle various spacing issues
        email_patterns = [
            # Handle contaminated emails like "environment.deepikaprabhakaran54@gmail.com"
            r'(?:environment\.)?([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+)\.([a-zA-Z]{2,})',
            # Handle "vishaalkrishna tg@gmail.c om" pattern
            r'([a-zA-Z0-9._%+-]+)\s+([a-zA-Z0-9._%+-]*)\s*@\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,})',
            # Handle "user@domain.c om" pattern
            r'([a-zA-Z0-9._%+-]+)\s*@\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,})',
            # Handle spaces within username like "deepika prabhakaran54@gmail.com"
            r'([a-zA-Z0-9._%+-]+\s+[a-zA-Z0-9._%+-]*)\s*@\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,})',
            # Standard email pattern
            r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b',
        ]
        
        for i, pattern in enumerate(email_patterns):
            print(f"Trying pattern {i+1}: {pattern}")
            matches = re.findall(pattern, text, re.IGNORECASE)
            print(f"Pattern {i+1} matches: {matches}")
            
            if matches:
                if i == 0:  # Contaminated email pattern
                    # Clean the email by removing environment prefix
                    username, domain, tld = matches[0]
                    email = f"{username}@{domain}.{tld}"
                    email = re.sub(r'\s+', '', email)
                    # Additional cleaning for common contamination
                    email = self._clean_contaminated_email(email)
                    print(f"Cleaned contaminated email: {email}")
                    return email
                elif i == 1:  # First pattern with name parts
                    # Reconstruct email: "vishaalkrishna" + "tg" + "@gmail" + "." + "com"
                    first_part, second_part, domain, tld = matches[0]
                    email = f"{first_part}{second_part}@{domain}.{tld}"
                    email = re.sub(r'\s+', '', email)  # Remove any remaining spaces
                    print(f"Reconstructed email: {email}")
                    return email
                elif i == 2:  # Second pattern
                    # Reconstruct email from parts
                    user, domain, tld = matches[0]
                    email = f"{user}@{domain}.{tld}"
                    email = re.sub(r'\s+', '', email)
                    print(f"Reconstructed email: {email}")
                    return email
                elif i == 3:  # Third pattern with spaces in username
                    user, domain, tld = matches[0]
                    # Remove spaces from username part
                    user_clean = re.sub(r'\s+', '', user)
                    email = f"{user_clean}@{domain}.{tld}"
                    print(f"Reconstructed email: {email}")
                    return email
                else:  # Standard pattern
                    email = matches[0]
                    # Clean any contamination from standard emails too
                    email = self._clean_contaminated_email(email)
                    print(f"Found standard email: {email}")
                    return email
        
        print("No email found")
        return None
    
    def _clean_contaminated_email(self, email):
        """Clean contaminated email addresses"""
        # Remove common contamination prefixes from username
        contamination_prefixes = [
            'environment.', 'system.', 'application.', 'software.', 
            'platform.', 'website.', 'portal.', 'service.'
        ]
        
        for prefix in contamination_prefixes:
            if email.lower().startswith(prefix):
                # Remove the prefix
                email = email[len(prefix):]
                print(f"Removed contamination prefix '{prefix}' from email")
                break
        
        return email

    def extract_phone(self, text):
        """Extract phone number from resume text"""
        print(f"Searching for phone in text...")
        
        # Look for phone patterns with spaces and formatting
        phone_patterns = [
            # Handle heavily spaced numbers like "86673 22426" or "8 6 6 7 3 2 2 4 2 6"
            r'\b([6-9])\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\b',
            r'\b([6-9]\d)\s*(\d\d)\s*(\d\d)\s*(\d\d)\s*(\d)\b',  # Like "86 67 32 24 26"
            r'\b([6-9]\d\d)\s*(\d\d)\s*(\d\d)\s*(\d\d\d)\b',      # Like "866 73 22 426"
            r'\b([6-9]\d\d\d\d)\s*(\d\d\d\d\d)\b',                # Like "86673 22426"
            
            # With country code
            r'\+91\s*[-.\s]*([6-9])\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)',
            r'91\s*[-.\s]*([6-9])\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)',
            r'\(\+91\)\s*[-.\s]*([6-9])\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)',
            
            # Standard patterns (existing)
            r'\+91[-.\s]?[6-9]\d{9}',
            r'91[-.\s]?[6-9]\d{9}',
            r'\b[6-9]\d{9}\b',
            r'\(\+91\)[-.\s]?[6-9]\d{9}',
        ]
        
        for i, pattern in enumerate(phone_patterns):
            print(f"Trying phone pattern {i+1}")
            matches = re.findall(pattern, text)
            if matches:
                print(f"Phone pattern {i+1} matched: {matches}")
                
                if i < 7:  # Spaced number patterns
                    # Reconstruct phone number from captured groups
                    if isinstance(matches[0], tuple):
                        phone_digits = ''.join(matches[0])
                    else:
                        phone_digits = matches[0]
                    
                    # Clean the phone number - remove all non-digit characters
                    phone = re.sub(r'[^\d]', '', phone_digits)
                else:
                    # Standard patterns
                    phone = re.sub(r'[^\d]', '', matches[0])
                
                # Handle country code
                if phone.startswith('91') and len(phone) == 12:
                    phone = phone[2:]
                
                # Validate Indian mobile number
                if len(phone) == 10 and phone[0] in '6789':
                    print(f"Found valid phone: {phone}")
                    return phone
                else:
                    print(f"Invalid phone number: {phone} (length: {len(phone)}, starts with: {phone[0] if phone else 'N/A'})")
        
        print("No valid phone found")
        return None
    
    def extract_github(self, text):
        """Extract GitHub profile from resume text"""
        # Handle spaced GitHub URLs
        spaced_github_pattern = r'(?:https?://)?(?:www\s*\.\s*)?github\s*\.\s*com\s*/\s*[\w.-]+/?'
        matches = re.findall(spaced_github_pattern, text, re.IGNORECASE)
        
        if matches:
            github_url = re.sub(r'\s+', '', matches[0])  # Remove spaces
            if not github_url.startswith('http'):
                github_url = 'https://' + github_url
            return github_url
        
        # Fallback to original pattern
        matches = re.findall(self.github_pattern, text, re.IGNORECASE)
        if matches:
            github_url = matches[0]
            if not github_url.startswith('http'):
                github_url = 'https://' + github_url
            return github_url

        # Handle raw github/username or github : username or github - username
        raw_github_pattern = r'github\s*[/:\-]\s*([\w.-]+)'
        matches = re.findall(raw_github_pattern, text, re.IGNORECASE)
        if matches:
            username = matches[0]
            github_url = f'https://github.com/{username}'
            return github_url

        return None
    
    def extract_github_details(self, text_or_url):
        """Extract GitHub details using the crawler - can accept text or direct URL"""
        # If it looks like a direct GitHub URL, use it directly
        if 'github.com' in text_or_url and len(text_or_url.split()) <= 2:
            github_url = text_or_url.strip()
        else:
            # Extract GitHub URL from text
            github_url = self.extract_github(text_or_url)
        
        if not github_url:
            return None
            
        print(f"Using GitHub URL: {github_url}")
        crawler = GithubCrawler(github_url)
        return crawler.get_profile_data()
