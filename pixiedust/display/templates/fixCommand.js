{% if this.scalaKernel %}
command=command.replace(/(\w*?)\s*=\s*('(\\'|[^'])*'?)/g, function(a, b, c){
    return '("' + b + '","' + c.substring(1, c.length-1) + '")';
})
{% endif %}