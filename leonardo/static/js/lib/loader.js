/*
 *  Leonardo resource loader
 */
var leonardo = function(leonardo) {
    leonardo.utils = leonardo.utils || {};
    /**
     * Add JS / CSS resource to DOM, if not exists
     * @example loadResource({src:'/my.js',async:true,defer:true}) <br>
     * leonardo.utils.loadResource("/my.js") or arrays of them 
     * leonardo.utils.loadResource(["/lol.js","/lol2.js",{src:"/lol2",async:true}])
     * leonardo.utils.loadResource("/lol.css",{src:"/megalol.css"})
     * USE ONLY ABSOLUTE PATHS
     */
    leonardo.utils.loadResource = function (resources){
        var addScriptFn = function(script){
            var resources = document.getElementsByTagName('script'),found=false;
            for(var i=0;i<resources.length;i++){
                var fullSrc = (script.src.indexOf("://") > -1)?script.src:window.location.protocol+"//"+script.src;
                if(resources[i].src===fullSrc){
                    found=true;
                    break;
                }
            }
            if(!found){
                var domScript = document.createElement('script'); 
                domScript.type = "text/javascript";
                if(script.callback){ 
                    if(typeof script.callback === 'function'){
                        domScript.onload=script.callback;
                    }else{
                        domScript.onload=window[script.callback];
                    }
                }
                domScript.src = script.src;
                domScript.async = script.async && script.async==true;
                domScript.defer = script.defer && script.defer==true;
                resources[0].parentNode.insertBefore(domScript, resources[0]);
            }
        }, addStyleFn = function(style){
            var link = document.createElement("link");
            link.type = "text/css";
            link.rel = "stylesheet";
            link.href = style.src;
            document.getElementsByTagName("head")[0].appendChild(link);
        }, addElement = function(elem){
            var lastDot = elem.src.lastIndexOf("."), resExt = elem.src.substring(lastDot);
            if(resExt === '.css'){
                addStyleFn(elem);
            }else{
                addScriptFn(elem);
            }
        };
        if(resources instanceof Array){
            for(var i=0;i<resources.length;i++){
                if(typeof resources[i] === 'object' && resources[i].hasOwnProperty("src")){
                    addElement(resources[i])
                }else if(typeof resources[i] === 'string'){
                    addElement({src:resources[i]});
                }else{
                    console.log("Resource #"+i+" is invalid!");
                }
            }
        }else{
            if(typeof resources === 'object' && resources.hasOwnProperty("src")){
                addElement(resources);
            }else if(typeof resources === 'string'){
                addElement({src:resources});
            }else{
                console.log("Resource is invalid!");
            }
        }
    };
    
    // window and fn temponary fallback
    leonardo.fn = leonardo.fn || {loadResource: leonardo.utils.loadResource};
    window.loadResource = leonardo.utils.loadResource;
    return leonardo;
}(leonardo || {});