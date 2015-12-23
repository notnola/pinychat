# Pinychat

Pinychat is a Python module that allows you to easily interface with Tinychat.com. 

Some features: commandline arguments, logging, mod actions, public/private messages, user ignoring, dummy cams.

### Version
0.8.3

### Requirements 

Pinychat requires a few things to work properly:
* 32bit install of Python 2.7
* [requests] - https://github.com/kennethreitz/requests 
* [colorama] - https://github.com/tartley/colorama

    ```sh
    # pip install requests 
    # pip install colorama
    ```

### Usage

`tinychat.py NICK ROOM` or `tinychat.py -r ROOM -n NICK -u USERNAME -p PASSWORD -c COLOR`

See also the *Commands* section below.

`bot.py` currently only provides a small subset of the module's features/commands. Full module support will be integrated eventually.
	

### Development

Want to contribute? Great! Feel free to make pull requests at your discretion! Feel free to contact me at notnola@openmailbox.com aswell! 

### Todos

 - Allow bots to use all module features/commands
 - Add stream support
 - Write tests
 - Write better debug code
 - Add better comments / clean up code base


### Contributors
This is where I will thank the people who have helped make this project possible either by submitting pull requests, helping in the reversing process, or just with raw support. (If you create a pull requests and it gets approved, please feel free to add your name to this list!
- [swiftSwathSee](https://github.com/swiftSwathSee)
- [James Koss](http://www.jameskoss.com)
- [Lord Gaben]
- [Aida]

### Commands

`/command [options]`. Use `?` option for full list of options.  
Some commands are currently only accessible directly from the module. 

* `say` *[message]*: say message
* `adminsay` *[adminmessage]*: say admin message
* `topic` *[topic]*: set room topic 
* `list`: print user list
* `banlist`: print banlist 
* `ban` *[user]*: ban a user
* `forgive` *[user]*: uban a user
* `forgivename` *[user]*: unban a user and display banlist
* `userinfo` *[user]*: get account name for user
* `close` *[user]*: close a cam
* `ignore` *[user]*: ignore a user
* `unignore` *[user]*: unignore a user
* `pm` *[user]* *[message]*: PM user with message
* `nick` *[nick]*: set nick
* `what`: print room and nick names
* `color` *[color]*: set color
* `time` *[timeformat]*: set time format
* `title` *[title]*: set window title
* `/`: reset window title
* `playyoutube`/`yt` *[URL]*: play YouTube video from URL. If URL is `@`, the most recently-played video opens in your browser
* `stopyoutube` 
* `playsoundcloud` *[URL]*
* `stopsoundcloud` 
* `quit`
* `reconnect` 

