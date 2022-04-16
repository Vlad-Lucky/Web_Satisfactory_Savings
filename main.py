import threading
from source_code.site.site_session import run
from source_code.bots.discord import discord_session


# запуск flask-сайта
thread = threading.Thread(target=run)
thread.start()
# запуск дискорд бота
discord_session.run()
