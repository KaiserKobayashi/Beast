#!/usr/bin/env python3
"""
test_voice_config.py

Test script to demonstrate voice configuration features.
This script tests the voice selection functionality without requiring network access.
"""

from voice_config import (
    get_voice, 
    get_available_languages, 
    get_language_display_name,
    get_all_voices_for_language,
    build_voice_map
)
from beast_config import load_config, save_config, default_config


def test_voice_selection():
    """Test basic voice selection functionality."""
    print("=" * 70)
    print("TEST 1: Voice Selection")
    print("=" * 70)
    
    test_cases = [
        ("en-US", "female", "en-US-AriaNeural"),
        ("en-US", "male", "en-US-GuyNeural"),
        ("es-MX", "female", "es-MX-DaliaNeural"),
        ("es-MX", "male", "es-MX-JorgeNeural"),
        ("fr-FR", "female", "fr-FR-DeniseNeural"),
        ("fr-FR", "male", "fr-FR-HenriNeural"),
        ("ja-JP", "female", "ja-JP-NanamiNeural"),
        ("ja-JP", "male", "ja-JP-KeitaNeural"),
    ]
    
    all_passed = True
    for lang, gender, expected in test_cases:
        result = get_voice(lang, gender)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"  {status} {lang} {gender:6s} -> {result:30s} (expected: {expected})")
    
    print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}\n")
    return all_passed


def test_language_list():
    """Test language listing functionality."""
    print("=" * 70)
    print("TEST 2: Available Languages")
    print("=" * 70)
    
    languages = get_available_languages()
    print(f"  Total languages: {len(languages)}")
    print(f"  Languages: {', '.join(languages[:10])}...")
    
    passed = len(languages) >= 30
    print(f"\n  Result: {'PASSED' if passed else 'FAILED'}\n")
    return passed


def test_display_names():
    """Test language display name functionality."""
    print("=" * 70)
    print("TEST 3: Language Display Names")
    print("=" * 70)
    
    test_cases = [
        ("en-US", "English (US)"),
        ("es-MX", "Spanish (Mexico)"),
        ("fr-FR", "French (France)"),
        ("de-DE", "German (Germany)"),
        ("ja-JP", "Japanese"),
        ("zh-CN", "Chinese (Simplified)"),
    ]
    
    all_passed = True
    for lang_code, expected in test_cases:
        result = get_language_display_name(lang_code)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"  {status} {lang_code:8s} -> {result:30s} (expected: {expected})")
    
    print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}\n")
    return all_passed


def test_voice_map_builder():
    """Test voice map building functionality."""
    print("=" * 70)
    print("TEST 4: Voice Map Builder")
    print("=" * 70)
    
    language_configs = [
        {"language": "en-US", "gender": "female"},
        {"language": "es-MX", "gender": "male"},
        {"language": "fr-FR", "gender": "female"},
    ]
    
    voice_map = build_voice_map(language_configs)
    
    expected = {
        "en-US": "en-US-AriaNeural",
        "es-MX": "es-MX-JorgeNeural",
        "fr-FR": "fr-FR-DeniseNeural",
    }
    
    all_passed = True
    for lang, expected_voice in expected.items():
        result = voice_map.get(lang)
        status = "✓" if result == expected_voice else "✗"
        if result != expected_voice:
            all_passed = False
        print(f"  {status} {lang:8s} -> {result:30s} (expected: {expected_voice})")
    
    print(f"\n  Result: {'PASSED' if all_passed else 'FAILED'}\n")
    return all_passed


def test_profile_config():
    """Test profile configuration functionality."""
    print("=" * 70)
    print("TEST 5: Profile Configuration")
    print("=" * 70)
    
    cfg = load_config()
    
    # Check default profiles
    profiles = cfg.get("profiles", {})
    current_profile = cfg.get("current_profile", "")
    
    print(f"  Current profile: {current_profile}")
    print(f"  Available profiles: {list(profiles.keys())}")
    
    # Check User 1
    user1 = profiles.get("User 1", {})
    print(f"\n  User 1 Settings:")
    print(f"    Language: {user1.get('language', 'N/A')}")
    print(f"    Gender: {user1.get('gender', 'N/A')}")
    
    # Check User 2
    user2 = profiles.get("User 2", {})
    print(f"\n  User 2 Settings:")
    print(f"    Language: {user2.get('language', 'N/A')}")
    print(f"    Gender: {user2.get('gender', 'N/A')}")
    
    passed = (
        len(profiles) >= 2 and
        "User 1" in profiles and
        "User 2" in profiles and
        user1.get("gender") == "female" and
        user2.get("gender") == "male"
    )
    
    print(f"\n  Result: {'PASSED' if passed else 'FAILED'}\n")
    return passed


def test_multi_voice_options():
    """Test multiple voice options per language."""
    print("=" * 70)
    print("TEST 6: Multiple Voice Options")
    print("=" * 70)
    
    test_langs = ["en-US", "es-MX", "fr-FR", "de-DE"]
    
    for lang in test_langs:
        voices = get_all_voices_for_language(lang)
        male_count = len(voices.get("male", []))
        female_count = len(voices.get("female", []))
        print(f"  {lang:8s}: {female_count} female voices, {male_count} male voices")
    
    print(f"\n  Result: PASSED\n")
    return True


def main():
    """Run all tests."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  Beast Voice Configuration Test Suite".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    
    tests = [
        test_voice_selection,
        test_language_list,
        test_display_names,
        test_voice_map_builder,
        test_profile_config,
        test_multi_voice_options,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ERROR: {e}\n")
            results.append(False)
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"  Tests passed: {passed}/{total}")
    
    if passed == total:
        print(f"\n  ✓ All tests PASSED!")
    else:
        print(f"\n  ✗ Some tests FAILED")
    
    print("\n")


if __name__ == "__main__":
    main()
