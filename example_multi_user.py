#!/usr/bin/env python3
"""
example_multi_user.py

Example script demonstrating multi-user functionality with different
language and gender preferences.

This example shows how two users (Alice and Bob) can use the Beast app
with their own personalized settings.
"""

from voice_config import get_voice, get_language_display_name
from beast_config import load_config, save_config


def setup_example_profiles():
    """Set up example user profiles."""
    cfg = load_config()
    
    # Ensure profiles dict exists
    if "profiles" not in cfg:
        cfg["profiles"] = {}
    
    # Create Alice's profile - Spanish speaker preferring female voice
    cfg["profiles"]["Alice"] = {
        "language": "es-MX",
        "gender": "female",
        "voice_index": 0
    }
    
    # Create Bob's profile - French speaker preferring male voice
    cfg["profiles"]["Bob"] = {
        "language": "fr-FR",
        "gender": "male",
        "voice_index": 0
    }
    
    # Create Carol's profile - Japanese speaker preferring female voice
    cfg["profiles"]["Carol"] = {
        "language": "ja-JP",
        "gender": "female",
        "voice_index": 0
    }
    
    # Save configuration
    save_config(cfg)
    return cfg


def demonstrate_profile_switching():
    """Demonstrate switching between user profiles."""
    
    print("=" * 70)
    print("Multi-User Profile Demonstration")
    print("=" * 70)
    print()
    
    # Set up example profiles
    cfg = setup_example_profiles()
    
    print("Setting up three example users:")
    print()
    
    # Show all profiles
    profiles = cfg.get("profiles", {})
    for profile_name, profile_data in profiles.items():
        lang = profile_data.get("language", "en-US")
        gender = profile_data.get("gender", "female")
        voice = get_voice(lang, gender)
        lang_display = get_language_display_name(lang)
        
        print(f"Profile: {profile_name}")
        print(f"  Language: {lang_display} ({lang})")
        print(f"  Gender: {gender}")
        print(f"  Voice: {voice}")
        print()
    
    print("=" * 70)
    print("Simulating User Workflow")
    print("=" * 70)
    print()
    
    # Simulate Alice's session
    print("1. Alice starts the app:")
    cfg["current_profile"] = "Alice"
    save_config(cfg)
    alice_profile = profiles["Alice"]
    alice_lang = alice_profile["language"]
    alice_gender = alice_profile["gender"]
    alice_voice = get_voice(alice_lang, alice_gender)
    print(f"   - Selects profile: Alice")
    print(f"   - Language auto-set to: {get_language_display_name(alice_lang)}")
    print(f"   - Gender auto-set to: {alice_gender}")
    print(f"   - Voice auto-selected: {alice_voice}")
    print(f"   - Alice converts her Spanish video with female voice")
    print()
    
    # Simulate Bob's session
    print("2. Bob uses the app:")
    cfg["current_profile"] = "Bob"
    save_config(cfg)
    bob_profile = profiles["Bob"]
    bob_lang = bob_profile["language"]
    bob_gender = bob_profile["gender"]
    bob_voice = get_voice(bob_lang, bob_gender)
    print(f"   - Selects profile: Bob")
    print(f"   - Language auto-set to: {get_language_display_name(bob_lang)}")
    print(f"   - Gender auto-set to: {bob_gender}")
    print(f"   - Voice auto-selected: {bob_voice}")
    print(f"   - Bob converts his French video with male voice")
    print()
    
    # Simulate Carol's session
    print("3. Carol uses the app:")
    cfg["current_profile"] = "Carol"
    save_config(cfg)
    carol_profile = profiles["Carol"]
    carol_lang = carol_profile["language"]
    carol_gender = carol_profile["gender"]
    carol_voice = get_voice(carol_lang, carol_gender)
    print(f"   - Selects profile: Carol")
    print(f"   - Language auto-set to: {get_language_display_name(carol_lang)}")
    print(f"   - Gender auto-set to: {carol_gender}")
    print(f"   - Voice auto-selected: {carol_voice}")
    print(f"   - Carol converts her Japanese video with female voice")
    print()
    
    print("=" * 70)
    print("Benefits of Multi-User Profiles")
    print("=" * 70)
    print()
    print("✓ Each user has personalized settings")
    print("✓ Quick switching between profiles")
    print("✓ No need to reconfigure language/gender each time")
    print("✓ Multiple people can share the same application")
    print("✓ Settings are automatically restored when switching profiles")
    print()


def demonstrate_language_coverage():
    """Demonstrate the breadth of language support."""
    
    print("=" * 70)
    print("Language Coverage Demonstration")
    print("=" * 70)
    print()
    
    sample_languages = [
        ("en-US", "female", "American English"),
        ("en-GB", "male", "British English"),
        ("es-ES", "female", "European Spanish"),
        ("es-MX", "male", "Mexican Spanish"),
        ("fr-FR", "female", "French"),
        ("de-DE", "male", "German"),
        ("it-IT", "female", "Italian"),
        ("pt-BR", "male", "Brazilian Portuguese"),
        ("ru-RU", "female", "Russian"),
        ("ja-JP", "male", "Japanese"),
        ("ko-KR", "female", "Korean"),
        ("zh-CN", "male", "Chinese (Simplified)"),
        ("ar-SA", "female", "Arabic (Saudi Arabia)"),
        ("hi-IN", "male", "Hindi"),
    ]
    
    print("Sample of available voices with regional accents:")
    print()
    
    for lang, gender, description in sample_languages:
        voice = get_voice(lang, gender)
        print(f"  {description:30s} ({gender:6s}): {voice}")
    
    print()
    print(f"Total: 36+ languages with regional accents available!")
    print()


def main():
    """Run the demonstration."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  Beast Multi-User & Voice Configuration Demo".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    
    # Demonstrate profile switching
    demonstrate_profile_switching()
    
    # Demonstrate language coverage
    demonstrate_language_coverage()
    
    print("=" * 70)
    print("Next Steps")
    print("=" * 70)
    print()
    print("1. Run the GUI: python beast_gui.py")
    print("2. Create your own profile with the 'Add Profile' button")
    print("3. Select your preferred language and gender")
    print("4. Start converting videos with personalized voice settings!")
    print()


if __name__ == "__main__":
    main()
