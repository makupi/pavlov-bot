from bot import bot  
from bot.utils import config

def run():
    bot.run(config.token) 

if __name__ == "__main__":
    run()
