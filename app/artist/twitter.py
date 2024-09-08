import os
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse

live_img = "logo/live-transparent-xs.png"
bchat_url = "logo/url-transparent-xs.png"

def is_url(path):
    """
    Check if the given path is a URL.
    """
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def overlay_image(
        background_path,  # Can be a URL or a local path
        overlay1_path, 
        overlay2_path,
        output_path, 
        position=(0, 0)
    ):
    print(f"Looking for image: {background_path}")
    # Check if the background path is a URL or a local file
    if is_url(background_path):
        response = requests.get(background_path)
        if response.status_code == 200:
            background = Image.open(BytesIO(response.content)).convert("RGBA")
        else:
            raise ValueError("Unable to fetch the background image from the URL.")
    else:
        if os.path.exists(background_path):
            background = Image.open(background_path).convert("RGBA")
        else:
            raise ValueError(f"Background image file not found: {background_path}")

    # Resize background image to 360x270
    # background = background.resize((360, 270))

    # Create a new image by combining the background and overlay
    combined = Image.new("RGBA", background.size)
    combined.paste(background, (0, 0))

    # Open the overlay image (should have a transparent background)
    overlay = Image.open(overlay1_path).convert("RGBA")
    position = (4, 3)           # position of overlay
    combined.paste(overlay, position, overlay)  # The third parameter 'overlay' keeps transparency

    # Second image
    overlay = Image.open(overlay2_path).convert("RGBA")
    # 360x270
    position = (113, 230)       # position of overlay
    combined.paste(overlay, position, overlay)  # The third parameter 'overlay' keeps transparency

    # Save the result
    combined.save(output_path, format="PNG")
    print(f"Image saved to {output_path}")

    return output_path

def still_image(streamer_info: dict, promo_dir: os.PathLike) -> str:
    name = streamer_info['name']
    background_url = streamer_info['image_url']
    overlay1_path = live_img
    overlay2_path = bchat_url

    current_time = datetime.now()
    formatted_time = current_time.strftime('%Y-%m-%d_%H-%M-%S')
    fname = formatted_time + f'-{name}-.png'
    output_path = os.path.join(promo_dir, fname)

    output_path = overlay_image(
        background_url, 
        overlay1_path, 
        overlay2_path,
        output_path, 
    )
    return output_path

def overlay_logo_img_from_local(
        output_path:os.PathLike, 
        img_url: os.PathLike, 
    ) -> str:
    overlay1_path = live_img
    overlay2_path = bchat_url

    output_path = overlay_image(
        img_url, 
        overlay1_path, 
        overlay2_path,
        output_path, 
    )
    return output_path
