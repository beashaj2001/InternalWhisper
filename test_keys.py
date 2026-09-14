from pynput import keyboard

print("Press some keys to test detection (Ctrl, Shift, Alt, F-keys, etc).")
print("Press Escape to stop.\n")

def on_press(key):
    try:
        name = getattr(key, 'name', None)
        char = getattr(key, 'char', None)
        vk   = getattr(key, 'vk', None)
        print(f"  PRESS:  repr={key!r:30s}  name={str(name):15s}  char={str(char):10s}  vk={vk}")
    except Exception as e:
        print(f"  ERROR: {e}")

def on_release(key):
    if key == keyboard.Key.esc:
        return False

with keyboard.Listener(on_press=on_press, on_release=on_release) as l:
    l.join()

print("\nDone.")
