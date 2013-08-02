define ['utils', 
        'plots',
        'jquery', 'jquery-ui'], 
(utils, plots, $, _) ->
    console.log "Starting"
    
    group = utils.definitions.group
    
    $ ->
        scatter = new plots.ScatterPlot "#scatter"

        utils.loadJSON "/data/coinc/windows-#{group.id}.json", (data) ->
            console.log data