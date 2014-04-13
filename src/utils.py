"""
Utilities for IRC Bot.
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta

def filteringObserver(target, observerName):
    """
    Returns the observer instance of twisted.python.log
    """
    def observer(e):
        if e.get("observer") == observerName:
            target(e)
    return observer


def format_username(username):
    """
    Returns a cleaned up version of username. Typically a username is expected
    to be of the format 'username!~userscomputername@some_ip'.
    """
    return username.split("!")[0]


def calculate_time_difference(timestamp):
    """
    Returns a formatted datetime string of the difference between supplied
    timestamp and current time.
    
    :param timestamp: <type datetime.datetime>
    """
    if not isinstance(timestamp, datetime):
        raise TypeError("parameter timestamp is of %s. "\
                        "Expected type datetime.datetime" % type(timestamp))

    timedelta = relativedelta(datetime.utcnow(), timestamp)
    properties = timedelta.__dict__
    msg = ""
    keys = ["years", "months", "days", "hours", "minutes", "seconds"]
    non_zero_keys = []
    for key in keys:
        if properties[key] and properties[key] != 0:
            non_zero_keys.append(key)

    for i in range(len(keys)):
        pass
    for i in range(len(non_zero_keys)):
        key = non_zero_keys[i]
        value = properties[key]
        if value == 1:
            key = key[:-1]

        if len(non_zero_keys) == 1:
            return str(value) + " " + key + " ago."
        if i == len(non_zero_keys) - 1:
            msg = msg[:-2] + " and " + str(value) + " " + key + " ago."
        else:
            msg = msg + " " + str(value) + " " + key + ", "

    if msg:        
        return msg
    else:
        return "just now."

