from discord.ext import commands
from source_code.bots.discord.discord_bot import DiscordBot


class DiscordCommands(commands.Cog):
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    # получение id сервера/гильдии
    @commands.command(name='get_guild_id')
    async def get_guild_id(self, ctx):
        await ctx.send(f'Server id: {ctx.guild.id}')
