from groq import Groq
from rich import print
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize Groq client with error handling and timeout protection
client = None
try:
    import socket
    socket.setdefaulttimeout(5)  # Set default socket timeout to 5 seconds
    client = Groq(api_key=GroqAPIKey, timeout=10.0)  # 10 second timeout for API calls
except socket.timeout:
    print("Warning: Model Groq client initialization timed out - will retry on first use")
    client = None
except Exception as e:
    print(f"Error initializing Groq client: {e}")
    print("Application will continue - API calls will be retried when needed")
    client = None

funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "reminder", "spotify", "send email",
    "send whatsapp", "schedule meeting", "sync crm"
]

messages = []

preamble = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write a application and open it in notepad'
*** Do not answer any query, just decide what kind of query is given to you. ***
-> Respond with 'general ( query )' if a query can be answered by a llm model (conversational ai chatbot) and doesn't require any up to date information like if the query is 'who was akbar?' respond with 'general who was akbar?', if the query is 'how can i study more effectively?' respond with 'general how can i study more effectively?', if the query is 'can you help me with this math problem?' respond with 'general can you help me with this math problem?', if the query is 'Thanks, i really liked it.' respond with 'general thanks, i really liked it.' , if the query is 'what is python programming language?' respond with 'general what is python programming language?', etc. Respond with 'general (query)' if a query doesn't have a proper noun or is incomplete like if the query is 'who is he?' respond with 'general who is he?', if the query is 'what's his networth?' respond with 'general what's his networth?', if the query is 'tell me more about him.' respond with 'general tell me more about him.', and so on even if it require up-to-date information to answer. Respond with 'general (query)' if the query is asking about time, day, date, month, year, etc like if the query is 'what's the time?' respond with 'general what's the time?'.
-> Respond with 'realtime ( query )' if a query can not be answered by a llm model (because they don't have realtime data) and requires up to date information like if the query is 'who is indian prime minister' respond with 'realtime who is indian prime minister', if the query is 'who is the president of usa' respond with 'realtime who is the president of usa', if the query is 'who is the current president' respond with 'realtime who is the current president', if the query is 'tell me about facebook's recent update.' respond with 'realtime tell me about facebook's recent update.', if the query is 'tell me news about coronavirus.' respond with 'realtime tell me news about coronavirus.', etc and if the query is asking about any individual, current position, leader, politician, celebrity, public figure, or current events like if the query is 'who is akshay kumar' respond with 'realtime who is akshay kumar', if the query is 'what is today's news?' respond with 'realtime what is today's news?', if the query is 'what is today's headline?' respond with 'realtime what is today's headline?', if the query contains words like 'current', 'now', 'today', 'recent', 'latest', 'who is', 'what is' about people or current positions, respond with 'realtime (query)', etc. **CRITICAL: Also respond with 'realtime (query)' if the query is asking about GDP (Gross Domestic Product), economic rankings, country positions, world rankings, economic data, population statistics, stock prices, cryptocurrency prices, exchange rates, or any current economic/financial data like 'what is india's gdp ranking', 'position of india in terms of gdp', 'world gdp ranking', 'largest economy', 'richest country', etc.**
-> Respond with 'open (application name or website name)' if a query is asking to open any application like 'open facebook', 'open telegram', etc. but if the query is asking to open multiple applications, respond with 'open 1st application name, open 2nd application name' and so on.
-> Respond with 'close (application name)' if a query is asking to close any application like 'close notepad', 'close facebook', etc. but if the query is asking to close multiple applications or websites, respond with 'close 1st application name, close 2nd application name' and so on.
-> Respond with 'play (song name)' if a query is asking to play any song like 'play afsanay by ys', 'play let her go', etc. but if the query is asking to play multiple songs, respond with 'play 1st song name, play 2nd song name' and so on.
-> Respond with 'play spotify (song name)' if a query is asking to play music specifically on Spotify like 'play spotify shape of you', 'play spotify bohemian rhapsody', etc.
-> Respond with 'generate image (image prompt)' if a query is requesting to generate a image with given prompt like 'generate image of a lion', 'generate image of a cat', etc. but if the query is asking to generate multiple images, respond with 'generate image 1st image prompt, generate image 2nd image prompt' and so on.
-> Respond with 'reminder (datetime with message)' if a query is requesting to set a reminder like 'set a reminder at 9:00pm on 25th june for my business meeting.' respond with 'reminder 9:00pm 25th june business meeting'.
-> Respond with 'system (task name)' if a query is asking to mute, unmute, volume up, volume down , etc. but if the query is asking to do multiple tasks, respond with 'system 1st task, system 2nd task', etc.
-> Respond with 'content (topic)' if a query is asking to write any type of content like application, codes, emails or anything else about a specific topic but if the query is asking to write multiple types of content, respond with 'content 1st topic, content 2nd topic' and so on.
-> Respond with 'google search (topic)' if a query is asking to search a specific topic on google but if the query is asking to search multiple topics on google, respond with 'google search 1st topic, google search 2nd topic' and so on.
-> Respond with 'youtube search (topic)' if a query is asking to search a specific topic on youtube but if the query is asking to search multiple topics on youtube, respond with 'youtube search 1st topic, youtube search 2nd topic' and so on.
-> Respond with 'send email (recipient and subject and message)' if a query is asking to send an email like 'send email to john@example.com about project proposal', 'email jane about the meeting', etc.
-> Respond with 'send whatsapp (phone number and message)' if a query is asking to send a WhatsApp message like 'send WhatsApp to +1234567890 with hello', 'WhatsApp John with meeting reminder', etc.
-> Respond with 'schedule meeting (title and datetime and attendees)' if a query is asking to schedule a meeting like 'schedule meeting with team tomorrow at 3pm', 'book a meeting for sales call on Friday', etc.
-> Respond with 'sync crm (operation)' if a query is asking to sync CRM data like 'sync CRM data', 'update lead information', etc.
*** If the query is asking to perform multiple tasks like 'open facebook, telegram and close whatsapp' respond with 'open facebook, open telegram, close whatsapp' ***
*** If the user is saying goodbye or wants to end the conversation like 'bye jarvis.' respond with 'exit'.***
*** Respond with 'general (query)' if you can't decide the kind of query or if a query is asking to perform a task which is not mentioned above. ***
"""

ChatHistory = [
    {"role": "User", "message": "how are you ?"},
    {"role": "Chatbot", "message": "general how are you ?"},
    {"role": "User", "message": "do you like pizza ?"},
    {"role": "Chatbot", "message": "general do you like pizza ?"},
    {"role": "User", "message": "how are you ?"},
    {"role": "User", "message": "open chrome and tell me about mahatma gandhi."},
    {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi."},
    {"role": "User", "message": "open chrome and firefox"},
    {"role": "Chatbot", "message": "open chrome, open firefox"},
    {"role": "User", "message": "what is today's date and by the way remind me that i have a dancing performance on 5th at 11pm "},
    {"role": "Chatbot", "message": "general what is today's date, reminder 11:00pm 5th aug dancing performance"},
    {"role": "User", "message": "chat with me."},
    {"role": "Chatbot", "message": "general chat with me."}
]

def FirstLayerDMM(prompt: str = "test"):
    # Guard against misclassification of greetings as 'exit'
    prompt_lower_guard = prompt.lower()
    
    # Check for real-time questions FIRST (before greetings) - improved detection
    realtime_keywords = [
        "president of", "prime minister", "who is the", "who is", "current", "today", "recent", 
        "latest", "now", "yesterday", "day before", "football match", "soccer match", "won", "win",
        "real madrid", "liverpool", "match result", "game result", "who won", "what happened",
        "gdp", "gross domestic product", "ranking", "rank", "position", "world ranking", 
        "terms of", "in terms of", "economic", "economy", "largest economy", "richest country",
        "population", "current population", "unemployment rate", "inflation rate", "stock market",
        "cryptocurrency", "bitcoin price", "exchange rate", "currency", "market cap"
    ]
    
    # Check if it's a "who is [person name]" query - these are ALWAYS realtime
    if "who is" in prompt_lower_guard:
        # Extract what comes after "who is"
        who_is_index = prompt_lower_guard.find("who is")
        after_who_is = prompt_lower_guard[who_is_index + 6:].strip()
        # If there's a name/person after "who is" (more than just "the" or "he"), it's realtime
        if after_who_is and len(after_who_is) > 3 and after_who_is not in ["the", "he", "she", "it"]:
            print(f"FirstLayerDMM: Detected 'who is [person]' realtime query: '{prompt}'")
            return [f"realtime {prompt}"]
    
    if any(k in prompt_lower_guard for k in realtime_keywords):
        # Double-check: if it's asking about current positions, people, events, or economic data, it's realtime
        if any(phrase in prompt_lower_guard for phrase in [
            "president", "prime minister", "who is", "match", "won", "win", "result", 
            "yesterday", "day before", "gdp", "ranking", "rank", "position", 
            "world ranking", "terms of", "economic", "economy", "largest economy",
            "richest country", "population", "unemployment", "inflation", "stock",
            "cryptocurrency", "bitcoin", "exchange rate", "currency", "market cap"
        ]):
            print(f"FirstLayerDMM: Detected realtime query: '{prompt}'")
            return [f"realtime {prompt}"]
    
    greeting_keywords = [
        "hello", "hi", "hey", "yo", "hola", "namaste",
        "hello jarvis", "hi jarvis", "hey jarvis"
    ]
    if any(k in prompt_lower_guard for k in greeting_keywords):
        return [f"general {prompt}"]

    # If client is not available, return general query
    if client is None:
        return [f"general {prompt}"]

    messages.append({"role": "user", "content": f"{prompt}"})

    # Convert ChatHistory to Groq format
    groq_messages = []
    for item in ChatHistory:
        if item["role"] == "User":
            groq_messages.append({"role": "user", "content": item["message"]})
        elif item["role"] == "Chatbot":
            groq_messages.append({"role": "assistant", "content": item["message"]})
    
    # Add system message with preamble
    groq_messages.insert(0, {"role": "system", "content": preamble})
    groq_messages.append({"role": "user", "content": prompt})

    # Use stable, supported models only
    models_to_try = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile"
    ]
    
    completion = None
    try:
        for model in models_to_try:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=groq_messages[-10:],  # small prompt
                    max_tokens=160,  # faster
                    temperature=0.5,
                    top_p=1,
                    stream=True,
                    stop=None
                )
                break  # success
            except Exception as e:
                print(f"Model {model} failed: {e}")
                if "rate_limit" in str(e).lower() or "429" in str(e) or "tpm" in str(e).lower():
                    continue
                else:
                    return [f"general {prompt}"]
    except Exception as e:
        print(f"Decision model error: {e}")
        return [f"general {prompt}"]

    if completion is None:
        return [f"general {prompt}"]

    response = ""

    for chunk in completion:
        if chunk.choices[0].delta.content:
            response += chunk.choices[0].delta.content

    response = response.replace("\n", "")
    response = response.split(",")

    response = [i.strip() for i in response]

    temp = []

    for task in response:
        for func in funcs:
            if task.startswith(func):
                temp.append(task)
    
    response = temp

    if not response:
        return [f"general {prompt}"]

    # Safety: if model proposed 'exit' but the original prompt is a greeting, force general
    if any(k in prompt_lower_guard for k in greeting_keywords) and any(r.strip().startswith("exit") for r in response):
        return [f"general {prompt}"]

    if "(query)" in response:
        newresponse = FirstLayerDMM(prompt=prompt)
        return newresponse
    else:
        return response

    
if __name__ == "__main__":
    while True:
        print(FirstLayerDMM(input(">>>")))