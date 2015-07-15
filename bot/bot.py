import tinychat
import thread
import time
import random


_8_BALL_RESPONSES = ["Signs point to yes.", "Yes.", "Reply hazy, try again.", "Without a doubt.", "My sources say no.", "As I see it, yes.", "You may rely on it.", "Concentrate and ask again.", "Outlook not so good.", "It is decidedly so.", "Better not tell you now.", "Very doubtful.", "Yes - definitely.", "It is certain.", "Cannot predict now.", "Most likely.", "Ask again later.", "My reply is no.", "Outlook good.", "Don't count on it."]

SILENCE_BREAKERS = ["Anyone there?", "Hello?"] # add whatever you like xP
SILENT_DELAY_SECONDS = 300

MOD_ONLY_COMMANDS = ["yt", "cyt", "sc", "csc", "addbanword", "removebanword", "addbannick", "removebannick", "topic"] # automatically includs all youtube soundboard commands, so no need to add those
SUPER_PRIV_COMMANDS = ["supertest", "kick", "ban", "keeptopic", "say", "stopvotekick", "nuke"]

PRIV_USERNAMES = ["notreallynola"] # defaults, these are
PRIV_FILE = "priv_users"

BANNED_STRINGS = []
BANNED_FILE = "bannedStrings"
BANNED_NICKS = []
BANNED_NICKS_FILE = "bannedNicks"

mutedUsers = []
priviledgedUsers = []
youtubeSoundboard = {}
priviledgeCodes = {}

spoofedaccountName = "nolaBot"

CONSOLE_PRINT = True

def saveBannedNicks():
	f = open(BANNED_NICKS_FILE, "w")
	f.write("\n".join(BANNED_NICKS))
	f.close()

def importBannedNicks():
	f = open(BANNED_NICKS_FILE, "r")
	lines = f.readlines()
	f.close()

	for line in lines:
		line = line.strip()
		if line != "":
			BANNED_NICKS.append(line)
			print("Loading banned string: " + line)

def savePrivList():
	f = open(PRIV_FILE, "w")
	for u in PRIV_USERNAMES:
		f.write(str(u) + "\n")
	f.close()

def loadPrivList():
	global PRIV_USERNAMES
	try:
		f = open(PRIV_FILE, "r")
		lines = f.readlines()
		f.close()
		PRIV_USERNAMES = []
		for line in lines:
			line = line.strip()
			PRIV_USERNAMES.append(line)
	except Exception as e:
		print("No saved priv users file, using defaults then")

loadPrivList()

def saveBannedStrings():
	f = open(BANNED_FILE, "w")
	f.write("\n".join(BANNED_STRINGS))
	f.close()

def importBannedStrings():
	f = open(BANNED_FILE, "r")
	lines = f.readlines()
	f.close()

	for line in lines:
		line = line.strip()
		if line != "":
			BANNED_STRINGS.append(line)
			print("Loading banned string: " + line)

def importYoutubeSoundboard(filename="yt"):
	f = open(filename, "r")
	data = f.read().strip()
	f.close()

	lines = data.split("\n")
	for line in lines:
		line = line.strip()
		if line == "": continue
		parts = line.split(" ", 1)
		command = parts[0].strip().lower()
		url = parts[1].strip()
		youtubeSoundboard[command] = url

def importPriviledgeCodes(filename="codes"):
	f = open(filename, "r")
	data = f.read().strip()
	f.close()

	lines = data.split("\n")
	for line in lines:
		line = line.strip()
		if line == "": continue
		parts = line.split(" ", 1)
		name = parts[0].strip().lower()
		code = parts[1].strip()
		priviledgeCodes[name] = code

importYoutubeSoundboard()
importPriviledgeCodes()
importBannedStrings()
importBannedNicks()

privQueue = {}

def privCheck(user, code):
	if user.accountName in priviledgeCodes and code == priviledgeCodes[user.accountName]:
		room.pm("You are one of the chosen", user.nick)
		priviledgedUsers.append(user.accountName)
	else:
		room.pm("try again you sorry sack of shit", user.nick)

CONSOLE_REPLY = 523495743 # random enum id :P

class TinychatBot(tinychat.TinychatRoom):
	def onMessage(self, user, message):
		self.receivedMessageTime = time.time()
		if self.echo: message.printFormatted()
		self.handle(user, message)

	def onPM(self, user, message):
		if self.echo: message.printFormatted()
		m = message.msg.encode("ascii", "ignore").strip()
		if m.startswith("identify "):
			code = m.split(" ", 1)[1]
			if user.accountName == None:
				self.pm("One moment, please, while we stalk you to see who you really are...", user.nick)
				self.userinfo(u"" + user.nick)
				privQueue[user] = code
			else:
				privCheck(user, code)
		else:
			self.handle(user, message, user.nick)

	def identify(self, nick, forScore=False, admin=False, requestedBy=None):
		print("DEBUG creating request: " + str(nick) + "; requested by: " + str(requestedBy))
		request = {"nick": nick, "forScore": forScore, "admin": admin, "requestedBy": requestedBy}
		self.userInfoRequests.append(request)
		self.userinfo(u"" + nick)

	def onNickChange(self, new, old, user):
		if self.echo: print(self.room + ": " + old + " changed nickname to " + new + ".")
		if old in mutedUsers:
			mutedUsers.remove(old)
			if not new in mutedUsers:
				mutedUsers.append(new)
		if new == self.nick:
			'''Initlaization Stuff Here'''
			self.userInfoRequests = []
			self.kickQueue = []
			self.lockedTopic = ""
			self.kickVotes = {}
			self.voting = None
			self.voteTime = None
			self.adminsay("Booting Tinychat Bot - Stand by!")
			self.adminsay("http://github.com/notnola/pinychat_bot")
		else:
			if self._getUser(new).accountName == None:
				self.identify(new, False, True)
		for banned in BANNED_NICKS:
			if banned.lower() == new.lower():
				self.adminsay(new + " was banned for their nick")
				self.ban(new)
		if old == self.voting:
			self.voting = new
			self.outlaw = True

	def onUserInfoRequest(self, user):
		self.sendUserInfo(user.nick, U"" + spoofedaccountName)

	def idle(self):
		while True:
			if time.time() - self.receivedMessageTime > SILENT_DELAY_SECONDS:
				self.say(SILENCE_BREAKERS[random.randint(0, len(SILENCE_BREAKERS) - 1)])
				#self.say("Anyone there?")
				self.receivedMessageTime = time.time()
			if self.voting != None:
				if time.time() - self.voteTime >= 30:
					self.adminsay("Some one needs to vote on kicking " + self.voting + " or the voting will close!")
					self.voteTime = time.time()
			time.sleep(1)

	def banAll(self):
		try:
			for user in self.users.keys():
				u = self.users[user]
				if u.nick != self.nick:
					if not (u.nick in PRIV_USERNAMES):
						self.ban(u.nick)
		except Exception as e:
			print("DEBUG: " + str(e))

	def onUserInfo(self, user):
		print("DEBUG received user info for " + user.nick)
		print("DEBUG now looping through user info requests")
		i = 0
		for request in self.userInfoRequests:
			print("DEBUG this request was sent by " + str(request["requestedBy"]))
			if request["nick"] == user.nick:
				if request["forScore"]:
					pass#self.win(user)
				else:
					if request["admin"]:
						print(user.nick + " has been identified as " + user.accountName)
					else:
						if request["requestedBy"] == None:
							self.pm("You have been identified as *" + user.accountName + "*", user.nick)
						else:
							self.adminsay(user.nick + " has been identified as *" + user.accountName + "*")
							self.adminsay("Thanks for shopping at Walmart! :D")
				self.userInfoRequests.pop(i)
				break
			i += 1
		print("DEBUG done looping through user info requests")

	#def onUserInfo(self, user):
	#	if user in privQueue.keys():
	#		code = privQueue[user]
	#		del privQueue[user]
	#		privCheck(user, code)
	#	else:
	#		self.say("Account name for nick \"" + user.nick + "\" recieved: " + user.accountName)
	#		self.say("Thanks for shopping at walmart")

	def onBan(self, user):
		for i in self.kickQueue:
			self.forgive(i)
		self.kickQueue = []

	def onTopic(self, topic):
		if self.lockTopic:
			if topic != self.lockedTopic: self.setTopic(self.lockedTopic)
		else:
			self.lockedTopic = topic

	def reply(self, message, replyTo=None):
		if replyTo == None:
			self.say(message)
		elif replyTo == CONSOLE_REPLY:
			print(message)
		else:
			self.pm(message, replyTo)

	def adminreply(self, message, replyTo=None):
		if replyTo == None:
			self.adminsay(msg=message)
		elif replyTo == CONSOLE_REPLY:
			print(message)
		else:
			self.pm(message, replyTo)


	# voting stuff

	def doVote(self, nick, vote):
		if self.voting != None: # if there's voting going on
			if nick.lower() in self.kickVotes.keys(): # if they have already voted
				self.pm(nick + ", you already voted!", nick) # tell them that they already voted
			else:
				self.voteTime = time.time()
				self.kickVotes[nick] = vote # set this person's vote
				if self.votesNeeded() <= 0: # if we have enough votes
					decision = self.votedDecision() # get the result

					if decision: # if the decision was yes...
						if self.voting in self.users.keys():
							self.adminsay(self.voting + " was kicked from a group decision")
							if self.outlaw: self.adminsay("you thought you could outrun the banhanner eh?!")
							uid = self._getUser(self.voting).id # get their user id
							self.ban(self.voting) # ban them
							self.kickQueue.append(uid) # and then add them to the queue to be unbanned once they are gone
						else:
							self.adminsay("*swings banhammer and misses*") # non existant user defense # 1
					else: # if the decision was no, or a tie...
						self.adminsay("The decision was to not kick " + self.voting)

					self.kickVotes = {} # clear the votes for future use
					self.voting = None # we aren't voting anymore
				else: # we still need some more votes
					self.adminsay("Thank you " + nick + " for your vote! " + str(self.votesNeeded()) + " votes are now needed")

	def votedDecision(self): # return True or False, whether there are more yes votes than no votes
		yes = 0 # yes count
		no = 0 # no count
		for voter in self.kickVotes.keys(): # loop through the voters and their votes
			vote = self.kickVotes[voter] # get the voter's vote
			if vote: # if it was a yes vote (True)
				yes += 1 # increment the yes count
			else: # otherwise
				no += 1 # the no count
		return yes > no # returns if there are more yess than nos, a tie returns false

	def votesNeeded(self): # get how many votes are needed before a decision is needed
		if self.voting == None: # we aren't voting
			return 0 # so we don't need any votes
		else:
			votes = len(self.kickVotes.keys()) # how many votes have been cast
			population = len(self.users.keys()) # how many people are in the room
			percentageVoted = float(votes) / float(population) # the percentage of the room population that has voted
			targetPercent = 0.25 # the percentage of votes needed before the final decision is made
			deltaPercent = targetPercent - percentageVoted # the difference between the target percent and the actual percent so far
			voteValue = 1.0 / population # the value a single vote has
			needed = deltaPercent / voteValue # how many votes are still needed (how many times a single vote value goes into the distance between where we are and where we want to be)
			return needed # return the result

	def voteKick(self, nick, voter): # new verision!
		# .lower() makes  it lower case, because we don't want to be case sensitive
		nick = nick.lower() # the nick of the person to be kicked
		voter = voter.lower # and the voter
		exists = nick in self.users.keys() # if the user exists

		# check to see if there is a voting session going on
		if self.voting == None: # nope there isn't
			if nick == self.nick.lower():
				self.adminsay("Nobody can kick the " + self.nick + "!!")
			elif self._getUser(nick).accountName in PRIV_USERNAMES:
				self.adminsay("That person isn't allowed to be kicked! They are special!")
			elif exists: # if the user exists
				self.outlaw = False
				self.voting = nick # so set the voting session to be voting for this person
				self.voteTime = time.time()
				self.adminsay(nick + " is up against the tribal council - Should he be kicked off the island? Yes or No - " + str(self.votesNeeded()) + " votes needed") # and  say what's up
			else:
				self.adminsay("That person doesn't exist!")
		else: # yes there is
			self.adminsay("We are already voting about whether to kick " + self.voting + "! Yes or No - " + str(self.votesNeeded()) + " votes needed") # so inform them that there's already one going on

	#def voteKick(self, nick, voter): # this function is so messily written ._.
#		nick = nick.lower()
#		voter = voter.lower()
#		if nick in self.kickVotes.keys():
#			if not voter in self.kickVotes[nick]:
#				self.kickVotes[nick].append(voter)
#				p = len(self.kickVotes[nick])
#				t = len(self.users.keys())
#				per = float(p) / float(t)
#				dp = 0.25 - per
#				v = 1.0 / t
#				needed = dp / v
#				self.adminsay("Thank you " + voter + " for your vote! " + str(needed) + " votes are now needed")
#				print("Vote for kicking " + nick + " at " + str(int(per*100)) + "%")
#				if per >= 0.25:
#					self.adminsay(nick + " was kicked from a group decision")
#					uid = self._getUser(nick).id
#					self.ban(nick)
#					self.kickQueue.append(uid)
#					del self.kickVotes[nick]
#		else:
#			self.kickVotes[nick] = [voter]
#			p = len(self.kickVotes[nick])
#			t = len(self.users.keys())
#			per = float(p) / float(t)
#			dp = 0.25 - per
#			v = 1.0 / t
#			needed = dp / v
#			self.adminsay(nick + " is up against the tribal council - Should he be kicked off the island? Yes or No - " + str(needed) + " votes needed")
#			print("Vote for kicking " + nick + " at " + str(int(per*100)) + "%")
#			if per >= 0.25:
#				self.adminsay(nick + " was kicked from a group decision")
#				uid = self._getUser(nick).id
#				self.ban(nick)
#				self.kickQueue.append(uid)
#				del self.kickVotes[nick]

	def handle(self, user, message, replyTo=None):
		global spoofedaccountName
		msg = message.msg
		if replyTo != CONSOLE_REPLY and not "removebanword" in msg:
			for banned in BANNED_STRINGS:
				if banned.lower() in msg.lower():
					self.adminsay(user.nick + " was banned for saying \"" + banned + "\"")
					self.ban(user.nick)

		if self.voting != None: # if it's in the middle of a voting session...
			if "yes" == msg.lower(): # if someone says yes, then
				self.doVote(user.nick, True) # vote yes
			elif "no" == msg.lower(): # if someone says no, then
				self.doVote(user.nick, False) # vote no

		#print("Console: " + str(replyTo == CONSOLE_REPLY))
		if msg[0] == "!":
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

				#superPriv = user.accountName in priviledgedUsers
				superPriv = user.accountName in PRIV_USERNAMES
				if replyTo == CONSOLE_REPLY: superPriv = True

				# privilege check
				if user.nick.lower() in mutedUsers:
					pass
				elif (cmd.lower() in MOD_ONLY_COMMANDS or cmd.lower() in youtubeSoundboard.keys()) and not (user.oper or superPriv):
					self.reply(user.nick + ", you are not authorized to use this command.", replyTo)
				elif (cmd.lower() in SUPER_PRIV_COMMANDS) and not superPriv:
					self.reply(user.nick + ", you are *definitely* not authorized to use this command.", replyTo)
				elif cmd.lower() == "supertest":
									self.reply("Yes, " + user.nick + ", you are one of the chosen ones.", replyTo)
				elif cmd.lower() == "votekick":
					if par.strip() == "":
						self.reply("Please provide a nick!", replyTo)
					else:
						self.voteKick(par, user.nick)
				elif cmd.lower() == "stopvotekick":
					self.kickVotes = {} # clear the votes for future use
					self.voting = None # we aren't voting anymore
					self.adminsay("The vote has been cancelled")
				elif cmd.lower() == "say":
									if replyTo == CONSOLE_REPLY:
										self.say(par)
									else:
										self.reply(par, replyTo)
				elif cmd.lower() == "8ball":
									self.adminreply("*Magic 8 Ball:* " + _8_BALL_RESPONSES[random.randint(0, len(_8_BALL_RESPONSES) - 1)], replyTo)
				elif cmd.lower() == "userinfo":
					if par.strip() == "":
						self.reply("Please provide a nick!", replyTo)
						self.reply("Thanks for shopping at walmart", replyTo)
					else:
						self.identify(par, requestedBy=user.nick)#self.userinfo(u"" + par)
				elif cmd.lower() == "kick":
					if par.strip() == "":
						self.reply("Please provide a nick!", replyTo)
					else:
						exists = par in self.users.keys()
						if exists:
							self.adminsay(par + " has been kicked and will be allowed to return shortly")
							uid = self._getUser(par).id
							self.ban(par)
							self.kickQueue.append(uid)
							#self.forgive(uid)
						else:
							self.adminsay(par + " doesn't exist!")
				elif cmd.lower() == "ban":
					if par.strip() == "":
						self.reply("Please provide a nick to ban!", replyTo)
					else:
						self.ban(par)
				elif cmd.lower() == "topic":
					if par.strip() == "":
						self.reply("Please provide a topic!", replyTo)
					else:
						self.setTopic(par)
				elif cmd.lower() == "locktopic":
					self.lockTopic = not self.lockTopic
					if self.lockTopic:
						self.reply("Keep topic is *on*", replyTo)
					else:
						self.reply("Keep topic is *off*", replyTo)
					#Media Controls
				elif cmd.lower() == "yt":
										self.playYoutube(par)
				elif cmd.lower() == "cyt":
										self.stopYoutube()
				elif cmd.lower() == "sc":
										self.playSoundcloud(par)
				elif cmd.lower() == "csc":
										self.stopSoundcloud()
					#Youtube SoundBoard
				elif cmd.lower() in youtubeSoundboard.keys():
										self.playYoutube(youtubeSoundboard[cmd.lower()])

				elif cmd.lower() == "addbanword":
										print("PARS: " + str(pars))
										if len(pars) > 0:
											BANNED_STRINGS.append(par.lower())
											saveBannedStrings()
											self.reply("Banned string \"" + par.lower() + "\"", replyTo)
										else:
											self.reply("Please specify a string to ban!", replyTo)

				elif cmd.lower() == "removebanword":
										print("PARS: " + str(pars))
										if len(pars) > 0:
											s = par.lower()
											if s in BANNED_STRINGS:
												BANNED_STRINGS.remove(s)
												saveBannedStrings()
												self.reply("Unbanned string \"" + par.lower() + "\"", replyTo)
											else:
												self.reply("That string is not currently banned", replyTo)
										else:
											self.reply("Please specify a string to unban!", replyTo)

				elif cmd.lower() == "addbannick":
										print("PARS: " + str(pars))
										if len(pars) > 0:
											BANNED_NICKS.append(par.lower())
											saveBannedNicks()
											self.reply("Banned nick \"" + par.lower() + "\"", replyTo)
										else:
											self.reply("Please specify a nick to ban!", replyTo)

				elif cmd.lower() == "removebannick":
										print("PARS: " + str(pars))
										if len(pars) > 0:
											s = par.lower()
											if s in BANNED_NICKS:
												BANNED_NICKS.remove(s)
												saveBannedNicks()
												self.reply("Unbanned nick \"" + par.lower() + "\"", replyTo)
											else:
												self.reply("That nick is not currently banned", replyTo)
										else:
											self.reply("Please specify a nick to unban!", replyTo)

				## original console commands
				elif replyTo == CONSOLE_REPLY:
					if cmd.lower() == "say": # duplicate
										room.say(par)
					elif cmd.lower() == "listbanwords": # duplicate
										print("Banned strings:")
										for b in BANNED_STRINGS:
											print(b)
					elif cmd.lower() == "listbannicks": # duplicate
										print("Banned nicks:")
										for b in BANNED_NICKS:
											print(b)
					elif cmd.lower() == "pm":
										if len(pars) > 1:
												room.pm(" ".join(pars[1:]), pars[0])
										else:
												self.reply("Please supply the recipient's nick as well as the message to send", replyTo)
					elif cmd.lower() == "nick":
										room.setNick(par)
					elif cmd.lower() == "color":
										room.cycleColor()
					elif cmd.lower() == "quit":
										room.disconnect()
					elif cmd.lower() == "reconnect":
										room.reconnect()
					elif cmd.lower() == "spoofinfo":
										self.reply("Account name set to " + par, replyTo)
										spoofedaccountName = par
					elif cmd.lower() == "sendinfo":
										self.reply("Sending userinfo to " + par, replyTo)
										room.sendUserInfo(par, U"" + spoofedaccountName)
					elif cmd.lower() == "disablecommands":
										n = par.lower()
										if n in mutedUsers:
											while n in mutedUsers:
												mutedUsers.remove(n)
											self.reply("Unblocked " + n, replyTo)
										else:
											mutedUsers.append(n)
											self.reply("Blocked " + n, replyTo)
					elif cmd.lower() == "disabledusers":
										self.reply("Currently blocked nicks:", replyTo)
										for nick in mutedUsers:
											self.reply(nick, replyTo)
					elif cmd.lower() == "close":
										room.close(par)
					elif cmd.lower() == "adminsay":
										room.adminsay(par)
					elif cmd.lower() == "clr":
										for x in range( 500):
											room.clear()
					elif cmd.lower() == "dcapi":
										room._disconnectRequest()
					elif cmd.lower() == "nuke":
										self.banAll()
					#elif cmd.lower() == "raw":
					#                    if len(pars) >= 1:
					#                            room.raw(par)
					#                    else:
					#                            self.reply("Please supply a raw command", replyTo)

				else:
					self.pm("Unknown command: !" + cmd, user.nick) # Sends to PM
					#self.reply("Unknown command: !" + cmd, replyTo) # Sends to main chat

def inputLoginInfo():
	roomname = raw_input("Enter room name: ").strip()
	username = raw_input("Enter username (optional): ").strip()
	nickname = raw_input("Enter nickname (optional): ").strip()
	password = raw_input("Enter password (optional): ").strip()
	return {"roomname": roomname, "username": username, "nickname": nickname, "password": password}

def prompt(message):
	r = raw_input(message + " (Y/n) ").lower()
	return r == "y" or r == ""

def saveLoginInfo(loginInfo):
	print("Saving login info to login file")

	roomname = loginInfo["roomname"]
	username = loginInfo["username"]
	nickname = loginInfo["nickname"]
	password = loginInfo["password"]

	f = open("login", "a")
	f.write(roomname + " " + username + " " + nickname + " " + password + "\n");
	f.close()

def loadLoginInfo():
	try:
		f = open("login", "r")
		data = f.read();
		lines = data.split("\n")
		loginInfos = []
		for l in lines:
			if l == "": continue
			parts = l.split(" ")
			roomname = parts[0]
			username = parts[1]
			nickname = parts[2]
			password = parts[3]
			loginInfo = {"roomname": roomname, "username": username, "nickname": nickname, "password": password}
			loginInfos.append(loginInfo)
		f.close()
		return loginInfos
	except Exception as e:
		return None

loginInfos = loadLoginInfo()
loginInfo = None

if loginInfos != None:
	print(str(len(loginInfos)) + " saved logins found.")
	i = 0
	for l in loginInfos:
		roomname = l["roomname"]
		username = l["username"]
		nickname = l["nickname"]
		password = l["password"]
		print("(" + str(i) + ") " + roomname + ", " + username + ", " + nickname + ", " + password)
		i += 1

	c = raw_input("Enter the # of your choice OR press enter for manual login: ")
	if c != "":
		try:
			n = int(c)
			loginInfo = loginInfos[n]
			print("Loaded login info from login file")
		except Exception as e:
			pass

if loginInfo == None:
	loginInfo = inputLoginInfo()
	roomname = loginInfo["roomname"]
	username = loginInfo["username"]
	nickname = loginInfo["nickname"]
	password = loginInfo["password"]

	if(prompt("Would you like to save this login info?")):
		saveLoginInfo(loginInfo)

roomname = loginInfo["roomname"]
username = loginInfo["username"]
nickname = loginInfo["nickname"]
password = loginInfo["password"]

print("Connecting using...")
print("roomname: " + roomname)
print("username: " + username)
print("nickname: " + nickname)
print("password: " + password)

cu = tinychat.TinychatUser("nonsense blah blah blah")
room = TinychatBot(roomname, username, nickname, password)
room.echo2 = CONSOLE_PRINT
room.lockTopic = False
room.voting = None
room.chatlogging = True
room.receivedMessageTime = time.time()
thread.start_new_thread(room.connect, ())
thread.start_new_thread(room.idle, ())
while not room.connected: time.sleep(1)
while room.connected:
	msg = raw_input()
	if len(msg) > 0:
		if msg[0] == "/":
			msg = msg[1:]
			if len(msg) > 0:
				room.handle(cu, tinychat.TinychatMessage("!" + msg, cu.nick, cu), CONSOLE_REPLY)
			else:
				room.say(msg)
