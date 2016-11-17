$("#status{{prefix}}{{stageId}}").text("{{status}}")

{% if host%}
$("#host{{prefix}}{{stageId}}").text("{{host}}")
{%endif%}