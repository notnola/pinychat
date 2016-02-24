# Settings
pinychat.ini is a standard [INI file](https://en.wikipedia.org/wiki/INI_file\#Example) (so no quotes around strings). All settings are optional.

First line must be `[Main]`

### List

Setting | Default | Type
---|---|----
AUTO_OP_OVERRIDE | None | string
PROHASH_OVERRIDE | None | string
DefaultRoom | None | string
DefaultNick | None | string
useDefaultAccount | 0 | int bool
DefaultAccountName | None | string
DefaultAccountPass | None | string
LOG_BASE_DIRECTORY | log/ | string
DEBUG_CONSOLE | 0 | int bool
DEBUG_LOG | 0 | int bool
CHAT_LOGGING | 1 | int bool
textEditor | gedit | string
highContrast | 0 | int bool
timeOnRight | 0 | int bool
reCaptchaShow | 0 | int bool
windowTitlePrefix | pinychat | string
dateformat | %Y-%m-%d %H:%M:%S | strftime string
timeformat | %H:%M:%S | strftime string
delayMessage | 0 | int bool
notificationsOn | 1 | int bool

### Example:
    [Main]
    useDefaultAccount = 1
    DefaultAccountName = ausername
    DefaultAccountPass = apassword