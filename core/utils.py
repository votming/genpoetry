import re

ARTICLE_TITLE_TEXT_PATTERN = r'A:\s*(?P<title>.*?)\s*B:\s*(?P<text>.*?)$'


def parse_article_response(chatgpt_response_text: str):
    match = re.search(ARTICLE_TITLE_TEXT_PATTERN, chatgpt_response_text, re.DOTALL)
    text = match.group('text') if match else ''
    title = match.group('title') if match else chatgpt_response_text
    return title, text
