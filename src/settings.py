import os.path

# General settings
PROJECT_ROOT = os.path.dirname("%s/../" % os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath("%s/../" % os.path.dirname(__file__))

# IRC settings
HOST = "irc.freenode.net"
PORT = 6667
USE_SSL = False
NICKNAME = "leapbot"
REALNAME = "bot: logs #leap channel"

CHANNEL = "#test_leapbot"

WELCOME_MSG = "Hello %s, I am a logging bot. Also try '!help' to know more about me."


# Log Settings
LOG_ROOT = "%s/logs/" % (PROJECT_ROOT)
IRC_LOGFILE = "irc.log"
SYSTEM_LOGFILE = "system.log"


#Database Settings
DATABASE_NAME = "irc.db"
DATABASE_PATH = "%s/%s" % (PROJECT_ROOT, DATABASE_NAME)

