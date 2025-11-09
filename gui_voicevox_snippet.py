from voicevox_client import synthesize_and_play_async

def test_engine_popup():
    print("VoiceVox GUI snippet test starting...")
    try:
        synthesize_and_play_async("This is a real pain in the ass, i want a frikkin chu-hi.")
    except Exception as e:
        print("Error during synthesize_and_play_async:", e)
    print("VoiceVox GUI snippet finished.")
