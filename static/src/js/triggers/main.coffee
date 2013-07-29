define ['utils', 
        'triggers/scroller', 
        'triggers/store',
        'triggers/densities',
        'triggers/distributions',
        'jquery', 'jquery-ui'], 
(utils, scroller, store, densities, dist, $, _) ->
    console.log "Starting"
    
    channel = utils.definitions.channel
    
    $ ->
        tabs = $('#tabs').tabs()
        
        snrPlot = new dist.TriggerDistributionPlot("#snrs", channel).field "SNR"
        snrPlot.load()
        
        freqPlot = new dist.TriggerDistributionPlot("#freqs", channel).field "Frequency"
        freqPlot.load()
        
        amplPlot = new dist.TriggerDistributionPlot("#ampls", channel).field "Amplitude"
        amplPlot.load()
    
        
        store = new store.TriggerStore channel
        store.garbageCollecting yes
        store.indicateWindow utils.definitions.time_min
        
        scroller = new scroller.TriggerScroller store, "#clusters"
        scroller.windowSize 120
        scroller.scales
            y: d3.scale.log().clamp yes
            z: d3.scale.log().clamp yes
        scroller.limits
            y: [0.1, 100]
            z: [1, 200]
            
        scroller.scrollTo utils.definitions.time_min
        scroller.autoRefresh yes
        scroller.keyScroll yes
        
        #densityPlot = new densities.DensityPlot "#densities", channel
        #densityPlot.scroller scroller
        #densityPlot.load()