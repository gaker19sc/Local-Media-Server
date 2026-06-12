
# Local Media Server

A lightweight local media server designed to stream your personal movie library directly within the browser, complete with automated metadata fetching and subtitle support. I run it from a USB drive :)

## Prerequisites

To run this, you need Python and FFmpeg. Download them at https://www.python.org/ and https://ffmpeg.org/

## Setup

First, place your movie files in the Movies directory. I recommend renaming the files to the movies' titles to make sure the TMDB database is going to be able to find them. 

You can also add subtitles. The script will automatically pull any existing subtitles from your movie file, but in case you want to provide your own subtitles, the system supports using `.srt` files. It works like this:

1. Place your `.srt` files into the `Movies/Subtitles` folder.
2. The subtitle filename must match the movie filename exactly, followed by the respective language suffix (`_en`, `_de`, `_es`...).

**Example:**

* Movie file: `Project Hail Mary.mp4`
* Subtitle file: `Project Hail Mary_en.srt`

To get those subtitle files, I recommend VLC media player's VLsub tool, it's really cool, but anything works really.

Once you have your movies and subtitles in place, you'll need a free TMDB API key. Get it at https://www.themoviedb.org/settings/api and copy it to your clipboard.

Now you can run the setup script:

```bash
py setup.py

```

It will first ask you if you put your files into the folder already, which you of course already did, so type "y" and press enter. The setup will then convert your movie files to a browser-compatible format (don't worry, size and quality stay roughly the same), extract the subtitles and get the metadata for your movies.

Once the setup tells you that it has finished, you can close the window.

## Launching the Server

Now that everything is set up, you can start the interface by opening the following file in any standard web browser:

**`index.html`**

You should see your movie library. Click a film to play it.

## Adding movies

If you want to add a new movie, repeat the process again. Put it in the folder, then run the setup script again. It will have remembered your TMDB key so there is no need to reconfigure anything.
