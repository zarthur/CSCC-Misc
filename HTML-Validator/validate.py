"""Validate HTML/CSS of a page and linked subpages"""

import json
import sys

from pprint import PrettyPrinter
from typing import List
from urllib.parse import urljoin

import requests

from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector


class Validator:
    _HTML_VALIDATOR_URL = "http://validator.w3.org/nu/"
    _CSS_VALIDATOR_URL = "http://jigsaw.w3.org/css-validator/validator"

    def __init__(self, root_url: str):
        self.root_url = root_url
        self.errors = {'html': {}, 'css': {}}

    def validate(self) -> None:
        sub_urls = Validator._extract_links(self.root_url)
        for url in [self.root_url, *sub_urls]:
            results = Validator._validate_html(url)
            if results:
                self.errors['html'][url] = results
            else:
                self.errors['html'][url] = []

            css_results = Validator._validate_css(url)
            if css_results:
                self.errors['css'][url] = css_results
            else:
                self.errors['css'][url] = []

    def print_errors(self) -> None:
        printer = PrettyPrinter(indent=4)
        html_errors = 0
        for (page, errors) in self.errors['html'].items():
            html_errors += len(errors)

        css_errors = 0
        for (page, errors) in self.errors['css'].items():
            css_errors += len(errors)

        print("HTML\n####")
        print(json.dumps(self.errors['html'], indent=4))
        print("###\nCSS\n###")
        printer.pprint(self.errors['css'])
        print("#######\nSUMMARY\n#######")
        print("HTML: {0}, CSS: {1}".format(html_errors, css_errors))

    @staticmethod
    def _validate_html(url: str) -> List:
        parameters = {"doc": url, "out": "json"}
        response = requests.get(Validator._HTML_VALIDATOR_URL,
                                params=parameters)
        try:
            return response.json().get('messages', [])
        except json.JSONDecodeError:
            return [{'error': 'unexpected response from validator'}]

    @staticmethod
    def _validate_css(url: str) -> List:
        parameters = {'output': 'html', 'profile': 'css3', 'uri': url}
        response = requests.get(Validator._CSS_VALIDATOR_URL, params=parameters)
        soup = BeautifulSoup(response.text, 'lxml')
        results = []
        for error in soup.find_all("td", class_="parse-error"):
            error_text, *_ = error.contents
            results.append(error_text.strip())
        return results

    @staticmethod
    def _load_page(url: str) -> BeautifulSoup:
        response = requests.get(url)
        content_header = response.headers.get('content-type', '').lower()
        http_encoding = (response.encoding if 'charset' in content_header
                         else None)
        html_encoding = EncodingDetector.find_declared_encoding(
            response.content, is_html=True)
        encoding = html_encoding or http_encoding
        return BeautifulSoup(response.content, 'lxml', from_encoding=encoding)

    @staticmethod
    def _extract_links(url: str) -> List:
        soup = Validator._load_page(url)
        base_url, *_ = url.split('?')
        urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if href.startswith(base_url):
                urls.append(href)
            elif not href.startswith("http") or not href.startswith(".."):
                urls.append(urljoin(base_url, href))

        return urls


if __name__ == "__main__":
    url = sys.argv[1]
    validator = Validator(url)
    validator.validate()
    validator.print_errors()
