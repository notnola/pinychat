# Pinychat

Pinychat is a Python module and client that allows you to easily interface with Tinychat.com. 

Features: commandline arguments, room logging, mod actions, public/private messages, user ignoring, dummy cams, and much more.

### Requirements 

* 32bit install of Python 2.7
* [requests] - https://github.com/kennethreitz/requests 
* [colorama] - https://github.com/tartley/colorama

    ```sh
    # pip install requests 
    # pip install colorama
    ```

### Usage

#### Startup
All arguments optional.

Shorthand (quick mode): `tinychat.py NICK ROOM`  
Full: `tinychat.py -r ROOM -n NICK -u USERNAME -p PASSWORD -c COLOR`

 `ROOM` may also be a Tinychat.com room URL.

#### Using it as a standalone client

See the [Commands](#commands) section.

#### Using it as a module (i.e. as part of your own client)

This is currently very limited, but you can see the `bot.py` example. Only a small subset of the module's features are available. Full module support will be added eventually.

### Commands

Usage: `/command [options]`. Use the `?` option to see a full list of a commands features.

#### You

* `pm [user] [message]`: send a PM to a user
* `nick [nick]`: set your nick
* `delay [options]`: delay your messages
* `alert [command] [phrase]`: get alerts when a phrase is mentioned
* `say [message]`: say message (this is the default command if no command is used)
* `color [color]`: set your color (note: this is mostly useless, since Tinychat no longer has nick colors)
* `what`: print the current room and your nick
* `publish`: open your cam (close with `close`)

#### Mod

* `topic [topic]`: set room topic 
* `adminsay` (or `a`) ` [adminmessage]`: say admin message
* `ban [user]`: ban a user
* `forgive [user]`: unban a user
* `forgivename [user]`: unban a user and display banlist
* `banlist`: print banlist 
* `close [user]`: close a cam

#### Other users

* `list`: print user list
* `userinfo [user]`: get account name for a user
* `ignore [user]`: ignore a user
* `unignore [user]`: unignore a user

#### Room

* `playyoutube` (or `yt`) ` [URL]`: play video from URL or view last-played video
* `stopyoutube` 
* `playsoundcloud`  (or `sc`) ` [URL]`: play track from URL or view last-played track
* `stopsoundcloud` 

#### Client

* `/`: reset window title (useful for clearing alerts)
* `time [timeformat]`: set time format
* `title [title]`: set window title
* `notifications` (or `notes`) ` [setting]`: toggle notifications display or set on/off
* `sys [shell command]`: runs a shell command
* `quit`
* `reconnect` 

### Configuration

You can optionally configure the module via the `pinychat.ini` file. See [settings.md](settings.md) for the details.

### Development

Want to contribute? Feel free to make pull requests and issues at your discretion, or contact me at notnola@openmailbox.com!

### Contributors
Thanks to the people who have helped make this project possible either by submitting pull requests, helping in the reversing process, or just with raw support. If you create a pull requests and it gets approved, please feel free to add your name to this list!
- [swiftSwathSee](https://github.com/swiftSwathSee)
- [James Koss](http://www.jameskoss.com)
- [Lord Gaben]
- [Aida](https://github.com/Autotonic)
- [TechWhizZ199](https://github.com/TechWhizZ199)

### To-do

 - Do all the stuff labeled "todo" in the code.
 - Allow bots to use all module features/commands
 - Write full command documentation
 - Add stream support
 - Write tests
 - Write better debug code
 - Add better comments / clean up code base
