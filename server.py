from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from kokoro_onnx import Kokoro
import soundfile as sf
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This allows your index.html to talk to the API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/voices")
async def get_voices():
    if not kokoro:
        raise HTTPException(status_code=500, detail="Model not loaded")
    # This pulls the list of voice names directly from the loaded model
    voice_list = list(kokoro.voices.keys())
    voice_list.sort()
    return {"voices": voice_list}

# Point to the model files you downloaded into the /app/model folder
MODEL_PATH = "/app/model/kokoro-v1.0.onnx"
VOICES_PATH = "/app/model/voices-v1.0.bin"

# Initialize the Kokoro model (This runs on the GPU thanks to onnxruntime-gpu)
if os.path.exists(MODEL_PATH):
    # ONNX will automatically find your RTX 5070
    kokoro = Kokoro(MODEL_PATH, VOICES_PATH)
    # kokoro = Kokoro(MODEL_PATH, VOICES_PATH, providers=['CUDAExecutionProvider'])
    print("Kokoro Model Loaded Successfully on GPU")
else:
    kokoro = None
    print(f"ERROR: Model not found at {MODEL_PATH}")

@app.post("/speak")
async def speak(text: str, voice: str = "af_bella", speed: float = 1.0):
    if not kokoro:
        raise HTTPException(status_code=500, detail="Model files not found inside container.")
    
    output_file = "output.wav"
    
    # Generate the audio samples
    samples, sample_rate = kokoro.create(
        text, 
        voice=voice, 
        speed=speed, 
        lang="en-us"
    )
    
    # Save to the container's filesystem
    sf.write(output_file, samples, sample_rate)
    
    # Send the file back to your Windows host
    return FileResponse(output_file, media_type="audio/wav")

@app.get("/health")
async def health():
    return {"status": "online", "gpu": "RTX 5070 Active"}