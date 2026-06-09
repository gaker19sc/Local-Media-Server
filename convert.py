import os
import subprocess
import tempfile
import shutil
import json

def get_english_audio_index(filepath):
    """using ffprobe to find the best audio track"""
    cmd = [
        'ffprobe', '-v', 'quiet', 
        '-print_format', 'json', '-show_streams', 
        filepath
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        
        audio_streams = []
        for index, stream in enumerate(info.get('streams', [])):
            if stream.get('codec_type') == 'audio':
                audio_streams.append({
                    'absolute_index': index,
                    'relative_index': len(audio_streams),
                    'lang': stream.get('tags', {}).get('language', 'und').lower()
                })
        
        if not audio_streams:
            return None, False

        for stream in audio_streams:
            if stream['lang'] in ['eng', 'en']:
                print(f"English audio track found at index {stream['relative_index']}")
                return stream['relative_index'], True
        
        print("No English audio track found, using default track")
        return 0, False

    except Exception:
        return 0, False

def process_video():
    print("== Media Converter ==")
    file_input = input("Enter your video path or drag and drop it here and press enter: ").strip()
    
    filepath = file_input.strip('"').strip("'")

    if not os.path.exists(filepath):
        print(f"Error: Could't find file")
        return

    abs_source = os.path.abspath(filepath)
    source_dir = os.path.dirname(abs_source)
    base_name = os.path.basename(abs_source)
    name, ext = os.path.splitext(base_name)
    
    final_output_path = os.path.join(source_dir, f"{name}.mp4")
    
    temp_dir = tempfile.gettempdir()
    temp_output_path = os.path.join(temp_dir, f"Processing_{name}.mp4")

    audio_index, eng_found = get_english_audio_index(abs_source)

    print(f"Started processing...")
    print("Copying video track")
    if audio_index is not None:
        print("Removing other audio tracks")
        print("Encoding audio to AAC Stereo (192k), this might take a while")
    else:
        print("No audio found, copying video only")

    cmd = [
        'ffmpeg', '-y',
        '-i', abs_source,
        '-c:v', 'copy',
    ]

    if audio_index is not None:
        cmd += [
            '-map', '0:v:0',                      
            '-map', f'0:a:{audio_index}',         
            '-c:a', 'aac',                        
            '-ac', '2',                          
            '-b:a', '192k'                       
        ]
    else:
        cmd += [
            '-map', '0:v:0'                       
        ]

    cmd += ['-loglevel', 'error']
    cmd.append(temp_output_path)

    try:
        subprocess.run(cmd, check=True)
        
        if os.path.exists(temp_output_path):
            print("Copying file back to original path")
            
            if abs_source == final_output_path and os.path.exists(abs_source):
                os.remove(abs_source)
                
            shutil.move(temp_output_path, final_output_path)
            
            if ext.lower() == '.mkv' and os.path.exists(abs_source):
                os.remove(abs_source)
                print(f"deleted old mkv")

            print(f"Success! Your file '{os.path.basename(final_output_path)}' is browser compatible")
        else:
            print("Error: The file wasn't created")
            
    except subprocess.CalledProcessError:
        print("FFmpeg error: couldn't convert")
    except Exception as e:
        print(f"error: {e}")
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

if __name__ == "__main__":
    process_video()