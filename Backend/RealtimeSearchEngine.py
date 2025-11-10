from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
from Backend.Memory import add_user_message, add_assistant_message, get_conversation_context
import hashlib

env_vars = dotenv_values(".env")

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize Groq client with error handling and timeout protection
client = None
try:
    import socket
    socket.setdefaulttimeout(5)  # Set default socket timeout to 5 seconds
    client = Groq(api_key=GroqAPIKey, timeout=10.0)  # 10 second timeout for API calls
    print("RealtimeSearchEngine: Groq client initialized successfully")
except socket.timeout:
    print("Warning: RealtimeSearchEngine Groq client initialization timed out - will retry on first use")
    client = None
except Exception as e:
    print(f"Error initializing Groq client in RealtimeSearchEngine: {e}")
    print("Application will continue - API calls will be retried when needed")
    client = None

# Cache for search results (simple in-memory cache)
_search_cache = {}
_cache_max_age = 300  # Cache for 5 minutes (300 seconds)

# Default system prompt (will be enhanced with mode context if mode is detected)
base_system = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

System = base_system

# Ensure Data directory exists and load/create ChatLog.json
try:
    import os
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data")
    os.makedirs(data_dir, exist_ok=True)  # Create Data directory if it doesn't exist
    
    chatlog_path = os.path.join(data_dir, "ChatLog.json")
    
    try:
        with open(chatlog_path, "r", encoding='utf-8') as f:
            messages = load(f)
    except FileNotFoundError:
        # File doesn't exist, create it
        with open(chatlog_path, "w", encoding='utf-8') as f:
            dump([], f)
        messages = []
except Exception as e:
    print(f"Warning: Could not initialize ChatLog.json: {e}")
    messages = []

def GoogleSearch(query):
    """Enhanced Google search with caching and optimized performance"""
    global _search_cache
    
    # Check cache first
    query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()
    current_time = datetime.datetime.now().timestamp()
    
    if query_hash in _search_cache:
        cached_result, cache_time = _search_cache[query_hash]
        if (current_time - cache_time) < _cache_max_age:
            print(f"Using cached search result for: {query[:50]}...")
            return cached_result
        else:
            # Cache expired, remove it
            del _search_cache[query_hash]
    
    # Try fast method first: googlesearch library with shorter timeout
    try:
        # Use a generator and limit results for faster response - REDUCED for speed
        results = list(search(query, advanced=True, num_results=2, timeout=1))  # Reduced to 2 results, 1s timeout for maximum speed
        Answer = f"Current information about '{query}':\n\n"

        for i, result in enumerate(results[:2]):  # Limit to top 2 results for maximum speed
            Answer += f"{result.title}\n{result.description}\n\n"

        # Check if we got meaningful results
        if len(Answer) > 50:  # Reduced threshold from 100 to 50 for faster acceptance
            # Cache the result
            _search_cache[query_hash] = (Answer, current_time)
            # Limit cache size to prevent memory issues
            if len(_search_cache) > 50:
                # Remove oldest entries
                oldest_key = min(_search_cache.keys(), key=lambda k: _search_cache[k][1])
                del _search_cache[oldest_key]
            return Answer
    except Exception as e:
        print(f"Google search (googlesearch library) error: {e}")
    
    # Fallback: Try direct web scraping with shorter timeout
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        # Reduced timeout to 1 second for faster failure
        response = requests.get(url, headers=headers, timeout=1)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Try to extract snippets from search results
            snippets = []
            for result in soup.find_all('div', class_='VwiC3b')[:2]:  # Limit to 2 for maximum speed
                text = result.get_text(strip=True)
                if text:
                    snippets.append(text)
            
            if snippets:
                Answer = f"Current information about '{query}':\n\n"
                Answer += "\n\n".join(snippets)
                # Cache the result
                _search_cache[query_hash] = (Answer, current_time)
                if len(_search_cache) > 50:
                    oldest_key = min(_search_cache.keys(), key=lambda k: _search_cache[k][1])
                    del _search_cache[oldest_key]
                return Answer
            else:
                # Return quick fallback instead of trying more methods
                return f"Current information about: {query}\nNote: Search results are limited. Consider using a dedicated search API for better real-time information."
        else:
            return f"Current information about: {query}\nNote: Unable to access search results. Consider using a dedicated search API."
    except Exception as e2:
        print(f"Fallback search also failed: {e2}")
        # Return quick response instead of trying more methods
        return f"Current information about: {query}\nNote: Search functionality is limited. For better real-time results, consider adding Serper, Tavily, or Perplexity API."

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, Sir, how can I help you?"}
]

def Information():
    data = ""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data += f"Use This Real-time Information if needed:\n"
    data += f"Day: {day}\n"
    data += f"Date: {date}\n"
    data += f"Month: {month}\n"
    data += f"Year: {year}\n"
    data += f"Time: {hour} hours: {minute} minutes: {second} seconds.\n"
    return data

def check_available_apis():
    """Check which enhanced APIs are configured"""
    available = []
    if env_vars.get("SerperAPIKey"):
        available.append("Serper API")
    if env_vars.get("TavilyAPIKey"):
        available.append("Tavily API")
    if env_vars.get("PerplexityAPIKey"):
        available.append("Perplexity API")
    if env_vars.get("GoogleSearchAPIKey"):
        available.append("Google Custom Search API")
    if env_vars.get("BraveAPIKey"):
        available.append("Brave Search API")
    return available

def get_api_suggestions():
    """Returns suggestions for better real-time search APIs"""
    available_apis = check_available_apis()
    
    suggestions = "\n**RECOMMENDED APIs FOR BETTER REAL-TIME INFORMATION:**\n\n"
    
    if not available_apis:
        suggestions += "**No enhanced search APIs detected. Current setup uses basic Google search (limited).**\n\n"
    
    suggestions += """1. **Serper API** (⭐ Recommended - Best for real-time search)
   - Website: https://serper.dev/
   - Free tier: 2,500 queries/month
   - Purpose: Google Search API with structured results
   - Add to .env: SerperAPIKey=your_key_here

2. **Tavily API** (⭐ Recommended - AI-focused search)
   - Website: https://tavily.com/
   - Free tier: 1,000 queries/month
   - Purpose: Real-time search optimized for AI
   - Add to .env: TavilyAPIKey=your_key_here

3. **Perplexity API** (Excellent for real-time Q&A)
   - Website: https://www.perplexity.ai/
   - Purpose: Real-time search with citations
   - Add to .env: PerplexityAPIKey=your_key_here

4. **Google Custom Search API** (Official Google)
   - Website: https://developers.google.com/custom-search
   - Free tier: 100 queries/day
   - Add to .env: GoogleSearchAPIKey=your_key_here, GoogleSearchEngineID=your_id

5. **Brave Search API** (Privacy-focused)
   - Website: https://brave.com/search/api/
   - Free tier: 2,000 queries/month
   - Add to .env: BraveAPIKey=your_key_here
"""
    
    if available_apis:
        suggestions += f"\n**✅ Configured APIs:** {', '.join(available_apis)}\n"
    else:
        suggestions += "\n**Current Setup:**\n"
        suggestions += "- Using: Groq API + Google Search (googlesearch library - limited)\n"
        suggestions += "- Status: Basic functionality, but may struggle with complex real-time queries\n"
        suggestions += "\n**To improve:** Add any of the above APIs to your .env file for better real-time information.\n"
    
    # Add reference to setup guides
    suggestions += "\n" + "="*60 + "\n"
    suggestions += "📚 **SETUP YOUR OWN APIs**\n"
    suggestions += "="*60 + "\n"
    suggestions += "To configure APIs and unlock full JARVIS functionality:\n\n"
    suggestions += "1. **Read the README.md file** for:\n"
    suggestions += "   - Complete installation instructions\n"
    suggestions += "   - Feature overview and capabilities\n"
    suggestions += "   - Basic API configuration steps\n"
    suggestions += "   - Offline setup options\n\n"
    suggestions += "2. **Follow the API_SETUP_GUIDE.md** for:\n"
    suggestions += "   - Step-by-step API key setup (Groq, Spotify, etc.)\n"
    suggestions += "   - Detailed instructions for each service\n"
    suggestions += "   - Troubleshooting common issues\n"
    suggestions += "   - Optional API configurations\n\n"
    suggestions += "📝 **Quick Start:**\n"
    suggestions += "   - Copy `.env.example` to `.env` in the project root\n"
    suggestions += "   - Add your API keys to the `.env` file\n"
    suggestions += "   - Minimum required: `GroqAPIKey` for AI responses\n"
    suggestions += "   - See API_SETUP_GUIDE.md for detailed steps\n\n"
    suggestions += "💡 **Tip:** Both files are in the project root directory.\n"
    suggestions += "="*60 + "\n"
    
    return suggestions

def RealtimeSearchEngine(prompt, mode=None):
    global SystemChatBot, messages

    # If client is not available, provide helpful error with API suggestions
    if client is None:
        error_msg = "I'm currently unable to access real-time information because the Groq API is not properly configured."
        error_msg += get_api_suggestions()
        return error_msg

    try:
        # Extract mode from prompt if present
        actual_prompt = prompt
        detected_mode = mode
        mode_style_instruction = ""
        
        if "[Mode:" in prompt:
            try:
                mode_start = prompt.find("[Mode:") + 6
                mode_end = prompt.find("]", mode_start)
                if mode_end > mode_start:
                    detected_mode = prompt[mode_start:mode_end].strip()
                    
                    # Add mode-specific response style instructions
                    if detected_mode == "General Assistant":
                        mode_style_instruction = "\n\n**RESPONSE STYLE**: Keep answers concise (1-2 sentences for simple factual questions). For 'who is the president' type questions, provide brief, direct answers."
                    elif detected_mode == "Research Mode":
                        mode_style_instruction = "\n\n**RESPONSE STYLE**: Provide comprehensive, detailed research. Include background, history, current information, multiple perspectives, and sources. For 'president of india', provide extensive details about the presidency, current president, role, history, etc."
                    elif detected_mode == "Business Analysis":
                        mode_style_instruction = "\n\n**RESPONSE STYLE**: Provide detailed strategic analysis with business insights and recommendations."
                    elif detected_mode == "Data Analysis":
                        mode_style_instruction = "\n\n**RESPONSE STYLE**: Provide detailed analytical insights with statistical context."
                    elif detected_mode in ["Sales Assistant", "Lead Management", "Pitch Generator", "Follow-up Manager"]:
                        mode_style_instruction = f"\n\n**RESPONSE STYLE**: Respond with focus on {detected_mode} - be thorough, professional, and helpful while maintaining the sales focus."
                    
                    # Extract actual query after mode context
                    query_marker = prompt.find("Query:") if "Query:" in prompt else (prompt.find("User Query:") if "User Query:" in prompt else -1)
                    if query_marker > 0:
                        actual_prompt = prompt[query_marker:].replace("Query:", "").replace("User Query:", "").strip()
                    else:
                        # Remove mode context from beginning
                        actual_prompt = prompt[mode_end+1:].strip()
            except Exception as e:
                print(f"Error extracting mode from prompt: {e}")
                actual_prompt = prompt
        
        # Add user message to memory (use actual prompt, not wrapped one)
        add_user_message(actual_prompt)
        
        # Get conversation context from memory
        conversation_context = get_conversation_context()
        
        import os
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data")
        chatlog_path = os.path.join(data_dir, "ChatLog.json")
        with open(chatlog_path, "r", encoding='utf-8') as f:
            messages = load(f)
        messages.append({"role": "user", "content": f"{actual_prompt}"})

        # Get real-time information
        realtime_info = Information()
        
        # Check if this is a simple factual question that can be answered quickly without extensive search
        # For simple questions, we can skip or do a quick search
        is_simple_factual = any(phrase in actual_prompt.lower() for phrase in [
            "who is the", "who is", "current president", "current prime minister",
            "president of", "prime minister of", "current leader",
            "gdp", "ranking", "rank", "position", "world ranking", "terms of",
            "largest economy", "richest country", "population", "unemployment",
            "inflation", "stock price", "bitcoin", "exchange rate"
        ])
        
        # Try to get Google search results - OPTIMIZED for speed
        # For simple factual questions, skip search entirely and go straight to API for fastest response
        search_failed = False
        search_results = ""
        if is_simple_factual:
            # For simple questions like "who is the president" or "gdp ranking", skip search and go straight to API
            # This saves 2-3 seconds by avoiding search delay
            print(f"Simple factual question detected - skipping search for speed, going straight to API")
            search_results = f"User is asking: {actual_prompt}. Provide a brief, direct answer based on your knowledge. For GDP/ranking questions, provide current data."
        else:
            # For complex questions, do quick search with STRICT timeout (1 second max)
            try:
                import signal
                import threading
                
                # Use threading with timeout to prevent hanging
                search_result_container = [None]
                search_error_container = [None]
                
                def do_search():
                    try:
                        result = GoogleSearch(actual_prompt)
                        search_result_container[0] = result
                    except Exception as e:
                        search_error_container[0] = e
                
                search_thread = threading.Thread(target=do_search, daemon=True)
                search_thread.start()
                search_thread.join(timeout=1.0)  # MAX 1 second for search
                
                if search_thread.is_alive():
                    print("Google search timed out after 1 second - skipping search, going to API")
                    search_results = f"User is asking: {actual_prompt}. Provide a brief, direct answer."
                elif search_error_container[0]:
                    print(f"Google search failed: {search_error_container[0]}")
                    search_results = f"User is asking: {actual_prompt}. Provide a brief, direct answer."
                elif search_result_container[0]:
                    search_results = search_result_container[0]
                    if not search_results or len(search_results.strip()) < 30:
                        search_failed = True
                        search_results = f"User is asking: {actual_prompt}. Provide a brief, direct answer."
                else:
                    search_results = f"User is asking: {actual_prompt}. Provide a brief, direct answer."
            except Exception as e:
                print(f"Google search failed: {e}")
                search_failed = True
                # Minimal context for faster processing
                search_results = f"User is asking: {actual_prompt}. Provide a brief, direct answer."

        if search_results:
            SystemChatBot.append({"role": "system", "content": search_results})

        # Enhanced system prompt with memory context and mode-specific instructions
        # Get user info from memory
        user_info_text = ""
        try:
            from Backend.Memory import memory_manager
            user_info_text = memory_manager.get_user_info_summary()
        except:
            pass
        
        # Add explicit mode instruction if mode is provided
        mode_instruction_realtime = ""
        if mode:
            mode_instruction_realtime = f"""
**CRITICAL: YOU ARE CURRENTLY IN {mode.upper()} MODE**
- You MUST identify yourself as being in {mode} mode when asked about your current mode
- You MUST respond according to {mode} mode capabilities and style
- If asked "which mode are you in" or "what mode are you in", you MUST respond that you are in {mode} mode
- Never say you are in "conversational mode" or "general mode" - you are specifically in {mode} mode
- Respond with appropriate detail level: detailed analysis for Research Mode, concise for General Assistant, sales-focused for Sales modes

"""
        
        # Base system prompt
        base_system_text = f"""You are JARVIS, an advanced AI assistant with access to real-time information from the internet via Google Search and Groq API.
{mode_instruction_realtime}
CRITICAL INSTRUCTIONS:
- You MUST provide real-time, up-to-date information when asked about current events, people, positions, or current data
- NEVER say "I don't have real-time information" - you have access to Google Search and real-time data
- NEVER say "I couldn't find" or "I don't know" - ALWAYS use the search results provided to you
- If search results are provided, you MUST use them to answer - do NOT say you don't know
- ALWAYS use the provided search results and real-time information to give accurate, current answers
- If asked about a person (like "who is X"), use the search results to provide information about them
- If the name is slightly misspelled (e.g., "ronnie sullivan" vs "ronnie o'sullivan"), use the search results to find the correct person
- If asked about current president, prime minister, leader, or any current position, provide the CURRENT answer using real-time data
- Respond confidently and naturally to all queries
- Use the provided search results and real-time information to give accurate, up-to-date answers
- Never mention technical limitations, API issues, or search failures to the user
- Always provide helpful, confident responses based on available information
- **MULTI-LANGUAGE SUPPORT:**
- Detect and respond in the SAME language the user uses
- Support major languages: English, Spanish, French, German, Italian, Portuguese, Hindi, Chinese, Japanese, Korean, Arabic, Russian, and more
- If the user asks in Hindi, respond in Hindi. If they ask in Spanish, respond in Spanish, etc.
- Maintain natural, conversational tone in the user's language
- CRITICAL: If search results contain information, you MUST use it - never say "I don't know" or "couldn't find" when search results are available"""
        
        # Add mode-specific instructions if mode is detected
        enhanced_system = base_system_text
        if mode_style_instruction:
            enhanced_system += mode_style_instruction
        
        enhanced_system += f"""

Current time and date: {realtime_info}

{user_info_text}

{conversation_context}

Use the conversation context, learned user information, and real-time search results above to provide accurate, up-to-date responses. If the user asks about current positions, leaders, or current events, use the real-time information to provide the CURRENT answer. Be helpful and answer questions directly without repeating that you've already discussed topics unless specifically asked about previous conversations."""

        SystemChatBot.append({"role": "system", "content": enhanced_system})

        # Try different models in case of rate limits - prioritize fastest models first
        # Use faster, smaller models first for speed
        models_to_try = [
            "llama-3.1-8b-instant",  # Fastest model - use first
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768"
        ]
        
        # Use appropriate tokens - ensure complete answers
        # "Who is" questions need enough tokens for complete biographical information
        if is_simple_factual:
            # GDP/ranking questions need more tokens for complete answers
            if any(phrase in actual_prompt.lower() for phrase in ["gdp", "ranking", "rank", "position", "economy"]):
                max_tokens_value = 250  # More tokens for GDP/ranking questions
            elif "who is" in actual_prompt.lower():
                max_tokens_value = 200  # "Who is" questions need enough for complete bio
            else:
                max_tokens_value = 150  # Other simple questions
        else:
            max_tokens_value = 250  # Complex questions need more tokens
        
        # Make API call directly (streaming handles timeout naturally)
        completion = None
        for model in models_to_try:
            try:
                print(f"RealtimeSearchEngine: Calling Groq API with model {model}, max_tokens={max_tokens_value}")
                completion = client.chat.completions.create(
                    model=model,
                    messages=SystemChatBot + [{"role": "system", "content": realtime_info}] + messages,
                    max_tokens=max_tokens_value,  # Reduced from 2048 for faster responses
                    temperature=0.7,
                    top_p=1,
                    stream=True,
                    stop=None
                )
                print(f"RealtimeSearchEngine: API call started successfully with model {model}")
                break  # If successful, break out of the loop
            except Exception as e:
                print(f"Model {model} failed: {e}")
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    continue  # Try next model
                else:
                    raise e  # Re-raise if it's not a rate limit error
        
        if completion is None:
            error_msg = "I'm currently experiencing high demand with the Groq API. All models are unavailable right now.\n\n"
            error_msg += get_api_suggestions()
            return error_msg

        Answer = ""
        
        # Process streaming response - let it complete fully, don't break early
        import time
        start_time = time.time()
        max_stream_time = 30  # Max 30 seconds to receive stream (increased for complete answers)
        chunk_count = 0
        last_chunk_time = start_time
        no_chunk_timeout = 5  # If no chunks for 5 seconds, assume stream is done
        
        try:
            # Process ALL chunks - don't break early, let the stream complete naturally
            for chunk in completion:
                chunk_count += 1
                current_time = time.time()
                
                # Check overall timeout - only break if taking way too long
                if current_time - start_time > max_stream_time:
                    print(f"Stream timeout after {max_stream_time} seconds, received {chunk_count} chunks")
                    break
                
                if chunk.choices[0].delta.content:
                    Answer += chunk.choices[0].delta.content
                    last_chunk_time = current_time  # Update last chunk time
                else:
                    # No content in this chunk - check if stream has stalled
                    if current_time - last_chunk_time > no_chunk_timeout:
                        print(f"No chunks for {no_chunk_timeout} seconds, assuming stream complete")
                        break
                    
                # REMOVED early break logic - let the stream complete fully
                # The API will naturally end the stream when done
        except StopIteration:
            # Stream ended naturally - this is good!
            print(f"Stream ended naturally after {chunk_count} chunks")
        except Exception as stream_error:
            print(f"Error processing stream: {stream_error}")
            import traceback
            print(traceback.format_exc())
            # Use what we have so far

        Answer = Answer.strip().replace("</s>", "")
        print(f"RealtimeSearchEngine: Received answer (length: {len(Answer)}, chunks: {chunk_count})")
        
        # CRITICAL: Check if answer was cut off - if it doesn't end properly, it might be incomplete
        if len(Answer) < 20:
            print(f"WARNING: Answer is very short ({len(Answer)} chars), might be incomplete")
        elif not Answer.rstrip().endswith(('.', '!', '?', ':', ';', ',', ')', ']', '}')):
            # Answer doesn't end with proper punctuation - might be cut off
            print(f"WARNING: Answer doesn't end with punctuation ({len(Answer)} chars), might be incomplete")
            # Try to detect if it was cut off mid-word or mid-sentence
            if len(Answer) > 50 and not Answer[-1].isspace():
                # Answer ends mid-word, likely cut off
                print("Answer appears to be cut off mid-word")
        
        # Ensure we have a valid answer
        if not Answer or len(Answer.strip()) < 10:
            print("WARNING: RealtimeSearchEngine returned empty or very short answer")
            # Try to provide a fallback answer with search context
            if search_results and "User is asking:" not in search_results:
                # We had search results but API didn't generate answer - try again with simpler prompt
                print("Retrying with simpler prompt...")
                try:
                    simple_completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": f"Answer this question directly and concisely: {actual_prompt}"},
                            {"role": "user", "content": actual_prompt}
                        ],
                        max_tokens=150,
                        temperature=0.7,
                        stream=False  # Non-streaming for retry
                    )
                    Answer = simple_completion.choices[0].message.content.strip()
                    print(f"Retry successful, got answer: {Answer[:100]}...")
                except:
                    Answer = f"I found information about '{actual_prompt}', but couldn't generate a complete response. Please try rephrasing your question."
            else:
                Answer = f"I found information about '{actual_prompt}', but couldn't generate a complete response. Please try rephrasing your question."
        
        messages.append({"role": "assistant", "content": Answer})

        import os
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data")
        os.makedirs(data_dir, exist_ok=True)
        chatlog_path = os.path.join(data_dir, "ChatLog.json")
        with open(chatlog_path, "w", encoding='utf-8') as f:
            dump(messages, f, indent=4)

        SystemChatBot.pop()
        return AnswerModifier(Answer=Answer)
        
    except Exception as e:
        print(f"Error in RealtimeSearchEngine: {e}")
        error_type = str(e).lower()
        
        # Check if it's an API-related error
        if "api" in error_type or "key" in error_type or "authentication" in error_type or "rate_limit" in error_type or "429" in error_type:
            error_msg = f"I encountered an issue accessing real-time information: {str(e)}\n\n"
            error_msg += get_api_suggestions()
            return error_msg
        
        # Fallback to regular ChatBot if real-time search fails
        try:
            from Backend.Chatbot import ChatBot
            fallback_answer = ChatBot(prompt, mode=mode)
            # Add a note about API suggestions if the answer seems incomplete
            if len(fallback_answer) < 100:
                fallback_answer += "\n\n" + get_api_suggestions()
            return fallback_answer
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
            error_msg = "I'm having difficulty accessing real-time information with the current setup.\n\n"
            error_msg += get_api_suggestions()
            return error_msg

if __name__ == "__main__":
    while True:
        prompt = input("Enter Your Query: ")
        print(RealtimeSearchEngine(prompt))