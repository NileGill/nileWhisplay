from PIL import Image
import sys
import os

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

# Load and display the image
try:
    print(f"Loading image: {os.path.basename(image_path)}")
    image_data = load_image_as_rgb565(image_path, board.LCD_WIDTH, board.LCD_HEIGHT)
    board.draw_image(0, 0, board.LCD_WIDTH, board.LCD_HEIGHT, image_data)
    print(f"Image displayed successfully on the screen!")
    print("Press Ctrl+C to exit...")
    
    # Keep the program running so the image stays on screen
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
        
except Exception as e:
    print(f"Error loading or displaying image: {e}")
    board.cleanup()
    sys.exit(1)

finally:
    board.cleanup()

