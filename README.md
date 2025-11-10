# 🤖 JARVIS AI Assistant

A sophisticated AI voice assistant built with Python that combines speech recognition, natural language processing, and automation capabilities. JARVIS can understand voice commands, perform web searches, control applications, play music, and provide conversational AI responses.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green.svg)
![AI](https://img.shields.io/badge/AI-Groq%20API-orange.svg)
![Voice](https://img.shields.io/badge/Voice-Speech%20Recognition-red.svg)

## ✨ Features

### 🎤 Voice Interaction
- **Real-time Speech Recognition** using Chrome's Web Speech API
- **Text-to-Speech** with Microsoft Edge TTS
- **Continuous Listening** mode
- **Interrupt Capability** to stop mid-response

### 🧠 AI Capabilities
- **Multi-language Understanding** (responds in English)
- **Real-time Web Search** for up-to-date information
- **Conversational AI** powered by Groq's language models
- **Context Awareness** with conversation memory

### 🎵 Media & Entertainment
- **Spotify Integration** with web fallback
- **YouTube Playback** for music and videos
- **Voice-controlled Music** experience

### 🖥️ System Control
- **Application Launcher** for any installed app
- **Notepad Integration** for text editing
- **System Commands** execution
- **File Management** capabilities

### 📱 Modern Interface
- **Clean GUI** built with PyQt5
- **Clickable Links** for external resources
- **Real-time Status** updates
- **Chat History** with timestamps

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Google Chrome browser (for online STT, optional if using offline Vosk)
- Internet connection (optional for core voice loop if using offline STT/TTS)
- Microphone
- Windows/macOS/Linux (Windows tested, macOS/Linux supported)

### Local-First / Offline Support
JARVIS supports **offline operation** for core voice functionality:
- **Wake Word**: Porcupine (requires key) or Snowboy (free) or STT-based fallback
- **STT**: Vosk (offline) or Chrome Web Speech API (online)
- **TTS**: pyttsx3 (offline) or Edge TTS (online)
- **Core Voice Loop**: Works offline when using local STT/TTS

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/jarvis-ai-assistant.git
   cd jarvis-ai-assistant
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r Requirements.txt
   ```

4. **Configure environment (.env)**
   - Copy `.env.example` to `.env`
   - Fill values as needed (see [API Configuration](#api-configuration))
   - **Minimum required**: `GroqAPIKey` for AI responses
   - **For offline operation**: Set up Vosk model (see [Offline Setup](#offline-setup))
   - Keep the file in the project root (same folder as `Main.py`)

5. **Run the application**
   ```bash
   # From the project root with the venv activated
   python Main.py
   ```

### Offline Setup (Local STT/TTS)

#### Install Vosk Model (Offline STT)
1. Download a Vosk model from: https://alphacephei.com/vosk/models
2. Recommended: `vosk-model-small-en-us-0.15` (40MB) or `vosk-model-en-us-0.22` (1.8GB)
3. Extract to `models/` or `Data/` directory
4. The app will auto-detect the model

#### Wake Word Setup
- **Porcupine (Recommended)**: Get free key from https://console.picovoice.ai/
  - Add `PORCUPINE_ACCESS_KEY=your_key` to `.env`
- **Snowboy (Free)**: Download model from https://snowboy.kitt.ai/
  - Place `.pmdl` file in `models/` or `Data/`
- **Fallback**: STT-based detection (no setup needed, less efficient)

### Notes for Windows
- If you see an error about ChromeDriver, it will auto-install via `webdriver-manager`.
- If Spotify playback via API fails, it will open the track/search in the browser.
- Make sure microphone access is enabled for apps in Windows Privacy settings.

### Notes for macOS/Linux
- Replace Windows-style paths with POSIX paths if needed.
- You may need to install system packages for `PyQt5`, `opencv-python`, and `pytesseract`.
- For Tesseract OCR on macOS: `brew install tesseract`; on Ubuntu/Debian: `sudo apt-get install tesseract-ocr`.

## 🔑 API Configuration

### Required API Keys

| Service | Purpose | How to Get |
|---------|---------|------------|
| **Groq API** | Primary AI service | [console.groq.com](https://console.groq.com/) |
| **Cohere API** | Backup AI service | [dashboard.cohere.ai](https://dashboard.cohere.ai/) |
| **Spotify API** | Music integration (optional) | [developer.spotify.com](https://developer.spotify.com/dashboard) |
| **Hugging Face** | Additional AI capabilities | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |

### Environment Variables
Create a `.env` file with your configuration (you can copy from `env.example`):

```env
# User Configuration
Username=Your Name
Assistantname=JARVIS
InputLanguage=en-US
AssistantVoice=en-CA-LiamNeural

# API Keys
GroqAPIKey=your_groq_api_key_here
# Optional extra providers
CohereAPIKey=
HuggingFaceAPIKey=

# Spotify (optional; enables rich playback)
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

## 🎯 Usage

### Start the app
1) Activate your virtual environment
2) Run `python Main.py`
3) The full-screen GUI opens. Click the mic icon to toggle listening.
4) You can also type directly in the Message screen input and press Enter.

The status label shows: Available… → Listening… → Thinking… → Answering…

### Voice Commands

#### General Questions
- "Hello JARVIS, how are you?"
- "What's the weather like today?"
- "Tell me about artificial intelligence"
- "Who created you?"

#### Music & Media
- "Play Shape of You on Spotify"
- "Play Despacito on YouTube"
- "Open Spotify and play my playlist"

#### Application Control
- "Open notepad"
- "Open YouTube"
- "Open calculator"
- "Open Chrome browser"

#### System Commands
- "Search for Python tutorials"
- "What time is it?"
- "Tell me a joke"

## 📁 Project Structure

```
jarvis-ai-assistant/
├── Backend/                 # Core AI and processing modules
│   ├── Automation.py       # System control and app launching
│   ├── Chatbot.py          # Conversational AI logic
│   ├── Model.py            # Decision-making model
│   ├── SpeechToText.py     # Voice recognition
│   ├── TextToSpeech.py     # Voice synthesis
│   └── RealtimeSearchEngine.py # Web search capabilities
├── Frontend/               # User interface
│   ├── GUI.py             # Main interface
│   ├── Graphics/          # UI assets
│   └── Files/             # Data storage
├── Data/                  # Conversation logs and data
├── Main.py               # Application entry point
├── Requirements.txt      # Python dependencies
├── env.example          # Environment variables template
└── README.md            # This file
```

## 🛠️ Customization

### Voice Settings
Change the assistant's voice in `.env`:
```env
AssistantVoice=en-CA-LiamNeural  # Change to any Edge TTS voice
```

### Response Behavior
Modify response patterns in `Backend/Chatbot.py`:
- Adjust AI personality
- Change response length
- Add custom responses

### Interface Customization
Customize the GUI in `Frontend/GUI.py`:
- Change colors and styles
- Modify button layouts
- Add custom graphics

## 🔧 Troubleshooting

### Common Issues

#### Microphone not working
- Check microphone permissions in system settings
- Ensure Chrome is installed and updated
- Try running as administrator

#### API errors
- Verify API keys are correct in `.env` file
- Check internet connection
- Ensure API quotas haven't been exceeded

#### Speech recognition issues
    
#### OCR/image processing
- Install system Tesseract OCR engine as noted above if using image-to-text features.
- Ensure images are not too large for your RAM; close other heavy apps.
- Speak clearly and at normal volume
- Reduce background noise
- Check microphone sensitivity

### Performance Optimization
- Close unnecessary applications
- Ensure stable internet connection
- Use SSD storage if available

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Groq** for providing the AI language models
- **Microsoft** for Edge TTS voice synthesis
- **Google** for Chrome Web Speech API
- **PyQt5** for the GUI framework
- **OpenAI** for inspiration and AI concepts

## 📦 Deployment & Packaging

### Build Standalone Executable

#### Windows
```bash
# Run build script
build.bat

# Executable will be in dist/JARVIS.exe
# Copy .env file to dist/ folder before running
```

#### Linux/macOS
```bash
# Make script executable
chmod +x build.sh

# Run build script
./build.sh

# Executable will be in dist/JARVIS
# Copy .env file to dist/ folder before running
```

### Auto-Start Setup

#### Windows
1. Copy `start_jarvis.bat` to Windows Startup folder:
   - Press `Win+R`, type `shell:startup`, press Enter
   - Copy `start_jarvis.bat` there
   - Edit the script to point to your JARVIS installation

#### Linux (systemd)
Create `/etc/systemd/system/jarvis.service`:
```ini
[Unit]
Description=JARVIS AI Assistant
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/jarvis-ai-assistant
ExecStart=/path/to/jarvis-ai-assistant/dist/JARVIS
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable jarvis
sudo systemctl start jarvis
```

#### macOS (LaunchAgent)
Create `~/Library/LaunchAgents/com.jarvis.assistant.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jarvis.assistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/jarvis-ai-assistant/dist/JARVIS</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

### Raspberry Pi Deployment

1. Install dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip python3-venv portaudio19-dev
   ```

2. Build and run as above (use `build.sh`)

3. For headless operation, use systemd service (see Linux setup above)

## 📞 Support

If you encounter any issues or have questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the [API configuration guide](#api-configuration)
3. Check [CHANGELOG.md](CHANGELOG.md) for recent changes
4. Open an [issue](https://github.com/yourusername/jarvis-ai-assistant/issues)
5. Contact the developer

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/jarvis-ai-assistant&type=Date)](https://star-history.com/#yourusername/jarvis-ai-assistant&Date)

---

**Made with ❤️ by [Shubh Mishra](https://portfolio-shubh.vercel.app/)**

*Transform your computer into a smart assistant with JARVIS!* 🤖✨