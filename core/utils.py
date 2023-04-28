import re

ARTICLE_TITLE_TEXT_PATTERN = r'Title:\s*(?P<title>.*?)\s*Text:\s*(?P<text>.*?)$'


def parse_article_response(chatgpt_response_text: str):
    match = re.search(ARTICLE_TITLE_TEXT_PATTERN, chatgpt_response_text, re.DOTALL)
    text = chatgpt_response_text
    title = ''
    if match:
        title = match.group('title')
        text = match.group('text')
    return title, text
