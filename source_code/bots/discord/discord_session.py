import discord
from source_code.constants import DISCORD_BOT_TOKEN
from source_code.bots.discord.discord_bot import DiscordBot
from source_code.bots.discord.discord_commands import DiscordCommands


__factory = None


# получение активного дискорд бота
def get_discord_session() -> DiscordBot:
    if not __factory:
        raise Exception("Необходимо запустить дискорд бота.")
    return __factory


# запуск дискорд бота
def run():
    global __factory

    if not __factory:
        # устанавливаем зависимости для бота
        intents = discord.Intents.default()
        intents.members = True
        # запуск бота
        bot = DiscordBot(command_prefix='/', intents=intents)
        bot.add_cog(DiscordCommands(bot))
        # устанавливаем глобальную переменную боту
        __factory = bot
        # запуск бота
        bot.run(DISCORD_BOT_TOKEN)


if __name__ == '__main__':
    run()
