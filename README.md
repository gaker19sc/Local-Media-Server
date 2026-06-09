
# Local Media Server

A lightweight local media server designed to stream your personal movie library directly within the browser, complete with automated metadata fetching and subtitle support.



## Getting Started

### Automatic setup (recommended)

To set everything up, run the setup script:

```bash
py setup.py

```

Obtain a free API key at https://www.themoviedb.org/settings/api and follow the instructions on screen.

Once the setup has finished, you can close the window and open index.html to start the program.

---

### Manual setup

If you'd like to set everything up manually, follow these instructions.

### 1. Add Your Movies
Place your movie files into the `Movies` directory. All files must be in a browser-compatible format, such as `.mp4` or `.webm`.

If you are unsure whether your files are supported, you can convert them using the supplied conversion script. Open a terminal in the root folder and execute:

```bash
py convert.py

```

Follow the interactive instructions in the terminal to process your files.



### 2. Add Subtitles (Optional)

The system currently supports English and German subtitles using `.srt` files.

1. Place your `.srt` files into the `Movies/Subtitles` folder.
2. The subtitle filename must match the movie filename exactly, followed by the respective language suffix (`_en` or `_de`).

**Example:**

* Movie file: `Project Hail Mary.mp4`
* Subtitle file: `Project Hail Mary_en.srt`



### 3. Configure Metadata (TMDB API)

To automatically download movie posters, backdrops, logos, and descriptions, a free API key from The Movie Database (TMDB) is required.

1. Obtain a free API key at: https://www.themoviedb.org/settings/api
2. Open the `fetch.py` file in a text editor.
3. Locate the configuration section at the top of the file and replace the placeholder text `"YOUR_TMDB_API_KEY_HERE"` with your actual API key.

```python
# --- CONFIGURATION ---
TMDB_API_KEY = "YOUR_TMDB_API_KEY_HERE"
MOVIE_DIR = "./Movies"
METADATA_DIR = "./metadata"
OUTPUT_JS = "./movies.js"
# ---------------------

```

*Note: Ensure that your API key remains enclosed within the quotation marks.*



### 4. Fetch Media Metadata

After saving your API key, run the metadata aggregator to scan your library and generate the catalog data:

```bash
py fetch.py

```

The script will automatically download the required artwork and compile your library database.



## Launching the Server

Once all steps are completed, you can start the interface by opening the following file in any standard web browser:

**`index.html`**