from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import platform
import mtranslate as mt

# Vosk is PERMANENTLY DISABLED - using online STT only (Chrome Web Speech API)
# This ensures accurate speech recognition like before Vosk was added
VOSK_AVAILABLE = False
VOSK_MODEL = None
vosk_model_path = None
USE_VOSK = False  # Permanently disabled - always use online STT

print("Using online speech recognition (Chrome Web Speech API) - most accurate option")

# Load environment variables (if not already loaded)
if 'env_vars' not in locals():
    env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage")

# HTML content with speech recognition
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

# Inject Input Language
HtmlCode = HtmlCode.replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")

# Save HTML to file
os.makedirs("Data", exist_ok=True)
with open("Data/Voice.html", "w", encoding="utf-8") as f:
    f.write(HtmlCode)

# Construct local file URL
current_dir = os.getcwd()
Link = f"{current_dir}/Data/Voice.html"

# Set Chrome options (let Selenium find Chrome automatically)
chrome_options = Options()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")  # Modern headless mode
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36")

# Use webdriver-manager to automatically download and manage ChromeDriver
driver = None
try:
    system = platform.system()
    
    # Try to find Chrome installation (cross-platform)
    chrome_found = False
    chrome_path = None
    
    if system == "Windows":
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                chrome_found = True
                break
    elif system == "Darwin":  # macOS
        # Common Chrome paths on macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                chrome_found = True
                break
    elif system == "Linux":
        # Common Chrome paths on Linux
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                chrome_found = True
                break
    
    if chrome_path:
        chrome_options.binary_location = chrome_path
        print(f"Found Chrome at: {chrome_path}")
    
    if not chrome_found:
        print(f"Chrome browser not found on {system}. Speech recognition will be disabled.")
        print("Please install Google Chrome for speech recognition to work.")
        driver = None
    else:
        # Try to install and use ChromeDriver
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("ChromeDriver initialized successfully")
        except Exception as e:
            print(f"ChromeDriver initialization failed: {e}")
            # Try without service (webdriver-manager will handle it)
            try:
                driver = webdriver.Chrome(options=chrome_options)
                print("ChromeDriver initialized without service")
            except Exception as e2:
                print(f"ChromeDriver fallback failed: {e2}")
                driver = None
except Exception as e:
    print(f"ChromeDriver initialization failed: {e}")
    print("Speech recognition will be disabled. Please install Chrome browser and try again.")
    driver = None

# Setup temp status path
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
os.makedirs(TempDirPath, exist_ok=True)

def SetAssistantStatus(Status):
    with open(os.path.join(TempDirPath, "Status.data"), "w", encoding='utf-8') as file:
        file.write(Status)

def QueryModifier(Query):
    """Modify query and validate transcription quality"""
    if not Query or not isinstance(Query, str):
        return ""
    
    new_query = Query.lower().strip()
    
    # Filter out obviously bad transcriptions (repeated words, gibberish)
    words = new_query.split()
    
    if not words:
        return ""
    
    # Check for excessive repetition (like "the the the the")
    if len(words) > 2:
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        # If any word appears more than 50% of the time, it's likely noise
        max_repetition = max(word_counts.values()) if word_counts else 0
        if max_repetition > len(words) * 0.5:
            print(f"QueryModifier: Filtered out low-quality transcription (excessive repetition): '{new_query}'")
            return ""
    
    # Filter out very short or meaningless queries
    if len(new_query) < 3:
        return ""
    
    # Filter out queries that are mostly punctuation or special characters
    alnum_chars = len([c for c in new_query if c.isalnum()])
    if alnum_chars < len(new_query) * 0.3:
        print(f"QueryModifier: Filtered out low-quality transcription (too many special chars): '{new_query}'")
        return ""
    
    query_words = words
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]

    if any(word + " " in new_query for word in question_words):
        if query_words and query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words and query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation

def LocalSpeechRecognition(timeout=5):
    """
    Local offline speech recognition - DISABLED
    Always returns None to use online STT instead
    """
    # Vosk is permanently disabled - always use online STT
    return None

def SpeechRecognition():
    # Using online STT only (Chrome Web Speech API) - most accurate
    # Vosk is permanently disabled
    if driver is None:
        print("Speech recognition is disabled due to ChromeDriver issues.")
        return "Speech recognition unavailable"
    
    try:
        driver.get("file:///" + Link)
        driver.find_element(By.ID, "start").click()

        while True:
            try:
                Text = driver.find_element(By.ID, "output").text
                if Text:
                    driver.find_element(By.ID, "end").click()
                    if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                        return QueryModifier(Text)
                    else:
                        SetAssistantStatus("Translating...")
                        return QueryModifier(UniversalTranslator(Text))
            except Exception:
                pass
    except Exception as e:
        print(f"Speech recognition error: {e}")
        return "Speech recognition error"

def ContinuousLocalSpeechRecognition():
    """
    Continuous local offline speech recognition - DISABLED
    Always returns None to use online STT instead
    """
    # Vosk is permanently disabled - always use online STT
    return None

def ContinuousSpeechRecognition():
    """Continuous speech recognition that listens while mic is on"""
    # Using online STT only (Chrome Web Speech API) - most accurate and reliable
    # Vosk is permanently disabled
    if driver is None:
        print("Speech recognition is disabled due to ChromeDriver issues.")
        return ""
    
    try:
        # Only navigate to page if not already there or if recognition was stopped
        try:
            current_url = driver.current_url
            if "Voice.html" not in current_url:
                driver.get("file:///" + Link)
        except:
            driver.get("file:///" + Link)
        
        # Start recognition if not already running (safe to call multiple times)
        try:
            driver.find_element(By.ID, "start").click()
        except Exception:
            pass  # Already started or element not found
    except Exception as e:
        print(f"Continuous speech recognition initialization error: {e}")
        return ""
    
    accumulated_text = ""
    last_text_length = 0
    no_change_count = 0  # Counter for iterations without text change
    
    while True:
        try:
            # Check if microphone is still on
            mic_status_file = os.path.join(TempDirPath, "Mic.data")
            if os.path.exists(mic_status_file):
                with open(mic_status_file, "r", encoding='utf-8') as file:
                    mic_status = file.read().strip()
                if mic_status.lower() != "true":
                    # Mic turned off, return accumulated text
                    try:
                        driver.find_element(By.ID, "end").click()
                    except:
                        pass
                    
                    if accumulated_text.strip():
                        # Validate transcription before returning
                        modified_text = QueryModifier(accumulated_text) if InputLanguage.lower() == "en" or "en" in InputLanguage.lower() else QueryModifier(UniversalTranslator(accumulated_text))
                        if modified_text and modified_text.strip():
                            if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                                return modified_text
                            else:
                                SetAssistantStatus("Translating...")
                                return QueryModifier(UniversalTranslator(accumulated_text))
                        else:
                            print(f"QueryModifier filtered out transcription: '{accumulated_text}'")
                            return ""
                    else:
                        return ""
            
            # Get current text and clean it
            try:
                current_text = driver.find_element(By.ID, "output").text.strip()
            except:
                current_text = ""
            
            # Clean the text - remove excessive whitespace and normalize
            current_text = " ".join(current_text.split())
            
            # If text has grown, update accumulated text and reset no-change counter
            if len(current_text) > last_text_length:
                # Only update if the new text is meaningful (not just noise)
                if current_text and len(current_text) >= 2:
                    accumulated_text = current_text
                    last_text_length = len(current_text)
                    SetAssistantStatus("Listening...")
                    no_change_count = 0  # Reset counter when text changes
                else:
                    # Text is too short or empty, don't update
                    no_change_count += 1
            else:
                # Text hasn't changed - increment counter
                no_change_count += 1
                
                # If text hasn't changed for a while (user stopped speaking), return the accumulated text
                # Wait longer for natural speech pauses - user might be thinking or taking a breath
                if no_change_count > 150 and accumulated_text.strip():  # About 1.5-2 seconds of no new input
                    print(f"Speech paused - returning accumulated text: '{accumulated_text[:50]}...'")
                    # Save the text to return, then reset for next listening cycle
                    text_to_return = accumulated_text
                    accumulated_text = ""  # Reset for next command
                    last_text_length = 0
                    no_change_count = 0
                    
                    # Clear the output element so recognition can continue fresh
                    try:
                        driver.execute_script("document.getElementById('output').textContent = '';")
                    except:
                        pass
                    
                    # Validate and return the detected text
                    if text_to_return.strip():
                        # Apply QueryModifier which will filter bad transcriptions
                        modified_text = QueryModifier(text_to_return) if InputLanguage.lower() == "en" or "en" in InputLanguage.lower() else QueryModifier(UniversalTranslator(text_to_return))
                        
                        # Only return if QueryModifier didn't filter it out
                        if modified_text and modified_text.strip():
                            if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                                return modified_text
                            else:
                                SetAssistantStatus("Translating...")
                                return QueryModifier(UniversalTranslator(text_to_return))
                        else:
                            print(f"QueryModifier filtered out transcription: '{text_to_return}'")
                            return ""
                    else:
                        return ""
                
        except Exception as e:
            print(f"Error in continuous speech recognition: {e}")
            # If we have accumulated text, return it
            if accumulated_text.strip():
                try:
                    driver.find_element(By.ID, "end").click()
                    if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                        return QueryModifier(accumulated_text)
                    else:
                        SetAssistantStatus("Translating...")
                        return QueryModifier(UniversalTranslator(accumulated_text))
                except:
                    return accumulated_text
            pass

# Run the assistant
if __name__ == "__main__":
    while True:
        Text = SpeechRecognition()
        print(Text)
