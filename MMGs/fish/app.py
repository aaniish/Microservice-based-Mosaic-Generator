import os
import io
import base64
from PIL import Image, ImageStat
from flask import Flask, jsonify, render_template, request, make_response
import requests
from scipy.spatial import KDTree
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

app = Flask(__name__)

def load_tile_images(folder):
    tile_image_files = []
    for file in os.listdir(folder):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            tile_image_files.append(file)

    tile_images = []
    for file in tile_image_files:
        tile_images.append(os.path.join(folder, file))

    return tile_images

def average_color(image):
    avg_color = tuple(map(int, ImageStat.Stat(image).mean))
    return avg_color

def prepare_tiles(tile_images):
    tiles = []
    for tile in tile_images:
        img = Image.open(tile).convert("RGB")
        avg_color = average_color(img)
        tiles.append({"image": img, "average_color": avg_color})
    return tiles

def mosaic_generator(base_image, tiles_across, rendered_tile_size, tiles):
    aspect_ratio = base_image.height / base_image.width
    base_image_width = tiles_across
    base_image_height = int(base_image_width * aspect_ratio)
    base_image = base_image.resize((base_image_width, base_image_height), Image.ANTIALIAS)

    tiles_down = base_image_height

    colors = [tile["average_color"] for tile in tiles]
    kdtree = KDTree(colors)

    mosaic = Image.new('RGB', (tiles_across * rendered_tile_size, tiles_down * rendered_tile_size))
    height = base_image.height
    width = base_image.width

    for y in range(0, height):
        for x in range(0, width):
            color = base_image.getpixel((x, y))
            _, index = kdtree.query(color)
            selected_tile = tiles[index]
            mosaic.paste(selected_tile["image"].resize((rendered_tile_size, rendered_tile_size)), (x * rendered_tile_size, y * rendered_tile_size))

    return mosaic

def register_mmg():
    middleware_url = os.getenv("MIDDLEWARE_URL", "http://127.0.0.1:5000")
    mmg_name = "Fish"  
    mmg_url = "http://sp23-cs340-010.cs.illinois.edu:5012/mosaic"  
    author = "anisht3"  

    response = requests.put(
        f"{middleware_url}/addMMG",
        data={
            "name": mmg_name,
            "url": mmg_url,
            "author": author,
            "tileImageCount": len(tile_images)
        }
    )

    if response.status_code == 200:
        print("MMG successfully registered with the shared middleware.")
    else:
        print(f"Failed to register MMG with the shared middleware. Status code: {response.status_code}")

tile_images = load_tile_images(Path("fish"))
tiles = prepare_tiles(tile_images)

@app.route('/mosaic', methods=["POST"])
def generate_mosaic():
    f = request.files["image"]
    base_image = Image.open(f).convert("RGB")
    tiles_across = int(request.args.get("tilesAcross"))
    rendered_tile_size = int(request.args.get("renderedTileSize"))
    file_format = request.args.get("fileFormat")  

    mosaic = mosaic_generator(base_image, tiles_across, rendered_tile_size, tiles)

    buffer = io.BytesIO()
    mosaic.save(buffer, format=file_format)  
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.mimetype = f'image/{file_format.lower()}'

    return response

if __name__ == '__main__':
    register_mmg()
    app.run(port=5012, host="0.0.0.0")