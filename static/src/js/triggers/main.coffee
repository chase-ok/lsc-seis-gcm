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
        
        snrPlot = new dist.TriggerDistributionPlot("#snrs").field "SNR"
        snrPlot.load()
        
        #freqPlot = new dist.TriggerDistributionPlot("#freqs").field "Frequency"
        #freqPlot.load()
        
        amplPlot = new dist.TriggerDistributionPlot("#ampls").field "Amplitude"
        amplPlot.load()
    
    #console.log 'hello world!'
    #startTime = utils.definitions.time_min
    #
    #$ ->
        #store = new store.TriggerStore()
        #store.garbageCollecting yes
        #store.indicateWindow startTime, startTime + 30
        #
        #scroller = new scroller.TriggerScroller store, "#triggers"
        #scroller.windowSize 120
        #scroller.scales
            #y: d3.scale.log().clamp yes
            #z: d3.scale.log().clamp yes
        #scroller.title "Triggers"
        #scroller.limits
            #y: [0.1, 100]
            #z: [1, 200]
            #
        #scroller.scrollTo startTime
        #scroller.autoRefresh yes
        #scroller.keyScroll yes
        #
        #densityPlot = new densities.DensityPlot "#densities"
        #densityPlot.scroller scroller
        #densityPlot.load()