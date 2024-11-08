import discord
import toml

with open('config.toml', 'r') as f:
    config = toml.load(f)

token = config["discord"]["APP_KEY"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    user = await client.fetch_user("480182798989393950")
    await user.send('helloo')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

async def message_member(user_id, msg):
    user = await client.fetch_user(user_id)
    await user.send(msg)

def start_bot():
    client.run(token)

if __name__ == "__main__":
    start_bot()