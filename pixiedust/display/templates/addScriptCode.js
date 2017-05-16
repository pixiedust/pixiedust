if (typeof pixiedust == "undefined"){
    var s=document.getElementsByTagName('script')[0];
    var g=document.createElement({%if type is equalto "javascript"%} 'script' {%else%} 'style' {%endif%} );
    g.type={%if type is equalto "javascript"%} 'text/javascript'{%else%}'text/css'{%endif%};
    g.defer=false; 
    g.async=false;
    var code = "{{code|trim|removeJSComments|replace("\\","\\\\")|replace("\"" ,"\\\"")|replace("\n", "\\n\"+\n\"")}}";
    try{
        g.appendChild(document.createTextNode(code));
    }catch(e){
        g.text = code;
    }
    s.parentNode.insertBefore(g,s);
}