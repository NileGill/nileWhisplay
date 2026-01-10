# Quick Setup Guide

## Step 1: Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-pil python3-numpy cmake build-essential
sudo apt-get install -y portaudio19-dev python3-pyaudio wget
```

## Step 2: Install Python Dependencies

```bash
cd llmTest
pip3 install -r requirements.txt
```

If `llama-cpp-python` fails to install, try:
```bash
CMAKE_ARGS="-DLLAMA_BLAS=OFF" pip3 install llama-cpp-python
```

Or with OpenBLAS for better performance:
```bash
sudo apt-get install libopenblas-dev
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip3 install llama-cpp-python
```

## Step 3: Download Models

Run the download script:
```bash
chmod +x download_models.sh
./download_models.sh
```

Or download manually:
```bash
mkdir -p models
cd models

# Download TinyLlama model (~750MB)
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# Download Whisper model (~150MB) - optional if using openai-whisper
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
```

## Step 4: Test Audio

Make sure the WM8960 driver is working:
```bash
# Test playback
aplay -l  # Should show wm8960soundcard

# Test recording
arecord -D hw:wm8960soundcard -f S16_LE -r 16000 -c 2 -d 3 test.wav
aplay -D hw:wm8960soundcard test.wav
```

## Step 5: Run the Script

```bash
sudo python3 llmPy.py
```

## Usage

1. **Hold the button** for at least 0.5 seconds
2. **Speak your question** while holding
3. **Release the button** when done
4. Wait for processing (LED will change colors)
5. **Answer displays on screen**

## Troubleshooting

### "Permission denied" for audio
- Run with `sudo` (required for GPIO and audio)

### Models not found
- Check `models/` directory exists
- Verify filenames match those in `llmPy.py`
- Run download script again

### Slow performance
- Use a Raspberry Pi 4B or better
- Consider using a smaller Whisper model
- Reduce LLM context in the script

### Import errors
- Make sure you're using Python 3.7+
- Reinstall requirements: `pip3 install --upgrade -r requirements.txt`

