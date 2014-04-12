#Twisted Imports
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.words.protocols import irc
from twisted.python import log
from twisted.python.logfile import DailyLogFile
from twisted.enterprise import adbapi

#System Imports
import sys
import time
from datetime import datetime

# Local Imports
import settings
from commands import COMMANDS
from utils import filteringObserver, format_username, calculate_time_difference

dbpool = adbapi.ConnectionPool("sqlite3", settings.DATABASE_NAME)

class LeapBot(irc.IRCClient):

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
        log.msg("Signed onto %s on Port %s" % (settings.HOST, settings.PORT),
                observer="system")

    def joined(self, channel):
        """Called when the bot joins the channel."""
        self.channel = channel
        log.msg("%s joined channel %s" % (settings.NICKNAME, channel),
                observer="system")

    def privmsg(self, user, channel, msg):
        """Called when the bot receives a message."""
        time_string = datetime.strftime(datetime.utcnow(), "%c")
        log.msg("%s: %s" % (format_username(user), msg), observer="irc")
        self.update_last_seen(format_username(user), time_string,
                              msg).addCallback(self.verify_update)

        # If the message starts with '!', it may be a command.
        reply = ""
        if msg.startswith("!"):
            msg = msg[1:].split()
            if msg[0] == "give" and len(msg) == 3:
                nick, command = msg[1], msg[2]
                reply = "%s: %s" % (nick, COMMANDS[command])
            elif msg[0] in COMMANDS.keys():
                command = msg[0]
                if command == "seen":
                    if len(msg) == 1:
                        reply = "%s: %s" % (format_username(user),
                                            COMMANDS[command])
                    elif len(msg) == 2:    
                        nick = msg[1]
                        answer = self.get_last_seen(nick, user).addCallback(self.show_last_seen)
                else:
                    reply = "%s" % (COMMANDS[msg[0]])
            self.say(channel, reply)
        elif settings.NICKNAME in msg:
            reply = settings.WELCOME_MSG % (format_username(user))
            self.say(channel, reply)
            log.msg("%s: %s" % (settings.NICKNAME, reply), observer="irc")
        
        if reply:
            log.msg(reply, observer="irc")

    def userJoined(self, user, channel):
        """Called when a user joins the channel."""
        # TODO: Maybe send messages stored for the user
        log.msg("%s has joined #%s." % (format_username(user), channel),
                observer="irc")

    def userLeft(self, user, channel):
        """Called when a user leaves the channel."""
        log.msg("%s has left #%c." % (format_username(user), channel),
                observer="irc")

    def action(self, user, channel, data):
        """Called when a user performs an ACTION on the channel."""
        log.msg("* %s %s" % (format_username(user), data), observer="irc")

    def userRenamed(self, oldname, newname):
        """Called when a user changes their name."""
        log.msg("%s is now known as %s." % (oldname, newname), observer="irc")

    # IRC Callbacks
    def alterCollideNick(self, nickname):
        """Appends '_' if nickname is not available."""
        log.msg("Nickname %s is not available. Appending '_'. " % (nickname),
                observer="system")
        return nickname + '_'

    # DB Interaction
    def _get_last_seen(self, interact, nick, user):
        interact.execute("SELECT * FROM last_seen WHERE nick = ?", (nick, ))
        result = interact.fetchone()
        if result:
            return [result, user, nick]
        else:
            return [None, user, nick]

    def get_last_seen(self, nick, user):
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
            reply = "%s: Why do you want to do that? Try this on some"\
                    "other user." % (nick)
        elif nick == self.nickname:
            reply = "%s: I'm always here! Try !help." % (format_username(user))
        elif result:
            #Unpacking Tuple returned by DB query.
            time_string, last_msg = [str(result[i]) for i in range(1, 3)]
            time_string = datetime.strptime(time_string, "%c")
            reply = "%s: %s was last seen on channel %s %s -> <%s>: %s"\
                    % (format_username(user), nick, self.channel,
                       calculate_time_difference(time_string), nick, last_msg)
        else:
            reply = "%s: I have not seen %s yet. Try asking around."\
                    % (format_username(user), nick)
        self.say(self.channel, reply)
        log.msg(reply, observer="irc")

    def _update_last_seen(self, interact, nick, time, last_msg):
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
        return dbpool.runInteraction(self._update_last_seen, nick, time, last_msg)
    
    def verify_update(self, result):
        if result:
            return
        else:
            log.msg("Failed to update last_seen.", observer="system")

class LeapBotFactory(ReconnectingClientFactory):
    
    def __init__(self, channel):
        self.channel = channel

    def buildProtocol(self, address):
        protocol = LeapBot(settings.NICKNAME, settings.REALNAME)
        protocol.factory = self
        return protocol

    def clientConnectionLost(self, connector, reason):
        log.msg("Connection Lost: %s" % (reason), observer="system")
        log.msg("Attempting to reconnect...", observer="system")
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection Failed: %s" % (reason), observer="system")
        log.msg("Attempting to reconnect...", observer="system")
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)


def main():
    from twisted.internet import reactor

    #irc_log = open(settings.LOG_ROOT + settings.IRC_LOGFILE, "a")
    #system_log = open(settings.LOG_ROOT + settings.SYSTEM_LOGFILE, "a")
    irc_log = DailyLogFile(settings.LOG_ROOT + settings.IRC_LOGFILE,
                           settings.LOG_ROOT)
    system_log = DailyLogFile(settings.LOG_ROOT + settings.IRC_LOGFILE,
                              settings.LOG_ROOT)

    irc_observer = log.FileLogObserver(irc_log)
    system_observer = log.FileLogObserver(system_log)

    log.addObserver(filteringObserver(system_observer.emit, "system"))
    log.addObserver(filteringObserver(irc_observer.emit, "irc"))

    reactor.connectTCP(settings.HOST, settings.PORT, LeapBotFactory(settings.CHANNEL))
    reactor.run()


if __name__ == "__main__":
    main()

