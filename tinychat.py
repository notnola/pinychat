import rtmp_protocol
import requests
import random
import os
import sys
import time
import socket
import webbrowser
from datetime import datetime

AUTO_OP_OVERRIDE = None
PROHASH_OVERRIDE = None

LOG_BASE_DIRECTORY = "log/"
DEBUG_CONSOLE = False
DEBUG_LOG = False
CHAT_LOGGING = True # do not enable here and bot

# cheking for python 2 or 3; ensuring use with both versions
if sys.version_info[0] >= 3:
    get_input = input
    import _thread
    start_new_thread = _thread.start_new_thread
else:
    get_input = raw_input
    import thread
    start_new_thread = thread.start_new_thread

TINYCHAT_COLORS = ["#7db257", "#a78901", "#9d5bb5", "#5c1a7a", "#c53332", "#821615", "#a08f23", "#487d21", "#c356a3",
                   "#1d82eb", "#919104", "#a990", "#b9807f", "#7bb224", "#1965b6", "#32a5d9"]


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
            raw_input("Press any key when captcha has been solved")
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
                self._chatlog(" === Connected to " + str(self.room) + " === ")
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
                                else:
                                    self.onPM(user, message)
                                    self._chatlog(str(datetime.now().time()) + " (private) [" + str(user.nick) + "] " + str(message.msg))
                            else:
                                self.onMessage(user, message)
                            self._chatlog(str(datetime.now().time()) + " [" + str(user.nick) + "] " + str(message.msg))
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
                        self._chatlog(str(datetime.now().time()) + " " + (user.nick) + " joined " + str(self.room) + ".")
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
                        self._chatlog(str(datetime.now().time()) + " The topic of " + str(self.room) + " is now \"" + str(self.topic) + ".\"")
                    elif cmd == "nick":
                        user = self._getUser(pars[0])
                        old = user.nick
                        user.nick = pars[1]
                        if old.lower() in self.users.keys():
                            del self.users[old]
                            self.users[user.nick] = user
                        self.onNickChange(user.nick, old, user)
                        self._chatlog(str(datetime.now().time()) + " " + (old) + " is now known as " + str(user.nick) + ".")
                    elif cmd == "notice":
                        if str(pars[0]) == "avon":
                            print(str(datetime.now().time()) + " " + (pars[2]) + " is now broadcasting.")
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
                        self._chatlog(str(datetime.now().time()) + " " + (user.nick) + " left.")
                    elif cmd == "kick":
                        user = self.users[pars[1].lower()]
                        self.onBan(user)
                        self._chatlog(str(datetime.now().time()) + " " + (user.nick) + " was banned.")
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
        self._chatlog("*[" + str(self.nick) + "] " + msg.replace(" ", "%20"))

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
        self._chatlog("[" + str(self.nick) + "] " + msg)

    def pm(self, msg, recipient):
        self._sendCommand("privmsg", [u"" + self._encodeMessage("/msg" + " " + recipient + " " + msg),self.color+",en","n" + self._getUser(recipient).id +"-"+ recipient])
        self._sendCommand("privmsg", [u"" + self._encodeMessage("/msg" + " " + recipient + " " + msg),self.color+",en","b" + self._getUser(recipient).id +"-"+ recipient])
        self._chatlog("(@" + recipient +  ") [" + str(self.nick) + "] " + msg)

    def userinfo(self, recipient):
        self._sendCommand("privmsg", [u"" + self._encodeMessage("/userinfo $request"),"#0" + ",en","b" + self._getUser(recipient).id + "-" + recipient])
        self._sendCommand("privmsg", [u"" + self._encodeMessage("/userinfo $request"),"#0" + ",en","n" + self._getUser(recipient).id + "-" + recipient])

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
        try:
            try:
                yt = video.split(".be/")[1][:11]
            except:
                yt = video.split("?v=")[1][:11]
            self.say("/mbs youTube " + str(yt) + " 0")
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
    room = TinychatRoom(raw_input("Enter room name: "), raw_input("Enter username (optional): "), raw_input("Enter nickname (optional): "), raw_input("Enter password (optional): "))
    start_new_thread(room._recaptcha, ())
    while not room.connected: time.sleep(1)
    while room.connected:
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
                    elif cmd.lower() == "list":
                        print("User list:")
                        print("---")
                        users = room.users
                        for user in users.keys():
                            user = users[user]
                            print("Nick:\t" + str(user.nick))
                            print("User ID:\t" + str(user.id))
                            print("Color:\t" + str(user.color))
                            m = None
                            if user.lastMsg != None: m = user.lastMsg.msg
                            print("Last Message:\t" + str(m))
                            print("Mod:\t" + str(user.oper))
                            print("Admin:\t" + str(user.admin))
                            print("Account Name:\t" + str(user.accountName))
                            print("---")
                    elif cmd.lower() == "pm":
                        if len(pars) > 1:
                            room.pm(" ".join(pars[1:]), pars[0])
                        else:
                            print("Please supply the recipient's nick as well as the message to send")
                    elif cmd.lower() == "nick":
                        room.setNick(par)
                    elif cmd.lower() == "color":
                        room.cycleColor()
                    elif cmd.lower() == "close":
                        room.close(par)
                    elif cmd.lower() == "ban":
                        room.ban(par)
                    elif cmd.lower() == "quit":
                        room.disconnect()
                    elif cmd.lower() == "reconnect":
                        room.reconnect()
                    elif cmd.lower() == "playyoutube":
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
                    elif cmd.lower() == "adminsay":
                        room.adminsay(par)
            else:
                room.say(msg)