import discord
from discord import app_commands

from tracking import track as t
from mapping import map
token = "OTc5NTA4MTU5MjYzNjk4OTY0.GURUVW.OyRLT6Ja4VA131ebCb3-Idono4D3VimfC3ZWG0"
intents = discord.Intents.default()
intents.message_content = True
test_guild = discord.Object(id="951678432494911528")
application_id = 979508159263698964

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, application_id: int):
        super().__init__(intents=intents, application_id=application_id)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=test_guild)
        await self.tree.sync(guild=test_guild)

# In order to use a basic synchronization of the app commands in the setup_hook,
# you have to replace the 0 with your bot's application_id that you find in the developer portal.
client = MyClient(intents=intents, application_id=application_id)

#client.tree.add_command(Special(), guild=test_guild)

@client.tree.command()
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Still here!")

@client.tree.command()
async def track(interaction: discord.Interaction, bus: int):
    await interaction.response.send_message("Tracking...")
    await t(bus)
    await interaction.channel.send_message("Done tracking bus {}.".format(bus))

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online)
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    for guild in client.guilds:
        print(guild.name)


client.run(token)
