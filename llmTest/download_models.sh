#!/bin/bash
# Script to download LLM and Whisper models for the WhisPlay HAT LLM Assistant

MODEL_DIR="models"
mkdir -p "$MODEL_DIR"

echo "Downloading models for WhisPlay HAT LLM Assistant..."
echo "This may take a while depending on your internet connection."
echo ""

# Download TinyLlama model (small LLM for Raspberry Pi)
echo "Downloading TinyLlama LLM model..."
TINYLLAMA_URL="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
TINYLLAMA_FILE="$MODEL_DIR/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

if [ ! -f "$TINYLLAMA_FILE" ]; then
    echo "Downloading TinyLlama model (this is a ~750MB file)..."
    wget -O "$TINYLLAMA_FILE" "$TINYLLAMA_URL" || curl -L -o "$TINYLLAMA_FILE" "$TINYLLAMA_URL"
    if [ $? -eq 0 ]; then
        echo "TinyLlama model downloaded successfully!"
    else
        echo "Error downloading TinyLlama model. You may need to download it manually."
        echo "Visit: https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
    fi
else
    echo "TinyLlama model already exists, skipping download."
fi

echo ""

# Download Whisper base model
echo "Downloading Whisper base model for speech-to-text..."
WHISPER_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
WHISPER_FILE="$MODEL_DIR/ggml-base.bin"

if [ ! -f "$WHISPER_FILE" ]; then
    echo "Downloading Whisper base model (this is a ~150MB file)..."
    wget -O "$WHISPER_FILE" "$WHISPER_URL" || curl -L -o "$WHISPER_FILE" "$WHISPER_URL"
    if [ $? -eq 0 ]; then
        echo "Whisper model downloaded successfully!"
    else
        echo "Error downloading Whisper model. You may need to download it manually."
        echo "Visit: https://huggingface.co/ggerganov/whisper.cpp"
        echo ""
        echo "Alternative: Install openai-whisper with: pip install openai-whisper"
        echo "This will download models automatically when first used."
    fi
else
    echo "Whisper model already exists, skipping download."
fi

echo ""
echo "Model download complete!"
echo ""
echo "Next steps:"
echo "1. Install Python dependencies: pip install -r requirements.txt"
echo "2. If using whisper.cpp, build it: git clone https://github.com/ggerganov/whisper.cpp && cd whisper.cpp && make"
echo "3. Or install openai-whisper: pip install openai-whisper"
echo "4. Run the script: sudo python3 llmPy.py"

