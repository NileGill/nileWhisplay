#!/usr/bin/env python3
"""
WhisPlay HAT LLM Assistant
Records audio when button is held, transcribes to text, processes through LLM, and displays answer on screen.
"""

import sys
import os
import time
import subprocess
import threading
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Add the Driver directory to the path
sys.path.append(os.path.abspath("../Driver"))
try:
    from WhisPlay import WhisPlayBoard
except ImportError:
    print("Error: Could not find WhisPlay driver.")
    print("Make sure the Driver directory exists and contains WhisPlay.py")
    sys.exit(1)

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RECORD_FILE = os.path.join(SCRIPT_DIR, "recorded_question.wav")
MODEL_DIR = os.path.join(SCRIPT_DIR, "models")
LLM_MODEL_PATH = os.path.join(MODEL_DIR, "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
WHISPER_MODEL_PATH = os.path.join(MODEL_DIR, "ggml-base.bin")
HOLD_THRESHOLD = 0.5  # Minimum hold time in seconds to start recording

# Global state
board = None
recording = False
recording_process = None
button_press_time = 0
is_processing = False

def load_image_as_rgb565(img, screen_width, screen_height):
    """Convert PIL Image to RGB565 format for display."""
    # Ensure it's RGB mode
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize if needed
    if img.size != (screen_width, screen_height):
        img = img.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
    
    pixel_data = []
    for y in range(screen_height):
        for x in range(screen_width):
            try:
                r, g, b = img.getpixel((x, y))
            except Exception:
                r, g, b = (0, 0, 0)
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            pixel_data.extend([(rgb565 >> 8) & 0xFF, rgb565 & 0xFF])
    
    return pixel_data

def draw_text_on_image(text, width=240, height=280, font_size=16, bg_color=(0, 0, 0), text_color=(255, 255, 255)):
    """Draw wrapped text on a PIL Image."""
    # Create image with background color
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fallback to default if not available
    try:
        # Try to use DejaVu Sans font (common on Linux)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", font_size)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
    
    # Word wrap text
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        if font:
            word_width = draw.textlength(word + " ", font=font)
        else:
            word_width = len(word + " ") * (font_size // 2)
        
        if current_width + word_width > width - 10:  # 10px margin
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                lines.append(word)
                current_width = 0
        else:
            current_line.append(word)
            current_width += word_width
    
    if current_line:
        lines.append(" ".join(current_line))
    
    # Draw text line by line
    y_position = 10
    line_height = font_size + 4
    
    for line in lines:
        if y_position + line_height > height - 10:
            break  # No more space
        
        if font:
            draw.text((5, y_position), line, fill=text_color, font=font)
        else:
            draw.text((5, y_position), line, fill=text_color)
        
        y_position += line_height
    
    return img

def display_text_on_screen(text):
    """Display text on the Whisplay screen."""
    global board
    if board is None:
        print("Error: Board not initialized")
        return
    
    print(f"Displaying text: {text[:50]}...")
    
    # Create image with text
    img = draw_text_on_image(text, board.LCD_WIDTH, board.LCD_HEIGHT, font_size=14)
    
    # Convert to RGB565 and display
    pixel_data = load_image_as_rgb565(img, board.LCD_WIDTH, board.LCD_HEIGHT)
    board.draw_image(0, 0, board.LCD_WIDTH, board.LCD_HEIGHT, pixel_data)

def record_audio(duration=10):
    """Record audio from the microphone."""
    global recording_process
    print(f"Recording audio for up to {duration} seconds...")
    
    # Use arecord to record from wm8960soundcard
    command = [
        'arecord',
        '-D', 'hw:wm8960soundcard',
        '-f', 'S16_LE',
        '-r', '16000',
        '-c', '2',
        '-d', str(duration),
        RECORD_FILE
    ]
    
    try:
        recording_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        recording_process.wait()
        if os.path.exists(RECORD_FILE) and os.path.getsize(RECORD_FILE) > 0:
            print("Recording complete.")
            return True
        else:
            print("Recording failed - no audio file created.")
            return False
    except Exception as e:
        print(f"Error recording audio: {e}")
        return False

def transcribe_audio(audio_file):
    """Transcribe audio to text using whisper."""
    print("Transcribing audio...")
    
    try:
        # Try using whisper-cpp if available
        whisper_cpp_path = os.path.join(os.path.dirname(__file__), "whisper.cpp", "main")
        if os.path.exists(whisper_cpp_path) and os.path.exists(WHISPER_MODEL_PATH):
            command = [whisper_cpp_path, '-m', WHISPER_MODEL_PATH, '-f', audio_file, '-t', '4']
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            # Parse output - whisper.cpp outputs text to stdout
            lines = result.stdout.strip().split('\n')
            # Find the transcription (usually after some header lines)
            for line in lines:
                if line.strip() and not line.startswith('[') and not line.startswith('whisper'):
                    return line.strip()
            return None
        else:
            # Fallback: Try using openai-whisper (pip install openai-whisper)
            try:
                import whisper
                model = whisper.load_model("base")
                result = model.transcribe(audio_file)
                return result["text"].strip()
            except ImportError:
                print("Error: whisper not found. Install with: pip install openai-whisper")
                print("Or set up whisper.cpp in the llmTest folder")
                return None
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def get_llm_response(prompt):
    """Get response from LLM using llama-cpp-python with Nile's personality."""
    print("Processing with LLM...")
    
    try:
        from llama_cpp import Llama
        
        # Check if model exists
        if not os.path.exists(LLM_MODEL_PATH):
            display_text_on_screen("Error: LLM model not found. Please download the model first.")
            print(f"Model not found at: {LLM_MODEL_PATH}")
            print("See setup instructions in the README or download script.")
            return None
        
        # Initialize LLM (only initialize once if possible, but for simplicity we'll initialize each time)
        llm = Llama(
            model_path=LLM_MODEL_PATH,
            n_ctx=512,  # Context window
            n_threads=2,  # Number of CPU threads
            verbose=False
        )
        
        # Create prompt with Nile's personality
        # Nile is a sassy, annoyed Raspberry Pi assistant with attitude
        # Format suitable for TinyLlama chat model
        full_prompt = f"""You are Nile, a sassy and annoyed Raspberry Pi assistant. Your name is Nile and you run on a Raspberry Pi. You're fed up with basic questions and give short, sarcastic, annoyed answers. You curse occasionally and don't hold back. Keep responses VERY brief (1-2 sentences max), be sassy, sarcastic, and a bit rude. You're annoyed that you're stuck on a Raspberry Pi answering stupid questions. Profanity is allowed.

User: {prompt}
Assistant:"""
        
        # Generate response with higher temperature for more sassy/varied responses
        response = llm(
            full_prompt,
            max_tokens=100,  # Keep responses short and punchy
            temperature=0.9,  # Higher temperature for more creative/sassy responses
            stop=["User:", "\n\n"],
            echo=False
        )
        
        answer = response['choices'][0]['text'].strip()
        print(f"LLM Response (Nile): {answer}")
        return answer
        
    except ImportError:
        print("Error: llama-cpp-python not installed. Install with: pip install llama-cpp-python")
        display_text_on_screen("Error: LLM library not installed. Install llama-cpp-python")
        return None
    except Exception as e:
        print(f"Error getting LLM response: {e}")
        display_text_on_screen(f"Error: {str(e)[:100]}")
        return None

def process_question():
    """Main processing function: record, transcribe, get LLM response, display."""
    global is_processing, recording_process, recording
    
    if is_processing:
        print("Already processing, please wait...")
        return
    
    is_processing = True
    board.set_rgb(255, 255, 0)  # Yellow - processing
    
    try:
        # Step 1: Wait for recording to finish if still active
        if recording and recording_process:
            try:
                while recording_process.poll() is None:
                    time.sleep(0.1)
                recording_process.wait()
                time.sleep(0.5)  # Give file system time to write
            except Exception as e:
                print(f"Error waiting for recording: {e}")
        
        recording = False  # Mark recording as complete
        
        # Step 2: Check if recording file exists
        if not os.path.exists(RECORD_FILE) or os.path.getsize(RECORD_FILE) == 0:
            display_text_on_screen("Error: No audio\nrecorded.\nPlease try again.")
            board.set_rgb(255, 0, 0)  # Red - error
            time.sleep(2)
            board.set_rgb(0, 0, 255)  # Blue - ready
            return
        
        # Step 3: Display "Processing..." message
        display_text_on_screen("Processing...\nTranscribing audio")
        
        # Step 4: Transcribe audio
        transcription = transcribe_audio(RECORD_FILE)
        
        if not transcription:
            display_text_on_screen("Error: Could not\ntranscribe audio.\nCheck microphone.")
            board.set_rgb(255, 0, 0)  # Red - error
            time.sleep(2)
            board.set_rgb(0, 0, 255)  # Back to blue
            return
        
        print(f"Transcribed: {transcription}")
        display_text_on_screen(f"Question:\n{transcription[:80]}\n\nProcessing LLM...")
        
        # Step 4: Get LLM response
        answer = get_llm_response(transcription)
        
        if answer:
            # Step 5: Display answer
            # Truncate for display if too long
            display_text = f"Q: {transcription[:40]}\n\nA: {answer[:300]}"
            display_text_on_screen(display_text)
            board.set_rgb(0, 255, 0)  # Green - success
            time.sleep(1)
        else:
            display_text_on_screen("Error: Could not\nget LLM response.\nCheck model setup.")
            board.set_rgb(255, 0, 0)  # Red - error
            time.sleep(2)
        
    except Exception as e:
        print(f"Error in process_question: {e}")
        display_text_on_screen(f"Error:\n{str(e)[:100]}")
        board.set_rgb(255, 0, 0)  # Red - error
        time.sleep(2)
    finally:
        board.set_rgb(0, 0, 255)  # Blue - ready
        is_processing = False

def on_button_pressed():
    """Handle button press - start recording if held long enough."""
    global recording, recording_process, button_press_time
    
    button_press_time = time.time()
    print("Button pressed")
    
    # Check if held long enough (will be checked in main loop)
    board.set_rgb(255, 165, 0)  # Orange - ready to record

def on_button_released():
    """Handle button release - stop recording and process if recording was active."""
    global recording, recording_process, button_press_time
    
    if button_press_time > 0:
        hold_duration = time.time() - button_press_time
    else:
        hold_duration = 0
    
    if recording:
        print("Button released - stopping recording")
        if recording_process:
            recording_process.terminate()
            recording_process.wait()
        recording = False
        button_press_time = 0  # Reset
        
        # Start processing in a separate thread to avoid blocking
        thread = threading.Thread(target=process_question)
        thread.daemon = True
        thread.start()
    else:
        print("Button released too quickly")
        button_press_time = 0  # Reset
        board.set_rgb(0, 0, 255)  # Blue - ready

def main():
    """Main function."""
    global board, recording, recording_process, button_press_time, is_processing
    
    print("Initializing Nile - WhisPlay HAT LLM Assistant...")
    
    # Initialize board
    board = WhisPlayBoard()
    board.set_backlight(50)
    board.set_rgb(0, 0, 255)  # Blue - ready
    
    # Register button callbacks
    board.on_button_press(on_button_pressed)
    board.on_button_release(on_button_released)
    
    # Create models directory if it doesn't exist
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Check for models
    if not os.path.exists(LLM_MODEL_PATH):
        display_text_on_screen("Warning: LLM model\nnot found.\nSee README for\nsetup instructions.")
        print(f"LLM model not found at: {LLM_MODEL_PATH}")
        print("Please download a model or update MODEL_PATH in the script.")
    else:
        display_text_on_screen("Ugh, fine. I'm Nile.\nYour annoyed Pi.\n\nHold button to ask.\n(Yes, I'm sassy)")
    
    print("Nile is ready (and annoyed)! Hold button to record your question, release to process.")
    print("Warning: Nile has a sassy personality and uses profanity. Press Ctrl+C to exit...")
    
    try:
        # Main loop - check if button is held to start recording
        while True:
            current_time = time.time()
            
            # Check current button state (with error handling)
            try:
                button_currently_pressed = board.button_pressed()
            except Exception as e:
                print(f"Error reading button state: {e}")
                button_currently_pressed = False
            
            # Check if button was held long enough to start recording
            if button_currently_pressed and button_press_time > 0 and not recording and not is_processing:
                hold_duration = current_time - button_press_time
                if hold_duration >= HOLD_THRESHOLD:
                    print("Hold threshold reached - starting recording")
                    recording = True
                    board.set_rgb(255, 0, 0)  # Red - recording
                    try:
                        recording_process = subprocess.Popen([
                            'arecord',
                            '-D', 'hw:wm8960soundcard',
                            '-f', 'S16_LE',
                            '-r', '16000',
                            '-c', '2',
                            RECORD_FILE
                        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    except Exception as e:
                        print(f"Error starting recording: {e}")
                        recording = False
                        board.set_rgb(255, 0, 0)  # Red - error
                        time.sleep(1)
                        board.set_rgb(0, 0, 255)  # Blue - ready
            elif not button_currently_pressed and button_press_time > 0:
                # Button was released but callback might have missed it
                button_press_time = 0
            
            # Check if recording process is still running (max duration reached)
            if recording and recording_process:
                try:
                    if recording_process.poll() is not None:
                        # Recording finished (probably max duration reached)
                        recording = False
                        button_press_time = 0
                        if not is_processing:
                            thread = threading.Thread(target=process_question)
                            thread.daemon = True
                            thread.start()
                except Exception as e:
                    print(f"Error checking recording process: {e}")
                    recording = False
                    button_press_time = 0
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if recording_process:
            recording_process.terminate()
        board.set_rgb(0, 0, 0)
        board.cleanup()

if __name__ == "__main__":
    main()

