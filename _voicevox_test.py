import importlib.util, sys, time, os

spec = importlib.util.spec_from_file_location('voicevox_client', r'src\DownloadBeast\voicevox_client.py')
vv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vv)
print('voicevox_client loaded, synthesize_wav_bytes =', getattr(vv, 'synthesize_wav_bytes', None))

spec2 = importlib.util.spec_from_file_location('gui_snip', r'src\DownloadBeast\gui_voicevox_snippet.py')
gs = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(gs)
print('gui snippet loaded, test_engine_popup =', getattr(gs, 'test_engine_popup', None))

gs.test_engine_popup()
print('test_engine_popup called; waiting 10s for any popup/async work...')
time.sleep(10)
print('done')
