{% macro stageRow(stageInfo) -%}
    <tr>
        <td style="max-width:200px">
            Stage {{stageInfo.stageId}} <span id="progressNumTask{{prefix}}{{stageInfo.stageId}}">0</span>/{{stageInfo.numTasks}}:
        </td>
        <td style="max-width: 300px">
            <progress id="progress{{prefix}}{{stageInfo.stageId}}" max="{{stageInfo.numTasks}}" value="0" style="width:200px"></progress>
        </td>
        <td>
            <span id="host{{prefix}}{{stageInfo.stageId}}"></span>
        </td>
        <td>
            <i title="{{stageInfo.details}}" class="fa fa-info-circle"></i>
            <span id="status{{prefix}}{{stageInfo.stageId}}">Not Started</span>
        </td>
    </tr>
{%- endmacro %}

$("#pm_container{{prefix}}").css("border","1px solid #dddddd").css("padding","10px")
var jobName = 'Job {{data["jobId"]}} ({{data["stageInfos"]|length}} '+
            {%if data["stageInfos"]|length > 1%} 'Stages'+ {%else%} 'Stage'+ {%endif%} ')'
$("#pm_overallContainer{{prefix}}").show();
$("#pm_overallJobName{{prefix}}").text(jobName);
$("#pm_overallProgress{{prefix}}").attr("max", {{overalNumTasks}}).attr("value",0);
$("#progressMonitors{{prefix}}").append(
    '<li>'+
        '<a style="padding: 5px 5px;font-size: 12px;" data-toggle="tab" href="#menu{{prefix}}{{data["jobId"]}}">'+
            jobName +
        '</a>'+
    '</li>'
);

$("#tabContent{{prefix}}").append(
'<div id="menu{{prefix}}{{data["jobId"]}}" class="tab-pane fade in active">'+
    '<table>' + 
        '<thead>' +
            '<tr>' +
                '<th style="text-align:center">Stage</th>' +
                '<th style="text-align:center">Progress</th>' +
                '<th style="text-align:center">Executor</th>' +
                '<th style="text-align:center">Details</th>' +
            '</tr>' +
        '</thead>' +
        '<tbody>' + 
        {%for stageInfo in data["stageInfos"]%}
            '{{stageRow(stageInfo)|oneline}}'+
        {%endfor%}
        '</tbody>' +
    '</table>' +
'</div>'
)

$('.nav-tabs a[href="#menu{{prefix}}{{data["jobId"]}}"]').tab('show');
