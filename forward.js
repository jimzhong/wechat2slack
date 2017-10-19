var messageUrl = "https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsync";
var contactUrl = "https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxbatchgetcontact"
var forwardUrl = "http://127.0.0.1:8080/";

function addXMLRequestCallback(callback){
    var oldSend, i;
    if( XMLHttpRequest.callbacks ) {
        // we've already overridden send() so just add the callback
        XMLHttpRequest.callbacks.push( callback );
    } else {
        // create a callback queue
        XMLHttpRequest.callbacks = [callback];
        // store the native send()
        oldSend = XMLHttpRequest.prototype.send;
        // override the native send()
        XMLHttpRequest.prototype.send = function(){
            // process the callback queue
            // the xhr instance is passed into each callback but seems pretty useless
            // you can't tell what its destination is or call abort() without an error
            // so only really good for logging that a request has happened
            // I could be wrong, I hope so...
            // EDIT: I suppose you could override the onreadystatechange handler though
            for( i = 0; i < XMLHttpRequest.callbacks.length; i++ ) {
                XMLHttpRequest.callbacks[i]( this );
            }
            // call the native send()
            oldSend.apply(this, arguments);
        }
    }
}

function getUrlParts(url) {
    var a = document.createElement('a');
    a.href = url;

    return {
        href: a.href,
        host: a.host,
        hostname: a.hostname,
        port: a.port,
        pathname: a.pathname,
        protocol: a.protocol,
        hash: a.hash,
        search: a.search
    };
}

function forward(name, text) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", forwardUrl + name, true);
    xhr.send(text);
}

addXMLRequestCallback( function( xhr ) {
    setTimeout(function () {
        if (xhr.readyState == 4 && xhr.status == 200)
        {
            console.log(JSON.parse(xhr.responseText));
            forward(getUrlParts(xhr.responseURL).pathname.split("/").pop(), xhr.responseText);
        }
    }, 3000);
});
