define ['utils', 'jquery', 'datatables', 'd3'], (utils, $, _, d3) ->
    webRoot = utils.definitions.webRoot
    class ChannelsTable
        constructor: (container) ->
            @container = $ container
            
            @columnIndex = ["ifo", "subsystem", "name", "triggers"]
            
            viewLink = (channel, source) =>
                "<a href=\"#{@triggersUrl channel, source}\">View</a>"
            @columns =
                ifo:
                    sTitle: "IFO"
                    sWidth: "10%"
                subsystem:
                    sTitle: "Subsystem"
                    sWidth: "30%"
                name:
                    sTitle: "Channel"
                    sWidth: "40%"
                triggers:
                    sTitle: "Triggers"
                    sClass: "center"
                    mRender: (url, type, row) -> "<a href=\"#{url}\">View</a>"
                    sWidth: "10%"
            for name, def of @columns
                def.aTargets = [@columnIndex.indexOf name]
                
            @dataMap =
                ifo: (channel) -> channel.ifo
                subsystem: (channel) -> channel.subsystem
                name: (channel) -> channel.name
                triggers: (channel) ->
                    "#{webRoot}/triggers/#{channel.ifo}/" +
                    "#{channel.subsystem}/#{channel.name}"
        
        prepare: ->
            @table = $ "<table/>", 
                class: "dataTable"
                id: "channels"
                border: 0
                cellspacing: 0
                cellpadding: 0
            @table.appendTo @container
            
            @header = $ "<thead/>"
            @header.appendTo @table
            @headerRow = $ "<tr/>"
            @headerRow.appendTo @header
            
            for column, obj of @columns
                @headerRow.append $ "<th>#{obj.sTitle}</th>"
            
            @table = @table.dataTable
                aoColumns: (@columns[name] for name in @columnIndex)
            
        addChannel: (channel) ->
            row = (@dataMap[name] channel for name in @columnIndex)
            @table.fnAddData row
            
        loadFromUrl: (url="#{webRoot}/channels/all") ->
            d3.json url, (error, json) =>
                if error? or not json.success
                    console.log error
                    console.log json
                    return
                
                for channel in json.data.channels
                    @addChannel channel
    
    return {ChannelsTable}