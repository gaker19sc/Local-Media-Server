import os
import sys
import subprocess
import json
import tempfile
import time
import shutil
import re
import urllib.request
import urllib.parse

MOVIE_DIR = "./Movies"
CONFIG_FILE = "config.json"
METADATA_DIR = "./metadata"
OUTPUT_JS = "./movies.js"

ALLOWED_VIDEO_CODECS = ['h264', 'vp8', 'vp9', 'av1']
ALLOWED_AUDIO_CODECS = ['aac', 'mp3', 'opus', 'vorbis', 'flac']
ALLOWED_EXTENSIONS = ['.mp4', '.webm', '.ogg']

def print_step(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

# ==========================================
# FFPROBE & CONVERSION FUNCTIONS
# ==========================================

def get_video_info(filepath):
    """Using ffprobe"""
    cmd = [
        'ffprobe', 
        '-v', 'quiet', \
        '-print_format', 'json', \
        '-show_streams', \
        '-show_format', \
        filepath
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception:
        return None

def get_user_audio_choice(filepath):
    """Lists all available audio tracks and lets the user choose if multiple exist."""
    info = get_video_info(filepath)
    if not info:
        return 0
    
    audio_streams = []
    for index, stream in enumerate(info.get('streams', [])):
        if stream.get('codec_type') == 'audio':
            lang = stream.get('tags', {}).get('language', 'und').upper()
            title = stream.get('tags', {}).get('title', 'No Title')
            codec = stream.get('codec_name', 'unknown')
            audio_streams.append({
                'absolute_index': index,
                'relative_index': len(audio_streams),
                'lang': lang,
                'title': title,
                'codec': codec
            })
    
    if not audio_streams:
        return None
    if len(audio_streams) == 1:
        return audio_streams[0]['absolute_index']
    print(f"\n[?] Multiple audio tracks detected for '{os.path.basename(filepath)}':")
    for s in audio_streams:
        print(f"    [{s['relative_index']}] Language: {s['lang']} | Codec: {s['codec']} | Title: {s['title']}")
    
    while True:
        try:
            choice = input("    Which audio track would you like to keep? (Enter index number): ").strip()
            choice_idx = int(choice)
            if 0 <= choice_idx < len(audio_streams):
                return audio_streams[choice_idx]['absolute_index']
            print(f"    Invalid index. Please choose a number between 0 and {len(audio_streams)-1}.")
        except ValueError:
            print("    Please enter a valid number.")

def check_encoder_available(encoder_name):
    """Checks for ffmpeg compatibility"""
    try:
        result = subprocess.run(['ffmpeg', '-h', f'encoder={encoder_name}'], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
        return result.returncode == 0
    except Exception:
        return False

def get_best_video_encoder():
    """Checks for hardware acceleration"""
    print("Checking hardware acceleration...")
    
    if check_encoder_available('h264_nvenc'):
        print("   NVIDIA GPU detected (h264_nvenc). Using hardware encoding")
        return 'h264_nvenc'
        
    if check_encoder_available('h264_amf'):
        print("   AMD GPU detected (h264_amf). Using hardware encoding")
        return 'h264_amf'
        
    print("   No compatible GPU found. Using CPU encoding (libx264) instead")
    return 'libx264'

def auto_convert_file(filepath):
    """converting the file to work with fast hardware acceleration"""
    abs_source = os.path.abspath(filepath)
    source_dir = os.path.dirname(abs_source)
    base_name = os.path.basename(abs_source)
    name, ext = os.path.splitext(base_name)
    
    final_output_path = os.path.join(source_dir, f"{name}.mp4")
    temp_dir = tempfile.gettempdir()
    temp_output_path = os.path.join(temp_dir, f"Processing_{name}.mp4")
    info = get_video_info(abs_source)
    
    total_duration = 0
    if info and 'format' in info:
        try:
            total_duration = float(info['format'].get('duration', 0))
        except:
            pass
    video_codec_needed = False
    has_video_stream = False
    absolute_audio_index = get_user_audio_choice(abs_source)
    
    if info and 'streams' in info:
        for stream in info['streams']:
            if stream.get('codec_type') == 'video':
                has_video_stream = True
                codec_name = stream.get('codec_name')
                
                if codec_name not in ALLOWED_VIDEO_CODECS or codec_name == 'av1':
                    video_codec_needed = True
            
            if stream.get('codec_type') == 'audio' and absolute_audio_index is None:
                lang = stream.get('tags', {}).get('language', '')
                if lang in ['ger', 'deu', 'eng']:
                    absolute_audio_index = stream.get('index')
        
        if absolute_audio_index is None:
            for stream in info['streams']:
                if stream.get('codec_type') == 'audio':
                    absolute_audio_index = stream.get('index')
                    break
    if not has_video_stream or video_codec_needed:
        encoder = get_best_video_encoder()
        print(f"Converting video track for '{base_name}' ({encoder})...")
        
        if encoder == 'h264_nvenc':
            cmd = ['ffmpeg', '-y', '-i', abs_source, '-c:v', 'h264_nvenc', '-preset', 'fast', '-vf', 'format=yuv420p']
        elif encoder == 'h264_amf':
            cmd = ['ffmpeg', '-y', '-i', abs_source, '-c:v', 'h264_amf', '-vf', 'format=yuv420p']
        else:
            cmd = ['ffmpeg', '-y', '-i', abs_source, '-c:v', 'libx264', '-vf', 'format=yuv420p', '-crf', '22', '-preset', 'medium']
    else:
        print(f"Copying video track for '{base_name}'...")
        cmd = ['ffmpeg', '-y', '-i', abs_source, '-c:v', 'copy']
    if has_video_stream:
        if absolute_audio_index is not None:
            cmd += ['-map', '0:v:0', '-map', f'0:{absolute_audio_index}', '-c:a', 'aac', '-ac', '2', '-b:a', '192k']
        else:
            cmd += ['-map', '0:v:0']
    else:
        cmd += ['-map', '0', '-c:a', 'aac', '-ac', '2', '-b:a', '192k']
    cmd += [temp_output_path]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8')
        
        start_time = time.time()
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if "time=" in line:
                match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.?\d*)", line)
                if match and total_duration > 0:
                    time_str = match.group(1)
                    h, m, s = map(float, time_str.split(':'))
                    current_time = (h * 3600) + (m * 60) + s
                    percent = min(100.0, (current_time / total_duration) * 100.0)
                    elapsed = time.time() - start_time
                    if current_time > 0 and elapsed > 1:
                        eta_seconds = max(0.0, (elapsed / (current_time / total_duration)) - elapsed)
                        eta_str = f"{int(eta_seconds)//60:02d}:{int(eta_seconds)%60:02d}"
                    else:
                        eta_str = "--:--"
                    bar = '█' * int(20 * percent / 100) + '░' * (20 - int(20 * percent / 100))
                    sys.stdout.write(f"\r[{bar}] {percent:.1f}% | ETA: {eta_str} ")
                    sys.stdout.flush()
        rc = process.wait()
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()
        
        if rc != 0:
            raise subprocess.CalledProcessError(rc, cmd)
        if os.path.exists(temp_output_path) and os.path.getsize(temp_output_path) > 10 * 1024 * 1024:
            check_info = get_video_info(temp_output_path)
            has_video_now = False
            if check_info and 'streams' in check_info:
                for stream in check_info['streams']:
                    if stream.get('codec_type') == 'video':
                        has_video_now = True
                        break
            
            if has_video_now:
                if abs_source == final_output_path and os.path.exists(abs_source):
                    os.remove(abs_source)
                shutil.move(temp_output_path, final_output_path)
                if ext.lower() != '.mp4' and os.path.exists(abs_source):
                    os.remove(abs_source)
                print(f"     Fixed compatibility successfully")
                return
        
        print(f"     [WARNING] Track loss caught! Temp file had no video. Original preserved.")
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)
            
    except Exception as e:
        print(f"     Error while converting {base_name}: {e}")
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)


# ==========================================
# METADATA SCRAPER FUNCTIONS (FORMERLY FETCH.PY)
# ==========================================

def clean_filename(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'(1080p|720p|2160p|4k|bluray|x264|x265|h264|h265|web-dl|webrip|dd5\.1).*', '', name, flags=re.IGNORECASE)
    return name.replace('.', ' ').replace('_', ' ').strip()

def fetch_tmdb_metadata(query, api_key):
    if not api_key or api_key == "YOUR_TMDB_API_KEY_HERE":
        return None
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={encoded_query}"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            if data['results']:
                return data['results'][0]
    except Exception as e:
        print(f"Error fetching metadata for {query}: {e}")
    return None

def fetch_movie_logo(movie_id, api_key):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/images?api_key={api_key}&include_image_language=en,de,null"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            logos = data.get('logos', [])
            if logos:
                return logos[0]['file_path']
    except Exception as e:
        print(f"Error fetching logo for ID {movie_id}: {e}")
    return None

def download_image(url, filepath):
    try:
        urllib.request.urlretrieve(url, filepath)
        return True
    except Exception:
        return False

def scrape_metadata(api_key):
    os.makedirs(f"{METADATA_DIR}/posters", exist_ok=True)
    os.makedirs(f"{METADATA_DIR}/backdrops", exist_ok=True)
    os.makedirs(f"{METADATA_DIR}/logos", exist_ok=True)

    movies_list = []
    print("== Metadata Scraper ==")
    
    if not os.path.exists(MOVIE_DIR):
        print(f"Error: {MOVIE_DIR} directory does not exist.")
        return

    for file in os.listdir(MOVIE_DIR):
        if file.lower().endswith(('.mp4', '.mkv')):
            print(f"\nProcessing: {file}")
            clean_name = clean_filename(file)
            
            movie_entry = {
                "title": clean_name,
                "file": f"Movies/{file}",
                "poster": "",
                "backdrop": "",
                "logo": "",
                "description": "No local description available. Update your TMDB API key in setup.py to fetch metadata.",
                "subtitles": {} 
            }
            
            metadata = fetch_tmdb_metadata(clean_name, api_key)
            if metadata:
                movie_id = metadata.get("id")
                movie_entry["title"] = metadata.get("title", clean_name)
                movie_entry["description"] = metadata.get("overview", "")
                
                if metadata.get("poster_path"):
                    poster_url = f"https://image.tmdb.org/t/p/w500{metadata['poster_path']}"
                    poster_path = f"{METADATA_DIR}/posters/{movie_id}.jpg"
                    if download_image(poster_url, poster_path):
                        movie_entry["poster"] = poster_path
                
                if metadata.get("backdrop_path"):
                    backdrop_url = f"https://image.tmdb.org/t/p/w1280{metadata['backdrop_path']}"
                    backdrop_path = f"{METADATA_DIR}/backdrops/{movie_id}.jpg"
                    if download_image(backdrop_url, backdrop_path):
                        movie_entry["backdrop"] = backdrop_path

                logo_path_hd = fetch_movie_logo(movie_id, api_key)
                if logo_path_hd:
                    logo_url = f"https://image.tmdb.org/t/p/w500{logo_path_hd}"
                    local_logo_path = f"{METADATA_DIR}/logos/{movie_id}.png"
                    if download_image(logo_url, local_logo_path):
                        movie_entry["logo"] = local_logo_path

            subtitles_dir = os.path.join(MOVIE_DIR, "Subtitles")
            if not os.path.exists(subtitles_dir):
                subtitles_dir = os.path.join(MOVIE_DIR, "subtitles")

            if os.path.exists(subtitles_dir):
                base_name = os.path.splitext(file)[0]
                base_name_lower = base_name.lower()
                
                for sub_file in os.listdir(subtitles_dir):
                    if sub_file.lower().endswith(('.srt', '.vtt')):
                        if sub_file.lower().startswith(base_name_lower):
                            suffix = sub_file[len(base_name_lower):]
                            match = re.match(r'^_([a-zA-Z]{2})\.(srt|vtt)$', suffix, re.IGNORECASE)
                            
                            if match:
                                lang = match.group(1).lower()
                                sub_path = os.path.join(subtitles_dir, sub_file)
                                try:
                                    try:
                                        with open(sub_path, "r", encoding="utf-8") as sf:
                                            content = sf.read()
                                    except UnicodeDecodeError:
                                        with open(sub_path, "r", encoding="cp1252", errors="ignore") as sf:
                                            content = sf.read()
                                            
                                    movie_entry["subtitles"][lang] = content
                                    print(f"     Embedded subtitles: '{lang}' {sub_file}")
                                except Exception as e:
                                    print(f"     Error reading subtitles for file {sub_file}: {e}")
            
            movies_list.append(movie_entry)

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(f"const movieLibrary = {json.dumps(movies_list, indent=2)};")

    print(f"\nSuccess! Generated library data for {len(movies_list)} movies.")


# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    print_step("Checking the movie directory")
    answer = input("Did you already place your movie files in the Movies directory? (y/n): ").strip().lower()
    if answer != 'y':
        print("\nPlease put your files in the directory and run the script again")
        sys.exit(0)
    if not os.path.exists(MOVIE_DIR):
        print(f"\nCouldn't find '{MOVIE_DIR}'. Creating...")
        os.makedirs(MOVIE_DIR)
        print(f"Folder '{MOVIE_DIR}' created. Please move your files and restart the script")
        sys.exit(0)
        
    print_step("Converting Files")
    print(f"Scanning '{MOVIE_DIR}' for incompatible files...")
    
    video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.webm')
    files_to_convert = []
    for file in os.listdir(MOVIE_DIR):
        filepath = os.path.join(MOVIE_DIR, file)
        if not os.path.isfile(filepath) or not file.lower().endswith(video_extensions):
            continue
            
        info = get_video_info(filepath)
        if not info or 'streams' not in info:
            continue
        ext = os.path.splitext(file)[1].lower()
        has_video_issue = False
        has_audio_issue = False
        if ext not in ALLOWED_EXTENSIONS:
            has_video_issue = True
        for stream in info['streams']:
            codec_type = stream.get('codec_type')
            codec_name = stream.get('codec_name')
            if codec_type == 'video' and codec_name not in ALLOWED_VIDEO_CODECS:
                has_video_issue = True
            elif codec_type == 'audio' and codec_name not in ALLOWED_AUDIO_CODECS:
                has_audio_issue = True
        if has_video_issue or has_audio_issue:
            files_to_convert.append(filepath)
            
    if files_to_convert:
        print(f"Found {len(files_to_convert)} incompatible movies. Converting...\n")
        for filepath in files_to_convert:
            auto_convert_file(filepath)
        print("\nConverted all movies successfully")
    else:
        print("All movies are already compatible, great!")
        
    print_step("TMDB API configuration")
    
    config_data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except json.JSONDecodeError:
            pass

    tmdb_key = config_data.get("TMDB_API_KEY")
    
    if tmdb_key and tmdb_key != "YOUR_TMDB_API_KEY_HERE":
        print("TMDB API detected from config file")
    else:
        tmdb_key = input("Please enter your TMDB API key: ").strip()
        config_data["TMDB_API_KEY"] = tmdb_key
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        print(f" API key configured and stored successfully in '{CONFIG_FILE}'")

    print_step("Scraping Meta Data")
    print("Starting metadata generation...")
    
    scrape_metadata(tmdb_key)
    
    print("\nSetup completed successfully! You can run index.html now.")

if __name__ == "__main__":
    main()