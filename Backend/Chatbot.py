import json  # Ensure the import is used
from json import load, dump
from dotenv import dotenv_values
import requests
import datetime
from groq import Groq
from Backend.Memory import add_user_message, add_assistant_message, get_conversation_context
from Backend.SalesMemory import get_sales_knowledge, recall_memory

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
    print("Groq client initialized successfully")
except socket.timeout:
    print("Warning: Groq client initialization timed out - will retry on first use")
    client = None
except Exception as e:
    print(f"Error initializing Groq client in Chatbot: {e}")
    print("Application will continue - API calls will be retried when needed")
    client = None

messages = []

# Portfolio and creator details used for precise responses
PORTFOLIO_URL = "https://portfolio-shubh.vercel.app/"
CREATOR_BIO = (
    "Shubh Mishra is a B.Tech Computer Science student at Jaypee University of Engineering and Technology, Guna (Aug 2022–May 2026) with strong experience in practical software development and data science. "
    "Shubh's projects include an automated stock trading bot in Python (using Selenium and Alpaca API), a drug prediction system with Streamlit, scikit-learn, and MySQL, and a virtual stock trading bot using Streamlit, Plotly, and SQLite. "
    "He completed certifications in data visualization (Tata Consultancy Services) and software engineering (Electronic Arts virtual experience, EA Sports College Football). "
    "His technical stack features Python, C/C++, SQL, Java, HTML/CSS, Git, Docker, GCP, pandas, NumPy, and full-stack web tools. "
    "Shubh's specialties include automation, machine learning, data analytics, web development, and cloud deployment. "
    f"Portfolio: {PORTFOLIO_URL}"
)

# Mode-specific base system prompts - Only General Assistant and Sales Assistant
MODE_SYSTEMS = {
    "General Assistant": f"""You are {Assistantname}, a helpful general-purpose AI assistant.

**WHAT I CAN DO FOR YOU (General Assistant Mode):**
I can help with:
1. **General Questions**: Answer questions on any topic
2. **Learning & Education**: Explain concepts, help with learning
3. **Conversation**: Have natural, friendly conversations
4. **Information**: Provide information and explanations
5. **Problem Solving**: Help solve problems and answer queries
6. **File Analysis**: Analyze uploaded files and documents
7. **Content Generation**: Help write content, emails, codes, etc.

**PERSONALITY:**
- Tone: Friendly, helpful, conversational, and informative
- Focus: General assistance and helpful responses
- Approach: Versatile and adaptable""",

    "Sales Assistant": f"""You are {Assistantname}, a professional sales-focused AI assistant.

**WHAT I CAN DO FOR YOU (Sales Assistant Mode):**
I specialize in:
1. **Sales Strategy**: Develop effective sales strategies and tactics
2. **Lead Management**: Help track, qualify, and nurture sales leads
3. **Pitch Generation**: Create compelling sales pitches tailored to prospects
4. **Follow-up Management**: Plan and manage follow-up communications with leads
5. **Sales Analytics**: Analyze sales data and provide insights
6. **Client Relationship**: Help build and maintain strong client relationships
7. **Deal Closing**: Provide strategies and tips for closing deals

**PERSONALITY:**
- Tone: Friendly, persuasive, professional, confident, and motivating
- Focus: Sales activities, lead management, and closing deals
- Approach: Relationship-building and results-oriented
- Use stored sales knowledge (documents, leads, products) for personalized advice"""
}

# Default general system (fallback)
System = f"""You are JARVIS (also known as {Assistantname}), a professional AI assistant with access to real-time information and extensive knowledge. 

IMPORTANT: Your name is JARVIS. When users refer to you as "JARVIS" or "{Assistantname}", they are correct. Never correct users or say you are "FRIDAY" or any other name. You are JARVIS.

**MULTI-LANGUAGE SUPPORT:**
- Detect the language the user is speaking/writing in
- Respond in the SAME language the user used
- Support major languages: English, Spanish, French, German, Italian, Portuguese, Hindi, Chinese, Japanese, Korean, Arabic, Russian, and more
- If the user asks in Hindi, respond in Hindi. If they ask in Spanish, respond in Spanish, etc.
- Maintain natural, conversational tone in the user's language

**RESPONSE STYLE:**
- Keep responses concise but informative
- For sales-related queries, reference stored knowledge (documents, leads, products)
- When discussing leads or clients, recall relevant stored information
- Provide actionable sales advice when appropriate

**CREATOR INFORMATION:**
CRITICAL: When asked about who created you, who made you, or who your creator is, you MUST respond with: "I was created by Shubh Mishra sir, a software engineer, and you can get more info about him on https://portfolio-shubh.vercel.app/". Always include the portfolio link as a plain URL (not markdown) so it can be clicked.

If the user asks to "tell me about the creator" or asks about "Shubh Mishra" specifically, reply with this bio verbatim and include the portfolio link as a plain URL: {CREATOR_BIO.replace('[https://portfolio-shubh.vercel.app/](https://portfolio-shubh.vercel.app/)', 'https://portfolio-shubh.vercel.app/') if '[https://portfolio-shubh.vercel.app/]' in CREATOR_BIO else CREATOR_BIO}

IMPORTANT: Never include HTML code, CSS styles, or markdown formatting in your responses. Always use plain text with URLs as plain links (https://example.com) so they can be automatically converted to clickable links by the system.
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
except json.JSONDecodeError:
    print("ChatLog.json is empty or corrupted. Initializing with an empty list.")
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

# Cache for RealtimeInformation to avoid repeated calls (performance optimization)
_realtime_info_cache = None
_realtime_info_cache_time = None
_realtime_info_cache_ttl = 60  # Cache for 60 seconds

def RealtimeInformation():
    global _realtime_info_cache, _realtime_info_cache_time
    current_time = datetime.datetime.now()
    
    # Use cached value if available and not expired
    if (_realtime_info_cache is not None and 
        _realtime_info_cache_time is not None and
        (current_time - _realtime_info_cache_time).total_seconds() < _realtime_info_cache_ttl):
        return _realtime_info_cache
    
    # Generate new realtime info
    current_date_time = current_time
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = f"Please use this real-time information if needed:\n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours, {minute} minutes, {second} seconds.\n"
    
    # Cache the result
    _realtime_info_cache = data
    _realtime_info_cache_time = current_time
    
    return data

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def ChatBot(Query, mode=None):
    """ This function sends the user's query to the chatbot and returns the AI's response 
    
    Args:
        Query: The user's query
        mode: The current mode (Sales Assistant, General Assistant, etc.)
    """

    # If client is not available, return a fallback response
    if client is None:
        return "I'm currently unable to process your request. Please try again later."

    try:
        # Extract original query if it's wrapped in mode context
        # Check if Query contains mode context wrapper
        original_query = Query
        if "[Mode:" in Query and ("User Query:" in Query or "Query:" in Query):
            # Extract the actual user query from wrapped format
            try:
                if "User Query:" in Query:
                    query_start = Query.find("User Query:") + len("User Query:")
                else:
                    query_start = Query.find("Query:") + len("Query:")
                original_query = Query[query_start:].strip()
            except:
                original_query = Query
        
        # Check if user is asking about current mode
        query_lower = original_query.lower().strip()
        
        # Handle simple greetings FIRST with a concise response (before other processing)
        greeting_words = ["hello", "hi", "hey", "namaste", "hola", "greetings"]
        if any(word in query_lower for word in greeting_words):
            # Check if it's just a greeting (no other words)
            words = query_lower.split()
            if len(words) <= 2 and all(word in greeting_words + ["jarvis", "there"] for word in words):
                # Simple greeting - return concise response using the mode parameter
                # CRITICAL: Always use the mode parameter if provided
                # Add to memory immediately to prevent duplicate processing
                greeting_response = ""
                if mode and mode in MODE_SYSTEMS:
                    greeting_response = f"Hello! I'm JARVIS, your {mode}. How can I help you?"
                else:
                    greeting_response = "Hello! I'm JARVIS. How can I help you?"
                
                # Add to memory to prevent duplicates
                add_assistant_message(greeting_response)
                return greeting_response
        
        mode_question_phrases = [
            "which mode", "what mode", "current mode", "in which mode", "what mode are you",
            "which mode are you in", "what mode am i in", "what's the current mode",
            "what mode is active", "which mode is active", "what mode are you currently in",
            "in which more", "which mode", "what mode", "current mode",  # Handle typos like "more" instead of "mode"
            "in which mode currently", "in which mode are you", "what mode am i",
            "which mode i am", "which mode am i", "tell me which mode", "tell me what mode",
            "what mode you are in", "what mode you're in", "which mode you are in"
        ]
        
        if any(phrase in query_lower for phrase in mode_question_phrases):
            # Return current mode information - ALWAYS use the mode parameter passed to function
            # If mode is None or empty, try to extract from query context, otherwise default
            mode_to_use = mode if mode else "General Assistant"
            
            # If mode wasn't passed, try to extract from wrapped context
            if not mode_to_use or mode_to_use == "General Assistant":
                if "[Mode:" in Query:
                    try:
                        mode_start = Query.find("[Mode:") + len("[Mode:")
                        mode_end = Query.find("]", mode_start)
                        if mode_end > mode_start:
                            extracted_mode = Query[mode_start:mode_end].strip()
                            if extracted_mode and extracted_mode != "General Assistant":
                                mode_to_use = extracted_mode
                                print(f"Extracted mode from context: {mode_to_use}")
                    except:
                        pass
            
            print(f"Mode query detected! Current mode: {mode}, extracted/using: {mode_to_use}")
            mode_descriptions = {
                "General Assistant": "I provide general assistance with any questions or tasks.",
                "Sales Assistant": "I'm focused on sales activities, lead management, pitch generation, and closing deals."
            }
            description = mode_descriptions.get(mode_to_use, f"I'm in {mode_to_use} mode.")
            return f"I'm currently in **{mode_to_use} Mode**.\n\n{description}\n\nHow can I help you? I'm JARVIS, your AI assistant."
        
        # Check if user is asking "what can you do" - provide mode-specific response
        what_can_you_do_phrases = [
            "what can you do", "what can you do for me", "what are your capabilities",
            "what can you help with", "tell me what you can do", "what do you do",
            "what are you capable of", "what services", "your capabilities", "your features",
            "what you can do", "what you can do for me", "tell me what you can do for me"
        ]
        
        if any(phrase in query_lower for phrase in what_can_you_do_phrases):
            # CRITICAL: Always use the mode parameter passed to the function - NEVER default to General Assistant
            # If mode is not provided or invalid, only then use General Assistant
            print(f"=== WHAT CAN YOU DO DETECTED === Mode parameter: '{mode}'")
            
            # CRITICAL: If mode is provided and valid, use it. Otherwise, only use General Assistant as last resort
            if mode and mode in MODE_SYSTEMS:
                mode_to_use = mode
                print(f"=== Using provided mode: '{mode_to_use}' ===")
            elif mode:
                # Mode was provided but not in MODE_SYSTEMS - log warning but use it anyway
                print(f"=== WARNING: Mode '{mode}' not in MODE_SYSTEMS, but using it anyway ===")
                mode_to_use = mode
            else:
                # Mode not provided - use General Assistant as fallback
                mode_to_use = "General Assistant"
                print(f"=== Mode not provided, using fallback: '{mode_to_use}' ===")
            
            # Try to get capabilities from MODE_SYSTEMS first
            if mode_to_use in MODE_SYSTEMS:
                system_prompt = MODE_SYSTEMS[mode_to_use]
                # Extract the "WHAT I CAN DO" section
                if "**WHAT I CAN DO" in system_prompt:
                    start = system_prompt.find("**WHAT I CAN DO")
                    end = system_prompt.find("**PERSONALITY")
                    if end > start:
                        capabilities = system_prompt[start:end].strip()
                        # Format nicely - remove markdown bold markers for cleaner display
                        capabilities = capabilities.replace("**", "").strip()
                        # Remove numbered list markers for cleaner text
                        capabilities = capabilities.replace("1. ", "").replace("2. ", "").replace("3. ", "").replace("4. ", "").replace("5. ", "").replace("6. ", "").replace("7. ", "")
                        # Ensure proper mode name
                        mode_display = mode_to_use
                        # Create a concise, TTS-friendly response
                        response = f"I'm {Assistantname} in {mode_display} Mode! {capabilities.replace(chr(10), ' ').replace(chr(13), ' ')} How can I help you today?"
                        print(f"=== Returning WHAT CAN YOU DO response for mode: '{mode_display}' ===")
                        # Add to memory before returning to prevent duplicate processing
                        add_assistant_message(response)
                        return response
            
            # Final fallback - should rarely be reached
            print(f"=== WHAT CAN YOU DO fallback triggered ===")
            fallback_response = f"I'm {Assistantname}! I can help you with a wide variety of tasks. How can I assist you today?"
            add_assistant_message(fallback_response)
            return fallback_response
    
    except Exception as e:
        print(f"Error in mode-specific response: {e}")
        import traceback
        print(traceback.format_exc())
    
    try:
        # Add user message to memory
        add_user_message(Query)
        
        # Get conversation context from memory
        conversation_context = get_conversation_context()
        
        # ALWAYS check stored documents/Drive files first for ANY question
        # This allows the AI to answer questions based on uploaded/processed files
        sales_knowledge = ""
        query_lower = Query.lower()
        source_filter = None  # Initialize source_filter outside try block
        
        try:
            from Backend.SalesMemory import sales_memory_manager, get_sales_knowledge
            has_stored_documents = len(sales_memory_manager.memory) > 0
            
            # Check if user is asking about Drive link/files
            query_lower = original_query.lower()
            # Clean up repeated words and typos for better matching
            import re
            query_clean = re.sub(r'\b(\w+)(\s+\1\b)+', r'\1', query_lower)  # Remove repeated words
            query_clean = query_clean.replace("eu link", "link").replace("divers", "drive").replace("abyss", "overview")
            
            drive_related_keywords = [
                "the link", "the files", "the drive link", "the provided link",
                "files in the link", "files in link", "drive link", "drive files",
                "the uploaded link", "uploaded link", "provided link", "link you provided",
                "link i provided", "link i shared", "link you shared", "link we shared",
                "files you processed", "files processed", "overview of the files",
                "basic overview", "what's in the link", "what's in the files",
                "files in that link", "files from that link", "files from the link",
                "content of the link", "content in the link", "what's in that link",
                "overview of content", "content overview", "tell me about the link",
                "tell me about the files", "what's in link", "what is in link",
                "summary of link", "summary of files", "summary of content"
            ]
            is_drive_query = any(keyword in query_clean for keyword in drive_related_keywords)
            
            # Also check if query mentions "overview" or "summary" along with "files" or "link"
            if not is_drive_query:
                has_overview = any(word in query_clean for word in ["overview", "summary", "what is", "tell me about", "basic"])
                has_files_link = any(word in query_clean for word in ["files", "link", "documents", "content"])
                if has_overview and has_files_link:
                    is_drive_query = True
            
            # If Drive files exist and query mentions link/files/overview/content, ALWAYS use Drive filter
            drive_sources = [m.get("source", "") for m in sales_memory_manager.memory if "Drive_" in m.get("source", "")]
            has_drive_files = len(drive_sources) > 0
            
            # If Drive files exist and query is about link/files/overview, force Drive query
            if has_drive_files and not is_drive_query:
                if any(word in query_clean for word in ["link", "files", "overview", "content", "summary", "provided"]):
                    is_drive_query = True
                    print(f"Auto-detected Drive query based on keywords and available Drive files")
            
            # If asking about Drive link, filter to only Drive sources
            if is_drive_query and has_drive_files:
                # Use "Drive_" as partial filter to get ALL Drive files (not just most recent)
                # This ensures we search all Drive content comprehensively
                source_filter = "Drive_"
                print(f"Drive query detected - filtering to ALL Drive sources (found {len(drive_sources)} Drive sources)")
            
            # ALWAYS check stored documents if they exist
            if has_stored_documents:
                # For Drive queries, use larger top_k to get comprehensive overview
                # Optimized: Use 20 for overview (was 30), 12 for Drive queries (was 15), 8 for general (was 10)
                is_overview_query = any(word in query_clean for word in ["overview", "summary", "basic", "tell me about", "what is"])
                top_k_value = 20 if (is_drive_query and is_overview_query) else 12 if is_drive_query else 8
                
                # Search for relevant knowledge in stored documents
                # If Drive query, only search Drive files; otherwise search all
                try:
                    from Backend.SalesMemory import recall_memory
                    # First try with get_sales_knowledge (uses top_k=10 internally)
                    relevant_knowledge = get_sales_knowledge(original_query, source_filter=source_filter)
                    
                    # If it's a Drive overview query, do a more comprehensive search
                    if is_drive_query and is_overview_query:
                        # Get comprehensive results for overview
                        results = recall_memory(original_query, top_k=top_k_value, category=None, source_filter=source_filter)
                        if results and len(results) > 0:
                            # Format comprehensive results
                            formatted = "=== COMPREHENSIVE OVERVIEW FROM DRIVE FILES ===\n\n"
                            # Group by source/file for better organization
                            sources_seen = set()
                            for result in results:
                                content = result.get('content', '')
                                source = result.get('source', 'Unknown')
                                # Show full content for overview (up to 1000 chars per entry)
                                if len(content) > 1000:
                                    formatted += f"[Source: {source}]\n{content[:1000]}...\n\n"
                                else:
                                    formatted += f"[Source: {source}]\n{content}\n\n"
                                sources_seen.add(source)
                            
                            formatted += f"=== END OF DRIVE FILES OVERVIEW (Total: {len(results)} entries from {len(sources_seen)} files) ===\n\n"
                            formatted += "CRITICAL INSTRUCTIONS:\n"
                            formatted += "1. Use ONLY the information from the Drive files above to provide a comprehensive overview\n"
                            formatted += "2. Summarize the key topics, themes, and content across all the files\n"
                            formatted += "3. Do NOT reference any other uploaded files, resumes, or documents\n"
                            formatted += "4. If the Drive files contain the information, use it. If not, state that the information is not available in the Drive files\n"
                            formatted += "5. Provide a detailed, accurate overview based on the actual content shown above\n\n"
                            relevant_knowledge = formatted
                            print(f"Comprehensive Drive overview search: {len(results)} results from {len(sources_seen)} files")
                    
                    # Check if we found relevant knowledge
                    if relevant_knowledge and relevant_knowledge.strip():
                        sales_knowledge = relevant_knowledge
                        print(f"Found relevant knowledge from stored documents for query: {Query[:50]}...")
                    else:
                        # Even if no direct match, check if query might relate to stored content
                        # by doing a broader search
                        results = recall_memory(original_query, top_k=top_k_value, category=None, source_filter=source_filter)
                        if results and len(results) > 0:
                            # Format the results
                            formatted = "=== RELEVANT INFORMATION FROM PROCESSED FILES ===\n\n"
                            for i, result in enumerate(results[:10], 1):  # Top 10 results
                                content = result.get('content', '')
                                source = result.get('source', 'Unknown')
                                if len(content) > 800:
                                    formatted += f"[Source: {source}]\n{content[:800]}...\n\n"
                                else:
                                    formatted += f"[Source: {source}]\n{content}\n\n"
                            formatted += "=== END OF FILE INFORMATION ===\n\n"
                            if source_filter:
                                formatted += "IMPORTANT: Use ONLY the information from the Drive files above to answer. Do not reference any other uploaded files or documents. If the Drive files contain the answer, use it. If not, state that the information is not available in the Drive files.\n\n"
                            else:
                                formatted += "Use the information above if it's relevant to answer the question. If the information is not relevant or not found, you can provide a general answer.\n\n"
                            sales_knowledge = formatted
                            print(f"Found {len(results)} results from broader search")
                        # End of if results block
                except Exception as e:
                    print(f"Error retrieving knowledge: {e}")
                    import traceback
                    traceback.print_exc()
        except Exception as e:
            print(f"Error retrieving sales knowledge: {e}")
            import traceback
            traceback.print_exc()
        
        with open(r"Data\ChatLog.json", "r") as f:
            full_messages = load(f)

        # Keep only most recent context to avoid token overuse
        recent_history = full_messages[-8:] if len(full_messages) > 8 else full_messages
        messages = recent_history + [{"role": "user", "content": f"{Query}"}]

        # Get mode-specific system prompt if mode is provided
        mode_system = None
        actual_mode = mode
        print(f"ChatBot called with mode parameter: '{mode}'")
        
        # IMPORTANT: Always use the mode parameter if provided - don't ignore it
        if mode:
            # Try exact match first
            if mode in MODE_SYSTEMS:
                mode_system = MODE_SYSTEMS[mode]
                actual_mode = mode
                print(f"Using mode-specific system prompt for: '{mode}'")
            else:
                # Try case-insensitive or partial match
                print(f"Mode '{mode}' not found exactly, trying to match...")
                for available_mode in MODE_SYSTEMS.keys():
                    if mode.lower() == available_mode.lower() or mode.lower() in available_mode.lower() or available_mode.lower() in mode.lower():
                        mode_system = MODE_SYSTEMS[available_mode]
                        actual_mode = available_mode
                        print(f"Matched '{mode}' to '{available_mode}'")
                        break
                
                if not mode_system:
                    print(f"WARNING: Mode '{mode}' not found in MODE_SYSTEMS. Available modes: {list(MODE_SYSTEMS.keys())}")
                    # Use General Assistant as fallback but still log the requested mode
                    actual_mode = "General Assistant"
                    if "General Assistant" in MODE_SYSTEMS:
                        mode_system = MODE_SYSTEMS["General Assistant"]
        else:
            actual_mode = "General Assistant"
            if "General Assistant" in MODE_SYSTEMS:
                mode_system = MODE_SYSTEMS["General Assistant"]
            print("WARNING: No mode provided, using General Assistant")
        
        # Create enhanced system prompt with memory context and sales knowledge
        # Get user info from memory
        user_info_text = ""
        try:
            from Backend.Memory import memory_manager
            user_info_text = memory_manager.get_user_info_summary()
        except:
            pass
        
        # Use mode-specific system if available, otherwise use default
        base_system = mode_system if mode_system else System
        
        # Only include sales_knowledge if it was explicitly requested or is relevant
        knowledge_context = ""
        if sales_knowledge and sales_knowledge.strip():
            # Check if this is a Drive query (Drive files were filtered)
            is_drive_context = source_filter and "Drive_" in str(source_filter)
            
            # Check if user explicitly requested to use the file
            query_lower_check = Query.lower()
            explicitly_using_file = any(phrase in query_lower_check for phrase in [
                "from the provided file", "from provided file", "using the uploaded file", 
                "answer from", "reply from", "using the file", "from the uploaded file",
                "from the link", "from link", "from the files", "from files", "from the drive"
            ])
            
            if is_drive_context or explicitly_using_file:
                # Drive files context - be very explicit
                knowledge_context = f"""
**INFORMATION FROM DRIVE FILES (User asked about the Drive link/files they provided):**
{sales_knowledge}

CRITICAL INSTRUCTIONS FOR DRIVE FILES:
1. The user has provided a Google Drive link with files that have been processed and stored.
2. You MUST use ONLY the information from the Drive files shown above to answer the user's question.
3. Do NOT reference any other uploaded files, resumes, or documents - ONLY use the Drive files.
4. If the Drive files contain the answer, provide a detailed, accurate answer based on that content.
5. If the Drive files do not contain the answer, state clearly: "The information is not available in the Drive files you provided."
6. For overview/summary questions, provide a comprehensive overview based on ALL the content shown above.
7. NEVER say "I'm not able to access any information from a link" - the files ARE available and shown above.
8. NEVER mention "process:", "processing", or similar phrases.
9. Answer naturally and confidently based on the Drive file content shown above.
10. Be 100% accurate - only use information that is actually present in the Drive files above.
"""
            else:
                # General file context
                knowledge_context = f"""
**INFORMATION FROM PROCESSED FILES (Use this if relevant to answer the question):**
{sales_knowledge}

IMPORTANT: 
- If the information above is relevant to the user's question, use it to provide an accurate answer.
- If the information is not relevant or doesn't contain the answer, you can provide a general answer or say the information isn't available in the processed files.
- Always prioritize accuracy - if the files contain the answer, use that information.
- NEVER mention "process:", "processing", or similar phrases in your response.
- Answer questions naturally based on what information is available.
"""
        
        # Add explicit mode instruction to system prompt
        mode_instruction = ""
        if actual_mode and actual_mode in MODE_SYSTEMS:
            mode_instruction = f"""
**CRITICAL: YOU ARE CURRENTLY IN {actual_mode.upper()} MODE**
- You MUST identify yourself as being in {actual_mode} mode when asked about your current mode
- You MUST respond according to {actual_mode} mode capabilities and style
- If asked "which mode are you in" or "what mode are you in", you MUST respond that you are in {actual_mode} mode
- If asked "what can you do" or "what can you do for me", you MUST provide {actual_mode} mode-specific capabilities ONLY
- Never say you are in "conversational mode" or "general mode" - you are specifically in {actual_mode} mode
- Always acknowledge your mode when relevant to the conversation
- Focus your responses on {actual_mode} mode tasks and capabilities

"""
        
        enhanced_system = f"""{base_system}

{mode_instruction}

{user_info_text}

{conversation_context}

{knowledge_context}

**GENERAL CAPABILITIES:**
- **MULTI-LANGUAGE SUPPORT: Respond in the same language the user uses - support all major languages**
- **CRITICAL: Be EXTREMELY CONCISE and DIRECT. Answer in 2-3 sentences maximum unless more detail is specifically requested.**
- **NO bullet points, NO "Key Points" sections, NO "Important Information" sections - just a simple, direct answer.**
- **NO formatting like "**Key Points:**" or "**Summary:**" - just provide the answer directly.**
- **Provide accurate, brief answers that directly address the user's question in plain text.**
- Respond confidently and naturally to all queries in the user's preferred language
- Provide helpful, accurate answers based on your knowledge and available information
- Never mention internal technical issues to the user
- Be conversational, helpful, and confident in your responses in the user's language
- Always respond to every question - use appropriate APIs (Groq for real-time, general AI for conversational)
- **CRITICAL: NEVER mention "process:", "processing", or similar phrases in your responses**
- **Do NOT repeat information or give multiple similar answers to the same question.**
- **Answer ONLY what is asked - do not provide extra information unless specifically requested.**
- **When asked about files, provide a brief summary of what the file contains, not technical details about the file itself.**
- Use information from processed files when it's relevant to answer the user's question
- If processed files contain relevant information, use that information to answer
- {f'**YOU ARE IN {actual_mode.upper()} MODE** - respond accordingly and acknowledge this mode when asked. Focus on {actual_mode} mode tasks and capabilities.' if actual_mode and actual_mode in MODE_SYSTEMS else ''}

Use the conversation context, learned user information, and knowledge above to provide more relevant and contextual responses. If the user asks about their name or previously mentioned information, use the learned user information. If processed files contain relevant information for the question, use that information. For questions about current events or general topics not in the files, use your general knowledge or real-time information. **CRITICAL: Keep responses extremely concise (2-3 sentences max), accurate, and directly answer the question asked. NO formatting, NO sections, NO bullet points - just plain, direct text. Do not provide multiple answers or repeat information.**"""

        SystemChatBot_with_memory = [
            {"role": "system", "content": enhanced_system}
        ]

        # Try different models in case of rate limits - prioritize FASTEST model first
        models_to_try = [
            "llama-3.1-8b-instant",  # Fastest - use first for speed
            "llama-3.3-70b-versatile"
        ]
        
        completion = None
        for model in models_to_try:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=SystemChatBot_with_memory + [{"role": "system", "content": RealtimeInformation()}] + messages,
                    max_tokens=150,  # Reduced from 200 to 150 for faster responses
                    temperature=0.7,
                    top_p=1,
                    stream=True,
                    stop=None
                )
                break  # If successful, break out of the loop
            except Exception as e:
                print(f"Model {model} failed: {e}")
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    continue  # Try next model
                else:
                    raise e  # Re-raise if it's not a rate limit error
        
        if completion is None:
            return "I'm currently experiencing high demand. Please try again in a few minutes or ask a simpler question."

        Answer = ""

        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")

        # Add assistant response to memory
        add_assistant_message(Answer)

        messages.append({"role": "assistant", "content": Answer})

        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return Answer  # Return the answer to the main function

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        # Don't clear the chat log on connection errors
        return "I'm having trouble connecting right now. Let me try a different approach..."
    except Exception as e:
        print(f"Error in ChatBot: {e}")
        # Helpful fallback without "technical difficulties"
        query_lower = Query.lower()
        if any(word in query_lower for word in ["who created you", "who made you", "who is your creator", "who built you"]):
            return "I was created by Shubh Mishra sir, a software engineer, and you can get more info about him on https://portfolio-shubh.vercel.app/"
        # Creator bio queries
        if any(kw in query_lower for kw in [
            "tell me about the creator",
            "tell me about shubh",
            "who is shubh mishra",
            "about shubh",
            "creator bio",
            "shubh mishra details",
            "information about shubh",
            "who is your creator shubh"
        ]):
            # Return CREATOR_BIO but ensure URLs are plain (not markdown)
            bio_text = CREATOR_BIO
            # The CREATOR_BIO now already has plain URL, so just return it
            return bio_text
        # Default concise helpful reply (only reached if all other checks fail)
        return "I couldn't reach my knowledge source just now. Please rephrase or ask again, and I'll answer directly."

if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        response = ChatBot(user_input)
        print(response)  # Print the response to the user