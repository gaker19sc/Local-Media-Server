
# Local Media Server

A lightweight local media server designed to stream your personal movie library directly within the browser, complete with automated metadata fetching and subtitle support. I run it from a USB drive :)

## Prerequisites

To run this, you need Python and FFmpeg. Download them at https://www.python.org/ and https://ffmpeg.org/

## Getting Started

To set everything up, place your movie files in the Movies directory. You can also add subtitles.
The system supports subtitles using `.srt` files.

1. Place your `.srt` files into the `Movies/Subtitles` folder.
2. The subtitle filename must match the movie filename exactly, followed by the respective language suffix (`_en`, `_de`, `_es`...).

**Example:**

* Movie file: `Project Hail Mary.mp4`
* Subtitle file: `Project Hail Mary_en.srt`

Once that is done, run the setup script:

```bash
py setup.py

```

Obtain a free TMDB API key at https://www.themoviedb.org/settings/api and follow the instructions on screen.

Once the setup has finished, you can close the window.

## Launching the Server

Once all steps are completed, you can start the interface by opening the following file in any standard web browser:

**`index.html`**

## Adding movies

If you have added a new movie file to the folder, in order to add it to the list, simply run the setup.py file again like you did the first time. It will remember your TMDB key so there's no need to reconfigure anything.
