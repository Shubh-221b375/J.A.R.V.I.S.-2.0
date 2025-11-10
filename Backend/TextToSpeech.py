import pygame
import random
import asyncio
import edge_tts
import os
import pyttsx3
import platform
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
# Use a single high-quality multilingual voice that works well across all languages
# en-US-AriaNeural is a premium neural voice that sounds natural and realistic
# It handles multiple languages reasonably well and provides consistent, genuine voice quality
AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural")

def get_universal_voice():
    """
    Get the universal voice that works well for all languages.
    Returns a high-quality neural voice code for edge_tts.
    This voice is chosen for its natural, realistic sound across multiple languages.
    """
    # en-US-AriaNeural is a premium neural voice that:
    # - Sounds natural and realistic (not robotic)
    # - Works reasonably well with multiple languages
    # - Provides consistent voice quality
    # - Has excellent pronunciation and intonation
    return AssistantVoice

# Global variable to control speech interruption
speech_interrupted = False
interrupt_requested = False  # New flag for immediate interruption

def interrupt_speech():
    """Function to interrupt current speech immediately"""
    global speech_interrupted, interrupt_requested
    print("interrupt_speech() called - setting flags to True")
    speech_interrupted = True
    interrupt_requested = True
    
    try:
        # Force stop all audio (pygame mixer)
        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        # Reinitialize mixer for next use
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    except Exception as e:
        print(f"Error interrupting pygame audio: {e}")
        # Force reinitialize even if there's an error
        try:
            pygame.mixer.init()
        except:
            pass
    
    # Also try to stop any pyttsx3 engines that might be running
    try:
        # Force stop all pyttsx3 engines by killing any running instances
        import sys
        import os
        # This is a more aggressive approach - we can't directly stop pyttsx3,
        # but the flags will be checked and the engine.stop() will be called
        print("Interrupt flags set - pyttsx3 will check these flags")
    except Exception as e:
        print(f"Error in interrupt_speech cleanup: {e}")

def reset_speech_interrupt():
    """Function to reset speech interruption flag"""
    global speech_interrupted, interrupt_requested
    speech_interrupted = False
    interrupt_requested = False

def prepare_tts_text(text):
    """Prepare text for TTS - if more than 2 lines, summarize and ask to check chat"""
    text = str(text).strip()
    
    # Split text into lines
    lines = text.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    
    # If more than 2 lines, only speak first 2 lines + prompt
    if len(non_empty_lines) > 2:
        first_two_lines = '\n'.join(non_empty_lines[:2])
        # Ensure it ends properly
        if not first_two_lines.rstrip().endswith(('.', '!', '?')):
            first_two_lines += "."
        speech_text = first_two_lines + " Please see the chat for more information."
        print(f"TTS: Text has {len(non_empty_lines)} lines, summarizing to: '{speech_text}'")
        return speech_text
    else:
        # For 2 lines or less, speak everything
        return text

def fallback_tts(text):
    """Fallback TTS using pyttsx3 when edge_tts fails"""
    global speech_interrupted, interrupt_requested
    
    # Prepare text (summarize if needed)
    text = prepare_tts_text(text)
    
    engine = None
    try:
        # Ensure text is a string and not empty
        text = str(text).strip()
        if not text:
            print("Fallback TTS: Empty text, cannot speak")
            return False
        
        # Check if already interrupted
        if speech_interrupted or interrupt_requested:
            print("Fallback TTS: Speech interrupted before starting")
            reset_speech_interrupt()  # Reset for next time
            return False
        
        print(f"Fallback TTS: Initializing engine for text: '{text[:50]}...' (length: {len(text)})")
        
        # Initialize engine with error handling
        try:
            engine = pyttsx3.init()
            print("Fallback TTS: Engine initialized successfully")
        except Exception as init_error:
            print(f"Fallback TTS: CRITICAL - Failed to initialize engine: {init_error}")
            import traceback
            print(traceback.format_exc())
            return False
        
        # Use a universal voice that works well for all languages
        # Try to find a high-quality English voice (works well across languages)
        try:
            voices = engine.getProperty('voices')
            if voices:
                voice_found = False
                # Look for high-quality English voices first (they work well across languages)
                preferred_voices = ['aria', 'jenny', 'guy', 'jane', 'zira', 'david', 'mark']
                for voice in voices:
                    voice_name_lower = voice.name.lower()
                    # Check if it's a preferred high-quality voice
                    if any(pref in voice_name_lower for pref in preferred_voices):
                        engine.setProperty('voice', voice.id)
                        print(f"Fallback TTS: Using universal voice: {voice.name} (ID: {voice.id})")
                        voice_found = True
                        break
                
                # If no preferred voice found, look for any English voice
                if not voice_found:
                    for voice in voices:
                        voice_name_lower = voice.name.lower()
                        voice_id_lower = voice.id.lower()
                        if 'english' in voice_name_lower or 'en' in voice_id_lower:
                            engine.setProperty('voice', voice.id)
                            print(f"Fallback TTS: Using English voice: {voice.name} (ID: {voice.id})")
                            voice_found = True
                            break
                
                # If no specific voice found, use first available voice
                if not voice_found and voices:
                    engine.setProperty('voice', voices[0].id)
                    print(f"Fallback TTS: Using default voice: {voices[0].name} (ID: {voices[0].id})")
        except Exception as e:
            print(f"Fallback TTS: Voice selection warning: {e}")
        
        # Set speech rate and volume for natural, less robotic sound
        try:
            engine.setProperty('rate', 175)  # Slower rate for more natural sound (reduced from 200)
            engine.setProperty('volume', 1.0)  # Full volume
            actual_rate = engine.getProperty('rate')
            actual_volume = engine.getProperty('volume')
            print(f"Fallback TTS: Rate set to {actual_rate}, Volume set to {actual_volume}")
            
            # Verify properties were set correctly
            if actual_volume < 0.5:
                print("WARNING: Volume is too low! Setting to maximum...")
                engine.setProperty('volume', 1.0)
                actual_volume = engine.getProperty('volume')
                print(f"Fallback TTS: Volume corrected to {actual_volume}")
        except Exception as e:
            print(f"Fallback TTS: Property setting warning: {e}")
        
        # Check for interruption one more time before speaking
        if speech_interrupted or interrupt_requested:
            print("Fallback TTS: Speech interrupted before speak()")
            try:
                if engine:
                    engine.stop()
            except:
                pass
            reset_speech_interrupt()  # Reset for next time
            return False
        
        # Reset interrupt flags ONLY when we actually start speaking
        # This ensures interrupt works from the very start
        reset_speech_interrupt()
        
        # Clean text for TTS: replace newlines with spaces, remove extra whitespace
        text_clean = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Remove multiple spaces
        while '  ' in text_clean:
            text_clean = text_clean.replace('  ', ' ')
        text_clean = text_clean.strip()
        
        # If text is empty after cleaning, don't speak
        if not text_clean:
            print("Fallback TTS: Text is empty after cleaning, skipping TTS")
            return False
        
        print(f"Fallback TTS: Speaking text now: '{text_clean[:50]}...'")
        print(f"Fallback TTS: Original length: {len(text)}, Cleaned length: {len(text_clean)}")
        print(f"Fallback TTS: Interrupt flags - speech_interrupted={speech_interrupted}, interrupt_requested={interrupt_requested}")
        
        try:
            # Queue the cleaned text and speak immediately - simple and direct
            engine.say(text_clean)
            print("Fallback TTS: Text queued, starting speech...")
            print(f"Fallback TTS: About to call engine.runAndWait() with text: '{text_clean[:100]}...'")
            
            # CRITICAL: Call runAndWait() directly (blocking) to ensure speech actually happens
            # This is more reliable than threading for ensuring speech executes
            try:
                print("Fallback TTS: Calling engine.runAndWait() NOW (blocking call)...")
                engine.runAndWait()
                print("Fallback TTS: engine.runAndWait() completed successfully!")
            except Exception as run_error:
                print(f"Fallback TTS: ERROR in runAndWait(): {run_error}")
                import traceback
                print(traceback.format_exc())
                # Try to stop and reinitialize
                try:
                    engine.stop()
                except:
                    pass
                # Try one more time with a fresh engine
                try:
                    print("Fallback TTS: Retrying with fresh engine...")
                    engine2 = pyttsx3.init()
                    engine2.setProperty('rate', 200)
                    engine2.setProperty('volume', 1.0)
                    engine2.say(text_clean[:500])  # Limit length for retry
                    engine2.runAndWait()
                    print("Fallback TTS: Retry succeeded!")
                except Exception as retry_error:
                    print(f"Fallback TTS: Retry also failed: {retry_error}")
                    raise run_error
            
            # Small delay to ensure audio is completely finished
            import time
            time.sleep(0.1)
            
            print("Fallback TTS: Speech completed successfully!")
        except Exception as speak_error:
            print(f"Fallback TTS: Error during speech: {speak_error}")
            import traceback
            print(traceback.format_exc())
            try:
                if engine:
                    engine.stop()
            except:
                pass
            return False
        
        return True
        
    except Exception as e:
        import traceback
        print(f"Fallback TTS: CRITICAL ERROR: {e}")
        print(f"Fallback TTS: Traceback: {traceback.format_exc()}")
        # Try to stop the engine if it exists
        try:
            if engine:
                engine.stop()
        except:
            pass
        return False

async def TextToAudioFile(text) -> None:
    # Cross-platform file path handling
    data_dir = os.path.join("Data")
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, "speech.mp3")

    # Remove old file faster (non-blocking check)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass  # Continue even if file removal fails

    # Use universal voice for all languages (consistent, natural sound)
    voice_to_use = get_universal_voice()
    
    print(f"TTS: Using universal voice: {voice_to_use} (works for all languages)")

    try:
        # Use the universal voice with natural pitch and rate for realistic, non-robotic sound
        # Natural settings: pitch='+0Hz', rate='+0%' for genuine, realistic voice
        communicate = edge_tts.Communicate(text, voice_to_use, pitch='+0Hz', rate='+0%')
        await communicate.save(file_path)
        print(f"TTS: Successfully generated audio with universal voice: {voice_to_use}")
    except Exception as e:
        print(f"Error with voice {voice_to_use}: {e}")
        # Fallback to alternative high-quality voices
        fallback_voices = [
            "en-US-AriaNeural",  # Premium neural voice
            "en-US-JennyNeural",  # High-quality alternative
            "en-US-GuyNeural",    # Male alternative
        ]
        
        for fallback_voice in fallback_voices:
            try:
                print(f"TTS: Trying fallback voice: {fallback_voice}")
                communicate = edge_tts.Communicate(text, fallback_voice, pitch='+0Hz', rate='+0%')
                await communicate.save(file_path)
                print(f"TTS: Successfully generated audio with fallback voice: {fallback_voice}")
                break
            except Exception as e2:
                print(f"Error with fallback voice {fallback_voice}: {e2}")
                continue
        else:
            # All fallback attempts failed
            raise Exception(f"TTS: All voice attempts failed. Last error: {e}")

def TTS(Text, func=lambda r=None: True):
    global speech_interrupted, interrupt_requested
    
    # Check if already interrupted before doing anything
    if speech_interrupted or interrupt_requested:
        print("Speech already interrupted - not starting")
        reset_speech_interrupt()  # Reset for next time
        return False
    
    # DON'T reset interrupt flags at start - only reset when we actually start speaking
    # This allows immediate interruption if user interrupts right at the start
    
    # Try edge_tts first (optimized for speed)
    try:
        # Check if speech was interrupted before starting
        if speech_interrupted or interrupt_requested:
            print("Speech interrupted before starting")
            return False
        
        # Generate audio file (this is the main delay)
        print(f"Generating audio for text length: {len(Text)}")
        asyncio.run(TextToAudioFile(Text))
        print("Audio file generated, starting playback...")

        # Cross-platform file path handling
        data_dir = os.path.join("Data")
        speech_file = os.path.join(data_dir, "speech.mp3")
        
        # Check again after audio file generation
        if speech_interrupted or interrupt_requested:
            print("Speech interrupted after audio generation")
            try:
                # Try to clean up audio file if interrupted
                if os.path.exists(speech_file):
                    os.remove(speech_file)
            except:
                pass
            return False

        # Initialize pygame mixer with error handling
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except Exception as e:
            print(f"Error initializing pygame mixer: {e}")
            pygame.mixer.init()
        
        # Check again after mixer initialization
        if speech_interrupted or interrupt_requested:
            print("Speech interrupted after mixer initialization")
            reset_speech_interrupt()  # Reset for next time
            return False

        pygame.mixer.music.load(speech_file)
        
        # Reset interrupt flags ONLY when we actually start playing
        # This ensures interrupt works from the very start
        reset_speech_interrupt()
        
        pygame.mixer.music.play()

        clock = pygame.time.Clock()

        while pygame.mixer.music.get_busy():
            # Check for interruption during playback VERY frequently (every frame)
            # Priority: Check interruption flags first (fastest check)
            if speech_interrupted or interrupt_requested:
                print("Speech interrupted during playback - stopping immediately")
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                except:
                    pass
                # Reset flags for next speech
                reset_speech_interrupt()
                return False
                
            # Also check function return (external interrupt check)
            if not func():
                print("External interrupt detected - stopping speech")
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                except:
                    pass
                reset_speech_interrupt()
                return False
                
            clock.tick(120)  # Check 120 times per second for ultra-responsive interruption

        # Wait a tiny bit to ensure audio is completely finished
        import time
        time.sleep(0.1)
        
        return True
        
    except Exception as e:
        print(f"Error in edge_tts: {e}")
        print("Switching to fallback TTS...")
        
        # Use fallback TTS
        try:
            if speech_interrupted or interrupt_requested:
                print("Speech interrupted before fallback TTS")
                return False
                
            # Use pyttsx3 fallback
            success = fallback_tts(Text)
            if success:
                print("Fallback TTS completed successfully")
                return True
            else:
                print("Fallback TTS failed")
                return False
                
        except Exception as e2:
            print(f"Fallback TTS error: {e2}")
            return False
            
    finally:
        try:
            func(False)
            if pygame.mixer.get_init() is not None:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
        except Exception as e:
            print(f"Error in finally block: {e}")

def TextToSpeech(Text, func=lambda r=None: True):
    """
    Speak the full response if under 300 characters, otherwise speak a summary.
    Checks for interruption frequently during speech.
    Optimized for faster response time - uses fallback TTS immediately for speed.
    """
    text = str(Text).strip()
    
    # Quick text processing for faster TTS start
    # Split text into lines
    lines = text.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    
    responses = [
        "Please check the screen for the complete response.",
        "The full answer is displayed on the screen.",
        "See the screen for more details.",
        "Check the screen for the full response.",
        "The complete information is on the screen."
    ]
    
    # If text is under 300 characters, speak the full response
    if len(text) <= 300:
        speech_text = text  # Speak full response for short messages
    # If we have more than 2 lines, speak only first 2 lines + prompt
    elif len(non_empty_lines) > 2:
        first_two_lines = '\n'.join(non_empty_lines[:2])
        # Ensure it ends properly
        if not first_two_lines.rstrip().endswith(('.', '!', '?')):
            first_two_lines += "."
        speech_text = first_two_lines + " " + random.choice(responses)
    # If text is long (more than ~150 chars), speak first 2 sentences or ~120 chars
    elif len(text) > 300:
        # Try to split by sentences first (faster regex)
        import re
        sentences = re.split(r'[.!?]+\s+', text)
        if len(sentences) >= 2:
            first_two_sentences = '. '.join(sentences[:2])
            if not first_two_sentences.endswith(('.', '!', '?')):
                first_two_sentences += "."
            speech_text = first_two_sentences + " " + random.choice(responses)
        else:
            # Fallback: take first ~200 characters (for longer messages)
            short_text = text[:200].strip()
            # Try to cut at word boundary
            last_space = short_text.rfind(' ')
            if last_space > 150:
                short_text = short_text[:last_space]
            if not short_text.endswith(('.', '!', '?')):
                short_text += "..."
            speech_text = short_text + " " + random.choice(responses)
    else:
        # Medium text (150-300 chars) - speak fully
        speech_text = text
    
    # Use fallback TTS immediately for faster response (no file generation delay)
    # pyttsx3 is faster since it doesn't need to generate audio files
    try:
        print(f"TextToSpeech: Using fast TTS (pyttsx3) for text length: {len(speech_text)}")
        print(f"TextToSpeech: Text preview: {speech_text[:100]}...")
        print(f"TextToSpeech: Full text to speak: '{speech_text}'")
        result = fallback_tts(speech_text)
        print(f"TextToSpeech: fallback_tts returned: {result}")
        if result:
            print("TextToSpeech: Fast TTS (pyttsx3) completed successfully")
            return True
        else:
            print("TextToSpeech: Fast TTS (pyttsx3) returned False, falling back to edge_tts")
    except Exception as e:
        import traceback
        print(f"TextToSpeech: Fast TTS error: {e}")
        print(f"TextToSpeech: Traceback: {traceback.format_exc()}")
        print("TextToSpeech: Falling back to edge_tts")
    
    # Fallback to edge_tts if pyttsx3 fails
    print("TextToSpeech: Using edge_tts fallback")
    try:
        TTS(speech_text, func)
        print("TextToSpeech: edge_tts completed")
        return True
    except Exception as e:
        print(f"TextToSpeech: edge_tts also failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False
# jar tumhala purna read karaich lavaich asel tr TTS cha use kara jar 4 or tya peksha line 
# jast lines text asel tr TTS use kra ani Short made read karacih asel tr texttosppech use kara  
if __name__ == "__main__":
    while True:
        TextToSpeech(input("Enter the text : "))