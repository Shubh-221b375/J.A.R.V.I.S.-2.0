"""
Google Drive Integration
Downloads and processes files from Google Drive links (folders or individual files)
"""

import os
import re
import requests
import tempfile
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
import json
from datetime import datetime

# Try to import BeautifulSoup
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("Warning: BeautifulSoup4 not available. Install with: pip install beautifulsoup4")

# Try to import gdown (better for Google Drive downloads)
try:
    import gdown
    GDOWN_AVAILABLE = True
except ImportError:
    GDOWN_AVAILABLE = False

from Backend.DocumentProcessor import process_document
from Backend.SalesMemory import sales_memory_manager

class DriveProcessor:
    """Process Google Drive links and download files"""
    
    def __init__(self, download_dir: Optional[str] = None):
        """
        Initialize Drive Processor
        
        Args:
            download_dir: Directory to download files to (default: temp directory)
        """
        if download_dir:
            self.download_dir = download_dir
        else:
            self.download_dir = os.path.join(tempfile.gettempdir(), "jarvis_drive_downloads")
        
        os.makedirs(self.download_dir, exist_ok=True)
    
    def extract_drive_id(self, drive_link: str) -> Optional[Dict[str, str]]:
        """
        Extract file/folder ID from various Google Drive link formats
        
        Supported formats:
        - https://drive.google.com/file/d/FILE_ID/view
        - https://drive.google.com/drive/folders/FOLDER_ID
        - https://drive.google.com/open?id=FILE_ID
        - https://docs.google.com/document/d/FILE_ID/edit
        
        Returns:
            Dict with 'id' and 'type' ('file' or 'folder')
        """
        # Remove any trailing slashes and whitespace
        drive_link = drive_link.strip().rstrip('/')
        
        # Pattern 1: /file/d/FILE_ID/view or /file/d/FILE_ID
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_link)
        if match:
            return {'id': match.group(1), 'type': 'file'}
        
        # Pattern 2: /drive/folders/FOLDER_ID
        match = re.search(r'/drive/folders/([a-zA-Z0-9_-]+)', drive_link)
        if match:
            return {'id': match.group(1), 'type': 'folder'}
        
        # Pattern 3: /open?id=FILE_ID
        match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', drive_link)
        if match:
            # Try to determine if it's a folder by checking the URL
            if 'folders' in drive_link:
                return {'id': match.group(1), 'type': 'folder'}
            return {'id': match.group(1), 'type': 'file'}
        
        # Pattern 4: /document/d/FILE_ID, /spreadsheets/d/FILE_ID, etc.
        match = re.search(r'/(?:document|spreadsheets|presentation)/d/([a-zA-Z0-9_-]+)', drive_link)
        if match:
            return {'id': match.group(1), 'type': 'file'}
        
        return None
    
    def download_file(self, file_id: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Download a file from Google Drive using direct download link
        
        Args:
            file_id: Google Drive file ID
            filename: Optional filename (if not provided, will try to detect)
            
        Returns:
            Path to downloaded file, or None if failed
        """
        try:
            # Direct download URL format
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            # First, try to get the file info
            response = requests.get(download_url, allow_redirects=True, stream=True, timeout=30)
            
            # Check for virus scan warning
            if 'virus scan warning' in response.text.lower() or 'download_warning' in response.url:
                # Extract the confirm token
                confirm_match = re.search(r'confirm=([a-zA-Z0-9_-]+)', response.url)
                if confirm_match:
                    confirm_token = confirm_match.group(1)
                    download_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={confirm_token}"
                    response = requests.get(download_url, stream=True, timeout=30)
            
            if response.status_code != 200:
                return None  # Don't print error for invalid files
            
            # Get MIME type from Content-Type header
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Try to get filename from Content-Disposition header
            if not filename:
                content_disposition = response.headers.get('Content-Disposition', '')
                filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
                if filename_match:
                    filename = filename_match.group(1)
                else:
                    filename = f"drive_file_{file_id}"
            
            # Clean filename
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            # If no extension, try to add one based on MIME type
            if not os.path.splitext(filename)[1]:
                mime_to_ext = {
                    'application/pdf': '.pdf',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
                    'application/msword': '.doc',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
                    'application/vnd.ms-excel': '.xls',
                    'text/plain': '.txt',
                    'text/csv': '.csv',
                    'image/png': '.png',
                    'image/jpeg': '.jpg',
                    'image/jpg': '.jpg',
                    'application/json': '.json',
                    'application/xml': '.xml',
                    'text/xml': '.xml'
                }
                if content_type in mime_to_ext:
                    filename += mime_to_ext[content_type]
            
            # Download to temp file first (so we can detect type)
            temp_file_path = os.path.join(self.download_dir, f"temp_{file_id}")
            
            # Download the file
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # If no extension, detect from file content
            if not os.path.splitext(filename)[1]:
                try:
                    with open(temp_file_path, 'rb') as f:
                        first_bytes = f.read(4)
                        if first_bytes.startswith(b'%PDF'):
                            filename += '.pdf'
                        elif first_bytes.startswith(b'PK\x03\x04'):
                            # Check if it's docx or xlsx
                            f.seek(0)
                            content = f.read(1024)
                            if b'word/' in content:
                                filename += '.docx'
                            elif b'xl/' in content or b'worksheets/' in content:
                                filename += '.xlsx'
                            else:
                                filename += '.zip'
                        else:
                            # Try as text
                            try:
                                with open(temp_file_path, 'r', encoding='utf-8') as tf:
                                    tf.read(100)
                                filename += '.txt'
                            except:
                                pass
                except:
                    pass
            
            # Final file path
            file_path = os.path.join(self.download_dir, filename)
            
            # Rename temp file to final name
            if os.path.exists(file_path):
                os.remove(file_path)  # Remove if exists
            os.rename(temp_file_path, file_path)
            
            print(f"Downloaded: {filename} to {file_path}")
            return file_path
            
        except Exception as e:
            return None  # Don't print error for invalid files
    
    def list_folder_files(self, folder_id: str) -> List[Dict[str, str]]:
        """
        List all files in a Google Drive folder
        
        Uses Selenium to load the page with JavaScript execution since Google Drive
        loads files dynamically. Falls back to HTML parsing if Selenium is unavailable.
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            List of file info dicts with 'id' and 'name'
        """
        files = []
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}?usp=sharing"
        
        # Method 1: Try using Selenium to load page with JavaScript
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            
            print("Using Selenium to load Google Drive folder...")
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(folder_url)
            
            # Wait for page to load (Google Drive takes time to render)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                import time
                time.sleep(3)  # Give extra time for JavaScript to load files
            except:
                pass
            
            # Get page source after JavaScript execution
            page_source = driver.page_source
            driver.quit()
            
            # Extract file IDs from the rendered page
            if BS4_AVAILABLE:
                soup = BeautifulSoup(page_source, 'html.parser')
                # Look for file links
                file_links = soup.find_all('a', href=re.compile(r'/file/d/([a-zA-Z0-9_-]+)'))
                for link in file_links:
                    href = link.get('href', '')
                    file_id_match = re.search(r'/file/d/([a-zA-Z0-9_-]{25,})', href)
                    if file_id_match:
                        file_id = file_id_match.group(1)
                        filename = link.get_text(strip=True) or link.get('title', '') or f'file_{file_id}'
                        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                        if file_id not in [f['id'] for f in files]:
                            files.append({'id': file_id, 'name': filename[:100]})
            
            # Also extract from page source directly
            file_ids = re.findall(r'/file/d/([a-zA-Z0-9_-]{25,})', page_source)
            for file_id in set(file_ids):
                # Filter out invalid IDs (API keys, folder IDs, etc.)
                if self._is_valid_file_id(file_id) and file_id not in [f['id'] for f in files]:
                    files.append({'id': file_id, 'name': f'file_{file_id}'})
            
            print(f"Found {len(files)} files using Selenium")
            if files:
                return files
                
        except Exception as e:
            print(f"Selenium method failed: {e}")
            # Continue to fallback methods
        
        # Method 2: Try HTML parsing (may not work for JS-loaded content)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(folder_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Extract all file IDs from the HTML (even if not fully rendered)
                # Only look for /file/d/ pattern to avoid false positives
                file_ids = re.findall(r'/file/d/([a-zA-Z0-9_-]{25,})', response.text)
                
                for file_id in set(file_ids):
                    # Filter out invalid IDs
                    if self._is_valid_file_id(file_id) and file_id not in [f['id'] for f in files]:
                        files.append({'id': file_id, 'name': f'file_{file_id}'})
                
                print(f"Found {len(files)} files using HTML parsing")
                
        except Exception as e:
            print(f"HTML parsing method failed: {e}")
            import traceback
            traceback.print_exc()
        
        return files
    
    def _is_valid_file_id(self, file_id: str) -> bool:
        """
        Check if a file ID is valid (not an API key, folder ID, or other invalid ID)
        
        Args:
            file_id: Potential file ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Google Drive file IDs are typically 25-33 characters
        if len(file_id) < 25 or len(file_id) > 50:  # Increased max to 50 for edge cases
            return False
        
        # Filter out common patterns that are not file IDs
        invalid_patterns = [
            r'^AIza',  # API keys
            r'^[0-9]+$',  # Pure numbers
            r'^[A-Z]{20,}$',  # All uppercase long strings (API keys)
            r'^[a-z]{30,}$',  # All lowercase very long strings
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, file_id):
                return False
        
        # Check for suspicious patterns (API keys often have specific structure)
        if 'AIza' in file_id or (file_id.startswith('Sy') and len(file_id) > 30):
            return False
        
        # Must have mix of alphanumeric and underscores/dashes
        if not re.search(r'[a-zA-Z]', file_id) or not re.search(r'[0-9_-]', file_id):
            # Allow if it's a valid-looking ID with mixed case
            if not re.search(r'[A-Z]', file_id) and not re.search(r'[a-z]', file_id):
                return False
        
        return True
    
    def process_drive_link(self, drive_link: str, source_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a Google Drive link (file or folder) and store content in memory
        
        Args:
            drive_link: Google Drive link (file or folder)
            source_name: Optional name for the source
            
        Returns:
            Dictionary with processing results
        """
        try:
            if not source_name:
                source_name = f"Drive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Clean the link - remove any HTML tags that might be in it
            original_link = drive_link
            drive_link = re.sub(r'<[^>]+>', '', drive_link).strip()
            
            # Also extract from href if it's an HTML link
            href_match = re.search(r'href=["\']([^"\']+)["\']', original_link)
            if href_match:
                drive_link = href_match.group(1)
            
            # Remove any trailing characters that might be part of HTML
            drive_link = drive_link.strip().rstrip('>').rstrip('"').rstrip("'")
            
            print(f"Cleaned Drive link: {drive_link}")
            
            # Extract drive ID and type
            drive_info = self.extract_drive_id(drive_link)
            if not drive_info:
                print(f"Failed to extract drive ID from: {drive_link}")
                return {
                    "success": False,
                    "error": f"Invalid Google Drive link format. Link received: {drive_link[:100]}",
                    "files_processed": 0,
                    "entries_created": 0
                }
            
            file_id = drive_info['id']
            link_type = drive_info['type']
            
            print(f"Processing Drive {link_type}: {file_id}")
            
            total_files = 0
            total_entries = 0
            processed_files = []
            errors = []
            
            if link_type == 'file':
                # Process single file
                print(f"Processing single file: {file_id}")
                file_path = self.download_file(file_id)
                
                if file_path and os.path.exists(file_path):
                    result = process_document(file_path, source_name)
                    if result.get('success'):
                        total_files = 1
                        total_entries = result.get('entries_created', 0)
                        processed_files.append(os.path.basename(file_path))
                    else:
                        errors.append(f"Failed to process {os.path.basename(file_path)}: {result.get('error')}")
                else:
                    errors.append(f"Failed to download file {file_id}")
            
            elif link_type == 'folder':
                # Process folder - list and download all files
                print(f"Processing folder: {file_id}")
                
                # Try using gdown first (better for folders)
                if GDOWN_AVAILABLE:
                    try:
                        print("Trying gdown to download folder...")
                        folder_url = f"https://drive.google.com/drive/folders/{file_id}?usp=sharing"
                        # gdown can download entire folders (but has 50 file limit)
                        try:
                            gdown.download_folder(folder_url, output=self.download_dir, quiet=False, use_cookies=False)
                        except Exception as gdown_error:
                            # gdown may fail if folder has >50 files, but may have downloaded some
                            print(f"gdown hit limit or error: {gdown_error}")
                            # Continue to process whatever was downloaded
                        
                        # List downloaded files (even if gdown failed partway)
                        downloaded_files = [f for f in os.listdir(self.download_dir) 
                                          if os.path.isfile(os.path.join(self.download_dir, f)) 
                                          and not f.startswith('temp_')]
                        
                        if downloaded_files:
                            print(f"Found {len(downloaded_files)} downloaded files, processing...")
                            # Process each downloaded file
                            for filename in downloaded_files:
                                file_path = os.path.join(self.download_dir, filename)
                                try:
                                    result = process_document(file_path, f"{source_name}_{filename}")
                                    if result.get('success'):
                                        total_files += 1
                                        total_entries += result.get('entries_created', 0)
                                        processed_files.append(filename)
                                        print(f"✅ Processed: {filename}")
                                    else:
                                        errors.append(f"Failed to process {filename}: {result.get('error')}")
                                except Exception as e:
                                    errors.append(f"Error processing {filename}: {str(e)}")
                            
                            # If we processed files successfully, note it but continue to try other methods for remaining files
                            if total_files > 0:
                                print(f"Successfully processed {total_files} files with {total_entries} entries from gdown")
                                # Continue to try other methods for any remaining files
                    except Exception as e:
                        print(f"gdown method failed: {e}")
                        import traceback
                        traceback.print_exc()
                        # Continue to other methods
                
                # Fallback to manual file listing
                files = self.list_folder_files(file_id)
                
                if not files:
                    # Try alternative method: direct folder access
                    print("Trying alternative method to access folder...")
                    try:
                        # Try accessing the folder page with different parameters
                        folder_url = f"https://drive.google.com/drive/folders/{file_id}?usp=sharing"
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        response = requests.get(folder_url, headers=headers, timeout=30)
                        if response.status_code == 200:
                            # Try parsing again with the sharing URL
                            files = self.list_folder_files(file_id)
                    except:
                        pass
                    
                    # If we already processed some files from gdown, return success even if we can't get more
                    if not files:
                        if total_files > 0:
                            # We already processed some files, return success
                            return {
                                "success": True,
                                "source": source_name,
                                "files_processed": total_files,
                                "entries_created": total_entries,
                                "processed_files": processed_files,
                                "errors": errors if errors else None,
                                "note": f"Processed {total_files} files. Some files may not have been accessible."
                            }
                        else:
                            return {
                                "success": False,
                                "error": "Could not access folder files. The folder may be private or require authentication.",
                                "files_processed": 0,
                                "entries_created": 0,
                                "suggestion": "Please ensure the folder is shared with 'Anyone with the link can view' permission, or install gdown: pip install gdown"
                            }
                
                # Download and process each file
                for file_info in files:
                    file_id = file_info['id']
                    file_path = self.download_file(file_id, file_info.get('name'))
                    
                    if file_path and os.path.exists(file_path):
                        result = process_document(file_path, f"{source_name}_{os.path.basename(file_path)}")
                        if result.get('success'):
                            total_files += 1
                            total_entries += result.get('entries_created', 0)
                            processed_files.append(os.path.basename(file_path))
                        else:
                            errors.append(f"Failed to process {os.path.basename(file_path)}: {result.get('error')}")
                    else:
                        errors.append(f"Failed to download file {file_id}")
            
            # Clean up downloaded files (optional - can keep for caching)
            # self.cleanup_downloads()
            
            return {
                "success": total_files > 0,
                "source": source_name,
                "files_processed": total_files,
                "entries_created": total_entries,
                "processed_files": processed_files,
                "errors": errors if errors else None
            }
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in process_drive_link: {e}")
            print(f"Traceback: {error_trace}")
            return {
                "success": False,
                "error": f"Error processing Drive link: {str(e)}",
                "files_processed": 0,
                "entries_created": 0,
                "traceback": error_trace if "ImportError" in str(e) or "ModuleNotFoundError" in str(e) else None
            }
    
    def cleanup_downloads(self):
        """Clean up downloaded files"""
        try:
            import shutil
            if os.path.exists(self.download_dir):
                shutil.rmtree(self.download_dir)
                os.makedirs(self.download_dir, exist_ok=True)
        except Exception as e:
            print(f"Error cleaning up downloads: {e}")


# Global instance
drive_processor = DriveProcessor()

def extract_drive_id(drive_link: str) -> Optional[Dict[str, str]]:
    """
    Convenience function to extract Google Drive ID from a link
    
    Args:
        drive_link: Google Drive link
        
    Returns:
        Dict with 'id' and 'type' ('file' or 'folder'), or None if invalid
    """
    return drive_processor.extract_drive_id(drive_link)

def process_drive_link(drive_link: str, source_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to process a Google Drive link
    
    Args:
        drive_link: Google Drive link
        source_name: Optional source name
        
    Returns:
        Processing results dictionary
    """
    return drive_processor.process_drive_link(drive_link, source_name)


