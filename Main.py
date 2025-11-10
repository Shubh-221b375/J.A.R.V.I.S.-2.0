from Frontend.GUI import (
    GraphicalUserInterface,
    SetAsssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition, ContinuousSpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech, interrupt_speech, reset_speech_interrupt
from Backend.ModeManager import get_mode_manager, get_current_mode, set_mode, get_mode_prompt
from Backend.WakeWordDetection import create_wake_word_detector, WakeWordDetector
from Backend.Logger import get_logger, log_wake_word, log_command_routing, log_tts
# Import log_mode_change with fallback
try:
    from Backend.Logger import log_mode_change
except ImportError:
    def log_mode_change(old_mode, new_mode):
        pass
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os

# Initialize logger
logger = get_logger("Main")

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

DefaultMessage = f""" {Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}! I'm your sales-focused AI assistant, ready to help with leads, pitches, follow-ups, and sales strategies. How can I assist you today? """

functions = ["open", "close", "play", "system", "content", "google search", "youtube search", "spotify", "send email", "send whatsapp", "schedule meeting", "sync crm"]
subprocess_list = []

# Global variable to track if we're currently speaking
currently_speaking = False

# Global wake word detector
wake_word_detector = None
wake_word_detected = False
command_listening_mode = False

# Global variables for query deduplication (accessible from GUI too)
last_processed_query = None
last_processed_time = 0
processing_query = False  # Flag to prevent concurrent processing
last_response_text = None  # Track last response to prevent duplicates
last_spoken_text = None  # Track last spoken text to prevent duplicate TTS
last_spoken_time = 0  # Track when last TTS occurred

def on_wake_word_detected():
    """Callback when wake word is detected"""
    global wake_word_detected, command_listening_mode
    logger.info("🔔 WAKE WORD DETECTED - Entering command listening mode")
    wake_word_detected = True
    command_listening_mode = True
    SetAsssistantStatus("Listening...")
    # Play a brief audio cue (optional - can be a simple beep)
    try:
        from Backend.TextToSpeech import fallback_tts
        fallback_tts("Yes?")  # Quick audible cue
    except:
        pass

def check_for_interruption():
    """Check if there's new microphone input to interrupt current speech"""
    global currently_speaking
    if currently_speaking:
        # Actively check for new speech input while speaking
        try:
            from Backend.SpeechToText import ContinuousSpeechRecognition
            # Try to get any new speech input (non-blocking check)
            # This will detect if user starts speaking while JARVIS is speaking
            mic_status = GetMicrophoneStatus()
            if mic_status.lower() == "true":
                # Check if there's new speech by trying to get a quick recognition
                # We'll use a timeout to make it non-blocking
                import threading
                import queue
                
                result_queue = queue.Queue()
                
                def quick_listen():
                    try:
                        # Try to get speech with a very short timeout
                        from Backend.SpeechToText import driver
                        if driver:
                            try:
                                current_text = driver.find_element(By.ID, "output").text.strip()
                                if current_text and len(current_text) > 2:
                                    # New speech detected!
                                    result_queue.put(current_text)
                            except:
                                pass
                    except:
                        pass
                
                # Run quick check in a thread with timeout
                check_thread = threading.Thread(target=quick_listen, daemon=True)
                check_thread.start()
                check_thread.join(timeout=0.1)  # 100ms timeout
                
                # Check if we got any new speech
                try:
                    new_speech = result_queue.get_nowait()
                    if new_speech and len(new_speech.strip()) > 2:
                        print(f"New speech detected during TTS: '{new_speech}' - interrupting!")
                        interrupt_speech()
                        currently_speaking = False
                        return True
                except queue.Empty:
                    pass
                
                # Also check for wake word "jarvis" in any detected text
                try:
                    from Backend.SpeechToText import driver
                    from selenium.webdriver.common.by import By
                    if driver:
                        try:
                            current_text = driver.find_element(By.ID, "output").text.strip().lower()
                            if current_text and ("jarvis" in current_text or "hey jarvis" in current_text or "okay jarvis" in current_text):
                                print(f"Wake word detected during TTS: '{current_text}' - interrupting!")
                                interrupt_speech()
                                currently_speaking = False
                                return True
                        except:
                            pass
                except:
                    pass
        except Exception as e:
            # If check fails, just check mic status as fallback
            current_mic_status = GetMicrophoneStatus()
            if current_mic_status.lower() == "true":
                # For now, if mic is on and we're speaking, allow interrupt
                # (This is a fallback - the active listening above is better)
                pass
    return False

def force_interrupt_speech():
    """Force interrupt any ongoing speech immediately"""
    global currently_speaking
    print("Force interrupting speech")
    interrupt_speech()
    currently_speaking = False
    # Don't return True here to avoid triggering exit logic
    return False

def safe_interrupt_speech():
    """Safe interrupt that only stops speech without affecting execution flow"""
    global currently_speaking
    print("Safe interrupt speech called")
    interrupt_speech()
    currently_speaking = False
    # Always return False to prevent any exit logic
    return False



# Ensure a default chat log exists if no chats are logged
def ShowDefaultChatIfNoChats():
    try:
        with open(r'Data\ChatLog.json', "r", encoding='utf-8') as file:
            if len(file.read()) < 5:
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as temp_file:
                    temp_file.write("")
                with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as response_file:
                    response_file.write(DefaultMessage)
    except FileNotFoundError:
        print("ChatLog.json file not found. Creating default response.")
        os.makedirs("Data", exist_ok=True)
        with open(r'Data\ChatLog.json', "w", encoding='utf-8') as file:
            file.write("[]")
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as response_file:
            response_file.write(DefaultMessage)

# Read chat log from JSON
def ReadChatLogJson():
    try:
        with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
            chatlog_data = json.load(file)
        return chatlog_data
    except FileNotFoundError:
        print("ChatLog.json not found.")
        return []

# Integrate chat logs into a readable format


def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"{Username}: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"{Assistantname}: {entry['content']}\n"

    # Ensure the Temp directory exists
    temp_dir_path = TempDirectoryPath('')  # Get the directory path
    if not os.path.exists(temp_dir_path):
        os.makedirs(temp_dir_path)

    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

# Display the chat on the GUI
def ShowChatOnGUI():
    try:
        with open(TempDirectoryPath('Database.data'), 'r', encoding='utf-8') as file:
            data = file.read()
        if len(str(data)) > 0:
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as response_file:
                response_file.write(data)
    except FileNotFoundError:
        print("Database.data file not found.")

# Initial execution setup
def InitialExecution():
    global wake_word_detector
    
    # Initialize wake word detector with timeout protection
    try:
        import socket
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(5)  # 5 second timeout for network operations
        
        wake_word_detector = create_wake_word_detector(on_wake_word_detected)
        if wake_word_detector.engine_type != "fallback":
            logger.info(f"Wake word detector initialized: {wake_word_detector.engine_type}")
            wake_word_detector.start_listening()
        else:
            logger.info("Wake word detector in fallback mode (STT-based)")
        
        # Restore original timeout
        socket.setdefaulttimeout(original_timeout)
    except socket.timeout:
        logger.warning("Wake word detector initialization timed out - using fallback mode")
        wake_word_detector = None
    except Exception as e:
        logger.error(f"Error initializing wake word detector: {e}", exc_info=True)
        logger.info("Continuing with fallback STT-based detection")
        wake_word_detector = None
    
    SetMicrophoneStatus("True")  # Start with mic ON for continuous listening
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatOnGUI()
    
    # Initialize mode manager
    mode_manager = get_mode_manager()
    current_mode = mode_manager.get_current_mode()
    logger.info(f"JARVIS initialized in {current_mode} mode")

# Main execution logic
def MainExecution():
    global last_processed_query, last_processed_time, processing_query, last_response_text
    
    # Prevent concurrent processing
    if processing_query:
        print("MainExecution: Already processing a query, skipping...")
        return False
    
    try:
        TaskExecution = False
        ImageExecution = False
        ImageGenerationQuery = ""

        # Check for wake word in continuous listening mode
        global wake_word_detected, command_listening_mode
        
        # If using wake word detection and wake word not detected, check for it in text
        if wake_word_detector and wake_word_detector.engine_type == "fallback":
            # In fallback mode, check for wake word in continuous STT
            pass  # Will check in the text below
        
        SetAsssistantStatus("Listening...")
        try:
            # Use continuous speech recognition when mic is ON - it will listen until mic is turned off or speech is detected
            Query = ContinuousSpeechRecognition()
            
            # Check for wake word in the recognized text (fallback mode)
            if Query and wake_word_detector:
                if wake_word_detector.is_wake_word_in_text(Query):
                    logger.info("Wake word detected in text: 'Jarvis'")
                    # Remove wake word from query
                    Query = Query.lower().replace("jarvis", "").replace("hey jarvis", "").replace("okay jarvis", "").strip()
                    if not Query:
                        # Only wake word, no command yet
                        wake_word_detected = True
                        command_listening_mode = True
                        SetAsssistantStatus("Yes? Listening...")
                        try:
                            from Backend.TextToSpeech import fallback_tts
                            fallback_tts("Yes?")
                        except:
                            pass
                        return False  # Continue listening for command
            
            # If continuous recognition returned empty (no speech detected yet or mic turned off)
            if not Query or Query.strip() == "":
                # Check if mic is still ON
                mic_status = GetMicrophoneStatus()
                if mic_status.lower() != "true":
                    print("Mic turned off - stopping listening")
                    SetAsssistantStatus("Available...")
                    return False
                # Mic is still ON but no speech detected yet - this is normal, keep listening
                print("No speech detected yet, continuing to listen (waiting for input)...")
                SetAsssistantStatus("Listening...")
                # Return False so the loop continues listening (doesn't exit)
                return False
            
            # If we got text from continuous recognition, use it
            # Also check if QueryModifier filtered it out (empty string means bad transcription)
            if Query and Query.strip() and Query not in ["Speech recognition unavailable", "Speech recognition error"]:
                # Additional validation - if query is too short or looks like noise, skip it
                query_clean = Query.strip().lower()
                if len(query_clean) < 3:
                    print(f"Query too short, ignoring: '{Query}'")
                    # Continue listening - return False to keep listening
                    return False
                
                # DEDUPLICATION: Check if this is the same query as the last one (prevent duplicate processing)
                import time
                current_time = time.time()
                # Normalize query more aggressively - remove punctuation, extra spaces, convert to lowercase
                query_normalized = query_clean.strip().lower()
                # Remove common punctuation
                import re
                query_normalized = re.sub(r'[^\w\s]', '', query_normalized)
                # Remove extra spaces
                query_normalized = ' '.join(query_normalized.split())
                
                # Special handling for greetings - normalize all greetings to "hello"
                greeting_words = ["hello", "hi", "hey", "namaste", "hola", "greetings"]
                words_list = query_normalized.split()
                if len(words_list) <= 2 and any(word in greeting_words for word in words_list):
                    # Normalize all greetings to "hello" for duplicate detection
                    query_normalized = "hello"
                
                # Skip if it's the same query and was processed recently (within 15 seconds - increased to catch cross-path duplicates)
                # This prevents the same query from being processed multiple times through different paths (voice/text)
                if (last_processed_query == query_normalized and 
                    (current_time - last_processed_time) < 15.0):
                    print(f"MainExecution: Duplicate query detected and skipped: '{Query}' (normalized: '{query_normalized}', processed {current_time - last_processed_time:.2f}s ago)")
                    processing_query = False  # Reset flag since we're skipping
                    return False
                
                # Mark that we're processing this query
                processing_query = True
                last_processed_query = query_normalized
                last_processed_time = current_time
                print(f"MainExecution: Processing new query: '{Query}'")
                # Check if this is a mode switch command
                query_lower = Query.lower().strip()
                mode_switch_commands = {
                    "switch to sales": "Sales Assistant",
                    "sales mode": "Sales Assistant",
                    "sales assistant": "Sales Assistant",
                    "switch to general": "General Assistant",
                    "general mode": "General Assistant",
                    "general assistant": "General Assistant"
                }
                
                # Check for mode switch
                mode_switched = False
                for cmd, mode in mode_switch_commands.items():
                    if cmd in query_lower:
                        old_mode = get_current_mode()
                        if set_mode(mode, source="voice"):
                            mode_switched = True
                            logger.info(f"Mode switched via voice: {old_mode} → {mode}")
                            # Announce mode change via TTS
                            mode_guidance = get_mode_manager().get_mode_guidance(mode)
                            ShowTextToScreen(f"{Assistantname}: {mode_guidance}")
                            SetAsssistantStatus("Answering...")
                            currently_speaking = True
                            try:
                                from Backend.TextToSpeech import fallback_tts, reset_speech_interrupt
                                reset_speech_interrupt()
                                fallback_tts(f"Now in {mode} mode.")
                            except:
                                pass
                            currently_speaking = False
                            # Remove mode command from query if it was just a switch
                            if query_lower.strip() == cmd or query_lower.strip().startswith(cmd):
                                # Just a mode switch, no other command
                                return True
                        break
                
                # Add user message to chat GUI (only once - add_user_message_to_chat handles display)
                # CRITICAL: Always add user message to chat for voice input
                try:
                    from Frontend.GUI import add_user_message_to_chat
                    print(f"Main.py: Adding user voice message to chat: '{Query[:50]}...'")
                    add_user_message_to_chat(Query)
                except Exception as e:
                    print(f"Could not add user message to chat: {e}")
                    import traceback
                    print(traceback.format_exc())
                    # Fallback to ShowTextToScreen if add_user_message_to_chat fails
                    try:
                        ShowTextToScreen(f"{Username}: {Query}")
                    except:
                        print(f"ShowTextToScreen also failed")
                SetAsssistantStatus("Thinking...")
                log_command_routing(Query, "main_execution")
            else:
                print(f"Speech recognition returned error: {Query}")
                # Check mic status - if still ON, go back to listening
                mic_status = GetMicrophoneStatus()
                if mic_status.lower() == "true":
                    SetAsssistantStatus("Listening...")
                else:
                    SetAsssistantStatus("Available...")
                return False
        except Exception as e:
            print(f"Error in continuous speech recognition: {e}")
            # Fallback to regular recognition only if continuous fails completely
            try:
                Query = SpeechRecognition()
                if Query and Query.strip() and Query not in ["Speech recognition unavailable", "Speech recognition error"]:
                    # Add user message to chat GUI (only once - add_user_message_to_chat handles display)
                    try:
                        from Frontend.GUI import add_user_message_to_chat
                        add_user_message_to_chat(Query)
                    except Exception as e:
                        print(f"Could not add user message to chat: {e}")
                        # Fallback to ShowTextToScreen if add_user_message_to_chat fails
                        ShowTextToScreen(f"{Username}: {Query}")
                    SetAsssistantStatus("Thinking...")
                else:
                    mic_status = GetMicrophoneStatus()
                    if mic_status.lower() == "true":
                        SetAsssistantStatus("Listening...")
                    else:
                        SetAsssistantStatus("Available...")
                    return False
            except Exception as e2:
                print(f"Fallback speech recognition also failed: {e2}")
                mic_status = GetMicrophoneStatus()
                if mic_status.lower() == "true":
                    SetAsssistantStatus("Listening...")
                else:
                    SetAsssistantStatus("Available...")
                return False
        
        # Check for chat clearing commands BEFORE processing
        query_lower = Query.lower().strip()
        if any(phrase in query_lower for phrase in ["clear chat", "clear chat history", "clear history", "clear all chats", "delete chat history"]):
            try:
                from Frontend.GUI import clear_chat_history_global
                clear_chat_history_global()
                # Set status back to listening if mic is on
                mic_status = GetMicrophoneStatus()
                if mic_status and mic_status.lower() == "true":
                    SetAsssistantStatus("Listening...")
                else:
                    SetAsssistantStatus("Available...")
                return True
            except Exception as e:
                print(f"Error clearing chat history: {e}")
        
        # Add fallback for Decision making
        try:
            Decision = FirstLayerDMM(Query)
            # If the decision model returned nothing, default to general
            if not Decision:
                Decision = [f"general {Query}"]
        except Exception as e:
            print(f"Error in FirstLayerDMM: {e}")
            Decision = [f"general {Query}"]

        print(f"\nDecision: {Decision}\n")

        # Minimal natural-language to command mapping (no function edits)
        def _parse_play_intent(text: str):
            t = text.lower().strip()
            t = t.replace("\"", "").replace("'", "").replace("  ", " ")
            if ("play" in t and "on spotify" in t) or t.startswith("play spotify"):
                name = t
                if "on spotify" in t:
                    name = name.split("play", 1)[1].split("on spotify", 1)[0]
                elif t.startswith("play spotify"):
                    name = name.split("play spotify", 1)[1]
                return ("spotify", name.strip())
            if ("play" in t and "on youtube" in t) or t.startswith("play youtube"):
                name = t
                if "on youtube" in t:
                    name = name.split("play", 1)[1].split("on youtube", 1)[0]
                elif t.startswith("play youtube"):
                    name = name.split("play youtube", 1)[1]
                return ("youtube", name.strip())
            return (None, None)

        def _parse_open_intent(text: str):
            t = text.lower().strip()
            t = t.replace("\"", "").replace("'", "").replace("  ", " ")
            # starts with open
            if t.startswith("open "):
                return t.split("open ", 1)[1].strip()
            # contains ' open '
            if " open " in f" {t} ":
                return t.split(" open ", 1)[1].strip()
            return None

        # If the DMM labeled it as general but it's a play intent, prepend executable command
        intent, song_name = _parse_play_intent(Query)
        if intent == "spotify" and song_name:
            Decision = [f"play spotify {song_name}"] + Decision
        elif intent == "youtube" and song_name:
            Decision = [f"play {song_name}"] + Decision
        else:
            app_to_open = _parse_open_intent(Query)
            if app_to_open:
                Decision = [f"open {app_to_open}"] + Decision

        G = any([i for i in Decision if i.startswith("general")])
        R = any([i for i in Decision if i.startswith("realtime")])


        Merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        for queries in Decision:
            if "generate" in queries:
                ImageGenerationQuery = str(queries)
                ImageExecution = True

        for queries in Decision:
            if not TaskExecution:
                if any(queries.startswith(func) for func in functions):
                    SetAsssistantStatus("Executing task...")
                    try:
                        run(Automation(list(Decision)))
                        SetAsssistantStatus("Task completed...")
                        ShowTextToScreen(f"{Assistantname}: Task completed successfully!")
                        # Reduced delay for faster response
                        sleep(0.1)
                        # Check if mic is still ON - if so, continue listening
                        mic_status = GetMicrophoneStatus()
                        if mic_status.lower() == "true":
                            SetAsssistantStatus("Listening...")
                        else:
                            SetAsssistantStatus("Available...")
                    except Exception as e:
                        print(f"Automation error: {e}")
                        SetAsssistantStatus("Task failed...")
                        ShowTextToScreen(f"{Assistantname}: Task failed - {str(e)}")
                        sleep(0.1)
                        SetAsssistantStatus("Available...")
                    TaskExecution = True
                    return True  # Return immediately after task completion

        if ImageExecution:
            with open(r'Frontend\Files\ImageGeneration.data', "w") as file:
                file.write(f"{ImageGenerationQuery},True")

            try:
                p1 = subprocess.Popen(
                    ['python', r"Backend\ImageGeneration.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    shell=False,
                )
                subprocess_list.append(p1)
            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")

        if G and R or R:
            SetAsssistantStatus("Searching...")
            Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAsssistantStatus("Answering...")
            # Check for interruption before speaking
            if check_for_interruption():
                print("Interrupted before speaking")
                return True
            currently_speaking = True
            log_tts(Answer, "start")
            
            # CRITICAL: Use fallback_tts directly, NOT TextToSpeech (which calls fallback_tts internally)
            print(f"Main.py TTS (realtime): About to speak answer (length: {len(Answer)})")
            try:
                from Backend.TextToSpeech import fallback_tts, reset_speech_interrupt
                reset_speech_interrupt()
                print("Main.py TTS (realtime): Calling fallback_tts (ONLY ONCE - no duplicates)...")
                result = fallback_tts(Answer)
                print(f"Main.py TTS (realtime): fallback_tts returned: {result}")
                if result:
                    log_tts(Answer, "stop")
                    print("Main.py TTS (realtime): TTS completed successfully - DO NOT call TextToSpeech")
                else:
                    print("Main.py TTS (realtime): WARNING - fallback_tts returned False")
            except Exception as tts_error:
                print(f"Main.py TTS (realtime) ERROR: {tts_error}")
                import traceback
                print(traceback.format_exc())
                print("Main.py TTS (realtime): Error occurred, but NOT calling TextToSpeech to prevent duplicates")
            
            # IMPORTANT: Wait for TTS to completely finish (reduced delay for faster response)
            import time
            time.sleep(0.1)  # Reduced from 0.2 to 0.1 for faster response
            
            currently_speaking = False
            # IMMEDIATELY update status after TTS completes
            try:
                mic_status = GetMicrophoneStatus()
                if mic_status.lower() == "true":
                    SetAsssistantStatus("Listening...")
                    print("✅ Status updated to: Listening... (mic is ON)")
                else:
                    SetAsssistantStatus("Available...")
                    print("✅ Status updated to: Available... (mic is OFF)")
            except Exception as status_error:
                print(f"Error updating status: {status_error}")
                # Force set to Listening if mic is likely on
                try:
                    SetAsssistantStatus("Listening...")
                    print("✅ Force set status to: Listening...")
                except:
                    pass
            return True
        else:
            # Check if Decision list is empty or invalid
            if not Decision or len(Decision) == 0:
                print("Main.py: WARNING - Decision list is empty, defaulting to general query")
                Decision = [f"general {Query}"]
            
            print(f"Main.py: Processing Decision list: {Decision}")
            response_generated = False
            
            for queries in Decision:
                if "general" in queries:
                    SetAsssistantStatus("Thinking...")
                    QueryFinal = queries.replace("general", "").strip()
                    
                    if not QueryFinal:
                        QueryFinal = Query
                    
                    print(f"Main.py: Calling ChatBot with query: '{QueryFinal[:100]}...'")
                    
                    # Get current mode and use it in ChatBot
                    current_mode = get_current_mode()
                    logger.debug(f"Processing query in {current_mode} mode")
                    print(f"Main.py: Current mode: {current_mode}")
                    
                    try:
                        Answer = ChatBot(QueryModifier(QueryFinal), mode=current_mode)
                        print(f"Main.py: ChatBot returned answer (length: {len(Answer) if Answer else 0})")
                        response_generated = True
                    except Exception as e:
                        logger.error(f"Error in ChatBot: {e}", exc_info=True)
                        import traceback
                        print(f"Main.py: ChatBot ERROR: {traceback.format_exc()}")
                        Answer = "I'm here to help! What would you like to know?"
                        response_generated = True
                    
                    # Ensure Answer is not None or empty
                    if not Answer or not Answer.strip():
                        print("Main.py: WARNING - ChatBot returned empty answer, using default")
                        Answer = "I'm here to help! What would you like to know?"
                        response_generated = True
                    
                    # Check if this is a duplicate response (more robust comparison)
                    # last_response_text and last_processed_query are already declared as global at function start
                    import time
                    import re
                    # Normalize answer for comparison - remove extra spaces, punctuation, take first 200 chars
                    answer_normalized = Answer.strip().lower()
                    answer_normalized = re.sub(r'[^\w\s]', '', answer_normalized)  # Remove punctuation
                    answer_normalized = ' '.join(answer_normalized.split())  # Remove extra spaces
                    answer_normalized = answer_normalized[:200]  # First 200 chars for better comparison
                    
                    # Also check if this is the same query being processed again
                    query_normalized_check = last_processed_query
                    current_time_check = time.time()
                    
                    # CRITICAL: Skip ENTIRE response (display + TTS) if same query was processed very recently
                    # This prevents duplicate responses for the same query
                    # Note: We already check for duplicate queries at the start of MainExecution,
                    # but this is a safety check in case a query slips through
                    if (query_normalized_check and 
                        (current_time_check - last_processed_time) < 5.0):
                        # Check if this response is for the same query (by checking if it's very recent)
                        print(f"Main.py: Recent query detected - processed {current_time_check - last_processed_time:.2f}s ago")
                        # Don't skip here - let the text-based duplicate check handle it
                    
                    # Skip DISPLAY if same response text was shown very recently (within 5 seconds)
                    # This catches cases where different modes generate similar responses
                    is_duplicate_text = (last_response_text == answer_normalized and 
                                         (current_time_check - last_processed_time) < 5.0)
                    
                    if is_duplicate_text:
                        print(f"Main.py: Duplicate response text detected, skipping display and TTS")
                        processing_query = False  # Reset flag
                        return True  # Return early - don't display or speak
                    else:
                        last_response_text = answer_normalized
                        print(f"Main.py: Displaying answer: '{Answer[:100]}...'")
                        ShowTextToScreen(f"{Assistantname}: {Answer}")
                        print(f"Main.py: Answer displayed to screen")
                    
                    SetAsssistantStatus("Answering...")
                    
                    # Check for interruption before speaking
                    if check_for_interruption():
                        print("Interrupted before speaking")
                        return True
                    
                    # Check if this exact text was already spoken recently (within 5 seconds)
                    global last_spoken_text, last_spoken_time
                    import time
                    answer_normalized_tts = ' '.join(Answer.strip().split())
                    current_tts_time = time.time()
                    
                    if (last_spoken_text == answer_normalized_tts and 
                        (current_tts_time - last_spoken_time) < 5.0):
                        print(f"Main.py TTS: Duplicate speech detected, skipping TTS: '{Answer[:50]}...'")
                        currently_speaking = False
                        processing_query = False
                        return True
                    
                    # Mark this as about to be spoken
                    last_spoken_text = answer_normalized_tts
                    last_spoken_time = current_tts_time
                    
                    currently_speaking = True
                    log_tts(Answer, "start")
                    
                    # Use direct fallback_tts for maximum reliability (ONLY ONCE - no duplicates)
                    print(f"Main.py TTS: About to speak answer (length: {len(Answer)})")
                    print(f"Main.py TTS: Answer preview: {Answer[:150]}...")
                    has_newlines = '\n' in Answer
                    print(f"Main.py TTS: Answer contains newlines: {has_newlines}")
                    
                    # CRITICAL: Only call TTS ONCE - use fallback_tts directly, NEVER call TextToSpeech
                    # TextToSpeech internally calls fallback_tts, which would cause duplicates
                    tts_called = False
                    try:
                        from Backend.TextToSpeech import fallback_tts, reset_speech_interrupt
                        reset_speech_interrupt()
                        print("Main.py TTS: Calling fallback_tts (ONLY ONCE - no duplicates)...")
                        result = fallback_tts(Answer)
                        tts_called = True
                        print(f"Main.py TTS: fallback_tts returned: {result}")
                        if result:
                            log_tts(Answer, "stop")
                            print("Main.py TTS: TTS completed successfully - DO NOT call TextToSpeech")
                        else:
                            print("Main.py TTS: WARNING - fallback_tts returned False, trying simple pyttsx3 as fallback...")
                            # Try a simple direct pyttsx3 call as last resort (only if fallback_tts failed)
                            try:
                                import pyttsx3
                                simple_engine = pyttsx3.init()
                                simple_engine.setProperty('rate', 200)
                                simple_engine.setProperty('volume', 1.0)
                                # Clean text
                                clean_text = Answer.replace('\n', ' ').replace('\r', ' ').strip()
                                while '  ' in clean_text:
                                    clean_text = clean_text.replace('  ', ' ')
                                if clean_text:
                                    simple_engine.say(clean_text)
                                    simple_engine.runAndWait()
                                    print("Main.py TTS: Simple pyttsx3 fallback succeeded")
                            except Exception as simple_error:
                                print(f"Main.py TTS: Simple pyttsx3 fallback also failed: {simple_error}")
                    except Exception as tts_error:
                        print(f"Main.py TTS ERROR: {tts_error}")
                        import traceback
                        print(traceback.format_exc())
                        # Try simple pyttsx3 as last resort
                        try:
                            print("Main.py TTS: Trying simple pyttsx3 as last resort after exception...")
                            import pyttsx3
                            simple_engine = pyttsx3.init()
                            simple_engine.setProperty('rate', 200)
                            simple_engine.setProperty('volume', 1.0)
                            clean_text = Answer.replace('\n', ' ').replace('\r', ' ').strip()
                            while '  ' in clean_text:
                                clean_text = clean_text.replace('  ', ' ')
                            if clean_text:
                                simple_engine.say(clean_text)
                                simple_engine.runAndWait()
                                print("Main.py TTS: Simple pyttsx3 fallback succeeded after exception")
                        except Exception as simple_error:
                            print(f"Main.py TTS: All TTS methods failed: {simple_error}")
                    
                    # IMPORTANT: Wait for TTS to completely finish (reduced for speed)
                    import time
                    time.sleep(0.1)  # Reduced from 0.5 to 0.1 for faster response
                    
                    currently_speaking = False
                    # IMMEDIATELY update status after TTS completes
                    try:
                        mic_status = GetMicrophoneStatus()
                        if mic_status.lower() == "true":
                            SetAsssistantStatus("Listening...")
                            print("✅ Status updated to: Listening... (mic is ON)")
                        else:
                            SetAsssistantStatus("Available...")
                            print("✅ Status updated to: Available... (mic is OFF)")
                    except Exception as status_error:
                        print(f"Error updating status: {status_error}")
                        # Force set to Listening if mic is likely on
                        try:
                            SetAsssistantStatus("Listening...")
                            print("✅ Force set status to: Listening...")
                        except:
                            pass
                    return True
                elif "realtime" in queries:
                    SetAsssistantStatus("Searching...")
                    QueryFinal = queries.replace("realtime", "")
                    try:
                        Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                    except Exception as e:
                        print(f"Error in RealtimeSearchEngine: {e}")
                        Answer = "I'm here to help! What would you like to know?"
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAsssistantStatus("Answering...")
                    # Check for interruption before speaking
                    if check_for_interruption():
                        print("Interrupted before speaking")
                        return True
                    currently_speaking = True
                    log_tts(Answer, "start")
                    
                    # CRITICAL: Use fallback_tts directly, NEVER call TextToSpeech (which calls fallback_tts internally)
                    print(f"Main.py TTS (realtime-only): About to speak answer (length: {len(Answer)})")
                    print(f"Main.py TTS (realtime-only): Answer preview: {Answer[:100]}...")
                    try:
                        from Backend.TextToSpeech import fallback_tts, reset_speech_interrupt
                        reset_speech_interrupt()
                        print("Main.py TTS (realtime-only): Calling fallback_tts (ONLY ONCE - no duplicates)...")
                        result = fallback_tts(Answer)
                        print(f"Main.py TTS (realtime-only): fallback_tts returned: {result}")
                        if result:
                            log_tts(Answer, "stop")
                            print("Main.py TTS (realtime-only): TTS completed successfully - DO NOT call TextToSpeech")
                        else:
                            print("Main.py TTS (realtime-only): WARNING - fallback_tts returned False")
                    except Exception as tts_error:
                        print(f"Main.py TTS (realtime-only) ERROR: {tts_error}")
                        import traceback
                        print(traceback.format_exc())
                        print("Main.py TTS (realtime-only): Error occurred, but NOT calling TextToSpeech to prevent duplicates")
                    
                    # IMPORTANT: Wait for TTS to completely finish (reduced for speed)
                    import time
                    time.sleep(0.1)  # Reduced from 0.5 to 0.1 for faster response
                    
                    currently_speaking = False
                    # IMMEDIATELY update status after TTS completes
                    try:
                        mic_status = GetMicrophoneStatus()
                        if mic_status.lower() == "true":
                            SetAsssistantStatus("Listening...")
                            print("✅ Status updated to: Listening... (mic is ON)")
                        else:
                            SetAsssistantStatus("Available...")
                            print("✅ Status updated to: Available... (mic is OFF)")
                    except Exception as status_error:
                        print(f"Error updating status: {status_error}")
                        # Force set to Listening if mic is likely on
                        try:
                            SetAsssistantStatus("Listening...")
                            print("✅ Force set status to: Listening...")
                        except:
                            pass
                    return True
                elif "exit" in queries:
                    print(f"Exit command detected in queries: {queries}")
                    # Check if this is a real exit command or just part of interrupt
                    if "interrupt" in str(queries).lower() or "stop" in str(queries).lower():
                        print("Exit command appears to be part of interrupt - ignoring")
                        return True
                    QueryFinal = "Okay, Bye!"
                    try:
                        # Get current mode and pass it to ChatBot
                        current_mode = get_current_mode()
                        Answer = ChatBot(QueryModifier(QueryFinal), mode=current_mode)
                    except Exception as e:
                        print(f"Error in ChatBot: {e}")
                        Answer = "Goodbye! Have a great day!"
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAsssistantStatus("Answering...")
                    # Check for interruption before speaking
                    if check_for_interruption():
                        print("Interrupted before speaking")
                        return True
                    currently_speaking = True
                    # Create a callback function that checks for interruption
                    def check_interrupt():
                        return not (speech_interrupted or interrupt_requested or check_for_interruption())
                    
                    from Backend.TextToSpeech import speech_interrupted, interrupt_requested
                    TextToSpeech(Answer, check_interrupt)
                    currently_speaking = False
                    print("About to exit application...")
                    os._exit(1)
    except KeyboardInterrupt:
        print("MainExecution: Keyboard interrupt received")
        raise  # Re-raise to allow graceful shutdown
    except Exception as e:
        print(f"CRITICAL ERROR in MainExecution: {e}")
        import traceback
        print(traceback.format_exc())
        # Ensure we always return to available state
        try:
            SetAsssistantStatus("Available...")
        except:
            pass
        # Don't crash, just return False and continue
        return False
    finally:
        # Always reset processing flag when done
        processing_query = False
        print(f"MainExecution: Reset processing_query flag to False")

# Thread for primary execution loop
def FirstThread():
    while True:
        try:
            # Check for interruption if currently speaking - more aggressive checking
            if currently_speaking and check_for_interruption():
                print("Speech interrupted - processing new input")
                MainExecution()
                continue
                
            CurrentStatus = GetMicrophoneStatus()
            print(f"Current Microphone Status: {CurrentStatus}")  # Debugging

            if CurrentStatus.lower() == "true":  # Case-insensitive comparison - mic is ON
                # Set status to listening when mic is ON
                current_status_text = GetAssistantStatus()
                if "Listening" not in current_status_text and "Thinking" not in current_status_text and "Answering" not in current_status_text:
                    SetAsssistantStatus("Listening...")
                
                # Force interrupt any ongoing speech when new input is detected
                if currently_speaking:
                    print("New input detected while speaking - force interrupting")
                    force_interrupt_speech()
                print("Mic is ON - Executing MainExecution (continuous listening mode)")  # Debugging
                try:
                    result = MainExecution()
                    print(f"MainExecution completed with result: {result}")
                    
                    # After execution, ALWAYS check if mic is still ON and continue listening
                    final_mic_status = GetMicrophoneStatus()
                    if final_mic_status.lower() == "true":
                        # Mic still ON - automatically continue listening (loop will call MainExecution again)
                        print("Mic still ON - automatically continuing to listen...")
                        SetAsssistantStatus("Listening...")
                        sleep(0.3)  # Small delay to prevent rapid-fire execution
                    else:
                        # Mic was turned off
                        SetAsssistantStatus("Available...")
                        print("Mic turned OFF - stopped listening")
                        
                except Exception as e:
                    print(f"Error in MainExecution: {e}")
                    import traceback
                    print(traceback.format_exc())
                    # Check mic status - if ON, continue listening
                    final_mic_status = GetMicrophoneStatus()
                    if final_mic_status.lower() == "true":
                        SetAsssistantStatus("Listening...")
                    else:
                        SetAsssistantStatus("Available...")
            elif CurrentStatus.lower() == "false":  # Mic is OFF
                AIStatus = GetAssistantStatus()
                print(f"Current Assistant Status: {AIStatus}")  # Debugging

                if "Available..." in AIStatus:
                    sleep(0.001)  # Ultra fast - 1ms for maximum responsiveness
                else:
                    print("Setting Assistant Status to 'Available...'")  # Debugging
                    SetAsssistantStatus("Available...")
            else:
                print("Unexpected Microphone Status value. Defaulting to 'False'.")  # Debugging
                SetAsssistantStatus("Available...")
        except KeyboardInterrupt:
            print("FirstThread: Keyboard interrupt received, shutting down gracefully...")
            break
        except Exception as e:
            print(f"CRITICAL ERROR in FirstThread: {e}")
            import traceback
            print(traceback.format_exc())
            try:
                SetAsssistantStatus("Available...")
            except:
                pass
            sleep(1)  # Avoid infinite rapid errors
            # Continue the loop - don't exit
            continue



# Thread for GUI execution
def SecondThread():
    try:
        GraphicalUserInterface()
    except KeyboardInterrupt:
        print("SecondThread: Keyboard interrupt received, shutting down gracefully...")
    except Exception as e:
        print(f"CRITICAL ERROR in SecondThread (GUI): {e}")
        import traceback
        print(traceback.format_exc())
        # Try to show error to user
        try:
            from Frontend.GUI import ShowTextToScreen
            ShowTextToScreen("JARVIS: GUI Error occurred. Please restart the application.")
        except:
            pass

# Entry point
if __name__ == "__main__":
    try:
        InitialExecution()
       
        thread1 = threading.Thread(target=FirstThread, daemon=True)
        thread1.start()
        print("FirstThread started successfully")
        
        # Run GUI in main thread (blocking)
        print("Starting GUI...")
        SecondThread()
    except KeyboardInterrupt:
        print("\nApplication shutdown requested by user")
    except Exception as e:
        print(f"CRITICAL ERROR in main: {e}")
        import traceback
        print(traceback.format_exc())
        input("Press Enter to exit...")  # Keep window open to see error
    