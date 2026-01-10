from PIL import Image
import sys
import os
import time
import pygame
import subprocess

# Add the Driver directory to the path to import WhisPlayBoard
sys.path.append(os.path.abspath("../Driver"))
try:
    from WhisPlay import WhisPlayBoard
except ImportError:
    print("Error: Could not find WhisPlay driver.")
    print("Make sure the Driver directory exists and contains WhisPlay.py")
    sys.exit(1)

# Initialize the board
board = WhisPlayBoard()
board.set_backlight(50)

# Initialize pygame mixer for sound playback
pygame.mixer.init()
sound1 = None  # Global sound variable for sound1
sound2 = None  # Global sound variable for sound2
playing = False  # Global variable to track if sound is playing
last_button_press_time = 0  # Track time of last button press for double-tap detection
double_tap_threshold = 0.5  # Time window in seconds for double-tap detection (500ms)
pending_single_tap = False  # Flag to track if we're waiting to confirm a single tap

def load_image_as_rgb565(filepath, screen_width, screen_height):
    """Load and convert an image to RGB565 format for the display."""
    img = Image.open(filepath).convert('RGB')
    original_width, original_height = img.size

    aspect_ratio = original_width / original_height
    screen_aspect_ratio = screen_width / screen_height

    if aspect_ratio > screen_aspect_ratio:
        # Original image is wider, scale based on screen height
        new_height = screen_height
        new_width = int(new_height * aspect_ratio)
        resized_img = img.resize((new_width, new_height))
        # Calculate horizontal offset to center the image
        offset_x = (new_width - screen_width) // 2
        # Crop the image to fit screen width
        cropped_img = resized_img.crop(
            (offset_x, 0, offset_x + screen_width, screen_height))
    else:
        # Original image is taller or has the same aspect ratio, scale based on screen width
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)
        resized_img = img.resize((new_width, new_height))
        # Calculate vertical offset to center the image
        offset_y = (new_height - screen_height) // 2
        # Crop the image to fit screen height
        cropped_img = resized_img.crop(
            (0, offset_y, screen_width, offset_y + screen_height))

    pixel_data = []
    for y in range(screen_height):
        for x in range(screen_width):
            r, g, b = cropped_img.getpixel((x, y))
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            pixel_data.extend([(rgb565 >> 8) & 0xFF, rgb565 & 0xFF])

    return pixel_data

def set_wm8960_volume_stable(volume_level: str):
    """
    Sets the 'Speaker' volume for the wm8960 sound card using the amixer command.
    
    Args:
        volume_level (str): The desired volume value, e.g., '90%' or '121'.
    """
    CARD_NAME = 'wm8960soundcard'
    CONTROL_NAME = 'Speaker'
    DEVICE_ARG = f'hw:{CARD_NAME}'
    
    command = [
        'amixer',
        '-D', DEVICE_ARG,
        'sset',
        CONTROL_NAME,
        volume_level
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"INFO: Successfully set '{CONTROL_NAME}' volume to {volume_level} on card '{CARD_NAME}'.")
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Failed to set volume (this is okay if sound card isn't configured).", file=sys.stderr)
    except FileNotFoundError:
        print("WARNING: 'amixer' command not found. Volume setting skipped.", file=sys.stderr)

def play_sound(sound_obj, sound_name):
    """Helper function to play a sound file."""
    global playing
    if sound_obj:
        if playing:
            # Stop any currently playing sound
            pygame.mixer.stop()
            print("Stopping current sound...")
        sound_obj.play()
        print(f"Playing {sound_name}...")
        playing = True
    else:
        print(f"{sound_name} not loaded.")

def on_button_pressed():
    """Callback function when the button is pressed - detects single or double tap and plays appropriate sound."""
    global last_button_press_time, pending_single_tap, sound1, sound2, playing
    
    current_time = time.time()
    
    # Check if this is a double tap (button pressed within threshold time of previous press)
    if last_button_press_time > 0:
        time_since_last_press = current_time - last_button_press_time
        
        if time_since_last_press < double_tap_threshold and pending_single_tap:
            # This is a double tap!
            print("Double tap detected!")
            pending_single_tap = False  # Cancel the pending single tap
            play_sound(sound2, "sound2")
            last_button_press_time = 0  # Reset to prevent triple-tap detection
            return
    
    # This might be a single tap, but we need to wait to confirm no second press comes
    # Set a flag and the main loop will check after threshold time
    pending_single_tap = True
    last_button_press_time = current_time
    print("Button pressed (waiting to confirm single/double tap)...")

# Look for image1 with common extensions
image_name = "image1"
image_extensions = [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]
image_path = None

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Try to find the image file
for ext in image_extensions:
    potential_path = os.path.join(script_dir, image_name + ext)
    if os.path.exists(potential_path):
        image_path = potential_path
        break

if image_path is None:
    print(f"Error: Could not find image1 with extensions {image_extensions}")
    print(f"Please place an image named 'image1' (with extension .jpg, .jpeg, or .png) in the {script_dir} folder")
    board.cleanup()
    sys.exit(1)

# Look for sound1 with common audio extensions
sound1_name = "sound1"
sound_extensions = [".mp3", ".wav", ".ogg", ".MP3", ".WAV", ".OGG"]
sound1_path = None

# Try to find sound1 file
for ext in sound_extensions:
    potential_path = os.path.join(script_dir, sound1_name + ext)
    if os.path.exists(potential_path):
        sound1_path = potential_path
        break

# Load sound1 file if found
if sound1_path:
    try:
        sound1 = pygame.mixer.Sound(sound1_path)
        print(f"Sound1 {os.path.basename(sound1_path)} loaded successfully.")
        set_wm8960_volume_stable("121")  # Set volume (may fail gracefully if sound card not configured)
    except Exception as e:
        print(f"Warning: Failed to load sound1 from {sound1_path}: {e}")
        sound1 = None
else:
    print(f"Info: Could not find sound1 with extensions {sound_extensions}")
    print(f"Single tap will not play sound. Place a file named 'sound1' (with extension .mp3, .wav, or .ogg) in the {script_dir} folder to enable it.")

# Look for sound2 with common audio extensions
sound2_name = "sound2"
sound2_path = None

# Try to find sound2 file
for ext in sound_extensions:
    potential_path = os.path.join(script_dir, sound2_name + ext)
    if os.path.exists(potential_path):
        sound2_path = potential_path
        break

# Load sound2 file if found
if sound2_path:
    try:
        sound2 = pygame.mixer.Sound(sound2_path)
        print(f"Sound2 {os.path.basename(sound2_path)} loaded successfully.")
    except Exception as e:
        print(f"Warning: Failed to load sound2 from {sound2_path}: {e}")
        sound2 = None
else:
    print(f"Info: Could not find sound2 with extensions {sound_extensions}")
    print(f"Double tap will not play sound. Place a file named 'sound2' (with extension .mp3, .wav, or .ogg) in the {script_dir} folder to enable it.")

if sound1 is None and sound2 is None:
    print("No sound files loaded. Button presses will not play any sound.")

# Register button callback
board.on_button_press(on_button_pressed)

# Load and display the image
try:
    print(f"Loading image: {os.path.basename(image_path)}")
    image_data = load_image_as_rgb565(image_path, board.LCD_WIDTH, board.LCD_HEIGHT)
    board.draw_image(0, 0, board.LCD_WIDTH, board.LCD_HEIGHT, image_data)
    print(f"Image displayed successfully on the screen!")
    if sound1 or sound2:
        print("Single tap button: play sound1 | Double tap button: play sound2")
    print("Press Ctrl+C to exit...")
    
    # Keep the program running so the image stays on screen
    try:
        while True:
            # Check if the sound has finished playing and update the 'playing' flag
            if playing and not pygame.mixer.get_busy():
                playing = False
            
            # Handle delayed single tap detection
            if pending_single_tap and last_button_press_time > 0:
                time_since_press = time.time() - last_button_press_time
                if time_since_press >= double_tap_threshold:
                    # No second press came within the threshold, so this was a single tap
                    print("Single tap detected!")
                    play_sound(sound1, "sound1")
                    pending_single_tap = False
                    last_button_press_time = 0  # Reset for next detection cycle
            
            time.sleep(0.05)  # Check more frequently for better double-tap detection
    except KeyboardInterrupt:
        print("\nExiting...")
        
except Exception as e:
    print(f"Error loading or displaying image: {e}")
    board.cleanup()
    pygame.mixer.quit()
    sys.exit(1)

finally:
    board.cleanup()
    pygame.mixer.quit()  # Quit the mixer

