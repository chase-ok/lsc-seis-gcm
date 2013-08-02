define ['utils', 
        'plots',
        'jquery', 'jquery-ui'], 
(utils, plots, $, _) ->
    console.log "Starting"
    
    group = utils.definitions.group
    
    $ ->
        scatter = new plots.ScatterPlot "#scatter"
        scatter.title group.name
        scatter.axisLabels
            x: "Coincidence Window [s]"
            y: "Field"
        scatter.groups ["Actual", "Time Offset"]
        scatter.sizes
            "Actual": 6
            "Time Offset": 3
        scatter.colors
            "Actual": "black"
            "Time Offset": "#999999"
        scatter.showLegend yes

        utils.loadUnwrappedJSON "/data/coinc/windows-#{group.id}.json", (data) ->
            console.log data

            # silly me in including a window size of 1000...
            data = (datum for datum in data when datum.window <= 100)

            plotField = (name, getValue) ->
                scatter.axisLabels
                    y: name

                actual = []
                timeOffset = []
                for datum in data
                    actual.push [datum.window, getValue datum.actual]
                    for random in datum.rand
                        timeOffset.push [datum.window, getValue random]

                scatter.limits
                    x: d3.extent (x.window for x in data)
                    y: d3.extent (x[1] for x in actual).concat(x[1] for x in timeOffset)

                scatter.plot
                    "Actual": actual
                    "Time Offset": timeOffset

            plotField "Number of Coincidences", (analysis) ->
                analysis.num.overall_coincs

