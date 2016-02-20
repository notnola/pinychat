# Pinychat

Pinychat is a Python module that allows you to easily interface with Tinychat.com. 

Some features: commandline arguments, logging, mod actions, public/private messages, user ignoring, dummy cams, and much more.

### Requirements 

* 32bit install of Python 2.7
* [requests] - https://github.com/kennethreitz/requests 
* [colorama] - https://github.com/tartley/colorama

    ```sh
    # pip install requests 
    # pip install colorama
    ```

### Usage

Shorthand (quick mode): `tinychat.py NICK ROOM`
Full: `tinychat.py -r ROOM -n NICK -u USERNAME -p PASSWORD -c COLOR`

All arguments optional.

Tinychat.com room URLs are also accepted for `ROOM`.

See also the [Commands](#commands) section below.

`bot.py` currently only provides a small subset of the module's features/commands. Full module support will be integrated eventually.

### Commands

`/command [options]`. Use `?` option for full list of a command's options (help).  

Some commands are currently only accessible directly from the module. 

* `say [message]`: say message
* `delay [options]`: delay your messages
* `alert [command] [phrase]`: get alerts when a phrase is mentioned
* `adminsay` (or `a`) ` [adminmessage]`: say admin message
* `topic [topic]`: set room topic 
* `list`: print user list
* `banlist`: print banlist 
* `ban [user]`: ban a user
* `forgive [user]`: unban a user
* `forgivename [user]`: unban a user and display banlist
* `userinfo [user]`: get account name for user
* `close [user]`: close a cam
* `ignore [user]`: ignore a user
* `unignore [user]`: unignore a user
* `pm [user] [message]`: PM user with message
* `nick [nick]`: set nick
* `what`: print room and nick names
* `color [color]`: set color
* `time [timeformat]`: set time format
* `title [title]`: set window title
* `/`: reset window title
* `notifications` (or `notes`) ` [setting]`: toggle notifications display or set on/off
* `playyoutube` (or `yt`) ` [URL]`: play video from URL or view last-played video
* `stopyoutube` 
* `playsoundcloud`  (or `sc`) ` [URL]`: play track from URL or view last-played track
* `stopsoundcloud` 
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

 - Allow bots to use all module features/commands
 - Write full command documentation
 - Add stream support
 - Write tests
 - Write better debug code
 - Add better comments / clean up code base
