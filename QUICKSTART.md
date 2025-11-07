# Quick Start Guide - Voice Configuration & Multi-User Support

## Getting Started in 3 Minutes

### 1. Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

This installs:
- PySimpleGUI (for the GUI)
- edge-tts (for voice synthesis)
- pydub (for audio processing)

### 2. Run the GUI (30 seconds)

```bash
python beast_gui.py
```

### 3. Configure Your Profile (1 minute)

When the GUI opens, you'll see:

1. **Profile Selector** - Default profiles "User 1" and "User 2" are already created
2. **Language Dropdown** - 36+ languages available
3. **Gender Dropdown** - Male or Female voice selection

#### To Create Your Profile:

1. Click **"Add Profile"**
2. Enter your name (e.g., "Alice")
3. Select your language (e.g., "es-MX - Spanish (Mexico)")
4. Select your gender preference (e.g., "female")
5. The voice is automatically selected!

#### To Switch Between Users:

1. User 1 selects their profile → Settings load automatically
2. User 2 selects their profile → Settings load automatically
3. No need to reconfigure each time!

### 4. Process Your Video (30 seconds)

1. Click **"Browse"** next to "Input file or folder"
2. Select your video or SRT file
3. (Optional) Select an output folder
4. Click **"Run"**
5. Wait for processing to complete

Done! Your video now has TTS audio with the correct accent and gender!

## Common Scenarios

### Scenario 1: Two People Sharing the App

**Alice (Spanish speaker, prefers female voice):**
```
Profile: Alice
Language: es-MX - Spanish (Mexico)
Gender: female
Voice: es-MX-DaliaNeural (automatically selected)
```

**Bob (French speaker, prefers male voice):**
```
Profile: Bob
Language: fr-FR - French (France)
Gender: male
Voice: fr-FR-HenriNeural (automatically selected)
```

Both can switch profiles instantly without reconfiguring!

### Scenario 2: Single User, Multiple Languages

**Teacher preparing lessons in different languages:**
```
Profile: English Lessons
Language: en-US - English (US)
Gender: female

Profile: Spanish Lessons
Language: es-ES - Spanish (Spain)
Gender: male

Profile: French Lessons
Language: fr-FR - French (France)
Gender: female
```

Switch profiles to process videos in different languages!

### Scenario 3: Comparing Voice Genders

Create two profiles with the same language but different genders:
```
Profile: US Female
Language: en-US
Gender: female

Profile: US Male
Language: en-US
Gender: male
```

Process the same video with both to compare!

## Available Languages (Sample)

### English Variants
- en-US (United States)
- en-GB (United Kingdom)
- en-AU (Australia)
- en-CA (Canada)
- en-IN (India)

### Spanish Variants
- es-ES (Spain)
- es-MX (Mexico)
- es-AR (Argentina)

### Other Major Languages
- French (fr-FR, fr-CA)
- German (de-DE, de-AT)
- Italian (it-IT)
- Portuguese (pt-BR, pt-PT)
- Russian (ru-RU)
- Japanese (ja-JP)
- Korean (ko-KR)
- Chinese (zh-CN, zh-TW)
- Arabic (ar-SA, ar-EG)
- Hindi (hi-IN)
- And 20+ more!

## Tips & Tricks

### Tip 1: Test Voices with Example Script
```bash
python example_multi_user.py
```
This shows all available voices and demonstrates profile switching!

### Tip 2: Run Tests
```bash
python test_voice_config.py
```
Verify all 36+ languages are working correctly!

### Tip 3: Adjust Speech Rate
Use the **Rate slider** (0.5x to 2.0x) to control speech speed:
- 0.5 = Half speed (slower, easier to understand)
- 1.0 = Normal speed
- 2.0 = Double speed (faster)

### Tip 4: Quick Profile Switching
Keep the profile dropdown visible and accessible - switching takes just one click!

### Tip 5: Remove Unwanted Profiles
Select a profile and click **"Remove Profile"** to delete it.
(You must keep at least one profile)

## Keyboard Shortcuts (GUI)

- **Alt+F** - Focus on input file field
- **Alt+R** - Run processing
- **Alt+S** - Stop processing
- **Tab** - Navigate between fields

## Troubleshooting

### Problem: "edge-tts not installed"
**Solution**: Run `pip install edge-tts`

### Problem: Voice not working
**Solution**: Check your internet connection (edge-tts requires internet)

### Problem: Profile not saving
**Solution**: Check permissions on config directory:
- Windows: `%APPDATA%\beast\`
- Linux/Mac: `~/.config/beast/`

### Problem: GUI not opening
**Solution**: Make sure PySimpleGUI is installed: `pip install PySimpleGUI`

## Advanced Usage

### Custom Voice Selection
You can override the automatic voice selection by typing a voice name directly in the **Voice** field:
```
en-US-AriaNeural
es-MX-DaliaNeural
fr-FR-DeniseNeural
```

### Command Line Usage
For batch processing, use the command line:
```bash
python auto_srt_all_tts_wrapper.py --input video.mp4 --voice es-MX-DaliaNeural
```

### Multiple Files
Select a folder as input to process multiple files at once!

## What's Next?

1. **Explore Languages**: Try different language variants (British vs American English, European vs Mexican Spanish, etc.)
2. **Compare Genders**: Process the same content with male and female voices
3. **Share Profiles**: Multiple family members can each have their own profile
4. **Batch Processing**: Process entire folders of videos at once

## Need Help?

- Read the full guide: `VOICE_CONFIG_GUIDE.md`
- Check implementation details: `IMPLEMENTATION_SUMMARY.md`
- View example code: `example_multi_user.py`
- Run tests: `test_voice_config.py`

## Summary

**Time to get started**: 3 minutes
**Languages supported**: 36+
**Voice genders**: Male and Female for each language
**Multi-user**: Unlimited profiles

Enjoy your personalized voice configuration experience! 🎉
