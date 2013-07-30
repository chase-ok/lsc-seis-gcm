define ['utils', 'd3'], (utils, d3) ->
    {mash, describe, mergeObj} = utils
    
    _clipCount = 0

    defaultMargin =
        top: 40
        right: 70
        bottom: 50
        left: 60

    class SvgPlot
        constructor: (@rootSelector="body", @margin=defaultMargin, 
                      @dimensions=['x', 'y']) ->
            @root = d3.select @rootSelector
            
            @size = 
                x: @root.attr "width"
                y: @root.attr "height"
            @canvasSize = 
                x: @size.x - @margin.left - @margin.right
                y: @size.y - @margin.top - @margin.bottom

            @_scales = mash ([dim, d3.scale.linear()] for dim in @dimensions)
            @_title = ""
            @_prepared = no

        select: (selector) -> d3.select "#{@rootSelector} #{selector}"

        scales: (scales, 
                 ranges={x: [0, @canvasSize.x], y: [@canvasSize.y, 0]}) ->
            if scales?
                mergeObj @_scales, scales
                @declareDirty()
                this
            else
                for dim, range of ranges
                    @_scales[dim].range range
                @_scales
            
        title: (title) ->
            if title?
                @_title = title
                @select(".title").text title if @_prepared
                this
            else
                @_title
            
        limits: (limits) ->
            if limits?
                for dim, limit of limits
                    @_scales[dim].domain limit
                @declareDirty()
                this
            else
                mash ([dim, @_scales[dim].domain()] for dim in @dimensions)

        maps: ->
            mash ([dim, @_scales[dim].copy()] for dim in @dimensions)
        
        clear: ->
            return unless @_prepared
            @canvas.remove()
            @_prepared = no
            @prepare()
            
        prepare: ->
            return no if @_prepared
    
            @_prepareCanvas()
            @_prepareCanvasClipPath()
            @_prepareTitle()
            
            return @_prepared = yes
        
        declareDirty: ->
            # TODO: Make this wait a while to catch "all of the dirty" at once
            @clear()
            @prepare()
        
        _prepareCanvas: ->
            @canvas = describe @root.append("g"),
                transform: "translate(#{@margin.left}, #{@margin.top})"
            @svgDefs = @canvas.append("defs")
        
        _prepareCanvasClipPath: ->
            @canvasClipId = "canvas-clip-#{_clipCount+=1}"
            @_canvasClip = @canvas.append("clipPath").attr("id", @canvasClipId)
            describe @_canvasClip.append("rect"),
                x: 0
                y: 0
                width: @canvasSize.x
                height: @canvasSize.y

        _prepareTitle: ->
            fontHeight = 20
            
            describe @canvas.append("text").text(@_title),
                x: @canvasSize.x/2
                y: -@margin.top + fontHeight*1.1
                "text-anchor": "middle"
                "font-size": "#{fontHeight}"
                class: "title axis-label"


    class BasicPlot extends SvgPlot
        constructor: (rootSelector="body", dimensions=['x', 'y']) ->
            super rootSelector, null, dimensions

            @_axisLabels = mash ([dim, dim] for dim in @dimensions)
            @_ticks = mash ([dim, null] for dim in @dimensions)
            @_showGrid = yes
    
        select: (selector) -> d3.select "#{@rootSelector} #{selector}"
            
        axisLabels: (labels) ->
            if labels?
                mergeObj @_axisLabels, labels
                if @_prepared
                    for dim, label of @_axisLabels
                        @select(".#{dim}.axis-label").text label
                this
            else
                @_axisLabels
        
        ticks: (ticks) ->
            if ticks?
                mergeObj @_ticks, ticks
                @declareDirty()
                this
            else
                @_ticks
            
        showGrid: (showGrid) ->
            if showGrid?
                @_showGrid = showGrid
                @declareDirty()
                this
            else
                @_showGrid
        
        prepare: ->
            return unless super()

            @_prepareGrid()
            @_prepareAxes()
            @_prepareAxisLabels()
        
        _prepareGrid: ->
            return unless @_showGrid
    
            axes = @_makeAxes()
            axes.x.tickSize(-@canvasSize.y, 0, 0).tickFormat("")
            axes.y.tickSize(-@canvasSize.x, 0, 0).tickFormat("")
            
            (describe @canvas.append("g"),
                class: "x grid"
                transform: "translate(0, #{@canvasSize.y})"
            ).call(axes.x)
            (describe @canvas.append("g"),
                class: "y grid"
            ).call(axes.y)
            
        _prepareAxisLabels: ->
            fontHeight = 15
            
            describe @canvas.append("text").text(@_axisLabels.x),
                x: @canvasSize.x/2
                y: @canvasSize.y + @margin.bottom - fontHeight*1.1
                "text-anchor": "middle"
                "font-size": "#{fontHeight}"
                class: "x axis-label"
    
            rotated = @canvas.append("g").attr "transform", "rotate(-90)"
            describe rotated.append("text").text(@_axisLabels.y),
                x: -@canvasSize.y/2
                y: fontHeight*1.1 - @margin.left
                "text-anchor": "middle"
                "font-size": "#{fontHeight}"
                class: "y axis-label"
            
        _prepareAxes: ->
            axes = @_makeAxes()
            (describe @canvas.append("g"),
                class: "x axis"
                transform: "translate(0, #{@canvasSize.y})"
            ).call(axes.x)
            (describe @canvas.append("g"),
                class: "y axis"
            ).call(axes.y)
        
        _makeAxes: (orientations={x: "bottom", y: "left"})->
            axes = {}
            scales = @scales()
            for dim in @dimensions
                axis = d3.svg.axis().scale(scales[dim]).orient orientations[dim]
                axis.ticks @_ticks[dim]... if @_ticks[dim]?
                axes[dim] = axis
            axes
    
    class ZColorPlot extends BasicPlot
        constructor: (rootSelector, dimensions=['x', 'y', 'z']) ->
            super rootSelector, dimensions
            
            @_zBarWidth = 30
            @canvasSize.x -= @_zBarWidth
            
            @_zColor =
                lower: d3.rgb 0, 0, 0
                upper: d3.rgb 255, 0, 0
                
        zColor: (zColor) ->
            if zColor?
                mergeObj @_zColor zColor
                @declareDirty()
                this
            else
                @_zColor
                
        scales: (scales, ranges={z: [@canvasSize.y, 0]}) ->
            if scales?
                super scales
            else
                scales = super()
                for dim, range of ranges
                    scales[dim].range range
                scales
        
        maps: ->
            oldMaps = super()
            
            height = @canvasSize.y
            zColor = @zColor()
            colorInterp = d3.interpolateRgb zColor.lower, zColor.upper
            
            # TODO: this doesn't respect @dimensions
            x: oldMaps.x
            y: oldMaps.y
            z: (z) -> colorInterp(1.0 - oldMaps.z(z)/height)
            
        prepare: ->
            super()
            @_prepareZGradient()
            @_prepareZColorBar()
            @_prepareZAxis()
            @_prepareZLabel()
        
        _prepareZGradient: ->
            zColor = @zColor()
            
            @_zGradient = describe @svgDefs.append("linearGradient"),
                id: "zGradient"
                x1: "0%"
                y1: "100%"
                x2: "0%"
                y2: "0%"
            describe @_zGradient.append("stop"),
                offset: "0%"
                "stop-color": zColor.lower
                "stop-opacity": 1
            describe @_zGradient.append("stop"),
                offset:"100%"
                "stop-color": zColor.upper
                "stop-opacity": 1
        
        _prepareZColorBar: ->
            spacing = 10
            @_zColorBar = describe @canvas.append("rect"),
                x: @canvasSize.x + spacing
                y: 0
                width: @_zBarWidth - spacing
                height: @canvasSize.y
                fill: "url(##{@_zGradient.attr('id')})"
                
        _prepareZAxis: ->
            (describe @canvas.append("g"),
                class: "z axis"
                transform: "translate(#{@canvasSize.x + @_zBarWidth}, 0)"
            ).call(@_makeAxes({z: "right"}).z)
            
        _prepareZLabel: ->
            fontHeight = 15
            rotated = @canvas.append("g").attr "transform", "rotate(-90)"
            describe rotated.append("text").text(@axisLabels().z),
                x: -@canvasSize.y/2
                y: @canvasSize.x + @_zBarWidth + @margin.right
                "text-anchor": "middle"
                "font-size": "#{fontHeight}"
                class: "z axis-label"
    
    class Histogram extends BasicPlot
        constructor: (rootSelector) ->
            super rootSelector
            
            @bins [0..20]
            @useProbability yes
            @limits {y: [0, 1]}
            
        bins: (bins) ->
            if bins?
                @_bins = bins
                #@ticks {x: bins}
                @declareDirty()
                this
            else
                @_bins
        
        useProbability: (useProbability) ->
            if useProbability?
                @_useProbability = useProbability
                @axisLabels
                    y: if useProbability then "Probability" else "Frequency"
                @declareDirty()
                this
            else
                @_useProbability
        
        plot: (values) ->
            {x, y} = @scales()
            
            histogram = d3.layout.histogram()
            histogram.bins @bins() if @bins()?
            histogram.frequency not @useProbability()
            data = histogram values
            console.log data
            rects = @canvas.selectAll("rect.histogram-bar").data data
            describe rects.enter().append("rect"),
                class: "histogram-bar"
                x: (d) -> Math.floor x(d.x)
                y: (d) -> y d.y
                width: (d) -> Math.ceil(x(d.x + d.dx) - x(d.x))
                height: (d) -> y(0) - y(d.y)
                fill: "steelblue"
                "shape-rendering": "crispEdge"
            
            rects.exit().remove()

    return {SvgPlot, BasicPlot, ZColorPlot, Histogram}