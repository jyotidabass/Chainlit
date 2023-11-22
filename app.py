import asyncio

import chainlit as cl

from chain import Chain


@cl.on_chat_start
async def start_chat():
    chain = Chain(None)
    await chain.text("I will count to 5. How many concurrent times should I count?")


@cl.on_message
async def on_message(message: str, message_id: str):
    chain = Chain(message_id)

    try:
        num = int(message)
    except ValueError:
        await chain.text_stream("Sorry, that doesn't look like an integer to me.", final=True)
        return

    if num > 10:
        await chain.text_stream("Whoa, let's try a smaller number. (Max 10.)", final=True)
        return

    await chain.text("Alright, here we go:")
    coroutines = []
    for i in range(num):
        coroutines.append(chain.text_stream("1 2 3 4 5", delay=1, name=f"Counter {i + 1}"))
    await asyncio.gather(*coroutines)
    await chain.text_stream("Okay, I'm done counting now.", final=True)
