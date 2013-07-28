define ['utils', 'plots', 'd3', 'jquery'], (utils, plots, d3, $) ->
    {definitions: defs, describe, loadJSON} = utils
    
    toDate = (seconds) -> new Date(seconds*1000)
    
    class TriggerDistributionPlot extends plots.Histogram
        constructor: (rootSelector) ->
            super rootSelector
            
            @field "SNR"
            @clustered yes
            
        clustered: (clustered) ->
            if clustered?
                @_clustered = clustered
                @load()
                this
            else
                @_clustered
        
        field: (field) ->
            if field?
                @_field = field
                switch field
                    when "SNR" then @axisLabels {x: "SNR"}
                    when "Amplitude" then @axisLabels {x: "Amplitude"}
                    when "Frequency" then
                        @scales {x: d3.log().clamp yes}
                        @axisLabels {x: "Frequency"}
                    else
                        throw new Error("Invalid field: #{field}")
                @declareDirty()
                @load()
                this
            else
                @_field
                
        load: ->
            field = switch @field()
                when "SNR" then "snr"
                when "Amplitude" then "amplitude"
                when "Frequency" then "freq"
            url = "#{defs.webRoot}/triggers/channel/#{defs.channel.id}/" + 
                  "field/#{field}?clustered=#{@clustered()}"
            loadJSON url, (data) =>
                {values} = data
                
                xLimit = d3.extent values
                if @field() is "Frequency"
                    xLimit[0] = Math.max(1e-10, xLimit[0])
                @limits {x: xLimit}
                
                @plot values

    return {TriggerDistributionPlot}