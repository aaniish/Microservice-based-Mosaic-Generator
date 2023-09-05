import os
import io
import base64
from PIL import Image, ImageStat
from flask import Flask, jsonify, render_template, request, make_response
import requests
from scipy.spatial import KDTree
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

app = Flask(__name__)

def average_color(image):
    avg_color = tuple(map(int, ImageStat.Stat(image).mean))
    return avg_color

def reduce_mosaic(base_image, mosaic1, mosaic2, tiles_across, rendered_tile_size):
    aspect_ratio = base_image.height / base_image.width
    base_image_width = tiles_across
    base_image_height = int(base_image_width * aspect_ratio)
    base_image = base_image.resize((base_image_width, base_image_height), Image.ANTIALIAS)

    tiles_down = base_image_height

    reduced_mosaic = Image.new('RGB', (tiles_across * rendered_tile_size, tiles_down * rendered_tile_size))

    for y in range(0, tiles_down):
        for x in range(0, tiles_across):
            base_color = base_image.getpixel((x, y))
            mosaic1_tile = mosaic1.crop((x * rendered_tile_size, y * rendered_tile_size, (x + 1) * rendered_tile_size, (y + 1) * rendered_tile_size))
            mosaic2_tile = mosaic2.crop((x * rendered_tile_size, y * rendered_tile_size, (x + 1) * rendered_tile_size, (y + 1) * rendered_tile_size))

            mosaic1_avg_color = average_color(mosaic1_tile)
            mosaic2_avg_color = average_color(mosaic2_tile)

            mosaic1_diff = sum(abs(a - b) for a, b in zip(base_color, mosaic1_avg_color))
            mosaic2_diff = sum(abs(a - b) for a, b in zip(base_color, mosaic2_avg_color))

            if mosaic1_diff < mosaic2_diff:
                reduced_mosaic.paste(mosaic1_tile, (x * rendered_tile_size, y * rendered_tile_size))
            else:
                reduced_mosaic.paste(mosaic2_tile, (x * rendered_tile_size, y * rendered_tile_size))

    return reduced_mosaic

@app.route("/reduceMosaic", methods=["POST"])
def reduce():
    base_image = Image.open(request.files["baseImage"]).convert("RGB")
    mosaic1 = Image.open(request.files["mosaic1"]).convert("RGB")
    mosaic2 = Image.open(request.files["mosaic2"]).convert("RGB")

    rendered_tile_size = int(request.args.get("renderedTileSize"))
    tiles_across = int(request.args.get("tilesAcross"))
    file_format = request.args.get("fileFormat")

    mosaic_reduction = reduce_mosaic(base_image, mosaic1, mosaic2, tiles_across, rendered_tile_size)

    buffer = io.BytesIO()
    mosaic_reduction.save(buffer, format=file_format)
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.mimetype = f'image/{file_format.lower()}'
    return response

def register_reducer():
    middleware_url = os.getenv("MIDDLEWARE_URL", "http://127.0.0.1:5000")
    reducer_name = "Mosaic Reducer"
    reducer_url = "http://sp23-cs340-010.cs.illinois.edu:5014/reduceMosaic"
    author = "anisht3"

    response = requests.put(
        f"{middleware_url}/registerReducer",
        data={
            "name": reducer_name,
            "url": reducer_url,
            "author": author
        }
    )

    if response.status_code == 200:
        print("Reducer successfully registered with the shared middleware.")
    else:
        print(f"Failed to register reducer with the shared middleware. Status code: {response.status_code}")

if __name__ == '__main__':
    register_reducer()
    app.run(port=5014, host="0.0.0.0")