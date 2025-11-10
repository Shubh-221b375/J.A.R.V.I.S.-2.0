from AppOpener import close, open as appopen
from AppOpener import close, open as appopen
from webbrowser import open as webopen
# Lazy import for pywhatkit to avoid connection check on import
# from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os
from typing import Optional, Dict, Any, List

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize Groq client with error handling
client = None

classes = ["zCubwf", "hgKELc", "LTKOO SY7ric", "ZOLcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta",
           "IZ6rdc", "05uR6d LTKOO", "vlzY6d", "webanswers-webanswers_table_webanswers-table", "dDoNo ikb4Bb gsrt", "sXLa0e", 
           "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

# Initialize Groq client only if API key exists
if GroqAPIKey and client is None:
    try:
        client = Groq(api_key=GroqAPIKey)
    except Exception as e:
        print(f"Error initializing Groq client in Automation: {e}")
        client = None

professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need—don't hesitate to ask.",
]

messages = []

SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ.get('Username', 'User')}, a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems, etc."}]


def GoogleSearch(topic):
    try:
        from pywhatkit import search
        search(topic)
    except Exception as e:
        print(f"Error using pywhatkit search: {e}")
        # Fallback to direct web search
        webbrowser.open(f"https://www.google.com/search?q={topic.replace(' ', '+')}")
    return True


def Content(topic):
    def OpenNotepad(file):
        try:
            default_text_editor = 'notepad.exe'
            subprocess.Popen([default_text_editor, file])
            return True
        except Exception as e:
            print(f"Error opening notepad: {e}")
            return False

    def ContentWriterAI(prompt):
        if not client:
            print("Error: Groq API key not found. Please check your .env file.")
            return "Error: Unable to generate content - API key missing."
        
        try:
            messages.append({"role": "user", "content": f"{prompt}"})

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=SystemChatBot + messages,
                max_tokens=2048,
                temperature=0.7,
                top_p=1,
                stream=True,
                stop=None
            )

            answer = ""

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    answer += chunk.choices[0].delta.content

            answer = answer.replace("</s>", "")
            messages.append({"role": "assistant", "content": answer})
            return answer
        except Exception as e:
            print(f"Error generating content: {e}")
            return f"Error: Unable to generate content - {str(e)}"

    topic = topic.replace("content", "").strip()
    content_by_ai = ContentWriterAI(topic)

    # Create Data directory if it doesn't exist
    data_dir = "Data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")

    filepath = os.path.join(data_dir, f"{topic.lower().replace(' ', '_')}.txt")
    
    try:
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content_by_ai)
        print(f"Content written to: {filepath}")
        
        OpenNotepad(filepath)
        return True
    except Exception as e:
        print(f"Error writing content to file: {e}")
        return False

# Content("write A application for sick leave")
def YouTubeSearch(topic):
    url = f"https://www.youtube.com/results?search_query={topic}"
    webbrowser.open(url)
    return True


def PlayYoutube(query):
    try:
        from pywhatkit import playonyt
        playonyt(query)
        return True
    except Exception as e:
        print(f"Error playing YouTube video: {e}")
        # Fallback to direct YouTube search
        try:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(url)
            return True
        except Exception as e2:
            print(f"Fallback YouTube search also failed: {e2}")
            return False


def PlaySpotify(song_name):
    """Play music on Spotify via API if possible, fallback to web."""
    try:
        # First, try to open Spotify app if it's not already running
        # This ensures Spotify is available for playback
        try:
            import subprocess
            import platform
            import os
            if platform.system() == "Windows":
                # Check if Spotify is running, if not, open it
                try:
                    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Spotify.exe'], 
                                          capture_output=True, text=True)
                    if 'Spotify.exe' not in result.stdout:
                        # Spotify not running, try to open it
                        spotify_paths = [
                            os.path.expanduser(r"~\AppData\Roaming\Spotify\Spotify.exe"),
                            r"C:\Program Files\Spotify\Spotify.exe",
                            r"C:\Program Files (x86)\Spotify\Spotify.exe"
                        ]
                        for path in spotify_paths:
                            if os.path.exists(path):
                                subprocess.Popen([path])
                                print("Opened Spotify app for playback")
                                import time
                                time.sleep(2)  # Wait for Spotify to start
                                break
                except:
                    pass
        except Exception as open_error:
            print(f"Note: Could not verify/open Spotify app: {open_error}")
        
        from dotenv import dotenv_values
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth

        env = dotenv_values('.env')
        client_id = env.get('SPOTIFY_CLIENT_ID')
        client_secret = env.get('SPOTIFY_CLIENT_SECRET')
        redirect_uri = env.get('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8888/callback')
        # Fix common redirect URI typos
        if redirect_uri and redirect_uri.endswith('callbackc'):
            redirect_uri = redirect_uri[:-1]  # Remove trailing 'c'

        scope = 'user-modify-playback-state user-read-playback-state user-read-currently-playing app-remote-control streaming'

        if client_id and client_secret:
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                           client_secret=client_secret,
                                                           redirect_uri=redirect_uri,
                                                           scope=scope,
                                                           open_browser=True))
            # Search track
            results = sp.search(q=song_name, type='track', limit=1)
            tracks = results.get('tracks', {}).get('items', [])
            if tracks:
                track = tracks[0]
                uri = track['uri']
                # Try to get an active device
                try:
                    devices_response = sp.devices()
                    devices = devices_response.get('devices', []) if devices_response else []
                    # Find active device or first available device
                    device_id = None
                    for device in devices:
                        if device.get('is_active', False):
                            device_id = device['id']
                            break
                    if not device_id and devices:
                        device_id = devices[0]['id']
                except Exception as device_error:
                    print(f"Error getting devices: {device_error}")
                    devices = []
                    device_id = None
                
                try:
                    if device_id:
                        sp.start_playback(device_id=device_id, uris=[uri])
                        print(f"Playing on Spotify: {track['name']} - {track['artists'][0]['name']}")
                        return True
                    else:
                        # No active device: open track on the web as a hint for the user to pick device
                        webbrowser.open(track['external_urls']['spotify'])
                        print(f"Opened Spotify track: {track['name']} - {track['artists'][0]['name']}")
                        return True
                except Exception as e:
                    print(f"Spotify playback error: {e}")
                    webbrowser.open(track['external_urls']['spotify'])
                    return True
        # If no credentials or API fails, open web search
        spotify_url = f"https://open.spotify.com/search/{song_name.replace(' ', '%20')}"
        webbrowser.open(spotify_url)
        print(f"Opening Spotify search for: {song_name}")
        return True
    except Exception as e:
        print(f"Error opening/playing on Spotify: {e}")
        # Prefer Spotify Web fallback instead of YouTube
        try:
            spotify_url = f"https://open.spotify.com/search/{song_name.replace(' ', '%20')}"
            webbrowser.open(spotify_url)
            print(f"Fallback: Opening Spotify Web search for: {song_name}")
            return True
        except Exception as e2:
            print(f"Spotify Web fallback failed: {e2}")
            # Last-resort fallback: YouTube
            try:
                from pywhatkit import playonyt
                playonyt(song_name)
                print(f"Last resort: Playing on YouTube: {song_name}")
                return True
            except Exception as e3:
                print(f"Error with YouTube fallback: {e3}")
                # Final fallback - direct YouTube URL
                try:
                    url = f"https://www.youtube.com/results?search_query={song_name.replace(' ', '+')}"
                    webbrowser.open(url)
                    return True
                except:
                    return False


# Assuming `AppOpener` and `webopen` are defined or imported
import webbrowser
import requests
from bs4 import BeautifulSoup
import subprocess
import os
import platform
import threading
import time

# Lock to prevent multiple simultaneous opens of the same app
_app_open_locks = {}
_app_last_opened = {}
_open_lock = threading.Lock()

def OpenApp(app, sess=requests.session()):
    app_lower = app.lower()
    
    # CRITICAL: Prevent multiple simultaneous opens of the same app
    with _open_lock:
        current_time = time.time()
        # Check if this app was opened in the last 2 seconds
        if app_lower in _app_last_opened:
            time_since_last = current_time - _app_last_opened[app_lower]
            if time_since_last < 2.0:  # 2 second cooldown
                print(f"App '{app}' was opened {time_since_last:.2f} seconds ago - skipping duplicate open")
                return True  # Return True to indicate "success" (already open)
        
        # Update last opened time
        _app_last_opened[app_lower] = current_time
    
    # Handle specific apps directly to avoid AppOpener issues
    if "instagram" in app_lower:
        try:
            webbrowser.open("https://www.instagram.com")
            print("Opened Instagram in web browser")
            return True
        except Exception as e:
            print(f"Failed to open Instagram: {e}")
            return False
    elif "whatsapp" in app_lower:
        try:
            # Use webbrowser.get() to ensure only one tab opens
            browser = webbrowser.get()
            browser.open("https://web.whatsapp.com")
            print("Opened WhatsApp Web in browser")
            return True
        except Exception as e:
            print(f"Failed to open WhatsApp: {e}")
            return False
    elif "facebook" in app_lower:
        try:
            webbrowser.open("https://www.facebook.com")
            print("Opened Facebook in web browser")
            return True
        except Exception as e:
            print(f"Failed to open Facebook: {e}")
            return False
    elif "twitter" in app_lower or "x" in app_lower:
        try:
            webbrowser.open("https://www.twitter.com")
            print("Opened Twitter in web browser")
            return True
        except Exception as e:
            print(f"Failed to open Twitter: {e}")
            return False
    elif "youtube" in app_lower:
        try:
            # Use webbrowser.get() to ensure only one tab opens
            browser = webbrowser.get()
            browser.open("https://www.youtube.com")
            print("Opened YouTube in web browser (single tab)")
            return True
        except Exception as e:
            print(f"Failed to open YouTube: {e}")
            return False
    elif "spotify" in app_lower:
        try:
            # Try to open Spotify desktop app first
            try:
                # Windows
                if platform.system() == "Windows":
                    spotify_paths = [
                        os.path.expanduser(r"~\AppData\Roaming\Spotify\Spotify.exe"),
                        r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
                        r"C:\Program Files\Spotify\Spotify.exe",
                        r"C:\Program Files (x86)\Spotify\Spotify.exe"
                    ]
                    for path in spotify_paths:
                        if os.path.exists(path):
                            subprocess.Popen([path])
                            print("Opened Spotify desktop app")
                            return True
                    # Try AppOpener as fallback
                    result = appopen("spotify", match_closest=True, output=True, throw_error=False)
                    if result:
                        print("Opened Spotify using AppOpener")
                        return True
                # macOS
                elif platform.system() == "Darwin":
                    subprocess.run(["open", "-a", "Spotify"])
                    print("Opened Spotify desktop app")
                    return True
                # Linux
                elif platform.system() == "Linux":
                    subprocess.Popen(["spotify"])
                    print("Opened Spotify desktop app")
                    return True
            except Exception as app_error:
                print(f"Failed to open Spotify app: {app_error}")
            
            # Fallback: Open Spotify web player
            browser = webbrowser.get()
            browser.open("https://open.spotify.com")
            print("Opened Spotify web player")
            return True
        except Exception as e:
            print(f"Failed to open Spotify: {e}")
            return False
    
    # For other apps, try AppOpener
    try:
        # Try to open the app using AppOpener with better matching
        result = appopen(app, match_closest=True, output=True, throw_error=True)
        # Check if the result actually opened the right app
        if result and app.lower() in str(result).lower():
            return True
        else:
            print(f"AppOpener opened wrong app: {result}")
            raise Exception("Wrong app opened")

    except Exception as e:
        print(f"AppOpener failed for {app}: {e}")
        # Try alternative approaches for other apps
        if "chrome" in app_lower:
            try:
                subprocess.Popen(["chrome"])
                return True
            except:
                try:
                    subprocess.Popen(["google-chrome"])
                    return True
                except:
                    pass
        def extract_links(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, 'html.parser')
            # Find all anchors with valid href attributes
            links = soup.find_all('a', href=True)
            return [link.get('href') for link in links]
            
        def search_google(query):
            url = f"https://www.microsoft.com/en-us/search?q={query}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
            response = sess.get(url, headers=headers)
            if response.status_code == 200:
                return response.text
            else:
                print("Failed to retrieve search results.")
                return None

        def open_in_chrome_beta(url):
            """Open URL specifically in Google Chrome Beta"""
            system = platform.system()
            
            try:
                if system == "Windows":
                    # Common Chrome Beta paths on Windows
                    chrome_beta_paths = [
                        r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome Beta\Application\chrome.exe",
                        os.path.expanduser(r"~\AppData\Local\Google\Chrome Beta\Application\chrome.exe")
                    ]
                    
                    for path in chrome_beta_paths:
                        if os.path.exists(path):
                            subprocess.run([path, url])
                            return True
                    
                    # Fallback to regular Chrome if Beta not found
                    chrome_stable_paths = [
                        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
                    ]
                    
                    for path in chrome_stable_paths:
                        if os.path.exists(path):
                            print("Chrome Beta not found, using stable Chrome")
                            subprocess.run([path, url])
                            return True
                
                elif system == "Darwin":  # macOS
                    # Try Chrome Beta first
                    try:
                        subprocess.run(["open", "-a", "Google Chrome Beta", url])
                        return True
                    except:
                        print("Chrome Beta not found, trying stable Chrome")
                        subprocess.run(["open", "-a", "Google Chrome", url])
                        return True
                
                elif system == "Linux":
                    # Try Chrome Beta first
                    try:
                        subprocess.run(["google-chrome-beta", url])
                        return True
                    except:
                        print("Chrome Beta not found, trying stable Chrome")
                        subprocess.run(["google-chrome", url])
                        return True
                
                # Final fallback to default browser
                print("Chrome Beta and stable Chrome not found, opening in default browser")
                webbrowser.open(url)
                return True
                
            except Exception as e:
                print(f"Error opening Chrome Beta: {e}")
                # Final fallback
                webbrowser.open(url)
                return True

        # Attempt a search for the app
        try:
            html = search_google(app)
            if html:
                links = extract_links(html)
                if links:
                    link = links[0]
                    open_in_chrome_beta(link)
                    return True
        except Exception as e:
            print(f"Web search fallback failed: {e}")
        
        # Final fallback - just return False if nothing worked
        print(f"Could not open {app} - no suitable method found")
        return False
# OpenApp("instagram")
def CloseApp(app):
    if "chrome" in app.lower():
        try:
            subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], check=True)
            print(f"Closed Chrome using taskkill")
            return True
        except:
            pass
    
    try:
        close(app, match_closest=True, output=True, throw_error=True)
        print(f"Closed {app} using AppOpener")
        return True
    except Exception as e:
        print(f"Error closing {app}: {e}")
        return False


def System(command):
    def mute():
        keyboard.press_and_release("volume mute")

    def unmute():
        keyboard.press_and_release("volume mute")

    def volume_up():
        keyboard.press_and_release("volume up")

    def volume_down():
        keyboard.press_and_release("volume down")

    try:
        if command == "mute":
            mute()
        elif command == "unmute":
            unmute()
        elif command == "volume up":
            volume_up()
        elif command == "volume down":
            volume_down()
        else:
            print(f"Unknown system command: {command}")
            return False
        
        print(f"Executed system command: {command}")
        return True
    except Exception as e:
        print(f"Error executing system command {command}: {e}")
        return False


async def TranslateAndExecute(commands: list[str]):
    funcs = []
    
    # CRITICAL: Deduplicate commands to prevent multiple executions of the same command
    # This prevents "open youtube" from being executed 4 times
    seen_commands = set()
    unique_commands = []
    for cmd in commands:
        # Normalize command for comparison (lowercase, strip whitespace)
        cmd_normalized = cmd.lower().strip()
        if cmd_normalized not in seen_commands:
            seen_commands.add(cmd_normalized)
            unique_commands.append(cmd)  # Keep original case for execution
        else:
            print(f"Duplicate command detected and skipped: '{cmd}'")
    
    print(f"Original commands: {len(commands)}, Unique commands: {len(unique_commands)}")
    commands = unique_commands  # Use deduplicated list

    def parse_play_intent(text: str):
        t = text.lower().strip()
        # normalize quotes and dots
        t = t.replace("\"", "").replace("'", "").replace("  ", " ")
        # spotify patterns
        if ("play" in t and "on spotify" in t) or t.startswith("play spotify"):
            # extract after 'play' or 'play spotify'
            name = t
            if "on spotify" in t:
                name = name.split("play", 1)[1].split("on spotify", 1)[0]
            elif t.startswith("play spotify"):
                name = name.split("play spotify", 1)[1]
            return ("spotify", name.strip())
        # youtube patterns
        if ("play" in t and "on youtube" in t) or t.startswith("play youtube"):
            name = t
            if "on youtube" in t:
                name = name.split("play", 1)[1].split("on youtube", 1)[0]
            elif t.startswith("play youtube"):
                name = name.split("play youtube", 1)[1]
            return ("youtube", name.strip())
        return (None, None)

    def parse_open_intent(text: str):
        t = text.lower().strip().replace("\"", "").replace("'", "").replace("  ", " ")
        if t.startswith("open "):
            app = t.split("open ", 1)[1].strip()
            return app
        # common phrasing: "please open notepad", "could you open chrome"
        if " open " in f" {t} ":
            app = t.split(" open ", 1)[1].strip()
            return app
        return None

    for command in commands:
        print(f"Processing command: {command}")
        
        if command.startswith("open "):
            app_name = command.removeprefix("open ").strip()
            fun = asyncio.to_thread(OpenApp, app_name)
            funcs.append(fun)
        elif command.startswith("close "):
            app_name = command.removeprefix("close ").strip()
            fun = asyncio.to_thread(CloseApp, app_name)
            funcs.append(fun)
        elif command.startswith("play spotify "):
            song_name = command.removeprefix("play spotify ").strip()
            fun = asyncio.to_thread(PlaySpotify, song_name)
            funcs.append(fun)
        elif command.startswith("play "):
            query = command.removeprefix("play ").strip()
            fun = asyncio.to_thread(PlayYoutube, query)
            funcs.append(fun)
        elif command.startswith("general "):
            # Heuristic: map natural phrases to play actions without changing other systems
            natural_text = command.removeprefix("general ")
            
            # Check for combined commands like "open spotify and play song"
            if " and " in natural_text.lower():
                parts = natural_text.lower().split(" and ", 1)
                # Check if first part is "open spotify" and second part is "play song"
                if parts[0].strip().startswith("open spotify") and "play" in parts[1].strip():
                    # Extract song name from second part
                    play_part = parts[1].strip()
                    if play_part.startswith("play "):
                        song_name = play_part.replace("play ", "").strip()
                        # First open Spotify, then play song
                        print(f"Detected combined command: open spotify and play {song_name}")
                        funcs.append(asyncio.to_thread(OpenApp, "spotify"))
                        funcs.append(asyncio.to_thread(PlaySpotify, song_name))
                        continue
            
            intent, name = parse_play_intent(natural_text)
            if intent == "spotify" and name:
                funcs.append(asyncio.to_thread(PlaySpotify, name))
            elif intent == "youtube" and name:
                funcs.append(asyncio.to_thread(PlayYoutube, name))
            else:
                app = parse_open_intent(natural_text)
                if app:
                    # Check if we already have an "open {app}" command to avoid duplicates
                    app_command = f"open {app.lower()}"
                    if app_command not in [c.lower().strip() for c in commands]:
                        funcs.append(asyncio.to_thread(OpenApp, app))
                    else:
                        print(f"Skipping duplicate: 'general {natural_text}' already handled by 'open {app}' command")
        elif command.startswith("content "):
            topic = command.removeprefix("content ").strip()
            fun = asyncio.to_thread(Content, topic)
            funcs.append(fun)
        elif command.startswith("google search "):
            query = command.removeprefix("google search ").strip()
            fun = asyncio.to_thread(GoogleSearch, query)
            funcs.append(fun)
        elif command.startswith("youtube search "):
            query = command.removeprefix("youtube search ").strip()
            fun = asyncio.to_thread(YouTubeSearch, query)
            funcs.append(fun)
        elif command.startswith("system "):
            sys_command = command.removeprefix("system ").strip()
            fun = asyncio.to_thread(System, sys_command)
            funcs.append(fun)
        elif command.startswith("send email "):
            # Parse email command: "send email to email@example.com subject message"
            email_params = command.removeprefix("send email ").strip()
            # Try to extract email, subject, and message
            # Simple parsing - can be enhanced
            parts = email_params.split(" ", 2)
            if len(parts) >= 2:
                to_email = parts[0] if "@" in parts[0] else None
                if to_email:
                    subject = parts[1] if len(parts) > 1 else "No Subject"
                    body = parts[2] if len(parts) > 2 else "No message content"
                    fun = asyncio.to_thread(send_email, to_email, subject, body)
                    funcs.append(fun)
        elif command.startswith("send whatsapp "):
            # Parse WhatsApp command: "send whatsapp to +1234567890 message"
            whatsapp_params = command.removeprefix("send whatsapp ").strip()
            parts = whatsapp_params.split(" ", 2)
            if len(parts) >= 2:
                phone = parts[0]
                message = parts[1] if len(parts) > 1 else "Hello"
                fun = asyncio.to_thread(whatsapp_automation, phone, message)
                funcs.append(fun)
        elif command.startswith("schedule meeting "):
            # Parse meeting command: "schedule meeting title datetime attendees"
            meeting_params = command.removeprefix("schedule meeting ").strip()
            # Use ChatBot to parse this properly, then execute
            # For now, simple parsing
            parts = meeting_params.split(" ", 2)
            if len(parts) >= 1:
                title = parts[0] if len(parts) > 0 else "Meeting"
                datetime_str = parts[1] if len(parts) > 1 else None
                attendees = parts[2].split(",") if len(parts) > 2 else []
                fun = asyncio.to_thread(schedule_meeting, title, datetime_str or "", 30, attendees if attendees else None)
                funcs.append(fun)
        elif command.startswith("sync crm "):
            # Parse CRM sync command
            sync_params = command.removeprefix("sync crm ").strip()
            operation = sync_params if sync_params else "read"
            fun = asyncio.to_thread(data_sync, "sheets", operation)
            funcs.append(fun)
        else:
            print(f"No function found for command: {command}")

    if funcs:
        results = await asyncio.gather(*funcs, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Command {i+1} failed with exception: {result}")
            else:
                print(f"Command {i+1} result: {result}")
            yield result
    else:
        print("No valid commands to execute")


async def Automation(commands: list[str]):
    print(f"Starting automation with commands: {commands}")
    results = []
    async for result in TranslateAndExecute(commands):
        results.append(result)
    print(f"Automation completed. Results: {results}")
    return True


# ============================================================================
# SALES AUTOMATION FUNCTIONS
# Email, WhatsApp, and CRM integration functions for sales operations
# ============================================================================

def send_email(to_email: str, subject: str, body: str, from_email: Optional[str] = None) -> bool:
    """
    Send email using SMTP or email service API
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email (uses env var if not provided)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import smtplib
        
        env_vars = dotenv_values(".env")
        
        # Get email configuration from environment
        smtp_server = env_vars.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(env_vars.get("SMTP_PORT", "587"))
        email_user = from_email or env_vars.get("EMAIL_USER")
        email_password = env_vars.get("EMAIL_PASSWORD")
        
        if not email_user or not email_password:
            print("Email configuration not found in .env file")
            print("To enable email sending, add:")
            print("  EMAIL_USER=your_email@gmail.com")
            print("  EMAIL_PASSWORD=your_app_password")
            print("  SMTP_SERVER=smtp.gmail.com (optional)")
            print("  SMTP_PORT=587 (optional)")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_password)
        text = msg.as_string()
        server.sendmail(email_user, to_email, text)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        print("Note: For Gmail, you may need to use an 'App Password' instead of your regular password")
        return False


def whatsapp_automation(phone_number: str, message: str) -> bool:
    """
    Send WhatsApp message using Twilio API or web automation
    
    Args:
        phone_number: Phone number with country code (e.g., +1234567890)
        message: Message content to send
        
    Returns:
        True if message sent successfully, False otherwise
    """
    try:
        env_vars = dotenv_values(".env")
        
        # Try Twilio API first
        twilio_account_sid = env_vars.get("TWILIO_ACCOUNT_SID")
        twilio_auth_token = env_vars.get("TWILIO_AUTH_TOKEN")
        twilio_whatsapp_from = env_vars.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        
        if twilio_account_sid and twilio_auth_token:
            try:
                from twilio.rest import Client  # type: ignore
                
                client = Client(twilio_account_sid, twilio_auth_token)
                
                message_obj = client.messages.create(
                    body=message,
                    from_=twilio_whatsapp_from,
                    to=f"whatsapp:{phone_number}"
                )
                
                print(f"WhatsApp message sent successfully. SID: {message_obj.sid}")
                return True
            except ImportError:
                print("Twilio library not installed. Install with: pip install twilio")
            except Exception as e:
                print(f"Twilio API error: {e}")
        
        # Fallback: Open WhatsApp Web with pre-filled message
        print("Opening WhatsApp Web with pre-filled message...")
        whatsapp_url = f"https://web.whatsapp.com/send?phone={phone_number}&text={message.replace(' ', '%20')}"
        webbrowser.open(whatsapp_url)
        print("Please manually send the message from WhatsApp Web")
        return True
        
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False


def data_sync(source: str = "sheets", operation: str = "read") -> Dict[str, Any]:
    """
    Sync data with Google Sheets or CRM systems
    
    Args:
        source: Data source ("sheets", "crm", "csv")
        operation: Operation type ("read", "write", "update")
        
    Returns:
        Dictionary with sync results
    """
    try:
        env_vars = dotenv_values(".env")
        
        if source == "sheets":
            # Google Sheets integration
            try:
                import gspread  # type: ignore
                from google.oauth2.service_account import Credentials  # type: ignore
                
                credentials_path = env_vars.get("GOOGLE_CREDENTIALS_PATH")
                spreadsheet_id = env_vars.get("GOOGLE_SPREADSHEET_ID")
                
                if not credentials_path or not spreadsheet_id:
                    return {
                        "success": False,
                        "error": "Google Sheets credentials not configured. Add GOOGLE_CREDENTIALS_PATH and GOOGLE_SPREADSHEET_ID to .env"
                    }
                
                # Connect to Google Sheets
                scope = ['https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive']
                creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
                client = gspread.authorize(creds)
                sheet = client.open_by_key(spreadsheet_id).sheet1
                
                if operation == "read":
                    data = sheet.get_all_records()
                    return {
                        "success": True,
                        "data": data,
                        "rows": len(data)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Operation '{operation}' not yet implemented for Google Sheets"
                    }
                    
            except ImportError:
                return {
                    "success": False,
                    "error": "Google Sheets libraries not installed. Install with: pip install gspread google-auth"
                }
        
        elif source == "csv":
            # CSV file sync
            csv_path = env_vars.get("CRM_CSV_PATH", "Data/crm_data.csv")
            
            if operation == "read":
                try:
                    import pandas as pd
                    df = pd.read_csv(csv_path)
                    return {
                        "success": True,
                        "data": df.to_dict('records'),
                        "rows": len(df)
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Error reading CSV: {e}"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Operation '{operation}' not yet implemented for CSV"
                }
        
        else:
            return {
                "success": False,
                "error": f"Unsupported source: {source}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Data sync error: {e}"
        }


def schedule_meeting(title: str, date_time: str, duration_minutes: int = 30, attendees: List[str] = None) -> bool:
    """
    Schedule meeting in Google Calendar or Outlook
    
    Args:
        title: Meeting title
        date_time: Meeting date and time (ISO format or readable string)
        duration_minutes: Meeting duration in minutes
        attendees: List of attendee email addresses
        
    Returns:
        True if meeting scheduled successfully
    """
    try:
        # For now, create a calendar event file that can be imported
        from datetime import datetime, timedelta
        
        # Parse date_time
        try:
            if isinstance(date_time, str):
                meeting_time = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
            else:
                meeting_time = date_time
        except:
            # Try parsing common formats
            meeting_time = datetime.now() + timedelta(days=1)  # Default to tomorrow
        
        end_time = meeting_time + timedelta(minutes=duration_minutes)
        
        # Create ICS file for calendar import
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Sales Assistant//Meeting Scheduler//EN
BEGIN:VEVENT
DTSTART:{meeting_time.strftime('%Y%m%dT%H%M%S')}
DTEND:{end_time.strftime('%Y%m%dT%H%M%S')}
SUMMARY:{title}
"""
        
        if attendees:
            ics_content += "ATTENDEE:" + ",".join([f"mailto:{email}" for email in attendees]) + "\n"
        
        ics_content += """END:VEVENT
END:VCALENDAR"""
        
        # Save ICS file
        os.makedirs("Data", exist_ok=True)
        ics_file = f"Data/meeting_{meeting_time.strftime('%Y%m%d_%H%M%S')}.ics"
        with open(ics_file, 'w') as f:
            f.write(ics_content)
        
        print(f"Calendar event created: {ics_file}")
        print("You can import this .ics file into Google Calendar, Outlook, or Apple Calendar")
        
        # Optionally open calendar if configured
        calendar_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={title.replace(' ', '+')}&dates={meeting_time.strftime('%Y%m%dT%H%M%S')}/{end_time.strftime('%Y%m%dT%H%M%S')}"
        webbrowser.open(calendar_url)
        
        return True
        
    except Exception as e:
        print(f"Error scheduling meeting: {e}")
        return False

