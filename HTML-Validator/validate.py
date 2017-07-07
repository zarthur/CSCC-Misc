"""Validate HTML/CSS of a page and linked subpages"""

import json

from typing import List
from urllib.parse import urljoin

import requests

from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector


class Validator:
    _HTML_VALIDATOR_URL = "http://validator.w3.org/nu/"

    def __init__(self, root_url: str):
        self.root_url = root_url
        self.errors = {'html': {}, 'css': {}}

    def validate_html(self):
        sub_urls = Validator._extract_links(self.root_url)
        for url in [self.root_url, *sub_urls]:
            results = Validator._validate_page(url)
            if results:
                self.errors['html'][url] = results
            else:
                self.errors['html'][url] = []

    def validate_css(self):
        pass

    def print_errors(self):
        print("HTML\n####")
        print(json.dumps(self.errors['html'], indent=4))
        print("###\nCSS\n###")
        print(json.dumps(self.errors['css'], indent=4))
        print("#######\nSUMMARY\n#######")
        print("HTML: {0}, CSS: {1}".format(len(self.errors['html']),
                                           len(self.errors['css'])))

    @staticmethod
    def _validate_page(url: str) -> List:
        parameters = {"doc": url, "out": "json"}
        response = requests.get(Validator._HTML_VALIDATOR_URL,
                                params=parameters)
        try:
            return response.json().get('messages', [])
        except json.JSONDecodeError:
            return [{'error': 'unexpected response from validator'}]

    @staticmethod
    def _extract_links(url: str) -> List:
        response = requests.get(url)
        content_header = response.headers.get('content-type', '').lower()
        http_encoding = (response.encoding if 'charset' in content_header
                         else None)
        html_encoding = EncodingDetector.find_declared_encoding(
            response.content, is_html=True)
        encoding = html_encoding or http_encoding
        soup = BeautifulSoup(response.content, from_encoding=encoding)

        base_url, *_ = url.split('?')
        urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if href.startswith(base_url):
                urls.append(href)

            if not href.startswith("http") or not href.startswith(".."):
                urls.append(urljoin(base_url, href))

        return urls
