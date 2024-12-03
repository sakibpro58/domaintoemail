# #!/usr/bin/env python
# """
# Email scanner: prints all email addresses found on a domain.
# Joe Kamibeppu | 10 Oct 2016
# Dependencies:
#     Beautiful Soup (pip install beautifulsoup4)
#     Requests (pip install requests)
# Usage:
#     python find_email_addresses.py [domain name]
# """

# import sys
# import argparse
# from urlparse import urljoin, urlparse
# import requests
# from bs4 import BeautifulSoup, SoupStrainer

# def find_emails(base_url):
#     ''' finds email addresses by iteratively traversing through pages '''
#     emails = set()
#     to_visit = set()
#     visited = set()

#     to_visit.add(base_url)

#     while len(to_visit) > 0:
#         page = to_visit.pop()
#         response = requests.get(page)
#         visited.add(page)
#         hrefs = BeautifulSoup(response.text, 'html.parser',
#                               parse_only=SoupStrainer('a'))
#         for email_href in hrefs.select('a[href^=mailto]'):
#             emails.add(email_href.get('href').replace('mailto:', ''))
#         for link in hrefs.select('a[href]'):
#             new_url = urljoin(base_url, link['href'])
#             if urlparse(new_url).hostname == urlparse(base_url).hostname:
#                 if new_url not in visited:
#                     to_visit.add(new_url)
#         if len(to_visit) > 500:
#             print "More than 500 subpages have been found so far.", 
#             print "Terminating the program."
#             print_emails(emails)
#             sys.exit()
        
#     print_emails(emails)

# def print_emails(emails):
#     ''' prints all email addresses found '''
#     print "Found these email addresses:"
#     for email in emails:
#         print email

# def main(domain):
#     ''' main function '''
#     protocol = 'http://' # default is HTTP (some sites do not handle HTTPS)
#     find_emails(protocol + domain)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description='prints emails from a website')
#     parser.add_argument('domain', type=str, help='the domain to be searched')
#     args = parser.parse_args()
#     main(args.domain)




#!/usr/bin/env python
"""
Email scanner with API: prints all email addresses found on a domain.
Includes throttling and User-Agent randomization for anti-scraping evasion.
"""

import sys
import argparse
import random
import time
from urllib.parse import urljoin, urlparse
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup, SoupStrainer

app = Flask(__name__)

# List of User-Agent strings for randomization
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
]

def get_random_user_agent():
    """Returns a random User-Agent string."""
    return random.choice(USER_AGENTS)

def find_emails(base_url):
    """Finds email addresses by iteratively traversing through pages."""
    emails = set()
    to_visit = set()
    visited = set()

    to_visit.add(base_url)

    while to_visit:
        page = to_visit.pop()
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(page, headers=headers)
            time.sleep(random.uniform(1, 2))  # Throttling: 1-2 second delay
            visited.add(page)
            hrefs = BeautifulSoup(response.text, 'html.parser',
                                  parse_only=SoupStrainer('a'))
            for email_href in hrefs.select('a[href^=mailto]'):
                emails.add(email_href.get('href').replace('mailto:', ''))
            for link in hrefs.select('a[href]'):
                new_url = urljoin(base_url, link['href'])
                if urlparse(new_url).hostname == urlparse(base_url).hostname:
                    if new_url not in visited:
                        to_visit.add(new_url)
            if len(to_visit) > 500:
                print("More than 500 subpages have been found. Terminating.")
                return list(emails)
        except requests.RequestException as e:
            print(f"Error accessing {page}: {e}")
            continue

    return list(emails)

@app.route('/emails', methods=['GET'])
def get_emails():
    """API endpoint to find emails."""
    domain = request.args.get('domain')
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400

    protocol = 'http://'  # Default protocol
    emails = find_emails(protocol + domain)
    return jsonify({"emails": emails})

def main(domain):
    """Main function."""
    protocol = 'http://'  # Default is HTTP (some sites do not handle HTTPS)
    emails = find_emails(protocol + domain)
    print("Found these email addresses:")
    for email in emails:
        print(email)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Finds emails from a website or runs as an API server.')
    parser.add_argument('--domain', type=str, help='The domain to be searched')
    parser.add_argument('--server', action='store_true', help='Run as an API server')
    args = parser.parse_args()

    if args.server:
        app.run(host='0.0.0.0', port=5000)
    elif args.domain:
        main(args.domain)
    else:
        print("Please provide a domain or use --server to run as an API.")

