define ['utils', 'plots', 'd3', 'jquery'], (utils, plots, d3, $) ->
    {definitions: defs, describe, loadJSON} = utils
    
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
                outer = Math.min(@canvasSize.x, @canvasSize.y)/2
                inner = 50

            @_radiusChunk = (@radius.outer - @radius.inner)/@_numChannels
            @_spokeWidth = 10

            @center =
                x: @canvasSize.x/2
                y: @canvasSize.y/2

            @scales
                time:
                    d3.scale.linear().range([0, @_radiusChunk]).clamp(yes)
                snr:
                    d3.scale.linear().range([1.0, 4.0])
                snrRatio: 
                    d3.scale.log()
                            .domain([0.8e-1, 0.2e1])
                            .range([-1, 1])
                            .clamp(yes)
                channelColor: 
                    d3.scale.category20().domain(@_channelIds)
                chainPosition: 
                    d3.scale.ordinal()
                            .domain([0...@_numChannels])
                            .range(i*360/@_numChannels - 90
                                   for i in[0...@_numChannels])
                channelRadius:
                    d3.scale.ordinal()
                            .domain(@_channelIds)
                            .range(@radius.inner + i*@_radiusChunk
                                   for i in [0...@_numChannels])


        load: ->
            url = "#{defs.webRoot}/coincs/group/#{@group.id}/all"
            loadJSON url, (data) =>
                {coincs} = data
                @_draw coincs

        _draw: (coincs) ->
            # coincs best be sorted by time
            @limits
                time: [coincs[0].times[0], 
                       Math.max(coincs[coincs.length-1].times...)]
                snr: d3.extent (Math.min(c.snrs...) for c in coincs)

            @prepare()
            @_drawSpokes()
            @_drawLinks coincs

        _drawSpokes: ->
            {channelColor, chainPosition, channelRadius} = @maps()

            spokes = describe @canvas.selectAll(".spoke")
                                     .data([0...@_numChannels])
                                     .enter().append("g"),
                class: "spoke"
                transform: (spoke) -> "rotate(#{chainPosition spoke}) " + 
                                      "translate(#{center.x}, #{center.y})"

            describe spokes.selectAll("rect")
                           .data(@_channels)
                           .enter().append("rect"),
                x: (chann) -> channelRadius channel
                y: @_spokeWidth/2
                width: @_radiusChunk
                height: @_spokeWidth
                stroke: "none"
                fill: (channel) -> channelColor channel

        _drawLinks: (coincs) ->
            console.log coincs.length

    return {HivePlot}