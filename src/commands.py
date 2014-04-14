"""
Commands for Bot and command related helper functions.
"""

import settings


def give_help():
    help_text = "Available commands are: "
    for command in sorted(COMMANDS.iterkeys()):
        help_text += command + ", "
    help_text = help_text[:-2] + ". Syntax: '!give <nick> <command>' or !<command> <command_parameters>"
    return help_text

def give_paste():
    return "Use a pastebin for code snippets. You can try, http://bpaste.net/"\
        "or http://pastebin.com/"

def give_pastebinit():
    return "Use pastebinit to paste directly from the commandline."\
        "Syntax: 'command | pastebinit'"

def give_ask():
    return "Do not ask to ask. Also read this on how to ask smart questions ->"\
        "http://www.catb.org/esr/faqs/smart-questions.html"

def give_patient():
    return "Be patient. When someone who can answer your queries is availabe,"\
        "will surely respond. Not everyone is in the same time zone."

def give_seen():
    return "Use this to check when a user was last seen. Syntax: !seen <nick>"

def give_source():
    return "You can view the source here: " + settings.REPO_URL

COMMANDS = {
    "help": give_help,
    "paste": give_paste,
    "pastebinit": give_pastebinit,
    "ask": give_ask,
    "patient": give_patient,
    "seen": give_seen,
    "source": give_source,
}

