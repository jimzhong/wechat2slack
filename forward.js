var forwardUrl = "http://192.168.88.6:8080/";

function setXMLRequestCallback(cb){
    var oldSend;
    if( XMLHttpRequest.callback ) {
        // we've already overridden send() so just add the callback
        XMLHttpRequest.callback = cb;
    } else {
        XMLHttpRequest.callback = cb;
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
            XMLHttpRequest.callback( this );
            // call the native send()
            oldSend.apply(this, arguments);
        }
    }
}

function forward(name, text) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", forwardUrl + name, true);
    xhr.send(text);
}

function getPathName(url) {
    var a = document.createElement('a');
    a.href = url;
    return a.pathname
}

setXMLRequestCallback( function( xhr ) {
    setTimeout(function () {
        if (xhr.readyState == 4 && xhr.status == 200 && xhr.responseURL.indexOf(forwardUrl) != 0)
        {
            console.log(xhr);
            forward(getPathName(xhr.responseURL).split("/").pop(), xhr.responseText);
        }
    }, 2000);
});
