import argparse
import logging
import promoter
from promoter import perform_delay

def start_app(args):
    delay = bool(args.delay)
    user = args.user

    if delay:
        perform_delay()

    last_tweeted = []
    while True:
        logging.debug("Tweet.")
        promoter.new_tweet(user=user, debug=args.debug, last_tweeted=last_tweeted)
        perform_delay(1800)

### ====
# Main
### ====
def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Normalize whitespace in a text.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.", default=False)
    parser.add_argument("--delay", action="store_true", help="Delay execution.", default=False)
    parser.add_argument("--user", type=str, help="Specify a user.", default=None)

    # Parse the arguments
    args = parser.parse_args()

    start_app(args)

if __name__ == "__main__":
    main()
