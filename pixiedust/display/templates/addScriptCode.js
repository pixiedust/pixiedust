var s=document.getElementsByTagName('script')[0];
var g=document.createElement('script');
g.type='text/javascript';
g.defer=false; 
g.async=false;
var code = "{{code|trim|removeJSComments|replace("\\","\\\\")|replace("\"" ,"\\\"")|replace("\n", "\\n\"+\n\"")}}";
try{
    g.appendChild(document.createTextNode(code));
}catch(e){
    g.text = code;
}
s.parentNode.insertBefore(g,s);