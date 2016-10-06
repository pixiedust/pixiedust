{% macro savePixiedustOptions(cellId, options) -%}

var curCell=IPython.notebook.get_cells().filter(function(cell){
    return cell.cell_id=="{{cellId}}";
});
curCell=curCell.length>0?curCell[0]:null;
if (!curCell){
    return console.log("Unable to save options in cell metadata. Reason: Coud not find cell with id", cellId);
}

if(curCell&&curCell.output_area){
    curCell._metadata.pixiedust = curCell._metadata.pixiedust || {}
    var options = {{options}}
    for (var key in options) { 
        curCell._metadata.pixiedust.displayParams[key] = options[key]; 
    }
}

{%- endmacro %}
