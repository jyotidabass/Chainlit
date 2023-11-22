import asyncio
import os
import re

import chainlit as cl
import openai
from chainlit import LLMSettings
from chainlit.config import config


# TODO each chain should be able to make a child chain?
# root = Chain()
# first = root.child("something")
# first.llm('foo')
class Chain:
    def __init__(self, message_id: str | None, llm_settings: LLMSettings | None = None):
        self.llm_settings = llm_settings
        self.root_id = message_id

    def make_message(self, name, final, **kwargs) -> cl.Message:
        if not name:
            name = config.ui.name if final else "Child Chain"
        return cl.Message(
            author=name,
            parent_id=None if final else self.root_id,
            **kwargs,
        )

    async def text(self, text, final=False, name=None):
        message = self.make_message(content=text, final=final, name=name)
        await message.send()

    async def text_stream(self, text: str, delay=.1, name=None, final=False):
        message = self.make_message(content='', final=final, name=name)
        tokens = text.split(" ")
        first = True
        for token in tokens:
            if not first:
                token = " " + token
            await message.stream_token(token)
            await asyncio.sleep(delay)
            first = False
        await message.send()

    async def llm(self, template, *args, name=None, final=False, **kwargs) -> str:
        variables = re.findall(r'\{(.*?)}', template)
        if len(args) > 1:
            raise RuntimeError("If there is more than one argument, use kwargs")
        if len(args) > 0 and len(kwargs) > 0:
            raise RuntimeError("Cannot combine args and kwargs")
        if len(args) > 0:
            if len(variables) > 1:
                raise RuntimeError("This chain expects more than one argument. Use kwargs instead.")
            variable_dict = {variables[0]: args[0]}
        else:
            variable_dict = kwargs

        prompt = template.format(**variable_dict)
        message = self.make_message(content='', name=name, prompt=prompt, llm_settings=self.llm_settings, final=final)

        async for response in await openai.ChatCompletion.acreate(
                **self.llm_settings.to_settings_dict(), api_key=os.environ.get('OPENAI_API_KEY'), stream=True,
                messages=[{'role': 'user', 'content': prompt}]
        ):
            token = response.choices[0]["delta"].get("content", "")
            await message.stream_token(token)

        await message.send()
        return message.content
