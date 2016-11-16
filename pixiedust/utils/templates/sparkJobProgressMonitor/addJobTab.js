{% macro stageRow(stageInfo) -%}
    <tr>
        <td style="max-width:200px">
            Stage {{stageInfo.stageId}} <span id="progressNumTask{{prefix}}{{stageInfo.stageId}}">0</span>/{{stageInfo.numTasks}}:
        </td>
        <td style="max-width: 300px">
            <progress id="progress{{prefix}}{{stageInfo.stageId}}" max="{{stageInfo.numTasks}}" value="0" style="width:200px"></progress>
        </td>
        <td>
            <i title="{{stageInfo.details}}" class="fa fa-info-circle"></i>
            <span id="details{{prefix}}{{stageInfo.stageId}}"></span>
        </td>
    </tr>
{%- endmacro %}

$("#pm_container{{prefix}}").css("border","1px solid #dddddd").css("padding","10px")

$("#progressMonitors{{prefix}}").append(
    '<li><a style="padding: 5px 5px;font-size: 12px;" data-toggle="tab" href="#menu{{prefix}}{{data["jobId"]}}">Job {{data["jobId"]}}({{data["stageInfos"]|length}})</a></li>'
);

$("#tabContent{{prefix}}").append(
'<div id="menu{{prefix}}{{data["jobId"]}}" class="tab-pane fade in active">'+
    '<table>' + 
    {%for stageInfo in data["stageInfos"]%}
        '{{stageRow(stageInfo)|oneline}}'+
    {%endfor%}
    '</table>' +
'</div>'
)

$('.nav-tabs a[href="#menu{{prefix}}{{data["jobId"]}}"]').tab('show');
