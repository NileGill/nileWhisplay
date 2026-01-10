# WhisPlay HAT LLM Assistant

This script allows you to use your WhisPlay HAT as a voice-activated AI assistant. Hold down the button to record your question, release it to process through an LLM, and see the answer displayed on the screen.

## Features

- **Voice Input**: Hold the button to record your question
- **Speech-to-Text**: Automatically transcribes your audio to text
- **LLM Processing**: Processes your question through a local LLM (runs offline)
- **Screen Display**: Shows the question and answer on the WhisPlay HAT screen
- **Visual Feedback**: RGB LED changes color based on status:
  - Blue: Ready
  - Orange: Button pressed (waiting for hold)
  - Red: Recording
  - Yellow: Processing
  - Green: Success

## Requirements

### Hardware
- Raspberry Pi (3B+, 4B, or Zero 2 W recommended for better performance)
- WhisPlay HAT with microphone and speaker
- WM8960 audio driver installed (see main project README)

### Software Dependencies

1. **Python 3.7+**
2. **System packages**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-pil python3-numpy cmake build-essential
   sudo apt-get install -y portaudio19-dev python3-pyaudio
   ```

3. **Python packages** (install with pip):
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Models**:
   - LLM Model: TinyLlama (~750MB) - automatically downloaded or download manually
   - Whisper Model: Base model (~150MB) - automatically downloaded or use openai-whisper

## Setup

### Quick Setup (Automated)

1. **Download models**:
   ```bash
   cd llmTest
   chmod +x download_models.sh
   ./download_models.sh
   ```

2. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Build llama-cpp-python** (if needed):
   ```bash
   # For Raspberry Pi with limited memory, use:
   CMAKE_ARGS="-DLLAMA_BLAS=OFF" pip3 install llama-cpp-python
   
   # For faster performance (if OpenBLAS is available):
   sudo apt-get install libopenblas-dev
   CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip3 install llama-cpp-python
   ```

### Manual Setup

#### Download LLM Model

The script uses TinyLlama 1.1B Q4_K_M quantized model. Download it:

```bash
cd llmTest/models
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

Or visit: https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF

#### Speech-to-Text Options

**Option 1: OpenAI Whisper (Recommended for ease of use)**
```bash
pip3 install openai-whisper
```
This will automatically download models when first used.

**Option 2: whisper.cpp (Faster, lighter)**
```bash
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
cd ..
ln -s whisper.cpp/models models/whisper
# Download base model
cd models
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
```

## Usage

1. **Run the script**:
   ```bash
   cd llmTest
   sudo python3 llmPy.py
   ```

2. **Use the assistant**:
   - **Hold the button** for at least 0.5 seconds to start recording
   - **Speak your question** while holding the button
   - **Release the button** when done speaking (or wait for max recording time)
   - The system will:
     1. Transcribe your audio to text
     2. Process it through the LLM
     3. Display the question and answer on the screen

3. **Exit**: Press Ctrl+C

## Configuration

You can modify these settings in `llmPy.py`:

- `HOLD_THRESHOLD = 0.5`: Minimum hold time to start recording (seconds)
- `LLM_MODEL_PATH`: Path to the LLM model file
- `WHISPER_MODEL_PATH`: Path to the Whisper model file
- Recording duration: Maximum recording time (set in arecord command, default: unlimited until release)

## Troubleshooting

### "Model not found" error
- Check that the model files are in the `models/` directory
- Verify the file names match the paths in the script
- Re-run the download script or download manually

### "llama-cpp-python not installed"
```bash
pip3 install llama-cpp-python
# Or with BLAS support:
CMAKE_ARGS="-DLLAMA_BLAS=ON" pip3 install llama-cpp-python
```

### "whisper not found"
```bash
pip3 install openai-whisper
```

### Audio recording not working
- Check that WM8960 driver is installed: `aplay -l` should show wm8960soundcard
- Test microphone: `arecord -D hw:wm8960soundcard -f S16_LE -r 16000 -c 2 test.wav`
- Check permissions (may need sudo)

### Performance issues
- Use a Raspberry Pi 4B or better for best performance
- Consider using a smaller Whisper model (tiny, base instead of small/medium)
- Reduce LLM context window in the script (`n_ctx` parameter)

### Screen display issues
- Make sure the WhisPlay driver is installed correctly
- Check that the image conversion is working (try with a simple test image first)

## Model Alternatives

If TinyLlama is too slow or you want different capabilities:

- **Phi-2** (2.7B, more capable): https://huggingface.co/microsoft/phi-2
- **Qwen-1.8B** (good quality/speed balance): https://huggingface.co/Qwen/Qwen-1.8B
- **StableLM-Zephyr** (3B, good chat model): Various GGUF versions available

Download GGUF quantized versions (Q4_K_M or Q5_K_M) for Raspberry Pi compatibility.

## License

See the main project license.

