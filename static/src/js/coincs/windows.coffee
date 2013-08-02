define ['utils', 
        'plots',
        'd3',
        'jquery', 'jquery-ui'], 
(utils, plots, d3, $, _) ->
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

                yLimits = d3.extent (x[1] for x in actual).concat(x[1] for x in timeOffset)
                if yLimits[0] is yLimits[1]
                    yLimits[1] += 1.0
                else
                    yLimits[1] *= 1.1

                scatter.limits
                    x: d3.extent (x.window for x in data)
                    y: yLimits

                scatter.plot
                    "Actual": actual
                    "Time Offset": timeOffset

            fields = [["Number of Coincidences", (d) -> d.num.overall_coincs],
                      ["Coincidence Rate [1/s]", (d) -> d.rates.overall_coincs],
                      ["Coincidence Rate Ratio", (d) -> d.rates.overall_coincs/d.rates.overall_triggers],
                      ["Mean Coincidence Length", (d) -> d.lengths.mean],
                      ["Max Coincidence Length", (d) -> d.lengths.max],
                      ["Mean Abs. Frequency Diff [Hz]", (d) -> d.freqs.diffs.mean],
                      ["Frequency Spearman R", (d) -> d.freqs.correl.spearmanr[0]],
                      ["Frequency Pearson R", (d) -> d.freqs.correl.pearsonr[0]],
                      ["Mean Abs. SNR Diff", (d) -> d.snrs.diffs.mean],
                      ["SNR Spearman R", (d) -> d.snrs.correl.spearmanr[0]],
                      ["SNR Pearson R", (d) -> d.snrs.correl.pearsonr[0]],
                      ["Mean dt [s]", (d) -> d.dts.mean],
                      ["Median dt [s]", (d) -> d.dts.median],
                      ["Max dt [s]", (d) -> d.dts.max]]

            plotField fields[0]...

            select = d3.select("body").append("select")
            options = select.selectAll("option").data(fields).append("option")
            options.text (d) -> d[0]
            select.on "change", ->
                console.log select.node()
                plotField fields[select.node().selectedIndex]...


