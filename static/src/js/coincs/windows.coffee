define ['utils', 
        'plots',
        'jquery', 'jquery-ui'], 
(utils, plots, $, _) ->
    console.log "Starting"
    
    group = utils.definitions.group
    
    $ ->
        console.log "Page loaded"
        scatter = new plots.ScatterPlot "#scatter"