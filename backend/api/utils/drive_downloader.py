# drive_downloader.py

import requests
import re
import os
import time

class DriveDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def extract_file_id(self, drive_url):
        """More robustly extracts the Google Drive file ID from various URL formats."""
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, drive_url)
            if match:
                return match.group(1)
        return None

    def test_download(self, drive_url):
        """Test if a drive URL is accessible for downloading."""
        file_id = self.extract_file_id(drive_url)
        if not file_id:
            return False, "Could not extract valid File ID from URL"
        
        try:
            # Try the direct download URL first
            download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
            response = self.session.head(download_url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                return True, "File appears to be accessible"
            elif response.status_code == 403:
                return False, "File is not publicly accessible (403 Forbidden)"
            elif response.status_code == 404:
                return False, "File not found (404)"
            else:
                return False, f"HTTP {response.status_code} - File may not be publicly accessible"
                
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def download_pdf(self, drive_url):
        """
        Enhanced download method that handles various Google Drive scenarios.
        """
        file_id = self.extract_file_id(drive_url)
        if not file_id:
            print("Could not extract a valid File ID.")
            return None

        print(f"Attempting to download file with ID: {file_id}")
        
        # Try different download approaches
        download_methods = [
            # Method 1: Direct download
            f'https://drive.google.com/uc?export=download&id={file_id}',
            # Method 2: Alternative format
            f'https://drive.google.com/uc?id={file_id}&export=download',
            # Method 3: View format (sometimes works)
            f'https://drive.google.com/uc?id={file_id}'
        ]
        
        for method_idx, download_url in enumerate(download_methods, 1):
            print(f"Trying method {method_idx}: {download_url}")
            
            try:
                # First request
                response = self.session.get(download_url, timeout=30)
                
                # Check if we got a confirmation page (for large files)
                if 'download_warning' in response.text or 'confirm=' in response.text:
                    print("File requires confirmation (large file). Attempting to get confirmation token...")
                    
                    # Look for confirmation token in different ways
                    confirm_token = None
                    
                    # Method 1: From cookies
                    for key, value in response.cookies.items():
                        if key.startswith('download_warning'):
                            confirm_token = value
                            break
                    
                    # Method 2: From HTML content
                    if not confirm_token:
                        confirm_match = re.search(r'confirm=([^&"]+)', response.text)
                        if confirm_match:
                            confirm_token = confirm_match.group(1)
                    
                    # Method 3: From form action
                    if not confirm_token:
                        form_match = re.search(r'action="[^"]*[?&]confirm=([^&"]+)', response.text)
                        if form_match:
                            confirm_token = form_match.group(1)
                    
                    if confirm_token:
                        print(f"Found confirmation token: {confirm_token}")
                        confirmed_url = f'{download_url}&confirm={confirm_token}'
                        response = self.session.get(confirmed_url, timeout=30)
                    else:
                        print("Could not find confirmation token")
                        continue
                
                # Check response
                content_type = response.headers.get('content-type', '').lower()
                content_length = response.headers.get('content-length', 0)
                
                print(f"Response status: {response.status_code}")
                print(f"Content-Type: {content_type}")
                print(f"Content-Length: {content_length}")
                
                # Check if it's a PDF
                if (response.status_code == 200 and 
                    ('application/pdf' in content_type or 
                     response.content.startswith(b'%PDF'))):
                    print(f"✅ Download successful for file ID: {file_id}")
                    return response.content
                
                # Check if it's an HTML error page
                elif 'text/html' in content_type and response.status_code == 200:
                    print("Got HTML response - checking for error messages...")
                    
                    html_content = response.text.lower()
                    
                    if 'sign in' in html_content or 'login' in html_content:
                        print("❌ File requires authentication")
                        continue
                    elif 'access denied' in html_content or 'permission' in html_content:
                        print("❌ File access denied")
                        continue
                    elif 'file not found' in html_content or '404' in html_content:
                        print("❌ File not found")
                        continue
                    elif 'virus' in html_content or 'scan' in html_content:
                        print("❌ File blocked by virus scanner")
                        
                        # Try to find download anyway button
                        download_anyway_match = re.search(r'href="([^"]*download[^"]*)"', response.text)
                        if download_anyway_match:
                            download_anyway_url = download_anyway_match.group(1)
                            if download_anyway_url.startswith('/'):
                                download_anyway_url = 'https://drive.google.com' + download_anyway_url
                            
                            print(f"Found 'download anyway' link: {download_anyway_url}")
                            try:
                                response = self.session.get(download_anyway_url, timeout=30)
                                if response.status_code == 200 and response.content.startswith(b'%PDF'):
                                    print(f"✅ Download successful after virus warning for file ID: {file_id}")
                                    return response.content
                            except Exception as e:
                                print(f"Error with download anyway link: {e}")
                        
                        continue
                    else:
                        print("❌ Unknown HTML error response")
                        continue
                else:
                    print(f"❌ Unexpected response: Status {response.status_code}, Content-Type: {content_type}")
                    continue
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Network error for method {method_idx}: {e}")
                continue
        
        # If all methods failed, save error page for debugging
        print("❌ All download methods failed. Saving error page for debugging...")
        try:
            error_response = self.session.get(download_methods[0], timeout=30)
            error_file_path = f'gdrive_error_page_{file_id}.html'
            with open(error_file_path, 'w', encoding='utf-8') as f:
                f.write(error_response.text)
            
            print(f"\n‼️  DIAGNOSTIC FILE SAVED: '{os.path.abspath(error_file_path)}'")
            print("    Please open this file in a browser to see the exact error.\n")
            
            # Also check if the file is actually accessible via web
            print(f"🔍 Please manually check: https://drive.google.com/file/d/{file_id}/view")
            print("    Make sure the file is:")
            print("    - Set to 'Anyone with the link can view'")
            print("    - Actually a PDF file")
            print("    - Not restricted by organization policies")
            
        except Exception as e:
            print(f"Could not save error page: {e}")
        
        return None

    def get_file_info(self, drive_url):
        """Get basic file information from Google Drive link."""
        file_id = self.extract_file_id(drive_url)
        if not file_id:
            return None
        
        try:
            # Try to get file info from the view page
            view_url = f'https://drive.google.com/file/d/{file_id}/view'
            response = self.session.get(view_url, timeout=10)
            
            if response.status_code == 200:
                # Basic info we can extract
                info = {
                    'file_id': file_id,
                    'view_url': view_url,
                    'download_url': f'https://drive.google.com/uc?export=download&id={file_id}'
                }
                
                # Try to extract file name from page title or content
                if '<title>' in response.text:
                    title_match = re.search(r'<title>(.*?)</title>', response.text)
                    if title_match:
                        info['title'] = title_match.group(1).strip()
                
                return info
                
        except Exception as e:
            print(f"Error getting file info: {e}")
            return None