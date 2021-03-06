import os.path

# General settings
# PROJECT_ROOT = os.path.dirname("%s/../" % os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath("%s/../../" % os.path.dirname(__file__))
REPO_URL = "https://github.com/indradhanush/LeapBot"

# Bot Settings
CHANNEL = "#test_leapbot"
WELCOME_MSG = "Hello %s, I am a logging bot. Also try '!help' to know more about me."


# IRC settings
HOST = "irc.freenode.net"
PORT = 6667
USE_SSL = False
NICKNAME = "logbot"
REALNAME = "bot: logs %s channel on %s." % (CHANNEL, HOST)


# Log Settings
LOG_ROOT = "%s/logs/" % (PROJECT_ROOT)
IRC_LOGFILE = "irc.log"
SYSTEM_LOGFILE = "system.log"
LOG_URL = "http://gsocinfo.dhanush.kd.io/logs/irc.log"


# Database Settings
DATABASE_NAME = "irc.db"
DATABASE_PATH = "%s/%s" % (PROJECT_ROOT, DATABASE_NAME)

