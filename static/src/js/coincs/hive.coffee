define ['utils', 'plots', 'd3', 'jquery'], (utils, plots, d3, $) ->
    {definitions: defs, describe, loadJSON, radians} = utils
    
    class HivePlot extends plots.SvgPlot
        constructor: (rootSelector, @group) ->
            margin = 
                left: 30
                top: 30
                right: 10
                bottom: 10
            dimensions = ['time', 'snr', 'snrRatio', 'channelColor',
                          'chainPosition', 'channelPosition']
            super rootSelector, margin, dimensions
            
            @_channels = @group.channels
            @_channelIds = (c.id for c in @_channels)
            @_numChannels = @_channels.length

            @_infoSize =
                x: 100
                y: @canvasSize.y

            @_plotSize = 
                x: @canvasSize.x - @_infoSize.x
                y: @canvasSize.y

            @_barSpacing =
                x: @_plotSize.x/(@_numChannels - 1)
                y: 5
            @_barSize = 
                x: 10
                y: (@canvasSize.y - @_barSpacing.y*(@_numChannels+1))/@_numChannels

            @snrThreshold 0

            @scales
                time:
                    d3.scale.linear().range([0, @_barSize.y]).clamp(yes)
                snr:
                    d3.scale.linear().range([1.0, 6.0])
                snrRatio: 
                    d3.scale.linear()
                            .domain([0.5, 1.5])
                            .range([-1, 1])
                            .clamp(yes)
                channelColor: 
                    d3.scale.category20().domain(@_channelIds)
                chainPosition: 
                    d3.scale.ordinal()
                            .domain([0...@_numChannels])
                            .range(@_barSpacing.x*i for i in [0...@_numChannels])
                channelPosition:
                    d3.scale.ordinal()
                            .domain(@_channelIds)
                            .range((i+1)*@_barSpacing.y + i*@_barSize.y for i in [0...@_numChannels])

        snrThreshold: (threshold) ->
            if threshold?
                @_snrThreshold = threshold
                @declareDirty()
                this
            else
                @_snrThreshold

        load: ->
            url = "#{defs.webRoot}/coinc/group/#{@group.id}/all"
            loadJSON url, (data) =>
                {@coincs} = data
                @_draw()

        _draw: ->
            snrExtent = d3.extent (Math.min(c.snrs...) for c in @coincs)
            snrExtent[0] = Math.max @snrThreshold(), snrExtent[0]
            # coincs best be sorted by time
            @limits
                time: [@coincs[0].times[0], 
                       Math.max(@coincs[@coincs.length-1].times...)]
                snr: snrExtent

            @prepare()
            @_drawLinks()
            @_drawBars()

        _drawBars: ->
            {channelColor, chainPosition, channelPosition} = @maps()

            barGroups = describe @canvas.selectAll(".hive-bar")
                                        .data([0...@_numChannels])
                                        .enter().append("g"),
                class: "hive-bar"
                transform: (bar) -> "translate(#{chainPosition bar}, 0)"
                                      

            bars = describe barGroups.selectAll("rect")
                                     .data((pos) -> ([pos, c] for c in @_channels))
                                     .enter().append("rect"),
                x: -@_barSize.x/2
                y: (bar) -> channelPosition bar[1].id
                width: @_barSize.x
                height: @_barSize.y
                stroke: "none"
                fill: (bar) -> channelColor bar[1].id

            bars.on "mouseover", @_mouseOver (bar, link) =>
                @coincs[link.coincId].channel_ids[bar[0]] is bar[1].id

            bars.on "mouseout", @_mouseOut()

        _drawLinks: ->
            linkGroup = describe @canvas.append("g")
            
            links = []
            threshold = @snrThreshold()
            for i in [0...@coincs.length]
                coinc = @coincs[i]
                continue if coinc.snrs[0] < threshold

                for pos in [0...coinc.length-1]
                    links.push
                        coincId: i
                        chainPosition: pos
                        time: coinc.times[pos]
                        snr: coinc.snrs[0],
                        snrRatio: coinc.snrs[pos+1]/coinc.snrs[pos]
                        startChannelId: coinc.channel_ids[pos]
                        endChannelId: coinc.channel_ids[pos+1]
            
            {time, snr, snrRatio, channelColor, chainPosition, 
             channelPosition} = @maps()

            # NOTE! We need to flip x and y for diag to be horizontal!
            line = d3.svg.diagonal().projection (d) -> [d.y, d.x]

            path = describe linkGroup.selectAll("path.link")
                                     .data(links)
                                     .enter().append("path"),
                class: "link"
                fill: "none"
                stroke: (link) -> 
                    if snrRatio(link.snrRatio) > 0 then "red" else "green"
                "stroke-width": (link) -> snr link.snr
                "stroke-opacity": 0.5
                d: (link) ->
                    line
                        source:
                            y: chainPosition link.chainPosition
                            x: channelPosition(link.startChannelId) + time(link.time)
                        target:
                            y: chainPosition (link.chainPosition + 1)
                            x: channelPosition(link.endChannelId) + time(link.time)

            path.on "mouseover", @_mouseOver (link, match) -> 
                link.coincId is match.coincId

            path.on "mouseout", @_mouseOut()

        _mouseOver: (matches) ->
            {snr} = @maps()
            (data) ->
                describe @canvas.selectAll("path"),
                    "stroke-opacity": (link) ->
                        if matches data, link then 1.0 else 0.05
                    "stroke-width": (link) ->
                        base = snr link.snr
                        if matches data, link then 2*base else base/2

        _mouseOut: ->
            {snr} = @maps()
            ->
                describe linkGroup.selectAll("path"),
                    "stroke-opacity":  0.5
                    "stroke-width": (link) -> snr link.snr

    return {HivePlot}