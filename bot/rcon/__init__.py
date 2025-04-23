from .manager import PavlovRCONManager
from bot.utils import servers

rcon = PavlovRCONManager(servers=servers)

__all__ = (
    'rcon'
)