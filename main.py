import threading
from source_code.site import site_session
from source_code.bots.discord import discord_session


# запуск flask-сайта
thread = threading.Thread(target=site_session.run)
thread.start()
# запуск дискорд бота
discord_session.run()
