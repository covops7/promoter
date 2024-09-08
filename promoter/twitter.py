import os
import requests
import json
import re
import time
from datetime import datetime, timedelta
from typing import List
from bs4 import BeautifulSoup
import logging

from dotenv import load_dotenv
import artist

load_dotenv()

script_dir = os.path.dirname(os.path.abspath(__file__))

# Hashtags to manually add to each tweet
latest_hashtags = [
    'AEWDynamite',
    'nsfw',
    'stream',
    'telegram',
    'onlyfans'
]

# logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

iftt_webhook_url = f"https://maker.ifttt.com/trigger/send_tweet/with/key/{os.getenv('IFTT_WEBHOOK_KEY')}"
cb_api_url = "https://chaturbate.com/api/public/affiliates/onlinerooms/?wm=swoeK&client_ip={client_ip} "
explorer_url = "https://www.cbexplorer.com/top/growing"

current_time = datetime.now()
ymd = current_time.strftime('%Y-%m-%d')

script_dir = os.path.dirname(os.path.abspath(__file__))
explore_path = os.path.join(script_dir, "logs", "cb_explore_logs")
event_path = os.path.join(script_dir, "logs", "cb_api_logs")
webhook_logs = os.path.join(script_dir, "logs", "webhook_logs")
promo_dir = os.path.join(script_dir, "logs", "promo_materials")

promo_list_fp = os.path.join(explore_path, "promo_list.json")
explore_info_fp = os.path.join(explore_path, f"{ymd}.json")

### ====
# Timing function
### ====
def perform_delay(t: int = 300):
    while t: 
        mins, secs = divmod(t, 60) 
        timer = 'Timer: {:02d}:{:02d}'.format(mins, secs) 
        print(timer, end="\r") 
        time.sleep(1) 
        t -= 1

### ====
# Chaturbate API
### ====

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        ip_data = response.json()
        return ip_data['ip']
    except requests.RequestException as e:
        return f"Error fetching IP: {e}"
    
def get_cb_api_results(kwargs):
    try:
        # Send a GET request to the specified API URL
        response = requests.get(cb_api_url.format(**kwargs))
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the response JSON content
            return response.json()
        else:
            # Return an error message with the status code
            return f"Error: Received status code {response.status_code}"
    except requests.RequestException as e:
        # Return an error message in case of exception
        return f"Error fetching data: {e}"
    
def get_new_cb_events():
    logging.debug("Checking chaturbate for new info.")
    current_time = datetime.now()
    formatted_time = current_time.strftime('%Y-%m-%d_%H-%M-%S')
    response = get_cb_api_results(
        {'client_ip': get_public_ip()}
    )
    log_path = os.path.join(event_path, f'{formatted_time}.json')
    with open(log_path, 'w+') as f:
        json.dump(response, f, indent=4)

### ====
# CB Explorer Results
### ====

def get_explorer_results():
    # Send a GET request to the webpage
    response = requests.get(explorer_url)
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        root_div = soup.find('div', id='prefetch')
        if root_div:
            valid_json = list(root_div.contents)[0]
            try:
                data = json.loads(valid_json)
                # logging.debug(json.dumps(data, indent=4))  # Pretty print the JSON data
                return valid_json
            except json.JSONDecodeError:
                logging.debug("Failed to decode JSON. The extracted text may not be valid JSON.")
        else:
            logging.debug("No <div> with id 'root' found in the HTML.")
    else:
        logging.debug(f"Failed to retrieve the webpage. Status code: {response.status_code}")

        return soup

def get_cb_explore_log():
    current_time = datetime.now()
    formatted_time = current_time.strftime('%Y-%m-%d')
    log_path = os.path.join(explore_path, f'{formatted_time}.json')

    data = get_explorer_results()
    with open(log_path, 'w+') as f:
        f.write(data)

    with open(log_path, 'r') as f:
        data = json.load(f)

    pretty_json = json.dumps(data, indent=4)

    with open(log_path, 'w') as f:
        f.write(pretty_json)

    return data

def get_fastest_growing_performers(explore_log):
    promo_list_path = os.path.join(explore_path, "promo_list.json")
    fastest = [x['u'] for x in explore_log]
    
    with open(promo_list_path, 'w+') as f:
        # for x in fastest:
        #     f.write(x + '\n')
        json.dump(fastest, f, indent=4)
    return fastest

def get_explore_results():
    explore_log = get_cb_explore_log()
    get_fastest_growing_performers(explore_log)


def get_newest_log_file(directory, file_extension=".json"):
    """
    Get the newest log file in a specified directory.

    Parameters:
        directory (str): The path to the directory to search for log files.
        file_extension (str): The file extension to filter by (default is ".json").

    Returns:
        str: The path to the newest log file or None if no log files are found.
    """
    try:
        # List all files in the specified directory
        files = [f for f in os.listdir(directory) if f.endswith(file_extension)]

        # Get the full path for each file
        full_paths = [os.path.join(directory, f) for f in files]

        # Check if there are any log files
        if not full_paths:
            logging.debug("No log files found in the directory.")
            return None

        # Find the newest file by comparing the modification times
        newest_file = max(full_paths, key=os.path.getmtime)

        return newest_file
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
        return None
    
def get_newest_events():
    newest_event_path = get_newest_log_file(event_path)
    logging.debug("Newest event path: ", newest_event_path)

    if newest_event_path:
        # Get the last modification time of the newest log file
        last_mod_time = os.path.getmtime(newest_event_path)
        last_mod_datetime = datetime.fromtimestamp(last_mod_time)

        # Get the current time
        current_time = datetime.now()

        # Calculate the time difference
        time_difference = current_time - last_mod_datetime
        logging.debug("Time difference: ", time_difference)

        # Check if the time difference is greater than 10 minutes
        if time_difference < timedelta(minutes=10):
            with open(newest_event_path, 'r') as file:
                data = json.load(file)
            data['time difference'] = time_difference
            logging.debug(f"Last event log update: {time_difference}")
            logging.debug(f"Length of data: {len(data)}")
            return data
        else:
            get_new_cb_events()
            return get_newest_events()
    else:
        get_new_cb_events()
        return get_newest_events()

def read_promo_list():
    # Read the JSON data from the file
    with open(promo_list_fp, 'r') as file:
        data = json.load(file)

    # Ensure the data is a list
    if isinstance(data, list):
        # Convert the list to a set to remove duplicates and store unique names
        unique_people_set = set(data)
        
        # # Print the resulting set
        # logging.debug(unique_people_set)

        unique_people_set
    else:
        logging.debug("The JSON file does not contain a list.")
        
    return unique_people_set

def get_online_promo_users(all_online, promo_list):
    # Get everone who is online
    # Extract online users from the JSON data
    if 'results' in all_online and isinstance(all_online['results'], list):
        online_users = [user['username'] for user in all_online['results']]
    else:
        online_users = []

    # Find users who are online and also in the promo list
    online_promo_users = [user for user in online_users if user in promo_list]
    return online_promo_users

def get_explore_info():
    # Update explore log if doesn't exist
    if not os.path.exists(explore_info_fp):
        get_explore_results()

    # Read the JSON data from the file
    with open(explore_info_fp, 'r') as file:
        data = json.load(file)
    return data

def get_streamer_info(name, new_events, explore_info):
    streamer_info = dict(name=name)
    new_events = new_events['results']

    logging.debug("number of new events ", len(new_events))

    n_online = len(set([u["username"] for u in new_events]))
    logging.debug(f"number of unique streamers: {n_online}")

    target_events = [u for u in new_events if u["username"] == name] 
    logging.debug(f"Number of events that contain streamer: {len(target_events)}")
    
    if len(target_events) == 0: # not found in cb api
        return None
    
    streamer_info["cb_api"] = target_events[0]

    target_explore_info = [u for u in explore_info if u['u'] == name]
    streamer_info["explorer_info"] = target_explore_info[0]

    hd_image_url = None
    # hd_image_url = get_hd_url(streamer_info['chat_room_url_revshare'])

    result = dict(
        name=streamer_info['name'],
        room_url=transform_cb_to_bc(streamer_info['cb_api']['chat_room_url_revshare']),
        room_subject=streamer_info['cb_api']["room_subject"],
        image_url=streamer_info['cb_api']['image_url'],
        hd_image_url=hd_image_url
    )
    result['tags'] = streamer_info['explorer_info']['t']
    # if 'description' in streamer_blob['explorer_info'] and 'd' in streamer_blob['explorer_info']['description']:
    #     streamer_info['description'] = streamer_blob['explorer_info']['description']

    return result

def transform_cb_to_bc(url):
    result = str(url).replace("chaturbate.com", "www.babe-chat.com")

    # Replace "redirect profile to home page if you're offline" to "redirect to profile even if offline"
    result = str(result).replace("LQps", "dT8X") 

    return result

### ===
# Twitter Functions
### ===
def send_iftt_webhook(
    status: str, 
    image_url: str = None, 
    debug: bool = False,
    log_fp: os.PathLike = None,
    delay: bool = False
):
    
    # Create a dictionary to store the data to be sent in the request
    data = {
        'iftt_webhook_url': iftt_webhook_url,
        'response': None,
        'value1': status,
        'value2': image_url
    }
    
    if debug:
        response = 'debug'
        if log_fp:
            with open(log_fp, 'w+') as f:
                json.dump(data, f, indent=4)
            
            logging.debug(f"Wrote webhook log in :{log_fp}")

    else:
        # Send the POST request to the IFTTT webhook URL
        response = requests.post(iftt_webhook_url, json=data)

        # Check if the request was successful
        if response.status_code == 200:
            logging.debug('IFTTT Webhook triggered successfully!')
            logging.debug('Sent query: ', data)
        else:
            logging.debug(f'Failed to trigger IFTTT Webhook. Status code: {response.status_code}')
            logging.debug(f'Response: {response.text}')
        
        data['response'] = response.status_code

    t = 60
    while t:
        mins, secs = divmod(t, 60)
        timer = 'You have 60 seconds to check files before uploading: {:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        t -= 1

    # Cache webhook request
    if log_fp:
        with open(log_fp, 'w+') as f:
            json.dump(data, f, indent=4)
        
        logging.debug(f"Wrote webhook log in :{log_fp}")
    
    return response

def get_highest_ranked_streamers_online(new_events, n_streamers: int = 5, blacklist: List[str] = None):
    promo_list = read_promo_list()
    name2rank = {n:i for i, n in enumerate(promo_list)}
    rank2name = {i:n for i, n in enumerate(promo_list)}
    n_promo = len(promo_list)
    logging.debug(f"We have {n_promo} people on the promo list.")
    
    online_users = get_online_promo_users(new_events, promo_list)
    n_online = len(online_users)
    logging.debug(f"We have {n_online} people on the promo list online.")

    highest_rank = [name2rank[n] for n in online_users if n not in blacklist]
    highest_rank.sort()
    highest_ranked_streamers_online = {rank2name[r]: r for r in highest_rank[:n_streamers]}
    logging.debug(f"Our current highest ranked streamers online are: {highest_ranked_streamers_online}")

    return highest_ranked_streamers_online

def write_tweet(name: str, new_events: dict, explore_info: dict, debug):
    streamer_info = get_streamer_info(name, new_events, explore_info)
    if streamer_info:
        logging.debug(streamer_info)
        caption = write_tweet_text(streamer_info)
        image_url = streamer_info['image_url']
        if debug:
            logging.debug("[DEBUG mode]Generated caption: ")
            logging.debug(caption)
            logging.debug("[DEBUG mode]Image url: ", image_url)
        
        image_url, cloudflare_response = artist.twitter_promo(streamer_info, promo_dir)

        # Proceed with sending the webhook
        current_time = datetime.now()
        formatted_time = current_time.strftime('%Y-%m-%d_%H-%M-%S')
        log_fp = os.path.join(webhook_logs, f"{formatted_time}-{name}.json")

        resp = send_iftt_webhook(
            status=caption,
            image_url=image_url,
            debug=debug,
            log_fp=log_fp,
            delay=not debug
        )

        if not debug:
            logging.debug("Waiting 10 minutes to remove Cloudflare upload.")
            perform_delay(600)
        artist.delete_cloudflare(cloudflare_response)
        
        # Success
        status = resp == 200
        return status
    
def new_tweet(user: str = None, debug: bool = False, last_tweeted: List[str] = []) -> bool: 
    logging.debug("Writing tweet for user ", user)
    explore_info = get_explore_info()
    new_events = get_newest_events()
    n_events = len(new_events)
    logging.debug(f"We have {n_events} new events")
    # logging.debug("We have events pulled from :", new_events['time difference'])

    if user:
        write_tweet(user, new_events, explore_info, debug)
    else:
        logging.debug(f"No specific user given, so getting the highest rank streamer online.")
        highest_ranked_streamer = get_highest_ranked_streamers_online(
            new_events, 
            n_streamers=1, 
            blacklist=last_tweeted
        )
        last_tweeted = [highest_ranked_streamer,] + last_tweeted[:4]
        for name, rank in highest_ranked_streamer.items():
            logging.debug(f"{name} is online, rank {rank}")
            write_tweet(name, new_events, explore_info, debug)


def remove_hashtags(input_string, hashtags):
    # This regex pattern matches words starting with a hashtag
    hashtag_pattern = r"#\w+"
    # logging.debug("currently known hashtags: ", hashtags)
    
    # Use re.findall to get a list of hashtags
    found_hashtags = re.findall(hashtag_pattern, input_string)
    found_hashtags = [t.strip('#') for t in found_hashtags]
    # logging.debug("found hashtags: ", found_hashtags)
    
    # Use re.sub to replace the hashtagged words with an empty string
    result = re.sub(hashtag_pattern, '', input_string)
    
    # Strip leading and trailing whitespace
    result = result.strip()

    # add found hashtags to existinghashtags
    hashtags = set(hashtags + found_hashtags)

    # remove 18 from hashtags
    hashtags.discard("18")
    
    # Return the modified string and the list of found hashtags
    return result, hashtags

def remove_goal(input_string):
    # Combine both patterns to match "[X tokens remaining]" and "[ X tokens left ]" where X is any number
    pattern = r"\[\s*\d+\s*tokens\s*(left|remaining)\s*\]"
    
    # Use re.sub to replace the matched pattern with an empty string
    cleaned_string = re.sub(pattern, "", input_string)
    
    return cleaned_string

    # Return the cleaned string with surrounding whitespace stripped
    return cleaned_string.strip()

def normalize_whitespace(text):
    # Replace all sequences of whitespace with a single space
    text = str(text)
    return re.sub(r'\s+', ' ', text).strip()


def write_tweet_text(data):
    caption = """{name} online now! 💋 Link: {room_url}
{room_subject} 
{room_tags}"""
    name = data['name']
    room_tags = data['tags'] if data['tags'] is not None else []
    room_tags.extend(latest_hashtags)
    logging.debug("initial room tags: ", room_tags)

    room_subject = data['room_subject']
    logging.debug(f"Room subject: {room_subject}")

    room_subject, room_tags = remove_hashtags(room_subject, room_tags)
    logging.debug(f"Room subject, after removing hashtags: {room_subject}")

    room_subject = remove_goal(room_subject)
    logging.debug(f"Room subject, after removing goal message: {room_subject}")

    room_subject = normalize_whitespace(room_subject)
    logging.debug(f"Room subject, after normalizing: {room_subject}")

    room_url = data['room_url']
    
    room_tags = [f"#{t}" for t in room_tags]
    room_tags = ' '.join(room_tags)
    
    caption = caption.format(
        name=name,
        room_subject=room_subject,
        room_url=room_url,
        room_tags=room_tags
    )
    return caption