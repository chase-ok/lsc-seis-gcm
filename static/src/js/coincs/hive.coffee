define ['utils', 'plots', 'd3', 'jquery'], (utils, plots, d3, $) ->
    {definitions: defs, describe, loadJSON, radians} = utils
    
    class HivePlot extends plots.SvgPlot
        constructor: (rootSelector, @group) ->
            margin = 
                left: 10
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
                x: @_plotWidth/(@_numChannels - 1)
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

            bars = describe @canvas.selectAll(".bar")
                                   .data([0...@_numChannels])
                                   .enter().append("g"),
                class: "bar"
                transform: (bar) -> "translate(#{chainPosition bar}, 0)"
                                      

            describe bars.selectAll("rect")
                         .data(@_channels)
                         .enter().append("rect"),
                x: @_barSize.x/2
                y: (channel) -> channelPosition channel.id
                width: @_barSize.x
                height: @_barSize.y
                stroke: "none"
                fill: (channel) -> channelColor channel.id

            # TODO: bars.on(mouseover)

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

            line = d3.svg.line().interpolate('cardinal').tension(0.5)

            path = describe linkGroup.selectAll("path.link")
                                     .data(links)
                                     .enter().append("path"),
                class: "link"
                fill: "none"
                stroke: (link) -> 
                    if snrRatio(link.snrRatio) > 0 then "red" else "green"
                "stroke-width": (link) ->
                    snr link.snr
                "stroke-opacity": 0.5
                d: (link) ->
                    x0 = chainPosition link.chainPosition
                    y0 = channelPosition(link.startChannelId) + time(link.time)
                    x1 = chainPosition (link.chainPosition + 1)
                    y1 = channelPosition(link.endChannelId) + time(link.time)
                    line [[x0, y0], [x1, y1]]

            path.on "mouseover", (link) ->
                describe linkGroup.selectAll("path"),
                    "stroke-opacity": (match) ->
                        if match.coincId is link.coincId then 1.0 else 0.05
                    "stroke-width": (match) ->
                        base = snr match.snr
                        if match.coincId is link.coincId then 2*base else base/2

            path.on "mouseout", ->
                describe linkGroup.selectAll("path"),
                    "stroke-opacity":  0.5
                    "stroke-width": (link) -> snr link.snr

    return {HivePlot}