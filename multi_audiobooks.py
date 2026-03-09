import os
import argparse
import glob
import shutil
from gen_audiobook import generate_audiobook

def process_folder(input_dir, output_dir, voice="af_bella", speed=1.0, output_chunks_dir="audio_chunks", silence=200, delay=0.0):
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Find all text files
    text_files = glob.glob(os.path.join(input_dir, "*.txt"))
    
    if not text_files:
        print(f"No text files found in {input_dir}")
        return

    print(f"Found {len(text_files)} text files in {input_dir}")

    for i, text_file_path in enumerate(text_files):
        print(f"\n[{i+1}/{len(text_files)}] Processing: {text_file_path}")
        
        # Determine output filename
        base_name = os.path.splitext(os.path.basename(text_file_path))[0]
        output_wav_path = os.path.join(output_dir, base_name + ".wav")
        # Use a consistent temporary directory for chunks or a subdirectory per file
        # Using a subdir per file is safer to avoid mix-ups if a run is aborted and restarted
        file_chunks_dir = os.path.join(output_chunks_dir, base_name)
        
        if not os.path.exists(file_chunks_dir):
            os.makedirs(file_chunks_dir)
        
        mp3_file = generate_audiobook(
            text_file_path, 
            voice=voice, 
            speed=speed, 
            output_dir=file_chunks_dir, 
            silence=silence, 
            delay=delay,
            output_file=output_wav_path
        )
        
        if mp3_file:
            print(f"Finished: {mp3_file}")
            
            # Cleanup temporary chunks
            print(f"Cleaning up temporary files in {file_chunks_dir}...")
            shutil.rmtree(file_chunks_dir)
        else:
            print(f"No audio generated for {text_file_path}")

def main():
    parser = argparse.ArgumentParser(description="Batch convert text files to audiobooks.")
    parser.add_argument("input_dir", help="Directory containing input text files")
    parser.add_argument("output_dir", help="Directory to save output WAV files")
    parser.add_argument("--voice", default="af_bella", help="Voice to use (default: af_bella)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed of speech (default: 1.0)")
    parser.add_argument("--chunks_dir", default="temp_chunks", help="Directory for temporary audio chunks")
    parser.add_argument("--silence", type=int, default=300, help="Silence between chunks in ms (default: 300)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between requests in seconds")

    args = parser.parse_args()
    
    process_folder(
        args.input_dir, 
        args.output_dir, 
        voice=args.voice, 
        speed=args.speed, 
        output_chunks_dir=args.chunks_dir,
        silence=args.silence,
        delay=args.delay
    )

if __name__ == "__main__":
    main()
