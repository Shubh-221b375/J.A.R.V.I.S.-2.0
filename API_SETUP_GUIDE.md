# 🚀 Complete API Setup Guide - Step by Step

This guide will help you get ALL API keys configured for full JARVIS functionality.

## 📋 Quick Checklist

- [ ] Groq API Key (Required)
- [ ] Porcupine Access Key (Wake Word - Optional)
- [ ] Hugging Face API Key (Image Generation - Optional)
- [ ] Spotify API (Music - Optional)
- [ ] Email Credentials (Email Sending - Optional)
- [ ] Twilio API (WhatsApp - Optional)
- [ ] Google Sheets API (CRM Sync - Optional)

---

## 1️⃣ Groq API Key (REQUIRED)

**Why**: Powers all AI conversations and responses

**Steps**:
1. Go to https://console.groq.com/
2. Sign up or log in
3. Click "API Keys" in the sidebar
4. Click "Create API Key"
5. Copy the key (starts with `gsk_...`)
6. Paste in `.env` file: `GroqAPIKey=your_key_here`

**Cost**: Free tier with generous limits

---

## 2️⃣ Porcupine Access Key (Wake Word - Optional)

**Why**: Offline wake word detection ("Jarvis")

**Steps**:
1. Go to https://console.picovoice.ai/
2. Sign up (free account)
3. Navigate to "Access Keys"
4. Create a new access key
5. Copy the key
6. Paste in `.env` file: `PORCUPINE_ACCESS_KEY=your_key_here`

**Alternative**: Use Snowboy (free, no key needed)
- Download model from https://snowboy.kitt.ai/
- Place `.pmdl` file in `models/` or `Data/` folder

**Cost**: Free tier available

---

## 3️⃣ Hugging Face API Key (Image Generation - Optional)

**Why**: Generate images with AI

**Steps**:
1. Go to https://huggingface.co/
2. Sign up or log in
3. Go to https://huggingface.co/settings/tokens
4. Click "New token"
5. Name it "JARVIS" and select "Read" permission
6. Copy the token
7. Paste in `.env` file: `HuggingFaceAPIKey=your_token_here`

**Cost**: Free tier available

---

## 4️⃣ Spotify API (Music - Optional)

**Why**: Direct Spotify playback instead of opening browser

**Steps**:
1. Go to https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click "Create an app"
4. Fill in:
   - App name: "JARVIS Assistant"
   - App description: "AI Voice Assistant"
   - Redirect URI: `http://127.0.0.1:8888/callback`
5. Click "Save"
6. Copy "Client ID" and "Client Secret"
7. Add to `.env`:
   ```env
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
   ```

**Cost**: Free

---

## 5️⃣ Email Credentials (Email Sending - Optional)

**Why**: Send emails directly from JARVIS

### For Gmail:

**Steps**:
1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/security
3. Scroll to "2-Step Verification" and enable it
4. Go to "App passwords" (or search for it)
5. Select "Mail" and "Other (Custom name)"
6. Name it "JARVIS"
7. Click "Generate"
8. Copy the 16-character password
9. Add to `.env`:
   ```env
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_16_char_app_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

**Important**: Use the app password, NOT your regular Gmail password!

### For Other Email Providers:

**Outlook/Hotmail**:
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

**Yahoo**:
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

**Custom SMTP**: Check your email provider's documentation for SMTP settings.

---

## 6️⃣ Twilio API (WhatsApp - Optional)

**Why**: Send WhatsApp messages programmatically

**Steps**:
1. Go to https://www.twilio.com/
2. Sign up for free account (trial account with $15 credit)
3. Verify your phone number
4. Go to Dashboard
5. Copy "Account SID" and "Auth Token"
6. Go to "Messaging" → "Try it out" → "Send a WhatsApp message"
7. Follow instructions to enable WhatsApp Sandbox
8. Add to `.env`:
   ```env
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ```

**Note**: Sandbox mode allows testing with specific numbers. For production, you'll need to upgrade.

**Cost**: Free trial with $15 credit, then pay-as-you-go

---

## 7️⃣ Google Sheets API (CRM Sync - Optional)

**Why**: Read/write data from Google Sheets for CRM integration

**Steps**:

### Step 1: Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Name it "JARVIS" and click "Create"

### Step 2: Enable APIs
1. Go to "APIs & Services" → "Library"
2. Search for "Google Sheets API" and enable it
3. Search for "Google Drive API" and enable it

### Step 3: Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Name it "jarvis-assistant"
4. Click "Create and Continue"
5. Skip role assignment (click "Continue")
6. Click "Done"

### Step 4: Create Key
1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON" and click "Create"
5. Save the downloaded JSON file (e.g., `jarvis-credentials.json`)
6. Move it to your JARVIS project folder

### Step 5: Share Google Sheet
1. Open your Google Sheet
2. Copy the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`
3. Click "Share" button
4. Add the service account email (found in the JSON file, looks like `jarvis-assistant@...`)
5. Give it "Editor" permission
6. Click "Send"

### Step 6: Add to .env
```env
GOOGLE_CREDENTIALS_PATH=jarvis-credentials.json
GOOGLE_SPREADSHEET_ID=your_sheet_id_from_url
```

**Cost**: Free (with usage limits)

---

## ✅ Verification

After adding all keys to your `.env` file:

1. **Test Groq API**:
   ```bash
   python Main.py
   # Try asking a question - should get AI response
   ```

2. **Test Wake Word**:
   - Say "Jarvis" and verify it activates

3. **Test Image Generation**:
   - Say "generate an image of a cat"
   - Should create image if HuggingFace key is set

4. **Test Spotify**:
   - Say "play Shape of You on Spotify"
   - Should play directly if keys are set

5. **Test Email**:
   - Say "send email to test@example.com subject Test body Hello"
   - Check if email is sent (check spam folder)

6. **Test WhatsApp**:
   - Say "send whatsapp to +1234567890 message Hello"
   - Should send via Twilio if configured

7. **Test Google Sheets**:
   - Say "sync crm"
   - Should read from Google Sheets if configured

---

## 🆘 Troubleshooting

### "Invalid API key" errors
- Double-check you copied the entire key (no spaces)
- Verify the key is active in the provider's dashboard
- Check if you need to enable billing (some providers require it)

### Email not sending
- Verify you're using an app password (not regular password) for Gmail
- Check 2FA is enabled
- Try different SMTP port (465 for SSL)

### WhatsApp not working
- Verify you're in Twilio WhatsApp Sandbox
- Add your number to sandbox: Send "join [code]" to the sandbox number
- Check Twilio console for error messages

### Google Sheets access denied
- Verify service account email is shared with the sheet
- Check service account has "Editor" permission
- Verify JSON credentials file path is correct

---

## 📝 Notes

- **Keep your `.env` file secure** - never commit it to Git!
- **Start with just Groq API** - add others as needed
- **Free tiers** are available for most services
- **Test each feature** after adding its API key

---

**Need help?** Check the main README.md or open an issue on GitHub.

