# Twtsted Imports
from twisted.python import log
from logbot.common.utils import filteringObserver
from twisted.python.logfile import DailyLogFile

# Local Imports
from logbot.config import settings
from logbot.bot import LeapBotFactory


def main():
    from twisted.internet import reactor

    irc_log = DailyLogFile(settings.LOG_ROOT + settings.IRC_LOGFILE,
                           settings.LOG_ROOT)
    system_log = DailyLogFile(settings.LOG_ROOT + settings.SYSTEM_LOGFILE,
                              settings.LOG_ROOT)

    irc_observer = log.FileLogObserver(irc_log)
    system_observer = log.FileLogObserver(system_log)

    log.addObserver(filteringObserver(system_observer.emit, "system"))
    log.addObserver(filteringObserver(irc_observer.emit, "irc"))

    reactor.connectTCP(settings.HOST, settings.PORT, LeapBotFactory(settings.CHANNEL))
    reactor.run()


if __name__ == "__main__":
    main()
