import os
import requests
import os

from dotenv import load_dotenv
from .twitter import still_image

load_dotenv()

script_dir = os.path.dirname(os.path.abspath(__file__))


CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')

def upload_to_cloudflare(
        image_path: os.PathLike,
        API_TOKEN=CLOUDFLARE_API_TOKEN,
        ACCOUNT_ID=CLOUDFLARE_ACCOUNT_ID
):
    # Define the Cloudflare Images upload endpoint
    url = f'https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/images/v1'
    response = None

    # Define the headers including the authorization header with the API token
    headers = {
        f'Authorization': f'Bearer {API_TOKEN}',
    }

    # Define the files to be uploaded
    files = {
        'file': open(image_path, 'rb')
    }

    # Make the POST request to upload the image
    response = requests.post(url, headers=headers, files=files)

    # Check if the upload was successful
    if response.status_code == 200:
        print("Image uploaded successfully!")
        print("Response:", response.json())

        url = response.json()['result']['variants'][0]
        response = response.json()
    else:
        print(f"Failed to upload image. Status code: {response.status_code}")
        print("Response:", response.text)
        url = image_path

    print("Sending url: ", url)
    return url, response

def delete_cloudflare(
        cloudflare_response,
        api_token=CLOUDFLARE_API_TOKEN,
        account_id=CLOUDFLARE_ACCOUNT_ID
    ):
    image_id = cloudflare_response['result']['id']

    # Cloudflare API endpoint for image deletion
    url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1/{image_id}'

    # Set headers for authentication and content type
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    # Make the DELETE request to remove the image
    response = requests.delete(url, headers=headers)

    # Check the response status
    if response.status_code == 200:
        print("Image removed successfully.")
    else:
        print(f"Failed to remove image. Status code: {response.status_code}")
        print("Response:", response.json())

def twitter_promo(streamer_info: dict, promo_dir: os.PathLike) -> str:
    local_image_path = still_image(streamer_info, promo_dir)
    url, response = upload_to_cloudflare(local_image_path)
    return url, response
