define ['utils', 
        'coincs/hive',
        'jquery', 'jquery-ui'], 
(utils, hive, $, _) ->
    console.log "Starting"
    
    group = utils.definitions.group
    
    $ ->
        hivePlot = new hive.HivePlot "#hive", group
        hivePlot.snrBaseThreshold 10
        hivePlot.title group.name
        hivePlot.load()