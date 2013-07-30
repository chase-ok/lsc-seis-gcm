define ['utils', 
        'coincs/hive',
        'jquery', 'jquery-ui'], 
(utils, hive, $, _) ->
    console.log "Starting"
    
    group = utils.definitions.group
    
    $ ->
        hivePlot = new hive.HivePlot "#hive", group
        hivePlot.title group.name
        hivePlot.snrThreshold 15
        hivePlot.load()