import os
import json
import urllib.request
import urllib.parse
import re

# --- CONFIGURATION ---
TMDB_API_KEY = "YOUR_TMDB_API_KEY_HERE"
MOVIE_DIR = "./Movies"
METADATA_DIR = "./metadata"
OUTPUT_JS = "./movies.js"
# ---------------------

os.makedirs(f"{METADATA_DIR}/posters", exist_ok=True)
os.makedirs(f"{METADATA_DIR}/backdrops", exist_ok=True)
os.makedirs(f"{METADATA_DIR}/logos", exist_ok=True)

def clean_filename(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'(1080p|720p|2160p|4k|bluray|x264|x265|h264|h265|web-dl|webrip|dd5\.1).*', '', name, flags=re.IGNORECASE)
    return name.replace('.', ' ').replace('_', ' ').strip()

def fetch_tmdb_metadata(query):
    if TMDB_API_KEY == "YOUR_TMDB_API_KEY_HERE":
        return None
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={encoded_query}"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            if data['results']:
                return data['results'][0]
    except Exception as e:
        print(f"Error fetching metadata for {query}: {e}")
    return None

def fetch_movie_logo(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/images?api_key={TMDB_API_KEY}&include_image_language=en,de,null"
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

movies_list = []

print("== Metadata Scraper ==")
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
            "description": "No local description available. Update your TMDB API key in the fetch.py file to fetch metadata.",
            "subtitles": {} 
        }
        
        metadata = fetch_tmdb_metadata(clean_name)
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

            logo_path_hd = fetch_movie_logo(movie_id)
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
            
            print(f"Searching directory: {os.path.abspath(subtitles_dir)}")
            
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
                        else:
                            print(f"     Found file ({sub_file}), but the language is formatted incorrectly. (has to be _en or _de")
        else:
            print(f"Warning: Couldn't find subtitle directory at {os.path.abspath(subtitles_dir)}")

        movies_list.append(movie_entry)

with open(OUTPUT_JS, "w", encoding="utf-8") as f:
    f.write(f"const movieLibrary = {json.dumps(movies_list, indent=2)};")

print(f"Success! Generated library data for {len(movies_list)} movies.")