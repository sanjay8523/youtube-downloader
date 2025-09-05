import os
import subprocess
from flask import Flask, render_template, request, send_file
from pytubefix import YouTube


from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def clean_youtube_url(url: str) -> str:
    """
    Convert youtu.be or messy links into a clean YouTube watch URL.
    """
    url = url.strip()

    # Handle youtu.be short links
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"

    # Remove ?si= and other unnecessary params
    if "&" in url:
        url = url.split("&")[0]
    if "?si=" in url:
        url = url.split("?si=")[0]

    return url

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        raw_url = request.form["url"]
        option = request.form["option"]

        # ✅ Clean and standardize the URL
        url = clean_youtube_url(raw_url)
        print(f"Final cleaned URL: {url}")

        try:
            yt = YouTube(url)
            print(f"Video title: {yt.title}")

            if option == "video":
                stream = yt.streams.get_highest_resolution()
                filepath = stream.download(output_path=DOWNLOAD_FOLDER)
                return send_file(filepath, as_attachment=True)

            elif option == "audio":
                stream = yt.streams.filter(only_audio=True).first()
                filepath = stream.download(output_path=DOWNLOAD_FOLDER)

                # Convert to mp3
                mp3_path = filepath.rsplit(".", 1)[0] + ".mp3"
                subprocess.run(
                    ["ffmpeg", "-i", filepath, mp3_path, "-y"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                os.remove(filepath)
                return send_file(mp3_path, as_attachment=True)

        except Exception as e:
            print(f"Error: {str(e)}")
            return f"Error: {str(e)}"

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
