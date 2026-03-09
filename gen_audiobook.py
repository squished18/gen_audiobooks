import os
import re
import argparse
import time
import requests
import wave
import subprocess

def get_paragraphs(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split by one or more empty lines
    # This regex handles \n\n, \r\n\r\n, and even triple newlines
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Clean up: remove leading/trailing whitespace and filter out empty strings
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    return paragraphs

def generate_tts_for_paragraph(text, voice="af_bella", speed=1.0, output_dir="temp_chunks", index=0):
    """
    Sends a single paragraph to the Kokoro FastAPI server and saves the WAV file.
    """
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Your FastAPI endpoint (assuming it's running on localhost:8000)
    url = "http://localhost:8880/speak"
    
    # The 'text' is sent as a query parameter based on your FastAPI @app.post("/speak")
    params = {
        "text": text,
        "voice": voice,
        "speed": speed
    }

    try:
        # We use a POST request as defined in your server.py
        response = requests.post(url, params=params, timeout=60)
        
        if response.status_code == 200:
            # Generate a padded filename to keep them in order (e.g., chunk_0001.wav)
            file_path = os.path.join(output_dir, f"chunk_{index:04d}.wav")
            
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            print(f"Successfully generated: {file_path}")
            return file_path
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return None

def stitch_wav_files(wav_files, output_path, silence_ms=0):
    if not wav_files:
        print("No WAV files to stitch.")
        return

    # Sort files to ensure correct order (optional if list is already ordered)
    wav_files.sort()

    # Get parameters from the first file
    with wave.open(wav_files[0], 'rb') as first_wav:
        params = first_wav.getparams()
        # We need to set nframes to 0 because we don't know the total yet.
        # wave module will update it when we close the file.
        params = list(params)
        params[3] = 0 
        params = tuple(params)
        
        # Calculate silence frames
        # usage: silence_frames = (framerate * silence_ms) / 1000
        framerate = params[2]
        sampwidth = params[1]
        nchannels = params[0]
        silence_frames_count = int((framerate * silence_ms) / 1000)
        silence_data = (b'\x00' * sampwidth * nchannels) * silence_frames_count
    
    with wave.open(output_path, 'wb') as output_wav:
        output_wav.setparams(params)
        
        for i, wav_file in enumerate(wav_files):
            with wave.open(wav_file, 'rb') as input_wav:
                # Check for matching parameters (channels, width, rate)
                if input_wav.getparams()[0:3] != params[0:3]:
                     print(f"Warning: {wav_file} has different parameters which might cause issues. Skipping.")
                     continue
                output_wav.writeframes(input_wav.readframes(input_wav.getnframes()))
            
            # Add silence between files, but not after the last one
            if i < len(wav_files) - 1 and silence_ms > 0:
                output_wav.writeframes(silence_data)

    print(f"Successfully stitched {len(wav_files)} files into {output_path}")

def convert_wav_to_mp3(wav_filename, mp3_filename):
    print(f"Converting {wav_filename} to MP3...")
    try:
        subprocess.run(["ffmpeg", "-y", "-i", wav_filename, mp3_filename], check=True)
        print(f"Successfully converted to MP3: {mp3_filename}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting to MP3: {e}")
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please ensure ffmpeg is installed and in your PATH.")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate audiobook from text file using Kokoro TTS Server.")
    parser.add_argument("text_file_path", help="Path to the input text file")
    parser.add_argument("--voice", default="af_bella", help="Voice to use (default: af_bella)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed of speech (default: 1.0)")
    parser.add_argument("--output_dir", default="audio_chunks", help="Directory to save audio chunks")
    parser.add_argument("--silence", type=int, default=200, help="Silence between chunks in milliseconds (default: 300)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay in seconds between processing chunks (default: 0.0)")
    return parser.parse_args()

def generate_audio_chunks(paragraphs, voice, speed, output_dir, delay):
    generated_files = []
    print(f"Found {len(paragraphs)} paragraphs. Generating audio...")
    
    for i, paragraph in enumerate(paragraphs):
        if i > 0 and delay > 0:
            print(f"Cooling down for {delay} seconds...")
            time.sleep(delay)

        print(f"Processing paragraph {i+1}/{len(paragraphs)}...")
        # Skip empty paragraphs just in case
        if not paragraph.strip():
            continue
            
        file_path = generate_tts_for_paragraph(
            text=paragraph, 
            voice=voice, 
            speed=speed, 
            output_dir=output_dir, 
            index=i+1
        )
        
        if file_path:
            generated_files.append(file_path)
    
    return generated_files

def generate_audiobook(text_file_path, voice="af_bella", speed=1.0, output_dir="audio_chunks", silence=200, delay=0.0, output_file=None):
    paragraphs = get_paragraphs(text_file_path)
    
    generated_files = generate_audio_chunks(paragraphs, voice, speed, output_dir, delay)
            
    if generated_files:
        # Create output filename based on input text filename
        if output_file:
             output_filename = output_file
        else:
             output_filename = os.path.splitext(os.path.basename(text_file_path))[0] + ".wav"
             
        stitch_wav_files(generated_files, output_filename, silence_ms=silence)
        print(f"Audiobook saved to: {output_filename}")

        # Convert to MP3
        mp3_filename = output_filename.replace(".wav", ".mp3")
        convert_wav_to_mp3(output_filename, mp3_filename)
        return mp3_filename
    else:
        print("No audio files generated.")
        return None

def main():
    args = parse_arguments()
    generate_audiobook(args.text_file_path, args.voice, args.speed, args.output_dir, args.silence, args.delay)
    print("Done!")

if __name__ == "__main__":
    main()