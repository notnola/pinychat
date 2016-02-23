var instance = {};

function tinychat(flashvars, options)
{
	var embed = new TinychatEmbed(flashvars, options);
	embed.initialize();
	
	return embed;
}

function TinychatEmbed(flashvars, options)
{
	if(typeof flashvars.room != 'string')
	{
		this.initialize = function() { alert('Developer: please send "room" and "target" variables.'); };
		return this;
	}

   	 // Defaults
	this.applicationId = "tinychat" + flashvars.room;
 	this.flashvars = {
		target: "client",
		key: "tinychat"
	};
	
	this.options = {
     	baseUrl: document.location.protocol + "//tinychat.com/embed/",
		bgcolor: "#222222"
     };

     // Populate with custom settings from params
	for(var i in flashvars)
	{
		this.flashvars[i] = flashvars[i];
	}
	
	for(var i in options)
	{
		this.options[i] = options[i];
	}

	this.data = {
		scripts: Array(),
        interval: {},
		messageCount: 0,
		publicChatListInFocus: false,
		privateChatListInFocus: false,
		inFocus: true,
		originalDocumentTitle: document.title,
		titleSwapTimer: null,
		SWAP_TIMEOUT: 2000,
		swapToPrivateChatMessageNotice: true,
		privateChatSenderName: null
	};
	
	this.ping_interval = false;
}

TinychatEmbed.prototype.load_facebook_js = function()
{
	var _self = this;

    if(!document.getElementById("fb-root")) 
    {
        var div = document.createElement("div");
        div.id = "fb-root";
        document.body.appendChild(div);
    }

      (function(d, s, id){
         var js, fjs = d.getElementsByTagName(s)[0];
         if (d.getElementById(id)) {return;}
         js = d.createElement(s); js.id = id;
         js.src = "//connect.facebook.net/en_US/sdk.js";
         fjs.parentNode.insertBefore(js, fjs);
       }(document, 'script', 'facebook-jssdk'));


	_self.getApplication().facebook_loaded(true);
}


TinychatEmbed.prototype.load_script = function(url, callback, timeout)
{
	if(!timeout)
	{
		timeout = 5;
	}

	var _self = this;
	
	for(var i in this.data.scripts)
	{
		if(this.data.scripts[i] == url)
		{
            // If already loaded, invoke callback and bail.
			callback(true);
            return;
		}
	}
	
	this.data.scripts[this.data.scripts.length] = url;
	
 	var script = document.createElement("script");
	script.src = url;
	script.type = "text/javascript";
	
	if(typeof callback == 'function')
	{
		//http://www.aaronpeters.nl/blog/prevent-double-callback-execution-in-IE9
		if(script.readyState)
		{ // IE, incl. IE9
			script.onreadystatechange = function()
			{
				if (script.readyState == "loaded" || script.readyState == "complete")
				{
					script.onreadystatechange = null;
					window.clearTimeout(_self.data.interval[url]);
					callback(true);
				}
			};
		}
		else
		{
			script.onload = function()
			{ // Other browsers
				window.clearTimeout(_self.data.interval[url]);
				callback(true);
			};
		}
		
		
		document.getElementsByTagName("head")[0].appendChild(script);
		this.data.interval[url] = window.setTimeout(function()
		{
			script.onreadystatechange = function() {};
			script.onload = function() { };
			callback(false);
		}, (timeout * 1000));
	}
	
	return true;
}

TinychatEmbed.prototype.initialize = function()
{
	var _self = this;
	
	this.load_script("https://ajax.googleapis.com/ajax/libs/swfobject/2.2/swfobject.js", function()
	{
		_self.embedFlash();
		
		if(typeof _self.callback == 'function')
		{
			_self.callback();
		}
	
	});

	this.load_script("//connect.soundcloud.com/sdk-2.0.0.js", function()
	{
		 SC.initialize({
   			 client_id: "b85334a9b08edb6778a50d965444fd39"
 		 });
	
	});	
	
        var protocol = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
	this.load_script(protocol+'google-analytics.com/ga.js', function()
	{
	    var pageTracker = _gat._getTracker('UA-9094897-1');
	    pageTracker._initData();
	    pageTracker._trackPageview();
	});
}

TinychatEmbed.prototype.reloadFlash = function()
{
    var targetDiv = document.createElement("div");
    targetDiv.id = this.flashvars.target;
    document.getElementById(this.applicationId).parentNode.appendChild(targetDiv);

    swfobject.removeSWF(this.applicationId);
    this.embedFlash();
}

TinychatEmbed.prototype.embedFlash = function()
{
	instance[this.flashvars.target] = this;
    
	var majorVersion = swfobject.getFlashPlayerVersion().major;
	var minorVersion = swfobject.getFlashPlayerVersion().minor;
	var appUrl = this.getApplicationUrl(majorVersion, minorVersion);
	var versionString = majorVersion + "." + minorVersion + ".0"; 
	
	var params = {
		wmode: this.flashvars.wmode,
		quality: "high",
		allowFullscreen: "true",
		allowFullscreenInteractive: "true",
		allowScriptAccess: "always",
		bgcolor: this.options.bgcolor
	};

	var attributes = {
		id: this.applicationId ,
		name: this.applicationId,
		align: "middle"
	};
	
	swfobject.embedSWF(appUrl, this.flashvars.target, "100%", "100%", versionString, "/expressInstall.swf", this.flashvars, params, attributes);
	
	this.registerListeners();
	this.registerPingInterval();
	
	if (swfobject.hasFlashPlayerVersion("11.0")) {
          // has Flash
        }
        else {          
		// no Flash
                //alert("Sorry, you must install the Flash Player to continue.");                
		window.setTimeout( '$("#preload").html(\'<div id="flash_warning" style=" margin: 100px auto;"><p>The Adobe Flash Player is required.<br/><a href="http://www.adobe.com/go/getflashplayer" target="_blank"><img src="http://tinychat.com/public/images/get_flash_player.gif" alt="Get Adobe Flash player" /></a><br /><noscript>Please enable JavaScript</noscript></p></div>\');', 10000);
        }
	
}


TinychatEmbed.prototype.registerPingInterval = function()
{
	var that = this;
	var check_result = function(result)
	{
		
        /*if($(result).find('geoip').attr('country_name') == 'Morocco')
    	{
    		if(self == top)
    		{
                top.location = "http://tinychat.com/?land_ma";
            }
            else
            {
                window.location = "http://tinychat.com/?land_ma";
            }
        }*/
	};
	
	var ping = function()
	{
		
		$.get(document.location.protocol + "//tinychat.com/api/find.room/" + that.flashvars.room+"?site="+that.flashvars.key, function(result)
        {
	        	check_result(result);
        });
        
        if(that.flashvars.greenroom == "true")
        {
        
			$.get(document.location.protocol + "//tinychat.com/api/find.room/" + that.flashvars.room+"?site=greenroom", function(result)
	        {
	        	check_result(result);
	        }); 
        }
        
	};

	if(this.ping_interval)
	{
		window.clearInterval(this.ping_interval);
	}
	else
	{
		ping();
	}
	
	var seconds = 300;
	
	this.ping_interval = window.setInterval(ping, 1000 * seconds);
}


TinychatEmbed.prototype.onFocusHandler = function()
{
    if(this.data.publicChatListInFocus)
        this.data.messageCount = 0;
        
    if(this.data.privateChatListInFocus)
        this.resetPrivateChatMessageNotice();

    this.data.inFocus = true;    
    this.updateTitle();    
}

TinychatEmbed.prototype.onBlurHandler = function()
{
    this.data.inFocus = false;    
    this.updateTitle();    
}

TinychatEmbed.prototype.registerListeners = function()
{
	var _self = this;
	
	window.onfocus = function() { _self.onFocusHandler(); };
	window.onblur = function() { _self.onBlurHandler(); };

    if(window.addEventListener) {
        window.addEventListener("message", 
        function(event) { _self.oAuthDone(event.data); }, false);
    } 
    else if(window.attachEvent) {
        window.attachEvent("onmessage", 
        function(event) { _self.oAuthDone(event.data); });
    }
}

TinychatEmbed.prototype.getApplicationUrl = function(majorVersion, minorVersion)
{
    var swfName;
    swfName = "Tinychat-11.1-1.0.0.0643.swf";

/*    if(majorVersion > 10)
    {
        swfName = "Tinychat-11.1-1.0.0.0629.swf";
    }
    else if(majorVersion == 10)
    {
        if(minorVersion >= 3)
            swfName = "Tinychat-10.3-1.0.0.0629.swf";
        else if(minorVersion == 2)
            swfName = "Tinychat-10.2-1.0.0.0629.swf";
        else
            swfName = "Tinychat-10.0-1.0.0.0629.swf";
    } */

    // version is for cache busting, not choosing an actual version
    return this.options.baseUrl + swfName + "?version=1.0.0.0650";
}
	
TinychatEmbed.prototype.openSecurityPanel = function(panel)
{
	var url = this.options.baseUrl + "SecurityPanelPopup.html?panel=" + panel + "&" + Math.random();
	var iframe = createIframe("SecurityPanel", url, 215, 138);
	this.centerElement(iframe);
	
	document.body.appendChild(iframe);
}
	
TinychatEmbed.prototype.closeSecurityPanel = function()
{
	var iframe = getSecurityPanel();
	document.body.removeChild(iframe);
	
	var app = this.getApplication();
	app.securityPanelClosed();
}
	
TinychatEmbed.prototype.securityPanelAuthorizationChanged = function(bool)
{
	var app = this.getApplication();
	app.securityPanelAuthorizationChanged(bool);
}
	
TinychatEmbed.prototype.getSecurityPanel = function()
{
	return document.getElementById("SecurityPanel");
}
	
TinychatEmbed.prototype.getApplication = function()
{
	return document.getElementById(this.applicationId);
}

TinychatEmbed.prototype.createIframe = function(id, url, width, height)
{
	var iframe = document.createElement("IFRAME"); 
	iframe.allowTransparency = "true";
	iframe.frameBorder = 0;
	iframe.style.overflow = "hidden";
	iframe.style.position = "absolute";
	iframe.style.display = "block";
	iframe.id = id;
	iframe.setAttribute("src", url); 
	
	if(width)
	{
		iframe.width = width;
	}
	   
	if(height)
	{
		iframe.height = height;
	}
	
	return iframe;
}

TinychatEmbed.prototype.createFloatingDiv = function(id)
{
    var div = document.createElement("div");
    
    if(id)
    {
	    div.id = id;
    }
    
    document.body.appendChild(div);
	
	div.style.position = "fixed";
	div.style.left = "45%";
	div.style.top = "45%";
	div.style.zIndex = "50";
}

TinychatEmbed.prototype.toggleElementVisibility = function(id, visible)
{
    var element = document.getElementById(id);

    if(element)
    {
       if(visible)
       {
           element.style.display = "block";
       }
       else
       {
           element.style.display = "none";
       }
    }
}

TinychatEmbed.prototype.centerElement = function(element)
{
	var point = window.size();
	element.style.position = "fixed";
	element.style.left = point.x + "px";
	element.style.top = point.y + "px";
}

TinychatEmbed.prototype.clientOAuth = function(site, type, room, cid) 
{
    var _self = this;
    var app = _self.getApplication();
    var url = document.location.protocol + "//tinychat.com/api/clientoauth?type=" + type +
    "&site=" + site + "&room=" + room + "&cid=" + cid;

    var wid = _self.openPopup(url); 

    if(!wid || wid == null) 
    {  
        app.oAuthResponse("blocked");
		return; 
    }

    var lasthash = "" + window.location.hash;

    var timer = setInterval(function () {
        if(wid.closed) {
            clearInterval(timer);
			_self.clearHash();
            app.oAuthResponse("closed");
			return;
        }

        // location.hash method
	    try {
	        var l = "" + window.location.hash;

			if("" + window.location.hash != lasthash ) {
			    var json = unescape(window.location.hash.substring(1));
                
                if(json.indexOf('#') > 0) {
                        json = json.substring(0, json.indexOf('#'));
                }
					
                var resp = jQuery.parseJSON(json);
					
                try {
                      app.oAuthResponse(resp.res, resp.type, resp.id, resp.name, resp.pic);
                } 
                catch (x) { 
                    //  console.error ( x );
                }

                clearInterval(timer);
                wid.close();
                _self.clearHash();
                return;
			}
		} 
        catch(x) {}

        // try postmessage method for non tinychat.com embeds
        try {
            var l = "" + window.location;
            var tc = l.indexOf(document.location.protocol +"//tinychat.com");
            
            if(tc != 0 && wid.postMessage) { 
                wid.postMessage(timer, document.location.protocol +"//tinychat.com/closepopup"); 
			} 
            else {
                // materialize function method
			    var resp = wid.checkoauth();

				if(resp.done) {
		            try {
						  app.oAuthResponse(resp.res, resp.type, resp.id, resp.name, resp.pic);
                    } 
                    catch (x) { 
					    //  console.error ( x );
					}

                    clearInterval(timer);
                    wid.close();
                    _self.clearHash();
					return;
				}
			}
		} 
        catch(x) { 
            // console.error ( x ); 
		}
    }, 1000);
}

TinychatEmbed.prototype.clearHash = function() {
    var l = "" + window.location;
    window.location = l.indexOf('#') > 0 ? l.substring(0, l.indexOf('#')) + '#' : l + '#';
}

TinychatEmbed.prototype.oAuthDone = function(data) {
    try {
        if(data) {
            var resp = data.split(/,/);

            if(resp.length == 5) {
                clearInterval(resp[0]);
                var app = this.getApplication();
                app.oAuthResponse('OK', resp[1], resp[2], resp[3], resp[4]);
            }
        }
    } 
    catch (x) {
        console.error ( x );
    }
   // window.close();
}

TinychatEmbed.prototype.openPopup = function(url, width, height) 
{
    if(!width)
        width = 785;

    if(!height)
        height = 450;

    return window.open(url, "win", "menubar=no,width=" + width + ",height=" + height+ ",toolbar=no");
}

TinychatEmbed.prototype.openCaptchPanel = function(token) {
	ShowRecaptcha(token);
}

TinychatEmbed.prototype.openProfileInfo = function(profile_name) {
	ShowProfileInfo(profile_name);
}


TinychatEmbed.prototype.tracksLoadedSoundCloud = function(params) {
 
    var _self = this;

    SC.get("/tracks", params, function(tracks) {
	var app = _self.getApplication();
	app.soundcloud_loaded(tracks);
    });

}


// Doesn't return a window object as Flash may choke on parsing 
// responses from ExternalInterface calls.
TinychatEmbed.prototype.openPopupFromSwf = function(url, width, height)
{
    if (url.indexOf("facebook.com/sharer") > -1 )
    {
	return;
    } 
    this.openPopup(url, width, height);
    //alert(url, width, height);
}

/** Chat message received indicators **/
TinychatEmbed.prototype.getPublicChatUnreadMessageCount = function()
{
	return this.data.messageCount;
}

TinychatEmbed.prototype.increasePublicChatUnreadMessageCount = function()
{
    if(!this.data.publicChatListInFocus || !this.data.inFocus)
    {
        this.data.messageCount++;
        this.updateTitle();
    }
}

TinychatEmbed.prototype.privateMessageReceived = function(senderName)
{
    if(!this.data.privateChatListInFocus || !this.data.inFocus)
    {
        if(this.data.titleSwapTimer)
            this.resetPrivateChatMessageNotice();

        this.data.privateChatSenderName = senderName;
        this.swapTitleDisplay();
    }
}

TinychatEmbed.prototype.swapTitleDisplay = function()
{
    if(this.data.swapToPrivateChatMessageNotice)
    {
        document.title = this.data.privateChatSenderName + " sent you a message!";
    }
    else
    {
        this.updateTitle();
    }

    this.data.swapToPrivateChatMessageNotice = !this.data.swapToPrivateChatMessageNotice;

    // Loop until the timeout is cleared
    var _this = this;
    this.data.titleSwapTimer = setTimeout(function() { _this.swapTitleDisplay(); }, this.data.SWAP_TIMEOUT);
}

TinychatEmbed.prototype.publicChatListFocusChange = function(bool)
{
    this.data.publicChatListInFocus = bool;
    
    if(bool)
    {
        this.data.messageCount = 0;
        this.updateTitle();
    }
}

TinychatEmbed.prototype.privateChatListFocusChange = function(bool)
{
    this.data.privateChatListInFocus = bool;
    
    if(bool)
    {
        this.resetPrivateChatMessageNotice();
        this.updateTitle();
    }
}

TinychatEmbed.prototype.updateTitle = function()
{
    if(this.data.messageCount == 0)
    {
        document.title = this.data.originalDocumentTitle;
    }
    else if(this.data.messageCount > 99)
        document.title = this.data.originalDocumentTitle + " (99+)";
    else if(this.data.messageCount > 0)
        document.title = this.data.originalDocumentTitle + " (" + this.data.messageCount + ")";
}

TinychatEmbed.prototype.resetPrivateChatMessageNotice = function()
{
    clearTimeout(this.data.titleSwapTimer);
    this.data.titleSwapTimer = null;
    this.data.privateChatSenderName = null;
    this.data.swapToPrivateChatMessageNotice = true;
}

TinychatEmbed.prototype.showCaptcha = function(room, guestId)
{
    this.openPopup(document.location.protocol + "//tinychat.com/api/captcha?room=" + encodeURIComponent(room) + "&guest_id=" + encodeURIComponent(guestId), 400, 300);
};

function verifyEmbedCaptcha(hash)
{
    embed.getApplication().setChatHash(hash);
}

//Found at demtron.com
window.size=function()
{var w=0;var h=0;if(!window.innerWidth)
{if(!(document.documentElement.clientWidth==0))
{w=document.documentElement.clientWidth;h=document.documentElement.clientHeight;}
else
{w=document.body.clientWidth;h=document.body.clientHeight;}}
else
{w=window.innerWidth;h=window.innerHeight;}
return{width:w,height:h};}
window.center=function()
{var hWnd=(arguments[0]!=null)?arguments[0]:{width:0,height:0};var _x=0;var _y=0;var offsetX=0;var offsetY=0;if(!window.pageYOffset)
{if(!(document.documentElement.scrollTop==0))
{offsetY=document.documentElement.scrollTop;offsetX=document.documentElement.scrollLeft;}
else
{offsetY=document.body.scrollTop;offsetX=document.body.scrollLeft;}}
else
{offsetX=window.pageXOffset;offsetY=window.pageYOffset;}
_x=((this.size().width-hWnd.width)/2)+offsetX;_y=((this.size().height-hWnd.height)/2)+offsetY;return{x:_x,y:_y};}

