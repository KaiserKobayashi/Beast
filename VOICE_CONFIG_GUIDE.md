# Voice Configuration and Multi-User Support

## Overview
Beast now supports comprehensive voice configuration with male and female voices for 36+ languages with appropriate accents. The application also includes multi-user profile support, allowing two or more people to use the app with their own language and gender preferences.

## Features

### 1. Language Support
The application now supports 36+ languages including:
- English (US, UK, Australia, Canada, India)
- Spanish (Spain, Mexico, Argentina)
- French (France, Canada)
- German (Germany, Austria)
- Italian, Portuguese (Brazil, Portugal)
- Russian, Japanese, Korean
- Chinese (Simplified, Traditional)
- Arabic (Saudi Arabia, Egypt)
- Hindi, Dutch, Polish, Turkish
- Swedish, Norwegian, Danish, Finnish
- Thai, Vietnamese, Ukrainian, Czech
- Greek, Hebrew
- And many more!

### 2. Gender Selection
Each language has both male and female voice options with appropriate accents:
- **Female voices**: High-quality neural voices for natural-sounding speech
- **Male voices**: Professional neural voices with proper language accents

### 3. Multi-User Profiles
The application supports multiple user profiles, allowing:
- **Two or more people** to use the app simultaneously with different settings
- **Quick switching** between profiles
- **Personalized preferences** for each user (language and gender)
- **Profile management** (add, remove, switch)

## Usage

### GUI Interface

1. **Profile Selection**
   - Select your profile from the "Profile" dropdown
   - Click "Add Profile" to create a new user profile
   - Click "Remove Profile" to delete the current profile (requires at least one profile to remain)

2. **Language Selection**
   - Choose your preferred language from the "Language" dropdown
   - The language dropdown shows both the language code and display name (e.g., "en-US - English (US)")
   - Each language includes appropriate regional accents

3. **Gender Selection**
   - Select either "female" or "male" from the "Gender" dropdown
   - The voice will automatically update to match your selection

4. **Automatic Voice Selection**
   - When you select a language and gender, the appropriate voice is automatically chosen
   - The voice is displayed in the "Voice" field for reference

### Multi-User Workflow

**Scenario: Two people sharing the application**

1. **User 1 Setup**:
   - Create profile "Alice"
   - Select "es-MX - Spanish (Mexico)"
   - Select "female" gender
   - Voice automatically set to "es-MX-DaliaNeural"

2. **User 2 Setup**:
   - Create profile "Bob"
   - Select "en-GB - English (UK)"
   - Select "male" gender
   - Voice automatically set to "en-GB-RyanNeural"

3. **Switching Between Users**:
   - Alice selects her profile from the dropdown → settings automatically load
   - Bob selects his profile from the dropdown → settings automatically load
   - Both can work independently with their preferred settings

## Configuration

### Profile Storage
User profiles are stored in:
- **Windows**: `%APPDATA%\beast\config.json`
- **Linux/Mac**: `~/.config/beast/config.json`

### Profile Structure
```json
{
  "current_profile": "User 1",
  "profiles": {
    "User 1": {
      "language": "en-US",
      "gender": "female",
      "voice_index": 0
    },
    "User 2": {
      "language": "en-US",
      "gender": "male",
      "voice_index": 0
    }
  }
}
```

## Voice Configuration Module

The `voice_config.py` module provides:
- `get_voice(language, gender, index)`: Get a specific voice
- `get_available_languages()`: List all supported languages
- `get_language_display_name(code)`: Get display name for a language
- `get_all_voices_for_language(language)`: Get all voices for a specific language

## Technical Details

### Voice Library
The application uses Microsoft Azure's edge-tts service with neural voices:
- High-quality, natural-sounding speech
- Multiple voice options per language and gender
- Appropriate regional accents for each language variant

### Automatic Voice Mapping
When you select a language and gender:
1. The system looks up the appropriate voice from the voice library
2. The primary voice for that combination is automatically selected
3. The voice name is displayed in the UI
4. The voice is passed to the TTS engine for speech synthesis

## Examples

### Example Voice Mappings

| Language | Gender | Voice Name | Description |
|----------|--------|------------|-------------|
| en-US | female | en-US-AriaNeural | American English, Female |
| en-US | male | en-US-GuyNeural | American English, Male |
| es-MX | female | es-MX-DaliaNeural | Mexican Spanish, Female |
| es-MX | male | es-MX-JorgeNeural | Mexican Spanish, Male |
| fr-FR | female | fr-FR-DeniseNeural | French, Female |
| fr-FR | male | fr-FR-HenriNeural | French, Male |
| ja-JP | female | ja-JP-NanamiNeural | Japanese, Female |
| ja-JP | male | ja-JP-KeitaNeural | Japanese, Male |

## Benefits

1. **Accessibility**: Users can select voices that match their language preferences
2. **Authenticity**: Regional accents ensure authentic pronunciation
3. **Flexibility**: Multiple profiles support shared use cases
4. **Ease of Use**: Simple UI makes it easy to switch between languages and genders
5. **Personalization**: Each user can have their own customized settings

## Requirements

The following Python packages are required:
- PySimpleGUI>=4.60
- edge-tts (for voice synthesis)
- pydub (for audio processing)

Install dependencies:
```bash
pip install -r requirements.txt
```
