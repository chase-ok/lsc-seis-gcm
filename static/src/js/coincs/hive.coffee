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
                          'chainPosition', 'channelRadius']
            super rootSelector, margin, dimensions
            
            @_channels = @group.channels
            @_channelIds = (c.id for c in @_channels)
            @_numChannels = @_channels.length

            @radius =
                outer: Math.min(@canvasSize.x, @canvasSize.y)/2
                inner: 70

            @_radiusChunk = (@radius.outer - @radius.inner)/@_numChannels
            @_spokeWidth = 10

            @center =
                x: @canvasSize.x/2
                y: @canvasSize.y/2

            @snrThreshold 0

            @scales
                time:
                    d3.scale.linear().range([0, @_radiusChunk]).clamp(yes)
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
                            .range(340*i/(@_numChannels-1) - 80 for i in [0...@_numChannels])
                channelRadius:
                    d3.scale.ordinal()
                            .domain(@_channelIds)
                            .range(@radius.inner + i*@_radiusChunk for i in [0...@_numChannels])

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
                {coincs} = data
                @_draw coincs

        _draw: (coincs) ->
            snrExtent = d3.extent (Math.min(c.snrs...) for c in coincs)
            snrExtent[0] = Math.max @snrThreshold(), snrExtent[0]
            # coincs best be sorted by time
            @limits
                time: [coincs[0].times[0], 
                       Math.max(coincs[coincs.length-1].times...)]
                snr: snrExtent

            @prepare()
            @_drawLinks coincs
            @_drawSpokes()

        _drawSpokes: ->
            {channelColor, chainPosition, channelRadius} = @maps()

            spokes = describe @canvas.selectAll(".spoke")
                                     .data([0...@_numChannels])
                                     .enter().append("g"),
                class: "spoke"
                transform: (spoke) => "translate(#{@center.x}, #{@center.y}) " +
                                      "rotate(#{chainPosition spoke})" 
                                      

            describe spokes.selectAll("rect")
                           .data(@_channels)
                           .enter().append("rect"),
                x: (channel) -> channelRadius channel.id
                y: -@_spokeWidth/2
                width: @_radiusChunk
                height: @_spokeWidth
                stroke: "none"
                fill: (channel) -> channelColor channel.id

        _drawLinks: (coincs) ->
            linkGroup = describe @canvas.append("g"),
                transform: "translate(#{@center.x}, #{@center.y})"
            
            links = []
            threshold = @snrThreshold()
            for i in [0...coincs.length]
                coinc = coincs[i]
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
             channelRadius} = @maps()

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
                    makeHiveLink
                        start:
                            angle: radians chainPosition link.chainPosition
                            radius: channelRadius(link.startChannelId) + time(link.time)
                        end:
                            angle: radians chainPosition (link.chainPosition + 1)
                            radius: channelRadius(link.endChannelId) + time(link.time)

            path.on "mouseover", link ->
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


    makeHiveLink = (link) ->
        # from bost.ocks.org/mike/hive/
        a1 = link.start.angle + (link.end.angle - link.start.angle)/3
        a2 = link.end.angle - (link.end.angle - link.start.angle)/3
        return "M" + Math.cos(link.start.angle) * link.start.radius + "," + Math.sin(link.start.angle) * link.start.radius +
               "C" + Math.cos(a1) * link.start.radius + "," + Math.sin(a1) * link.start.radius +
               " " + Math.cos(a2) * link.end.radius + "," + Math.sin(a2) * link.end.radius + 
               " " + Math.cos(link.end.angle) * link.end.radius + "," + Math.sin(link.end.angle) * link.end.radius

    return {HivePlot}