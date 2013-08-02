define ['utils', 'plots', 'd3', 'jquery'], (utils, plots, d3, $) ->
    {definitions: defs, describe, loadJSON} = utils
    
    toDate = (seconds) -> new Date(seconds*1000)
    
    class TriggerDistributionPlot extends plots.Histogram
        constructor: (rootSelector, @channel) ->
            super rootSelector
            
            @field "SNR"
            @clustered yes
            
        clustered: (clustered) ->
            if clustered?
                @_clustered = clustered
                @declareDirty()
                this
            else
                @_clustered
        
        field: (field) ->
            if field?
                @_field = field
                switch field
                    when "SNR" 
                        @axisLabels {x: "SNR"}
                        @bins [0..30]
                    when "Amplitude" 
                        @axisLabels {x: "Amplitude"}
                        @bins (i/100.0 for i in [0..100])
                    when "Frequency"
                        @bins (Math.exp(0.05*i - 1) for i in [0..100])
                        @scales {x: d3.scale.log().clamp yes}
                        @axisLabels {x: "Frequency"}
                    else
                        throw new Error("Invalid field: #{field}")
                @limits {x: d3.extent @bins()}
                @declareDirty()
                this
            else
                @_field
                
        load: ->
            field = switch @field()
                when "SNR" then "snr"
                when "Amplitude" then "amplitude"
                when "Frequency" then "freq"
            url = "/triggers/channel/#{@channel.id}/" + 
                  "field/#{field}?clustered=#{@clustered()}"
            loadJSON url, (data) =>
                {values} = data
                
                #xLimit = d3.extent values
                #if @field() is "Frequency"
                #    xLimit[0] = Math.max(1e-10, xLimit[0])
                #@limits {x: xLimit}
                @plot values

    return {TriggerDistributionPlot}