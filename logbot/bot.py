# System Imports
import sys
import time
from datetime import datetime

# Twisted Imports
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.words.protocols import irc
from twisted.python import log
from twisted.python.logfile import DailyLogFile
from twisted.enterprise import adbapi
from twisted.web.client import getPage

# Other Imports
from bs4 import BeautifulSoup

# Local Imports
from logbot.config import settings
from logbot.commands import COMMANDS
from logbot.common.utils import format_username, calculate_time_difference


dbpool = adbapi.ConnectionPool("sqlite3", settings.DATABASE_NAME, check_same_thread=False)


class LogBot(irc.IRCClient):

    def __init__(self, nickname, realname):
        self.nickname = nickname
        self.realname = realname
        self.channel = None
    
    def connectionMade(self):
        """Called when a connection is made."""
        irc.IRCClient.connectionMade(self)
        log.msg("Connection Established.", observer="system")

    # def connectionLost(self, reason):
    #     """Called when a connection is lost."""
    #     irc.IRCClient.connectionLost(self, reason)
    #     log.msg("Connection Lost: %s" % (reason), observer="system")

    # Event Callbacks
    def signedOn(self):
        """Called when the bot has successfully signed on to the server."""
        self.join(self.factory.channel)
        log.msg("Signed onto {0} on Port {1}".format(settings.HOST, settings.PORT),
                observer="system")

    def joined(self, channel):
        """Called when the bot joins the channel."""
        self.channel = channel
        log.msg("{0} joined channel {1}".format(self.nickname, channel),
                observer="system")

    def privmsg(self, user, channel, msg):
        """Called when the bot receives a message."""
        time_string = datetime.strftime(datetime.utcnow(), "%c")
        log.msg("{0}: {1}".format(format_username(user), msg), observer="irc")
        self.update_last_seen(format_username(user), time_string,
                              msg).addBoth(self.verify_update)

        # If the message starts with '!', it may be a command.
        reply = ""
        if msg.startswith("!"):
            msg = msg[1:].split()
            if msg[0] == "give" and len(msg) == 3 and msg[2] in COMMANDS.keys():
                nick, command = msg[1], msg[2]
                reply = "{0}: {1}".format(nick, COMMANDS[command]())
            elif msg[0] in COMMANDS.keys():
                command = msg[0]
                if len(msg) == 1:
                    reply = COMMANDS[command]()
                elif command == "seen" and len(msg) == 2:
                    nick = msg[1]
                    answer = self.get_last_seen(nick, user).addCallback(self.show_last_seen)
            self.say(channel, reply)
        elif "http" in msg:
            key = "http"
            for word in msg.split():
                if key in word:
                    url = word[word.index(key):]
                    d = getPage(url)
                    d.addCallback(self.callbackGetTitle).addErrback(
                        self.errbackGetTitle)
        elif self.nickname in msg:
            reply = settings.WELCOME_MSG % (format_username(user))
            self.say(channel, reply)
             
        if reply:
            log.msg("{0}: {1}".format(self.nickname, reply), observer="irc")

    def userJoined(self, user, channel):
        """Called when a user joins the channel."""
        # TODO: Maybe send messages stored for the user
        log.msg("{0} has joined {1}.".format(format_username(user), channel),
                observer="irc")

    def userLeft(self, user, channel):
        """Called when a user leaves the channel."""
        log.msg("{0} has left {1}.".format(format_username(user), channel),
                observer="irc")

    def userQuit(self, user, channel):
        """Called when a user quits the channel."""
        log.msg("{0} has quit {1}.".format(format_username(user), channel),
                observer="irc")

    def action(self, user, channel, data):
        """Called when a user performs an ACTION on the channel."""
        log.msg("* {0} {1}".format(format_username(user), data), observer="irc")

    def userRenamed(self, oldname, newname):
        """Called when a user changes their name."""
        log.msg("{0} is now known as {1}.".format(oldname, newname), observer="irc")

    # IRC Callbacks
    def alterCollideNick(self, nickname):
        """Appends '_' if nickname is not available."""
        log.msg("Nickname {0} is not available. Appending '_'. ".format(nickname),
                observer="system")
        self.nickname += '_'
        return self.nickname

    # DB Interaction
    def _get_last_seen(self, interact, nick, user):
        """
        Method that runs in a separate thread. Called by dbpool.runInteraction
        in get_last_seen method.
        """
        interact.execute("SELECT * FROM last_seen WHERE nick = ?", (nick, ))
        result = interact.fetchone()
        if result:
            return [result, user, nick]
        else:
            return [None, user, nick]

    def get_last_seen(self, nick, user):
        """
        Used to fetch the last_seen parameter of a user.
        """
        return dbpool.runInteraction(self._get_last_seen, nick, user)

    def show_last_seen(self, result):
        """
        Callback for get_last_seen method.
        """
        reply = ""
        nick = result.pop()
        user = result.pop()
        result = result[0]
        if nick == format_username(user):
            reply = "{0}: Why do you want to do that? Try this on some"\
                    "other user.".format(nick)
        elif nick == self.nickname:
            reply = "{0}: I'm always here! Try !help.".format(format_username(user))
        elif result:
            #Unpacking Tuple returned by DB query.
            time_string, last_msg = [str(result[i]) for i in range(1, 3)]
            time_string = datetime.strptime(time_string, "%c")
            reply = "{0}: {1} was last seen on channel {2} {3} -> <{4}>: {5}"\
                    .format(format_username(user), nick, self.channel,
                            calculate_time_difference(time_string), nick, last_msg)
        else:
            reply = "{0}: I have not seen {1} yet. Try asking around."\
                    .format(format_username(user), nick)
        self.say(self.channel, reply)
        log.msg(reply, observer="irc")

    def _update_last_seen(self, interact, nick, time, last_msg):
        """
        Method that runs in a separate thread. Called by dbpool.runInteraction
        in update_last_seen method.
        """
        interact.execute("SELECT * FROM last_seen WHERE nick = ?", (nick, ))
        result = interact.fetchone()
        if result:
            interact.execute("UPDATE last_seen SET time = ?, last_msg = ?\
                             WHERE nick = ?", (time, last_msg, nick))
        else:
            interact.execute("INSERT INTO last_seen VALUES (?, ?, ?)",
                             (nick, time, last_msg))
        return True

    def update_last_seen(self, nick, time, last_msg):
        """
        Updates the last_seen parameter of a user.
        """
        return dbpool.runInteraction(self._update_last_seen, nick, time, last_msg)
    
    def verify_update(self, result):
        """
        Callback for update_last_seen method.
        """
        if result:
            return
        else:
            log.msg("Failed to update last_seen.", observer="system")

    def callbackGetTitle(self, result):
        """
        Callback method for twisted.web.client.getPage.
        """
        soup = BeautifulSoup(result)
        reply = str(soup.title.string)
        reply = "Title: {0}".format(reply)
        self.say(self.channel, reply)
        log.msg("{0}: {1}".format(self.nickname, reply), observer="irc")

    def errbackGetTitle(self, failure):
        """
        Errback method for twisted.web.client.getPage.
        """
        # Fail Silently.
        pass


class LogBotFactory(ReconnectingClientFactory):
    
    def __init__(self, channel):
        self.channel = channel

    def buildProtocol(self, address):
        protocol = LogBot(settings.NICKNAME, settings.REALNAME)
        protocol.factory = self
        return protocol

    def clientConnectionLost(self, connector, reason):
        log.msg("Connection Lost: {0}".format(reason), observer="system")
        log.msg("Attempting to reconnect...", observer="system")
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection Failed: {0}".format(reason), observer="system")
        log.msg("Attempting to reconnect...", observer="system")
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

