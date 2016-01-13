# Commandline options: -r ROOM -n NICK -u USERNAME -p PASSWORD -c COLOR
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
from colorama import Fore, Back, Style
from os import system

AUTO_OP_OVERRIDE = None
PROHASH_OVERRIDE = None

# SETTINGS #
LOG_BASE_DIRECTORY = "log/"
DEBUG_CONSOLE = False
DEBUG_LOG = False
CHAT_LOGGING = True # do not enable here and bot
highContrast = False
timeOnRight = False
reCaptchaShow = False

# cheking for python 2 or 3; ensuring use with both versions
if sys.version_info[0] >= 3:
    get_input = input
    import _thread
    start_new_thread = _thread.start_new_thread
else:
    get_input = raw_input
    import thread
    start_new_thread = thread.start_new_thread

dateformat = "%Y-%m-%d %H:%M:%S"
timeformat = "%H:%M:%S"

# Argument handling
roomnameArg = 0
nicknameArg = 0
usernameArg = 0
passwordArg = 0
colorArg = 0

allArgs = sys.argv[1:]
if len(allArgs) == 2:
    nicknameArg = allArgs[0]
    roomnameArg = allArgs[1]
else:
    options, args = getopt.getopt(allArgs,"r:n:u:p:c:x:f:",["info", "help"])
    for o, a in options:
        if o == '-r':
            roomnameArg = a
        elif o == '-n':
            nicknameArg = a
        elif o == '-u':
            usernameArg = a
        elif o == '-p':
            passwordArg = a
        elif o == '-c':
            colorArg = a
        elif o == '-x':
            repeatTarget = a
        elif o == '-f':
            fakeUsername = a
        elif o == "--info" or o == "--help":
            print("\nUsage: tinychat.py -r ROOM -n NICK -u USERNAME -p PASSWORD -c COLOR")
            print("       tinychat.py NICK ROOM\n")
            raise SystemExit

# COLORNAME and COLORNUMBER list (the commented one)
COLORS_DICT = { 
"dark blue": "#1965b6", #0 Color numbers
"sky blue": "#32a5d9", #1
"lime gray": "#7db257", #2
"gold": "#a78901", #3
"purple": "#9d5bb5", #4
"dark purple": "#5c1a7a", #5
"red": "#c53332", #6
"maroon": "#821615", #7
"gold gray": "#a08f23", #8
"green": "#487d21", #9
"pink": "#c356a3", #10
"blue": "#1d82eb", #11
"gold olive": "#919104", #12
"turquoise": "#00a990", #13
"pink gray": "#b9807f", #14
"lime": "#7bb224", #15
}
TINYCHAT_COLORS = []
firstRun = 1
colorNames = sorted(COLORS_DICT.keys())
for i in colorNames: # Dicts are unordered, this orders them and appends to TINYCHAT_COLORS so that the color numbers work
    if firstRun == 0:
        x += 1
    else:
        x = 0
    TINYCHAT_COLORS.append( COLORS_DICT[colorNames[x]] )
    if x == 0:
        firstRun = 0

def debugPrint(msg, room="unknown_room"):
    if DEBUG_CONSOLE:
        print("DEBUG: " + msg)
    if DEBUG_LOG:
        d = LOG_BASE_DIRECTORY + "/" + room + "/"
        if not os.path.exists(d):
            os.makedirs(d)
        logfile = open(d + "debug.log", "a")
        logfile.write(msg + "\n")
        logfile.close()

def initWindowTitle(title): # find a way to replace this with TinychatRoom.setWindowTitle()
    if os.name == "nt":
        system("title " + title)
    else:
        system("echo -e '\033]2;'" + title + "'\007'")

class TinychatMessage():
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

class TinychatUser():
    def __init__(self, nick, id=None, color=None, lastMsg=None):
        self.nick = nick
        self.id = id
        self.color = color
        self.lastMsg = lastMsg
        self.oper = False
        self.admin = False
        self.accountName = None
        self.swapCount = 0

class TinychatRoom():
    # Manages a single room connection
    def __init__(self, room, username=None, nick=None, passwd=None, roomPassword=None):
        self.room = room
        if username == None:
            self.username = ""
        else:
            self.username = username
        self.nick = nick
        self.passwd = passwd
        self.roomPassword = roomPassword
        self.s = requests.session()
        self.__authHTTP()
        self.autoop = self.__getAutoOp(room)
        self.prohash = self.__getProHash(room)
        self.tcurl = self.__getRTMPInfo()
        tcurlsplits = self.tcurl.split("/tinyconf")                     # >>['rtmp://127.0.0.1:1936', '']
        tcurlsplits1 = self.tcurl.split("/")                            # >>['rtmp:', '', '127.0.0.1:1936', 'tinyconf']
        tcurlsplits2 = self.tcurl.split(":")                            # >>['rtmp', '//127.0.0.1', '1936/tinyconf']
        tcurlsplits3 = tcurlsplits1[2].split(":")                       # >>[127.0.0.1', '1936']
        self.url = tcurlsplits[0]                                       # Defining Full RTMP URL "rtmp://127.0.0.1:1936"
        self.protocol = tcurlsplits2[0]                                 # Defining RTMP Type [RTMP/RTMPE,etc]
        self.ip = tcurlsplits3[0]                                       # Defining RTMP Server IP
        self.port = int(tcurlsplits3[1])
        self.app = tcurlsplits1[3]                                      # Defining Tinychat FMS App
        self.pageurl = "http://tinychat.com/" + room                    # Definging Tinychat's Room HTTP URL
        self.swfurl = "http://tinychat.com/embed/Tinychat-11.1-1.0.0.0632.swf?version=1.0.0.0632/[[DYNAMIC]]/8" #static
        self.flashver = "WIN 16,0,0,257"                                # static
        self.connected = False
        # self.queue = []
        
        # Set initial color (draft) - see section "Autoset initial color"
        # if nickColor == 0:
            # self.color = TINYCHAT_COLORS[random.randint(0, len(TINYCHAT_COLORS) - 1)]
        # else:
            # self.color = COLORS_DICT[nickColor]
        
        self.color = TINYCHAT_COLORS[random.randint(0, len(TINYCHAT_COLORS) - 1)]
        self.topic = None
        self.users = {}
        self.echo = False # the old one
        self.echo2 = __name__ == "__main__" # the new one!
        self.chatlogging = CHAT_LOGGING
        self.userID = None
        self.forgiveQueue = []
        self.connection = rtmp_protocol.RtmpClient(self.ip, self.port, self.tcurl, self.pageurl, '', self.app)

    def _recaptcha(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'DNT': 1,
                    'Connection': 'keep-alive'}
        url = "http://tinychat.com/cauth/captcha"
        r = self.s.request(method="GET", url=url, headers=headers, cookies=self.cookies)
        if '"need_to_solve_captcha":0' in r.text:
            self.timecookie = self.__getEncMills()
            self.connect()
        else:
            token = r.text.split('"token":"')[1].split('"')[0]
            urll = ("http://tinychat.com/cauth/recaptcha?token=" + token)
            webbrowser.open(urll)
            if reCaptchaShow == True:
                print(urll)
            raw_input("Ready to connect as " + ooO+self.nick+Ooo + " to " + ooO+self.room+Ooo + ".\nPress any key when captcha has been solved.")
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
                self.connection.connect([self.room, self.autoop, u'show', u'tinychat', self.username, "", self.timecookie])
                self.connected = True
                self._chatlog(" === Connected to " + str(self.room) + " === " + datetime.now().strftime(dateformat))
                self.onConnect()
                self._listen()
            except Exception as e:
                debugPrint("FAILED TO CONNECT", self.room)
                self.onConnectFail()

    def _listen(self):
        while self.connected:
            try:
                msg = self.connection.reader.next()
                debugPrint("SERVER: " + str(msg), str(self.room))
                if msg['msg'] == rtmp_protocol.DataTypes.COMMAND:
                    pars = msg['command']
                    cmd = pars[0].encode("ascii", "ignore").lower()
                    if len(pars) > 3:
                        pars = pars[3:]
                    else:
                        pars = []
                    for i in range(len(pars)):
                        if type(pars[i]) == str: pars[i] = pars[i].encode("ascii", "ignore")
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
                            if recipient.lower() == self.nick.lower():
                                message.pm = True
                                if message.msg.startswith("/msg ") and len(message.msg.split(" ")) >= 2: message.msg = " ".join(message.msg.split(" ")[2:])
                                if message.msg.startswith("/userinfo ") and len(message.msg.split(" ")) >= 2:
                                    if user.nick != self.nick:
                                        ac = " ".join(message.msg.split(" ")[1:])
                                        if ac == "$request":
                                            self.onUserInfoRequest(user)
                                        else:
                                            user.accountName = ac
                                            if self.room == ac: user.admin = True
                                            self.onUserInfo(user)
                                        message.msg = ppP+" ! "+Ppp+ssS+message.msg+Sss
                                        if str(user.nick) not in ignoreList:
                                            self.setWindowTitle("/userinfo: " + datetime.now().strftime(timeformat) + " (" + str(user.nick) + ")")
                                            global lastUserinfo
                                            lastUserinfo = user.nick
                                else:
                                    self.onPM(user, message)
                                    self._chatlog(ppP+" PM "+Ppp + " " + datetime.now().strftime(timeformat) + " " + ssS+str(user.nick)+":"+Sss+" " + str(message.msg))
                                    if str(user.nick) not in ignoreList:
                                        global lastPM
                                        lastPM = str(user.nick)
                                        self.setWindowTitle("PM: " + datetime.now().strftime(timeformat) + " (" + lastPM + "): " + str(message.msg)[:160] + "...")
                            else:
                                self.onMessage(user, message)
                            if message.msg.startswith("/mbs youTube "):
                                global lastYT
                                lastYT = message.msg.split(" ")[2]
                            if str(user.nick) not in ignoreList:
                                if timeOnRight == 1 or timeOnRight == True:
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
                        self._chatlog(datetime.now().strftime(timeformat) + " " + (user.nick) + " joined " + str(self.room) + ".")
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
                        self._chatlog(datetime.now().strftime(timeformat) + " " + (old) + " is now known as " + str(user.nick) + ".")
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
                        user = self.users[pars[0].lower()]
                        del self.users[pars[0].lower()]
                        self.onQuit(user)
                        self._chatlog(datetime.now().strftime(timeformat) + " " + (user.nick) + " left.")
                    elif cmd == "kick":
                        user = self.users[pars[1].lower()]
                        self.onBan(user)
                        self._chatlog(datetime.now().strftime(timeformat) + " " + (user.nick) + " was banned.")
                    elif cmd == "oper":
                        user = self._getUser(pars[1])
                        user.oper = True
            except Exception as e:
                debugPrint(str(e), self.room)

    def disconnect(self):
        if self.connected:
            self.connected = False
            try:
                self._shutdown()
            except:
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
        if not nick.lower() in self.users.keys(): self.users[nick.lower()] = TinychatUser(nick)
        return self.users[nick.lower()]

    def adminsay(self, msg):
        self._sendCommand("owner_run",[u"notice" + msg.replace(" ", "%20")])
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


    def say(self, msg):
        self._sendCommand("privmsg", [u"" + self._encodeMessage(msg), u"" + self.color + ",en"])
        self._chatlog(datetime.now().strftime(timeformat) + " " + ooO+str(self.nick)+":"+Ooo+" " + msg)

    def pm(self, msg, recipient):
        if recipient == "?":
            print(ssS+"""\
Description: Send PM.
Usage: /pm [OPTIONS]
    USER MESSAGE    PM a MESSAGE to USER
    
    Options for USER:
    @   Latest PM sender
    @@  Latest PM recipient
    @u  Latest userinfo request
    !   Clear (no MESSAGE needed)
"""+Sss)
            return
        # try:
        self._sendCommand("privmsg", [u"" + self._encodeMessage("/msg" + " " + recipient + " " + msg),self.color+",en","n" + str(self._getUser(recipient).id) +"-"+ recipient])
        self._sendCommand("privmsg", [u"" + self._encodeMessage("/msg" + " " + recipient + " " + msg),self.color+",en","b" + str(self._getUser(recipient).id) +"-"+ recipient])
        self._chatlog("(" + ppP+"@"+recipient+Ppp +  ") " +ooO+str(self.nick)+":"+Ooo+" " + msg)
        global lastPMRecip
        lastPMRecip = recipient
        # except TypeError:
            # print(ssS+"--- Error sending PM (user not found?) ---"+Sss)
    windowTitlePrefix = "pinychat"
    def setWindowTitle(self, title="", prefix=""):
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
        if prefix == "": # check if new prefix
            prefix = self.windowTitlePrefix 
        else:        
            self.windowTitlePrefix  = prefix
        title = str(title)
        prefix = str(prefix) + ": "
        
        if os.name == "nt":
            system("title " + prefix + title)
        else:
            system("echo -e '\033]2;'" + prefix + title + "'\007'")
    
    def setTimeformat(self, newformat):
        global timeformat
        global timeOnRight
        print(ssS),
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
            print("--- Timestamp now on right ---"+Sss)
        elif newformat == "l":
            timeOnRight = 0
            print("--- Timestamp now on left ---"+Sss)
        else:
            try:
                test = datetime.now().strftime(newformat)
                print("--- Timestamp preview: " + test)
                if raw_input("--- Enter 'y' to apply: "+Sss) == "y":
                    timeformat = newformat
            except:
                print("--- An error occured ---"+Sss)
        print(Sss),

    def userinfo(self, recipient):
        try:
            self._sendCommand("privmsg", [u"" + self._encodeMessage("/userinfo $request"),"#0" + ",en","b" + self._getUser(recipient).id + "-" + recipient])
            self._sendCommand("privmsg", [u"" + self._encodeMessage("/userinfo $request"),"#0" + ",en","n" + self._getUser(recipient).id + "-" + recipient])
        except:
            print(ssS+"--- Error getting user info. User might not exist ---"+Sss)

    def ignore(self, user):
        ignoreList.append(user)
        print(ssS+"--- Ignored " + user + " ---"+Sss)

    def unignore(self, user):
        try:
            ignoreList.remove(user)
            print(ssS+"--- Unignored " + user + " ---"+Sss)
        except:
            return

    def sendUserInfo(self, recipient, info):
        self._sendCommand("privmsg", [u"" + self._encodeMessage("/userinfo"+" "+u""+info), "#0,en" +"n" + self._getUser(recipient).id +"-"+ recipient])
        self._sendCommand("privmsg", [u"" + self._encodeMessage("/userinfo"+" "+u""+info), "#0,en" +"b" + self._getUser(recipient).id +"-"+ recipient])

    def setNick(self, nick=None):
        if not nick: nick = self.nick
        self.nick = nick
        self._sendCommand("nick", [u"" + nick])

    def setTopic(self, t):
        self._sendCommand("topic", [u"" + str(t)])

    def banlist(self):
        self._sendCommand("banlist", [])

    def close(self, nick):
        self._sendCommand("owner_run", [ u"_close" + nick])

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
        global lastYT
        if video == "@":
            if lastYT != "":
                webbrowser.open("https://www.youtube.com/watch?v="+lastYT)
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
            print(ssS+"""\
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
        for i in COLORS_DICT.keys(): # Get current color name
            if COLORS_DICT[i] == self.color:
                currentColor = i
                break
        if inputcolor == "black" or inputcolor == "00":
            colorBlack = 1
            newColor = "black"
        colorInfo = ssS+"--- Color: " + newColor + " (Old: " + currentColor + ") ---"+Sss
        invalidColor = ssS+"--- Invalid color ---"+Sss
        if colorBlack == 1:
            self.color = "#000000"
            print(colorInfo)
            colorBlack = 0
        elif inputcolor in COLORS_DICT.keys(): # If exising color name
            self.color = COLORS_DICT[inputcolor]
            print(colorInfo)
        else: # If existing color number
            try:
                i = int(inputcolor)
            except:
                print(invalidColor)
                return
            newColor = colorNames[i]
            colorInfo = ssS+"--- Color: " + newColor + " (Old: " + currentColor + ") ---"+Sss
            if i >= 0 and (i <= (len(TINYCHAT_COLORS)-1)): # Check if valid color number # todo: color nums don't work, max color num is wrong
                print(colorInfo)
                self.color = TINYCHAT_COLORS[i]
            else:
                print(invalidColor)
        print(Sss),

    def onConnect(self):
        if self.echo: print("You have connected to Tinychat.")

    def onConnectFail(self):
        if self.echo: print("You failed to connect to Tinychat.")

    def onJoin(self, user):
        if self.echo: print(self.room + ": " + user.nick + " entered the room.")

    def onQuit(self, user):
        if self.echo: print(self.room + ": " + user.nick + " left the room.")

    def onBan(self, user):
        if self.echo: print(self.room + ": " + user.nick + " was banned.")

    def onRegister(self, user):
        if self.echo: print("You have connected to " + self.room + ".")

    def onTopic(self, topic):
        if self.echo: print(self.room + ": Topic set to \"" + topic + "\".")

    def onUserInfo(self, user):
        if self.echo: print(self.room + ": Account name for nick \"" + user.nick + "\" recieved: " + user.accountName)

    def onUserInfoRequest(self, user):
        self.sendUserInfo(user.nick, self.username)

    def onMessage(self, user, message):
        if self.echo: message.printFormatted()

    def onPM(self, user, message):
        if self.echo: message.printFormatted()

    def onNickChange(self, new, old, user):
        if self.echo: print(self.room + ": " + old + " changed nickname to " + new + ".")

    def onNickTaken(self, nick):
        if self.echo: print("Nick in use, please set a different one")

    def onDisconnect(self):
        if self.echo: print("You have disconnected from " + self.room + ".")

    def _chatlog(self, msg):
        if self.echo2: print(msg)
        if self.chatlogging:
            d = LOG_BASE_DIRECTORY + "/" + self.room + "/"
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

    def __authHTTP(self): #todo - Rework this Funtions
        self.headers = {'Host': 'tinychat.com',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        "Referer": "http://tinychat.com/start/",
                        'Accept-Language': 'en-US,en;q=0.5',
                        'DNT': 1,
                        'Connection': 'keep-alive'}
        self.cookies = {}
        data = {"form_sent": "1",
                "username": self.username,
              "password": self.passwd,
                          "passwordfake": "Password"}
        url = "http://tinychat.com/login"
        raw = self.s.request(method='POST', url=url, data=data, headers=self.headers, cookies=self.cookies, stream=True)
        self.cookies = {}

    def __getRTMPInfo(self): #todo - Rework this Funtions
        if self.roomPassword:
            pwurl = "http://apl.tinychat.com/api/find.room/" + self.room + "?site=tinychat.com&url=tinychat.com&password=" + self.roomPassword
            raw = self.s.get(pwurl)

        else:
            url = "http://apl.tinychat.com/api/find.room/" + self.room + "?site=tinychat"
            raw = self.s.request(method="GET", url=url, headers=self.headers, cookies=self.cookies)
            if "result='PW'" in raw.text:
                self.roomPassword = get_input("Enter the password for room " + self.room + ": ")
                return self.__getRTMPInfo()
            else:
                return raw.text.split("rtmp='")[1].split("'")[0]

    def __getAutoOp(self, room):
        if AUTO_OP_OVERRIDE:
            r = AUTO_OP_OVERRIDE
        else:
            url = "http://tinychat.com/" + self.room
            raw = self.s.request(method="GET", url=url, headers=self.headers, cookies=self.cookies)
            if ", autoop: \"" in raw.text:
                r = raw.text.split(", autoop: \"")[1].split("\"")[0]
                return r
            else:
                return ""

    def __getProHash(self, room):
        if PROHASH_OVERRIDE:
            r = PROHASH_OVERRIDE
        else:
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
                'Connection': 'keep-alive'}
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

if __name__ == "__main__":
    initWindowTitle("pinychat")
    if roomnameArg == 0:
        roomnameArg = raw_input("Enter room name: ")
    if nicknameArg == 0:
        nicknameArg = raw_input("Enter nickname (optional): ")
    if usernameArg == 0:
       usernameArg = raw_input("Enter username (optional): ")
    if passwordArg == 0:
       passwordArg = raw_input("Enter password (optional): ")
    if colorArg == 0:
       colorArg = raw_input("Enter color (optional): ")

    room = TinychatRoom(roomnameArg, usernameArg, nicknameArg, passwordArg)
    initWindowTitle(nicknameArg)

    colorama.init() # todo: move this whole section somewhere else
    # nicks
    if highContrast == True:
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

    start_new_thread(room._recaptcha, ())
    while not room.connected: time.sleep(1)
    while room.connected:
        # Autoset initial color. Just does /color colorArg after connecting. Very lazy and wasteful. 
        # todo: Instead set color in the init method using its nickColor arg; see section "Set initial color (draft)".
        if colorArg != 0 and colorArg != "":
            msg = "/color " + str(colorArg)
            colorArg = 0
        else:
            msg = raw_input()
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
                    if cmd.lower() == "publish":
                        room._sendCreateStream()
                        room._sendPublish()
                    elif cmd.lower() == "say":
                        room.say(par)
                    elif cmd.lower() == "userinfo":
                        room.userinfo(par)
                    elif cmd.lower() == "ignore":
                        room.ignore(par)
                    elif cmd.lower() == "unignore":
                        room.unignore(par)
                    elif cmd.lower() == "list":
                        print("User list:")
                        print("---")
                        users = room.users
                        for user in users.keys():
                            user = users[user]
                            print(ssS+"Nick:\t" + str(user.nick))
                            print("User ID:\t" + str(user.id))
                            print("Color:\t" + str(user.color))
                            m = None
                            if user.lastMsg != None: m = user.lastMsg.msg
                            print("Last Message:\t" + str(m))
                            print("Mod:\t" + str(user.oper))
                            print("Admin:\t" + str(user.admin))
                            print("Account Name:\t" + str(user.accountName))
                            print("---"+Sss)
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
                                room.setWindowTitle()
                            else:
                                room.pm(pmMsg, pmRecip)
                        else:
                            print(ssS+"Argument required."+Sss)
                    elif cmd.lower() == "what":
                        print(ssS+"Room: " + room.room + "\tNick: " + room.nick+Sss)
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
                    elif cmd.lower() == "title": # todo: move this logic to setWindowTitle
                        if len(pars) > 0:
                            if pars[0] == "@": # nick
                                room.setWindowTitle(room.nick)
                            elif pars[0].startswith("@@"): # prefix
                                if pars[0] == "@@": # prefix = nick
                                    room.setWindowTitle("", room.nick)
                                else: # prefix = par
                                    room.setWindowTitle("", pars[1:])
                            elif pars[0] == "": # clear
                                room.setWindowTitle()
                            elif pars[0] == "?": # help
                                room.setWindowTitle("@?@")
                            else:
                                room.setWindowTitle(pars[0])
                    elif cmd.lower() == "/":
                        room.setWindowTitle()
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
                    elif cmd.lower() == "playsoundcloud":
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
            else:
                room.say(msg)