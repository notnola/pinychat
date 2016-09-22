""" pinychat (Legacy)"""

# Originally developed by NotNola.
# Modified by SwiftSwathSee.
# Legacy edit by GoelBiju (https://github.com/GoelBiju)

# Table of contents...(incomplete)
# INIT:
#   Python version check
#   Base room variables
# SETTINGS:
#   Default settings
#   Config file
#   Argument handling
# CLASSES:
#   Functions used by commands
# MESSAGE HANDLING:
#   If message is a user info request
#   If message is an incoming PM
#   If message is media command
#   If message is not from ignored user (i.e. all other messages)
#       Mentions
# MAIN:
#   Console colors
#   Command handling


import rtmp_protocol
import requests
import random
import os
import sys, getopt
import time
import socket
import webbrowser
from datetime import datetime
import colorama
from colorama import Fore, Style
from os import system

# Commandline options: -r ROOM -n NICK -u USERNAME -p PASSWORD -c COLOR

# Python version check: checking for 2 or 3.
if sys.version_info[0] >= 3:
    get_input = input
    import _thread
    start_new_thread = _thread.start_new_thread
    from configparser import ConfigParser, NoOptionError, NoSectionError
else:
    get_input = raw_input
    import thread
    start_new_thread = thread.start_new_thread
    from ConfigParser import ConfigParser, NoOptionError, NoSectionError

# Base room variables
roomnameArg = 0
nicknameArg = 0
usernameArg = 0
passwordArg = 0
colorArg = 0

# SETTINGS
# Default settings
defaultConfig = {
    "AUTO_OP_OVERRIDE": None,
    "PROHASH_OVERRIDE": None,
    "DefaultRoom": None,
    "DefaultNick": None,
    "useDefaultAccount": False,
    "DefaultAccountName": None,
    "DefaultAccountPass": None,
    "LOG_BASE_DIRECTORY": "log/",
    "DEBUG_CONSOLE": False,
    "DEBUG_LOG": False,
    "CHAT_LOGGING": True,
    "textEditor": "gedit",
    "highContrast": False,
    "timeOnRight": False,
    "reCaptchaShow": True,
    "windowTitlePrefix": "pinychat",
    "dateformat": "%Y-%m-%d %H:%M:%S",
    "timeformat": "%H:%M:%S",
    "delayMessage": False,
    "notificationsOn": True
}

# Regex for converting to settings.md:
# 1. Find: /^\s*?\"(.*)\"\: \"?(.*)\"?[,|$|\r\n]/     Replace: /$1 | $2 | /
# 2. Find: /\"?\, \| $/     Replace: / | /
# 3. Find: /True/     Replace: /1/
# 4. Find: /False/     Replace: /0/

# Config file:
configfileName = 'pinychat.ini'
config = ConfigParser(allow_no_value=True)
configCheck = config.read(configfileName)

if configCheck is []:  # make it if it doesn't exist
    configfile = open(configfileName, 'a')
    configfile.write("[Main]\n")
    print("Created settings file " + configfileName)
    configfile.close()
else:  # if it exists, check for the section header. todo: if add the header if needed
    configfile = open(configfileName, 'r')
    firstline = configfile.readline()
    if firstline != "[Main]\n":
        if firstline != "[Main]\r\n":
            if firstline != "[Main]":
                print("Settings file must start with '[Main]' to be used")
    configfile.close()


namespace = __import__(__name__)
for key in defaultConfig.keys():
    # turn default settings into variables
    settingName = key
    settingValue = defaultConfig[settingName]
    setattr(namespace, settingName, settingValue)

    # do the same for the config file
    makeVariable = 0
    settingValueIsString = 0
    try:
        tmpValue = config.getint("Main", settingName)
        makeVariable = 1
    except NoOptionError:
        pass
    except NoSectionError:
        pass
    except ValueError:  # if value is not a bool, it's probably a string, so use get()
        tmpValue = config.get("Main", settingName)
        makeVariable = 1
        settingValueIsString = 1

    if makeVariable == 1:
        if settingValueIsString == 0:
            if tmpValue == 1: settingValue = True
            elif tmpValue == 0: settingValue = False
            else: print("Config error: " + settingName + "must be either 1 (true) or 0 (false)")
        else: settingValue = tmpValue
        setattr(namespace, settingName, settingValue)
        # print "set " + str(settingName) + " " + str(settingValue)

if defaultConfig['useDefaultAccount'] is True and usernameArg is 0:
    usernameArg = defaultConfig['DefaultAccountName']
    passwordArg = defaultConfig['DefaultAccountPass']

if defaultConfig['DefaultRoom'] is not None and roomnameArg is 0:
    roomnameArg = defaultConfig['DefaultRoom']

if defaultConfig['DefaultNick'] is not None and nicknameArg is 0:
    nicknameArg = defaultConfig['DefaultNick']

# Argument handling
allArgs = sys.argv[1:]
quickMode = 0
if len(allArgs) is not 0:
    if allArgs[0][0] is not "-" and allArgs[1][0] is not "-":
        nicknameArg = allArgs[0]
        roomnameArg = allArgs[1]
        quickMode = 1
        allArgs.remove(nicknameArg)
        allArgs.remove(roomnameArg)
        fakedArgs = ["-n", nicknameArg, "-r", roomnameArg]  # since getopt doesn't play nicely with dashless options...
        allArgs = fakedArgs + allArgs

options, args = getopt.getopt(allArgs, "r:n:u:p:c:", ["info", "help"])
for o, a in options:
    if o is '-r':
        roomnameArg = a
    elif o is '-n':
        nicknameArg = a
    elif o is '-u':
        usernameArg = a
    elif o is '-p':
        passwordArg = a
    elif o is '-c':
        colorArg = a
    elif o is "--info" or o == "--help":
        print("\nUsage: tinychat.py -r ROOM -n NICK -u USERNAME -p PASSWORD -c COLOR")
        print("       tinychat.py NICK ROOM\n")
        raise SystemExit

# If room argument is a URL
if roomnameArg is str:
    if "tinychat.com/" in roomnameArg:
        # todo: replace this all with regex
        try:
            tmp = roomnameArg.split(".com/")[1]
            if "?" in tmp:
                tmp = tmp.split("?")[0]
            if "#" in tmp:
                tmp = tmp.split("#")[0]
            roomnameArg = tmp
        except Exception:
            pass


# Color name and color number list (the commented one)
COLORS_DICT = {
"dark blue": "#1965b6",  # 0 Color numbers
"sky blue": "#32a5d9",  # 1
"lime gray": "#7db257",  # 2
"gold": "#a78901",  # 3
"purple": "#9d5bb5",  # 4
"dark purple": "#5c1a7a",  # 5
"red": "#c53332",  # 6
"maroon": "#821615",  # 7
"gold gray": "#a08f23",  # 8
"green": "#487d21",  # 9
"pink": "#c356a3",  # 10
"blue": "#1d82eb",  # 11
"gold olive": "#919104",  # 12
"turquoise": "#00a990",  # 13
"pink gray": "#b9807f",  # 14
"lime": "#7bb224",  # 15
}

TINYCHAT_COLORS = []
firstRun = 1
colorNames = sorted(COLORS_DICT.keys())
# Dicts are unordered, this orders them and appends to TINYCHAT_COLORS so that the color numbers work.
for i in colorNames:
    if firstRun == 0:
        x += 1
    else:
        x = 0
    TINYCHAT_COLORS.append(COLORS_DICT[colorNames[x]])
    if x == 0:
        firstRun = 0


def debugPrint(msg, room="unknown_room"):
    if defaultConfig['DEBUG_CONSOLE']:
        print("DEBUG: " + msg)
    if defaultConfig['DEBUG_LOG']:
        d = defaultConfig['LOG_BASE_DIRECTORY'] + "/" + room + "/"
        if not os.path.exists(d):
            os.makedirs(d)
        logfile = open(d + "debug.log", "a")
        logfile.write(msg + "\n")
        logfile.close()


def setWindowTitle(title, firstRun=0):
    if firstRun != 0: title = windowTitlePrefix + ": " + title
    if os.name == "nt":
        system("title " + title)
    else:
        system("echo -e '\033]2;''" + title + "''\007'")


# CLASSES:
class TinychatMessage:
    def __init__(self, msg, nick, user=None, recipient=None, color=None, pm=False):
        self.msg = msg
        self.nick = nick
        self.user = user
        self.recipient = recipient
        self.color = color
        self.pm = pm

    def printFormatted(self):
        if self.pm:
            pm = "(PM) "
        else:
            pm = ""
        print(pm + self.recipient + ": " + self.nick + ": " + self.msg)


class TinychatUser:
    def __init__(self, nick, id=None, color=None, lastMsg=None):
        self.nick = nick
        self.id = id
        self.color = color
        self.lastMsg = lastMsg
        self.oper = False
        self.admin = False
        self.accountName = None
        self.swapCount = 0


class TinychatRoom:

    # Manages a single room connection
    def __init__(self, room, nick=None, username=None, passwd=None, roomPassword=None):

        self.room = room
        self.nick = nick
        self.username = username
        self.passwd = passwd
        self.roomPassword = roomPassword
        self.s = requests.session()
        self.__authHTTP()
        self.autoop = self.__getAutoOp()
        self.prohash = self.__getProHash()
        self.tcurl, self.roomtype = self.__getRTMPInfo()                # Return both the tcurl and the roomtype.
        tcurlsplits = self.tcurl.split("/tinyconf")                     # >>['rtmp://127.0.0.1:1936', '']
        tcurlsplits1 = self.tcurl.split("/")                            # >>['rtmp:', '', '127.0.0.1:1936', 'tinyconf']
        tcurlsplits2 = self.tcurl.split(":")                            # >>['rtmp', '//127.0.0.1', '1936/tinyconf']
        tcurlsplits3 = tcurlsplits1[2].split(":")                       # >>[127.0.0.1', '1936']
        self.url = tcurlsplits[0]                                       # Defining Full RTMP URL "rtmp://127.0.0.1:1936"
        self.protocol = tcurlsplits2[0]                                 # Defining RTMP Type [RTMP/RTMPE,etc]
        self.ip = tcurlsplits3[0]                                       # Defining RTMP Server IP
        self.port = int(tcurlsplits3[1])
        self.app = tcurlsplits1[3]                                      # Defining Tinychat FMS App
        self.pageurl = "http://tinychat.com/" + room                    # Defining Tinychat's Room HTTP URL
        self.swfurl = "http://tinychat.com/embed/Tinychat-11.1-1.0.0.0673.swf?version=1.0.0.0673/[[DYNAMIC]]/8"
        self.client_version = "Desktop 1.0.0.0673"
        self.flashver = "WIN 22,0,0,209"                                # static
        self.connected = False
        # self.queue = []

        # Set initial color (draft) - see section "Autoset initial color"
        # if nickColor is 0:
        #       self.color = TINYCHAT_COLORS[random.randint(0, len(TINYCHAT_COLORS) - 1)]
        # else:
        #       self.color = COLORS_DICT[nickColor]

        self.color = TINYCHAT_COLORS[random.randint(0, len(TINYCHAT_COLORS) - 1)]
        self.topic = None
        self.users = {}
        self.echo = False  # the old one
        self.echo2 = __name__ == "__main__"  # the new one!
        self.chatlogging = defaultConfig['CHAT_LOGGING']
        self.userID = None
        self.forgiveQueue = []
        self.connection = rtmp_protocol.RtmpClient(self.ip, self.port, self.tcurl, self.pageurl, self.swfurl, self.app)
        self.notificationsOn = defaultConfig['notificationsOn']
        self.pmsDict = {}
        self.mentions = [self.nick]
        self.prependMessage = ""
        self.delayMessageAmount = 1

        if defaultConfig['delayMessage']:
            self.delayMessageTrue = 1
        else:
            self.delayMessageTrue = 0

    def _recaptcha(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'en-US,en;q=0.5',
                   'DNT': 1,
                   'Connection': 'keep-alive'
        }

        url = "http://tinychat.com/cauth/captcha"
        r = self.s.request(method="GET", url=url, headers=headers, cookies=self.cookies)
        if '"need_to_solve_captcha":0' in r.text:
            self.timecookie = self.__getEncMills()
            self.connect()
        else:
            token = r.text.split('"token":"')[1].split('"')[0]
            urll = ("http://tinychat.com/cauth/recaptcha?token=" + token)
            webbrowser.open(urll)
            if self.username is None or len(self.username) is 0 or self.username is "":
                username = ""  # dupe of jf7k9... maybe make a usernameParenthesis function
            else:
                username = " (" + self.username + ")"
            if defaultConfig['reCaptchaShow']:
                print(urll)
            get_input("Ready to connect as " + ooO + self.nick + Ooo + username + " to " + ooO + self.room + Ooo +
                      ".\nPress enter when the captcha has been solved.")

            self.timecookie = self.__getEncMills()
            self.connect()

    def connect(self, force=False):
        if not self.connected or force:
            debugPrint("\n === NEW CONNECTION ===", str(self.room))
            debugPrint("Server: " + str(self.ip), str(self.room))
            debugPrint("Port: " + str(self.port), str(self.room))
            debugPrint("Tinychat URL: " + str(self.tcurl), str(self.room))
            debugPrint("URL: " + str(self.pageurl), str(self.room))
            debugPrint("App: " + str(self.app), str(self.room))
            debugPrint("Room: " + str(self.room), str(self.room))
            debugPrint("AutoOp: " + str(self.autoop), str(self.room))

            try:
                if self.username is None or len(self.username) is 0 or self.username is "":
                    username = ""  # dupe of jf7k9... maybe make a usernameParenthesis function
                else:
                    username = " (" + self.username + ")"

                # This old connection packet still works, however only on guest and not when signed in.
                # For some odd reason, connecting this way allows the 'avons', 'oper' and the old format for the
                # 'joins' packet to be sent from the server.
                # self.connection.connect([self.room, self.autoop, u'show', u'tinychat', self.username, "",
                #                          self.timecookie])

                # New format to connect to the RTMP (flash) application.
                self.connection.connect({
                    'account': self.username,
                    'type': self.roomtype,
                    'prefix': 'tinychat',
                    'room': self.room,
                    'version': self.client_version,
                    'cookie': self.timecookie})

                self.connected = True
                self._chatlog(" === Connected to " + str(self.room) + " as " + self.nick + username +
                              " === " + datetime.now().strftime(defaultConfig['dateformat']))

                self.onConnect()
                self._listen()

            except Exception:
                debugPrint("FAILED TO CONNECT", self.room)
                self.onConnectFail()

    def _listen(self):
        while self.connected:
            try:
                msg = self.connection.reader.next()
                print("-->", msg)

                if msg['msg'] == rtmp_protocol.DataTypes.SET_CHUNK_SIZE:
                    self.connection.reader.chunk_size = msg['chunk_size']
                    self.connection.writer.chunk_size = msg['chunk_size']
                    print("New chunk size:", self.connection.writer.chunk_size)
                else:
                    debugPrint("SERVER: " + str(msg), str(self.room))
                    if msg['msg'] == rtmp_protocol.DataTypes.COMMAND:
                        pars = msg['command']
                        cmd = pars[0].encode("ascii", "ignore").lower()
                        if len(pars) > 3:
                            pars = pars[3:]
                        else:
                            pars = []
                        for i in range(len(pars)):
                            if type(pars[i]) is str:
                                pars[i] = pars[i].encode("ascii", "ignore")

                        if cmd == "privmsg":
                            recipient = pars[0]
                            message = pars[1]
                            color = pars[2].lower().split(",")[0]
                            nick = pars[3]
                            m = self._decodeMessage(message)
                            if len(m) > 0:
                                if recipient[0] == "#":
                                    recipient = "^".join(recipient.split("^")[1:])
                                else:
                                    recipient = "-".join(recipient.split("-")[1:])
                                user = self._getUser(nick)
                                message = TinychatMessage(m, nick, user, recipient, color)
                                user.lastMsg = message
                                user.color = color

                                # MESSAGE HANDLING #
                                messageIsPM = 0
                                if recipient == self.nick:
                                    message.pm = True
                                    if message.msg.startswith("/msg ") and len(message.msg.split(" ")) >= 2: message.msg = " ".join(message.msg.split(" ")[2:])
                                    # If message is a userinfo request
                                    if message.msg.startswith("/userinfo ") and len(message.msg.split(" ")) >= 2:
                                        if user.nick != self.nick:
                                            ac = " ".join(message.msg.split(" ")[1:])
                                            if ac is "$request":
                                                self.onUserInfoRequest(user)
                                            else:
                                                user.accountName = ac
                                                if self.room is ac:
                                                    user.admin = True
                                                self.onUserInfo(user)

                                            message.msg = ppP+" ! "+Ppp+ssS+message.msg+Sss
                                            if str(user.nick) not in ignoreList:
                                                self.windowTitle("/userinfo: " + datetime.now().strftime(timeformat) + " (" + str(user.nick) + ")")
                                                global lastUserinfo
                                                lastUserinfo = user.nick

                                    # If message is an incoming PM
                                    else:
                                        messageIsPM = 1
                                        self.onPM(user, message)
                                        self.addToPMsDict(str(user.nick), str(message.msg), datetime.now())

                                        if timeOnRight == 1 or timeOnRight == True: # print
                                            self._chatlog(ssS+str(user.nick)+" (PM):"+Sss+" " + str(message.msg) + " [" + datetime.now().strftime(timeformat) + "]")
                                        else:
                                            self._chatlog(datetime.now().strftime(timeformat) + " " + ssS+str(user.nick)+" (PM):"+Sss+" " + str(message.msg))
                                        if str(user.nick) not in ignoreList: # window title
                                            global lastPM
                                            lastPM = str(user.nick)
                                            if len(str(message.msg)) > 160: dots = "..."
                                            else: dots = ""
                                            self.windowTitle("PM: " + datetime.now().strftime(timeformat) + " (" + lastPM + "): " + str(message.msg)[:160] + dots)
                                else:
                                    self.onMessage(user, message)

                                # If message is media command
                                if message.msg.startswith("/mbs "):
                                    tmp = message.msg.split(" ")
                                    if tmp[1] == "youTube":
                                        global lastYT
                                        lastYT = tmp[2]
                                    if tmp[1] == "soundCloud":
                                        global lastSC
                                        lastSC = tmp[2]
                                # If message is not from ignored user (i.e. all other messages)
                                if str(user.nick) not in ignoreList and messageIsPM == 0:
                                    # Mentions
                                    mentioned = 0
                                    for phrase in self.mentions:
                                        if phrase in str(message.msg):
                                            mentioned = 1
                                            # mentionedPhrase += [phrase]
                                            print(ssS+"["+phrase+"]")
                                    if timeOnRight is 1 or timeOnRight:
                                        self._chatlog(ooO+str(user.nick)+":"+Ooo+" " + str(message.msg) + " [" + datetime.now().strftime(timeformat) + "]")
                                    else:
                                        self._chatlog(datetime.now().strftime(timeformat) + " " + ooO+str(user.nick)+":"+Ooo+" " + str(message.msg))

                        elif cmd == "registered":
                            user = self._getUser(pars[0])
                            user.id = pars[1]
                            self.onRegister(user)
                            self.userID = user.id
                            user.accountName = self.username

                        elif cmd == "join":
                            user = self._getUser(pars[1])
                            user.id = pars[0]
                            self.onJoin(user)
                            tmp = 1
                            if not self.notificationsOn:
                                tmp = 0
                            self._chatlog(datetime.now().strftime(timeformat) + " " + (user.nick) + " joined " + str(self.room) + ".", tmp)

                        elif cmd == "joins":
                            for i in range((len(pars) - 1) / 2):
                                user = self._getUser(pars[i*2 + 2])
                                user.id = pars[i*2 + 1]

                        elif cmd == "joinsdone":
                            self.sendCauth(self.userID)
                            if self.nick: self.setNick()

                        elif cmd == "topic":
                            self.topic = pars[0].encode("ascii", "ignore")
                            self.onTopic(self.topic)
                            self._chatlog(datetime.now().strftime(timeformat) + " The topic of " + str(self.room) + " is now \"" + str(self.topic) + ".\"")

                        elif cmd == "nick":
                            user = self._getUser(pars[0])
                            old = user.nick
                            user.nick = pars[1]
                            if old.lower() in self.users.keys():
                                del self.users[old]
                                self.users[user.nick] = user
                            self.onNickChange(user.nick, old, user)
                            tmp = 1
                            if not self.notificationsOn:
                                tmp = 0
                            self._chatlog(datetime.now().strftime(timeformat) + " " + (old) + " is now known as " + str(user.nick) + ".", tmp)

                        elif cmd == "notice":
                            if str(pars[0]) == "avon":
                                print(datetime.now().strftime(timeformat) + " " + (pars[2]) + " is now broadcasting.")
                                user = self._getUser(pars[2])
                                user.avon = True

                        elif cmd == "avons":
                            for i in range(int((len(pars) - 1) / 2)):
                                user = self._getUser(pars[i*2 + 2])
                                user.avon = True

                        elif cmd == "quit":
                            user = self.users[pars[0]]
                            del self.users[pars[0]]
                            self.onQuit(user)
                            tmp = 1
                            if self.notificationsOn is False:
                                tmp = 0
                            self._chatlog(datetime.now().strftime(timeformat) + " " + (user.nick) + " left.", tmp)

                        elif cmd == "kick":
                            user = self.users[pars[1]]
                            self.onBan(user)
                            self._chatlog(datetime.now().strftime(timeformat) + " " + (user.nick) + " was banned.")

                        elif cmd == "banned":
                            self._chatlog(datetime.now().strftime(timeformat) + " You have been disconnected from the room.")

                        elif cmd == "oper":
                            user = self._getUser(pars[1])
                            user.oper = True

                        elif cmd == "from_owner":
                            self._chatlog(datetime.now().strftime(timeformat) + " " + pars[0].partition("notice")[2].replace("%20", " "))

            except Exception as e:
                debugPrint(str(e), self.room)

    def disconnect(self):
        if self.connected:
            self.connected = False
            try:
                self._shutdown()
            except Exception:
                pass
            self.onDisconnect()

    def _shutdown(self):
        self.connection.socket.shutdown(socket.SHUT_RDWR)

    def reconnect(self):
        self.disconnect()
        self.connected = True
        thread.start_new_thread(self._forceConnect, ())

    def _forceConnect(self):
        self.connect(True)

    def _getUser(self, nick):
        if nick not in self.users.keys():
            self.users[nick] = TinychatUser(nick)
        return self.users[nick]

    def adminsay(self, msg):
        self._sendCommand("owner_run", [u"notice" + msg.replace(" ", "%20")])
        self._chatlog("*[" + str(self.nick) + "] " + msg)

    def _decodeMessage(self, msg):
        chars = msg.split(",")
        msg = ""
        for i in chars:
            if int(i) < 128: msg += chr(int(i))
        return msg

    def _encodeMessage(self, msg):
        msg2 = []
        for i in msg:
            msg2.append(str(ord(i)))
        return ",".join(msg2)

    def _sendCommand(self, cmd, pars=[]):
        msg = {"msg": rtmp_protocol.DataTypes.COMMAND, "command": [u"" + cmd, 0, None,] + pars}
        debugPrint("CLIENT: " + str(msg), str(self.room))
        self.connection.writer.write(msg)
        self.connection.writer.flush()

# Functions used by commands
    def say(self, msg):
        if self.delayMessageTrue == 1:
            time.sleep(self.delayMessageAmount)
        msg = self.prependMessage + msg
        self._sendCommand("privmsg", [u"" + self._encodeMessage(msg), u"" + self.color + ",en"])
        self._chatlog(datetime.now().strftime(timeformat) + " " + ooO+str(self.nick)+":"+Ooo+" " + msg)

    def setPrepend(self, input):
        if input[0] == "?":
            print(ssS+"""\
Description: Manage message prepend.
Usage: /pre [OPTIONS]
    STRING   Set prepend to STRING
    !        Clear prepend
    @        Print prepend
"""+Sss)
            return
        if input[0] == "!":
            self.prependMessage = ""
            print(ssS+"--- Prepend cleared ---"+Sss)

        elif input[0] == "@":
            if self.prependMessage == "":
                print(ssS+"--- Prepend is not set ---"+Sss)
            else:
                print(ssS+"--- Prepend is: '" + self.prependMessage + "' ---"+Sss)

        elif len(input) > 0:
            string = " ".join(input[0:])
            if string.startswith("\\"):  # escape characters
                string = string[1:]
            self.prependMessage = string
            print(ssS+"--- Prepend is now: '" + self.prependMessage + "' ---"+Sss)

    def setMessageDelay(self, input):
        if input is "?":
            print(ssS+"""\
                Description: Manage message delay.
                Usage: /delay [OPTIONS]
                NUMBER   Set delay to NUMBER (seconds)
                on       Turn it on
                off      Turn it off
                """+Sss)
            return
        print(ssS)

        if input == "on":
            self.delayMessageTrue = 1
            print( ssS + "--- Message delay on ---"+Sss)
        elif input == "off":
            self.delayMessageTrue = 0
            print(ssS + "--- Message delay off ---"+Sss)
        else:
            try:
                input = float(input)
            except ValueError:
                print(ssS + "--- Value must be a number ---"+Sss)
                return
            self.delayMessageAmount = input
            print(ssS + "--- Message delay: " + str(input) + " seconds ---"+Sss)

    def setMentions(self, input):
        if input[0] == "?":
            print(ssS+"""\
            Description: Get alerts when certain phrases are mentioned.
            Usage: /alert [OPTIONS]
            + PHRASE   Add PHRASE to mentions
            - PHRASE   Remove PHRASE from mentions
            l          List mentions
            """+Sss)
            return
        print(ssS)

        cmd = input[0]
        string = " ".join(input[1:])

        if cmd == "list" or cmd == "l":
            print("--- Mentions:")
            for i in self.mentions:
                print("'"+i+"'"),
            print("--- ")

        elif cmd == "---":
            self.mentions = []
            print("--- Mentions cleared ---")

        elif cmd == "-":
            try:
                self.mentions.remove(string)
                print("--- Mention removed: '" + string + "' ---")
            except Exception:
                print("--- Error - mention doesn't exist? ---")
        elif cmd == "+":
            try:
                self.mentions.append(string)
            except Exception:
                print("--- Error ---")
            print("--- Mention added: '" + string + "' ---")
        print(Sss)

    def pm(self, msg, recipient, time=""):
        if recipient == "?":
            print(ssS+"""\
            Description: Send PM.
            Usage: /pm [USER] [MESSAGE]
            Options for USER:
            @       Latest PM sender
            @@      Latest PM recipient
            @u      Latest userinfo request
            !       Clear (no MESSAGE needed)
            list    List all PMs
            list X  List last X PMs (X=number)
            """+Sss)
            return

        if recipient == "list":
            numToShow = 0
            try:
                numToShow = int(msg)
            except ValueError:
                pass
            print(ssS+"PMs list"+Sss)

            sortedpmsDict = sorted(room.pmsDict.items())  # inefficient: maybe switch to multidimensional arrays instead of a dict, since arrays are already ordered
            indexEnd = len(sortedpmsDict)
            if numToShow > 0:
                indexStart = indexEnd-numToShow
            else:
                indexStart = 0

            for id, pm in sortedpmsDict[indexStart:indexEnd]:
                dictNick = pm[0]
                dictTime = datetime.strptime(pm[2], "%Y%m%d%H%M%S%f").strftime(timeformat)
                dictMsg = pm[1]
                print(ssS+"-"+Sss + "[" + dictTime + "] " + ooO+dictNick+": "+Ooo + dictMsg)
            return

        if recipient in room.users:
            if time == "":
                time = datetime.now()

            self._sendCommand("privmsg", [u"" + self._encodeMessage("/msg" + " " + recipient + " " + msg),
                                          self.color+",en", "n" + str(self._getUser(recipient).id) + "-" + recipient])
            self._sendCommand("privmsg", [u"" + self._encodeMessage("/msg" + " " + recipient + " " + msg),
                                          self.color+",en", "b" + str(self._getUser(recipient).id) + "-" + recipient])
            self._chatlog("(" + ppP+"@"+recipient+Ppp + ") " + ooO + str(self.nick)+":"+Ooo+" " + msg)

            global lastPMRecip
            lastPMRecip = recipient
            self.addToPMsDict(self.nick, msg, time)
        else:
            print(ssS+"--- Could not send PM: user does not exist ---"+Sss)

    def addToPMsDict(self, nick, msg, time):
        time = time.strftime("%Y%m%d%H%M%S%f")
        room.pmsDict[time] = [nick, msg, time]  # [user, msg, time]

    def windowTitle(self, title="", prefix=""):
        global windowTitlePrefix
        if title == "@?@":
            print(ssS+"""\
Description: Sets window title or title prefix
Usage: /title [OPTIONS]
    CUSTOM     Title is CUSTOM
    @          Title is nick
    @@         Prefix is nick
    @@ CUSTOM  Prefix is CUSTOM
"""+Sss)
            return
        if prefix == "":
            prefix = windowTitlePrefix
        else:
            windowTitlePrefix = prefix
        if title == "":
            title = self.nick

        prefix = str(prefix)
        # strip the start & end brackets
        if prefix.startswith("["):
            prefix = prefix[1:]
        if prefix.endswith("]"):
            prefix = prefix[:-1]

        title = str(title)
        prefix += ": "
        setWindowTitle(prefix + title)

    def setTimeformat(self, newformat):
        global timeformat
        global timeOnRight
        print(ssS)
        newformat = str(newformat).lower()
        if newformat == "?":
            print(ssS+"""\
Description: Sets timestamp format
Usage: /time [OPTIONS]
    hmss    00:00:00.00000 (H:M:S.microS)
    hms     00:00:00 (H:M:S)
    hm      00:00 (H:M)
    off     Disable timestamps
    FORMAT  Custom time format (strftime)
    R       Timestamp on right
    L       Timestamp on left
"""+Sss)
            return
        elif newformat == "hmss":
            timeformat = "%H:%M:%S.%f"
        elif newformat == "hms":
            timeformat = "%H:%M:%S"
        elif newformat == "hm":
            timeformat = "%H:%M"
        elif newformat == "off":
            timeformat = ""
        elif newformat == "r":
            timeOnRight = 1
            print("--- Timestamp now on right ---" + Sss)
        elif newformat == "l":
            timeOnRight = 0
            print("--- Timestamp now on left ---" + Sss)
        else:
            try:
                test = datetime.now().strftime(newformat)
                print("--- Timestamp preview: " + test)
                if get_input("--- Enter 'y' to apply: "+ Sss) == "y":
                    timeformat = newformat
            except:
                print("--- An error occured ---" + Sss)
        print(Sss)

    def toggleNotificationsDisplay(self, arg=""):
        if arg == "?":
            print(ssS+"""\
Description: Toggle notifications display
Usage: /notes [OPTIONS] ; If no options, toggle on or off.
    On|Off    Set on or off
"""+Sss)
            return
        status = ssS+"Notifications: "
        if arg == "":
            if self.notificationsOn == True:
                self.notificationsOn = False
                print(status + "off")
            else:
                self.notificationsOn = True
                print(status + "on")
        else:
            if arg == "on":
                self.notificationsOn = True
                print(status + "on")
            if arg == "off":
                print(status + "off")
                self.notificationsOn = False
        print(Sss)

    def userinfo(self, recipient):
        try:
            self._sendCommand("privmsg", [u"" + self._encodeMessage("/userinfo $request"), "#0" + ",en","b" +
                                          self._getUser(recipient).id + "-" + recipient])
            self._sendCommand("privmsg", [u"" + self._encodeMessage("/userinfo $request"), "#0" + ",en","n" +
                                          self._getUser(recipient).id + "-" + recipient])
        except:
            print(ssS+"--- Error getting user info. User might not exist ---"+Sss)

    def ignore(self, user):
        ignoreList.append(user)
        print(ssS+"--- Ignored " + user + " ---" + Sss)

    def unignore(self, user):
        try:
            ignoreList.remove(user)
            print(ssS+"--- Unignored " + user + " ---" + Sss)
        except:
            return

    def sendUserInfo(self, recipient, info):
        self._sendCommand("privmsg", [u"" + self._encodeMessage("/userinfo"+" "+u""+info), "#0,en" +"n" +
                                      self._getUser(recipient).id +"-"+ recipient])
        self._sendCommand("privmsg", [u"" + self._encodeMessage("/userinfo"+" "+u""+info), "#0,en" +"b" +
                                      self._getUser(recipient).id +"-"+ recipient])

    def setNick(self, nick=None):
        if not nick: nick = self.nick
        if nick not in room.users.keys():
            oldnick = self.nick
            self.nick = nick
            self._sendCommand("nick", [u"" + nick])
            room.users.pop(oldnick)
            self.windowTitle(nick)
        else: print(ssS+"--- Nick already in use ---"+Sss)

    def setTopic(self, t):
        self._sendCommand("topic", [u"" + str(t)])

    def openChatlog(self):
        self._chatlog("", "open")

    def banlist(self):
        self._sendCommand("banlist", [])

    def close(self, nick):
        if nick == "?":
            print(ssS+"""\
Description: Close a cam
Usage: /close [OPTIONS]
    NICK     Close NICK
    [blank]  If blank, close your own cam
"""+Sss)
            return
        if nick == "":
            self._sendCloseStream()  # close yours
        else:
            self._sendCommand("owner_run", [u"_close" + nick])

    def ban(self, nick):
        if nick not in self.users.keys():
            self.adminsay("That user is not in the room. When in doubt, tab it out!")
        else:
            self._sendCommand("kick", [u"" + nick, self._getUser(nick).id])

    def forgive(self, userid):
        self._sendCommand("forgive", [u"" + str(userid)])

    def forgiveName(self, n):
        self.forgiveQueue.append(n.lower())
        self.banlist()

    def playYoutube(self, video):
        if video == "?":
            print(ssS+"""\
Description: Play YouTube video
Usage: /sc [OPTIONS]
    VIDEO     Play track
    @         Open last-played video in browser
"""+Sss)
            return
        global lastYT
        if video == "@":
            if lastYT != "":
                webbrowser.open("https://www.youtube.com/watch?v=" + lastYT)
        else:
            try:
                try:
                    yt = video.split(".be/")[1][:11]
                except:
                    yt = video.split("?v=")[1][:11]
                self.say("/mbs youTube " + str(yt) + " 0")
                lastYT = str(yt)
            except:
                self.adminsay("Something went wrong, maybe that link was invalid. Try again.")

    def stopYoutube(self):
        self.say("/mbc youTube")

    def playSoundcloud(self, track):
        if track == "?":
            print(ssS+"""\
Description: Play SoundCloud track
Usage: /sc [OPTIONS]
    TRACK     Play track
    @         Open last-played track in browser
"""+Sss)
            return
        global lastSC
        if track == "@":
            if lastSC != "":
                webbrowser.open("https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/"+lastSC+"&amp;auto_play=true&amp;hide_related=false&amp;show_comments=true&amp;show_user=true&amp;show_reposts=false&amp;visual=true")
        else:
            self.say("/mbs soundCloud " + str(track) + " 0")

    def stopSoundcloud(self):
        self.say("/mbc soundCloud")

    def cycleColor(self):
        try:
            i = TINYCHAT_COLORS.index(self.color)
        except:
            i = TINYCHAT_COLORS[random.randint(0, len(TINYCHAT_COLORS) - 1)]

        i = (i + 1) % len(TINYCHAT_COLORS)
        self.color = TINYCHAT_COLORS[i]

    def selectColor(self, inputcolor):
        if inputcolor == "?":
            print(ssS + """\
Description: Sets your nick color
Usage: /color [OPTIONS]
    COLORNAME     Color name i.e. pink
    COLORNUMBER   Two-digit color number (see "COLORNUMBER list" in source)
    list          List available colors
"""+Sss)
            return
        if inputcolor == "list":
            print(ssS+"--- Available colors: " + (", ".join(COLORS_DICT.keys())) + " ---"+Sss)
            return

        currentColor = "black"
        colorBlack = 0
        newColor = inputcolor
        for i in COLORS_DICT.keys():  # Get current color name
            if COLORS_DICT[i] == self.color:
                currentColor = i
                break

        if inputcolor == "black" or inputcolor == "00":
            colorBlack = 1
            newColor = "black"

        colorInfo = ssS + "--- Color: " + newColor + " (Old: " + currentColor + ") ---" + Sss
        invalidColor = ssS+"--- Invalid color ---"+Sss
        if colorBlack == 1:
            self.color = "#000000"
            print(colorInfo)
            colorBlack = 0

        elif inputcolor in COLORS_DICT.keys(): # If existing color name
            self.color = COLORS_DICT[inputcolor]
            print(colorInfo)
        else:  # If existing color number
            try:
                i = int(inputcolor)
            except:
                print(invalidColor)
                return

            newColor = colorNames[i]
            colorInfo = ssS + "--- Color: " + newColor + " (Old: " + currentColor + ") ---" + Sss
            # Check if valid color number # todo: color nums don't work, max color num is wrong
            if i >= 0 and (i <= (len(TINYCHAT_COLORS)-1)):
                print(colorInfo)
                self.color = TINYCHAT_COLORS[i]
            else:
                print(invalidColor)
        print(Sss)

    def listUsers(self, input):
        print(ssS)
        if input == "?":
            print(ssS+"""\
Description: Lists users.
Usage: /list [OPTIONS]
    full   List full details
"""+Sss)
            return
        users = room.users
        userlist = []

        print("--- User list: "),
        for user in users.keys():
            user = users[user]
            nick = str(user.nick)
            account = str(user.accountName)
            if account == "None": userlist += [nick]
            else: userlist += [(nick + "(" + account + ")")]
        userlist = sorted(userlist)
        print(", ".join(userlist) + " ---")

        if input == "full":
            print("User list:\n---")
            for user in users.keys():
                user = users[user]
                m = None
                if user.lastMsg is not None:
                    m = user.lastMsg.msg
                print(ssS+"Nick: " + str(user.nick) + " | ID: " + str(user.id) + " | Color: " + str(user.color) +
                      " | Last Message: " + str(m) + " | Mod: " + str(user.oper) + " | Admin: " + str(user.admin) +
                      " | Account Name: " + str(user.accountName))
        print(Sss)

    def onConnect(self):
        if self.echo:
            print("You have connected to Tinychat.")

    def onConnectFail(self):
        if self.echo:
            print("You failed to connect to Tinychat.")

    def onJoin(self, user):
        if self.echo:
            print(self.room + ": " + user.nick + " entered the room.")

    def onQuit(self, user):
        if self.echo:
            print(self.room + ": " + user.nick + " left the room.")

    def onBan(self, user):
        if self.echo:
            print(self.room + ": " + user.nick + " was banned.")

    def onRegister(self, user):
        if self.echo:
            print("You have connected to " + self.room + ".")

    def onTopic(self, topic):
        if self.echo:
            print(self.room + ": Topic set to \"" + topic + "\".")

    def onUserInfo(self, user):
        if self.echo:
            print(self.room + ": Account name for nick \"" + user.nick + "\" recieved: " + user.accountName)

    def onUserInfoRequest(self, user):
        self.sendUserInfo(user.nick, self.username)

    def onMessage(self, user, message):
        if self.echo:
            message.printFormatted()

    def onPM(self, user, message):
        if self.echo:
            message.printFormatted()

    def onNickChange(self, new, old, user):
        if self.echo:
            print(self.room + ": " + old + " changed nickname to " + new + ".")

    def onNickTaken(self, nick):
        if self.echo:
            print("Nick in use, please set a different one")

    def onDisconnect(self):
        if self.echo:
            print("You have disconnected from " + self.room + ".")

    def _chatlog(self, msg, echo=1):
        if self.echo2 and echo == 1:
            print(msg)
        if echo == "open":
            logfile = defaultConfig['LOG_BASE_DIRECTORY'] + self.room + "/chatroom.log"
            if os.name == "nt":
                system('"' + logfile.replace('/', '\\') + '"')
            else:
                system(defaultConfig['textEditor'] + ' "' + logfile + '"')
        elif self.chatlogging:
            # strips ASCII escape codes added by console colors
            msg = msg.replace("[36m", "").replace("[0m", "").replace("[33m", "").replace("[1m", "")
            d = defaultConfig['LOG_BASE_DIRECTORY'] + "/" + self.room + "/"
            if not os.path.exists(d):
                os.makedirs(d)
            logfile = open(d + "chatroom.log", "a")
            logfile.write(msg + "\n")
            logfile.close()

    def _sendCreateStream(self):
        self._sendCommand("bauth", [self.__getBauth()])
        msg = {"msg": rtmp_protocol.DataTypes.COMMAND, "command": [u"" + "createStream", 12, None]}
        debugPrint("CLIENT: " + str(msg), str(self.room))
        self.connection.writer.write(msg)
        self.connection.writer.flush()

    def _sendPublish(self):
        msg = {"msg": rtmp_protocol.DataTypes.COMMAND, "command": [u"" + "publish", 0, None, u"" + self.userID, u"" + "live"]}
        debugPrint("CLIENT: " + str(msg), str(self.room))
        self.connection.writer.writepublish(msg)
        self.connection.writer.flush()

    def _sendCloseStream(self):
        msg = {"msg": rtmp_protocol.DataTypes.COMMAND, "command": [u"" + "closeStream", 0, None]}
        debugPrint("CLIENT: " + str(msg), str(self.room))
        self.connection.writer.writepublish(msg)
        self.connection.writer.flush()

    # todo - Rework this function.
    def __authHTTP(self):
        self.headers = {
            'Host': 'http://tinychat.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': 'http://tinychat.com/start/',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': 1,
            'Connection': 'keep-alive'
        }
        self.cookies = {}

        data = {
            "form_sent": "1",
            "referer": "",
            "next": "http://tinychat.com/home",
            "username": self.username,
            "password": self.passwd,
            "passwordfake": "Password",
            "remember": "1"
        }

        url = "http://tinychat.com/login"
        raw = self.s.request(method='POST', url=url, data=data, headers=self.headers, cookies=self.cookies)
        self.cookies = {}

    # todo - Rework this function.
    def __getRTMPInfo(self):
        if self.roomPassword:
            # api --> apl
            pwurl = "http://api.tinychat.com/api/find.room/" + self.room + "?site=tinychat.com&url=tinychat.com&password=" + self.roomPassword
            raw = self.s.get(pwurl)
        else:
            # api --> apl
            url = "http://api.tinychat.com/api/find.room/" + self.room + "?site=tinychat"

            raw = self.s.request(method="GET", url=url, headers=self.headers, cookies=self.cookies)

            if "result='PW'" in raw.text:
                self.roomPassword = get_input("Enter the password for room " + self.room + ": ")
                return self.__getRTMPInfo()
            else:
                roomtype = u'' + raw.text.split("roomtype='")[1].split("'")[0]
                rtmp_info = raw.text.split("rtmp='")[1].split("'")[0]
                return rtmp_info, roomtype

    def __getAutoOp(self):
        if not defaultConfig['AUTO_OP_OVERRIDE']:
            url = "http://tinychat.com/" + self.room
            raw = self.s.request(method="GET", url=url, headers=self.headers, cookies=self.cookies)
            if ", autoop: \"" in raw.text:
                r = raw.text.split(", autoop: \"")[1].split("\"")[0]
                return r
            else:
                return ""

    def __getProHash(self):
        if not defaultConfig['PROHASH_OVERRIDE']:
            url = "http://tinychat.com/" + self.room
            raw = self.s.request(method="GET", url=url, headers=self.headers, cookies=self.cookies)
            if ", prohash: \"" in raw.text:
                r = raw.text.split(", prohash: \"")[1].split("\"")[0]
                return r
            else:
                return ""

    def __getBauth(self):
        url = ("http://tinychat.com/api/broadcast.pw?nick=" + self.nick + "&site=tinychat&name=" + self.room + "&id=" + self.userID)
        r = self.s.request(method="GET", url=url)
        bauth = r.text.split("token='")[1].split("'")[0]
        return bauth

    def __getEncMills(self):
        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept': 'gzip, deflate',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': 1,
                'Connection': 'keep-alive'
        }

        mills = int(round(time.time() * 1000))
        url = "http://tinychat.com/cauth?room="+self.room+"&t="+str(mills)
        r = self.s.request(method="GET", url=url, headers=headers, cookies=self.cookies)
        return r.text.split('{"cookie":"')[1].split('"')[0]

    def sendCauth(self, userID):
        url = "http://tinychat.com/api/captcha/check.php?room=tinychat^" + self.room + "&guest_id=" + self.userID
        raw = self.s.get(url)
        if 'key":"' in raw.text:
            r = raw.text.split('key":"')[1].split('"')[0]
            rr = r.replace("\\", "")
            self._sendCommand("cauth", [u"" + rr])


# MAIN
if __name__ == "__main__":
    if roomnameArg == 0:
        roomnameArg = get_input("Enter room name: ")
    if nicknameArg == 0:
        nicknameArg = get_input("Enter nickname (optional): ")
    if quickMode == 0:
        if usernameArg == 0:
           usernameArg = get_input("Enter username (optional): ")
        if passwordArg == 0:
           passwordArg = get_input("Enter password (optional): ")

    if usernameArg == 0:
        usernameArg = ""
    if passwordArg == 0:
        passwordArg = ""

    room = TinychatRoom(roomnameArg, nicknameArg, usernameArg, passwordArg)
    setWindowTitle(nicknameArg, 1)

    # Console colors
    colorama.init()  # todo: move this whole section somewhere else
    # nicks
    if defaultConfig['highContrast']:
        ooO = Fore.CYAN + Style.BRIGHT
    else:
        ooO = Style.BRIGHT

    Ooo = Style.RESET_ALL
    # status/error
    ssS = Fore.YELLOW + Style.BRIGHT
    Sss = Style.RESET_ALL
    # PM
    ppP = Fore.YELLOW
    Ppp = Style.RESET_ALL

    lastPM = ""
    lastPMRecip = ""
    lastUserinfo = ""
    ignoreList = []
    lastYT = ""
    lastSC = ""

    # Solve the ReCaptcha.
    start_new_thread(room._recaptcha, ())

    # Wait for a connection.
    while not room.connected:
        time.sleep(1)

    # The connection once established can be used to send commands.
    while room.connected:
        # Auto-set initial color. Just does /color colorArg after connecting. Very lazy and wasteful.
        # todo: Instead set color in the init method using its nickColor arg; see section "Set initial color (draft)".
        if colorArg != 0 and colorArg != "":
            msg = "/color " + str(colorArg)
            colorArg = 0
        else:
            msg = get_input()

        if len(msg) > 0:
            if msg[0] == "/":
                msg = msg[1:]
                if len(msg) > 0:
                    parts = msg.split(" ")
                    if len(parts) == 1:
                        cmd = parts[0]
                        pars = []
                        par = ""
                    else:
                        cmd = parts[0]
                        pars = parts[1:]
                        par = " ".join(parts[1:])

                    # Command handling
                    if cmd.lower() == "publish":
                        room._sendCreateStream()
                        room._sendPublish()

                    elif cmd.lower() == "say":
                        room.say(par)

                    elif cmd.lower() == "pre":
                        room.setPrepend(pars)

                    elif cmd.lower() == "userinfo" or cmd.lower() == "whois":
                        room.userinfo(par)

                    elif cmd.lower() == "alert":
                        room.setMentions(pars)

                    elif cmd.lower() == "ignore":
                        room.ignore(par)

                    elif cmd.lower() == "unignore":
                        room.unignore(par)

                    elif cmd.lower() == "list":
                        room.listUsers(par)

                    elif cmd.lower() == "pm":
                        if len(pars) > 0:
                            pmMsg = " ".join(pars[1:])
                            pmRecip = pars[0]
                            if pmRecip == "@":
                                room.pm(pmMsg, lastPM)
                            elif pmRecip == "@@":
                                room.pm(pmMsg, lastPMRecip)
                            elif pmRecip == "@u":
                                room.pm(pmMsg, lastUserinfo)
                            elif pmRecip == "!":
                                room.windowTitle()
                            else:
                                room.pm(pmMsg, pmRecip, datetime.now())
                        else:
                            print(ssS + "Argument required." + Sss)

                    elif cmd.lower() == "what":
                        if room.username is None or room.username is 0 or room.username is "":
                            username = ""  # dupe of jf7k9... maybe make a usernameParenthesis function
                        else:
                            username = " (" + room.username + ")"
                        print(ssS + room.nick + username + " in " + room.room + Sss)

                    elif cmd.lower() == "nick":
                        room.setNick(par)

                    elif cmd.lower() == "color":
                        if len(par) > 0:
                            room.selectColor(par)
                        else:
                            room.cycleColor()

                    elif cmd.lower() == "time":
                        if len(par) > 0:
                            room.setTimeformat(par)

                    elif cmd.lower() == "title":  # todo: move this logic to windowTitle
                        if len(pars) > 0:
                            if pars[0] == "@":  # nick
                                room.windowTitle(room.nick)
                            elif pars[0].startswith("@@"):  # prefix
                                if pars[1] is not "":  # prefix = nick
                                    room.windowTitle("", pars[1:])
                                else: # prefix = par
                                    room.windowTitle("", room.nick)
                            elif pars[0] is "":  # clear
                                room.windowTitle()
                            elif pars[0] is "?":  # help
                                room.windowTitle("@?@")
                            else:
                                room.windowTitle(pars[0])

                    elif cmd.lower() == "/":
                        room.windowTitle()

                    elif cmd.lower() == "notifications" or cmd.lower() == "notes":
                        room.toggleNotificationsDisplay(par)

                    elif cmd.lower() == "close":
                        room.close(par)

                    elif cmd.lower() == "ban":
                        room.ban(par)

                    elif cmd.lower() == "quit":
                        room.disconnect()

                    elif cmd.lower() == "reconnect":
                        room.reconnect()

                    elif cmd.lower() == "playyoutube" or cmd.lower() == "yt":
                        room.playYoutube(par)

                    elif cmd.lower() == "stopyoutube":
                        room.stopYoutube()

                    elif cmd.lower() == "playsoundcloud" or cmd.lower() == "sc":
                        room.playSoundcloud(par)

                    elif cmd.lower() == "stopsoundcloud":
                        room.stopSoundcloud()

                    elif cmd.lower() == "banlist":
                        room.banlist()

                    elif cmd.lower() == "forgive":
                        room.forgive(par)

                    elif cmd.lower() == "forgivename":
                        room.forgiveName(par)

                    elif cmd.lower() == "topic":
                        room.setTopic(par)

                    elif cmd.lower() == "adminsay" or cmd.lower() == "a":
                        room.adminsay(par)

                    elif cmd.lower() == "sys":
                        system(" ".join(pars))

                    elif cmd.lower() == "log":
                        room.openChatlog()

                    elif cmd.lower() == "delay":
                        room.setMessageDelay(par)
            else:
                room.say(msg)
