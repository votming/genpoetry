import openai

from configuration import Config
from core.models import Article

openai.api_key = Config.CHATGPT_TOKEN


class GenerateChatGPTQuote:

    def __init__(self, request: str, chat_context: list[str] = None, temperature: int = 1, model: str = 'gpt-4',
                 chat_id: str = None, **kwargs):
        self.model = model
        self.request = request
        self.chat_context = chat_context
        self.temperature = temperature
        self.chat_id = chat_id

    def generate(self) -> str:
        messages = self._prepare_messages()
        try:
            chat = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                n=1,
                temperature=self.temperature
            )
            if chat.choices[0].finish_reason != 'stop':
                raise Exception(f"Wasn't able to finish the completion, status: {chat.choices[0].finish_reason}")
            text = chat.choices[0].message.content
            return text
        except Exception as ex:
            raise Exception(f"Couldn't generate chatgpt quote. Original error: {ex}")

    def _prepare_messages(self) -> list[dict]:
        messages = []

        if self.chat_id is None:
            self._append_message(messages, Config.DEFAULT_CHATGPT_SYSTEM_PROMPT + self.request, role='system')
        else:
            articles = Article.objects.filter(chat_id=self.chat_id)
            self._append_message(messages, Config.DEFAULT_CHATGPT_SYSTEM_PROMPT, role='system')
            for article in articles:
                self._append_message(messages, article.params['request'])
                self._append_message(messages, article.text, role='assistant')
            self._append_message(messages, self.request)

        return messages

    def _append_message(self, messages: list, text: str, role: str='user') -> None:
        messages.append({"role": role, "content": text})
