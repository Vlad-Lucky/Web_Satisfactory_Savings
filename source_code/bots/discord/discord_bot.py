import discord
from discord.ext.commands.bot import BotBase
from source_code.constants import MAIN_DISCORD_GUILD_ID


class DiscordBot(BotBase, discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sessionStorage = {}

    # проверка, находится ли пользователь в формате <name>#<discriminator> на главном сервере
    def is_guilder(self, discord_login) -> bool:
        guild = self.get_guild(MAIN_DISCORD_GUILD_ID)
        if guild is None:
            return False
        members = [f'{member.name}#{member.discriminator}' for member in guild.members]
        return discord_login in members
