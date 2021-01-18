import asyncio
import mqttools

asyncio.DefaultEventLoopPolicy = asyncio.WindowsSelectorEventLoopPolicy

async def subscriber():
    client = mqttools.Client('192.168.88.8', 1883)

    await client.start()
    await client.subscribe('/test/#')

    while True:
        topic, message = await client.messages.get()

        if topic is None:
            print('Broker connection lost!')
            break

        print(f'Topic:   {topic}')
        print(f'Message: {message}')

# asyncio.run(subscriber())


async def publisher():
    async with mqttools.Client('192.168.88.8', 1883) as client:
        client.publish('/test/mqttools/foo', b'bar')

#asyncio.run(publisher())






async def publish_to_self():
    client = mqttools.Client('192.168.88.8', 1883)

    await client.start()
    await client.subscribe('/test/mqttools/foo')

    client.publish('/test/mqttools/foo', b'publish_to_self message')
    topic, message = await client.messages.get()

    if topic is None:
        print('Broker connection lost!')
    else:
        print(f'Topic:   {topic}')
        print(f'Message: {message}')


asyncio.run(publish_to_self())