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
                        @bins [0..100]
                    when "Amplitude" 
                        @axisLabels {x: "Amplitude"}
                        @bins [1.0/100*i for i in [0..100]].concat
                    when "Frequency"
                        @scales {x: d3.log().clamp yes}
                        @axisLabels {x: "Frequency"}
                        @bins [Math.exp(0.2*i - 1) for i in [0..20]].concat [50]
                    else
                        throw new Error("Invalid field: #{field}")
                @declareDirty()
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
                
                #xLimit = d3.extent values
                #if @field() is "Frequency"
                #    xLimit[0] = Math.max(1e-10, xLimit[0])
                #@limits {x: xLimit}
                @limits {x: d3.extent @bins()}
                @plot values

    return {TriggerDistributionPlot}