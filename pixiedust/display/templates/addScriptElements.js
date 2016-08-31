(function(){
    var g,s=document.getElementsByTagName('script')[0];
    function hasScriptElement(script){
        var scripts = document.getElementsByTagName('script');
        for (var i=0;i<scripts.length;i++){
            if(scripts[i].src===script){
                return true;
            }
        }
        return false;
    }
    var callback;
    {%for t in this.scripts %}
        callback = function(){
            {%if t[2] is not none%}
                {%for locCall in t[2]|smartList %}
                    !function(){
                        {{locCall}}
                    }();
                {%endfor%}
            {%endif%}
        };
        if ({%if t[1] is not none%}(typeof {{t[1]}}=='undefined')&&{%endif%}!hasScriptElement('{{t[0]}}')){
            g=document.createElement('script');
            g.type='text/javascript';
            g.defer=false; 
            g.async=false; 
            g.src='{{t[0]}}';
            g.onload = g.onreadystatechange = callback;
            s=s.parentNode.insertBefore(g,s).nextSibling;
        }else{
            callback();
        }
    {%endfor%}
})();