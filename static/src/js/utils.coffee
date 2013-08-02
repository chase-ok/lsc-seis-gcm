
define ['d3'], (d3) ->
    class IntervalFunc
        constructor: (@_func, @_period=1000) ->
            @_id = null
            @_running = no
        
        func: (func) ->
            if func?
                @_func = func
                @reset() if @running()
                this
            else
                @_func
        
        period: (period) ->
            if period?
                @_period = period
                @reset() if @running()
                this
            else
                @_period
        
        running: (running) ->
            if running?
                @_running = running
                if @_id?
                    clearInterval @_id
                    @_id = null
                @_id = setInterval @func(), @period() if running
                this
            else
                @_running
        
        reset: ->
            @running no
            @running yes
            
    definitions: window.definitions
    
    describe: (obj, attrs) ->
        for attr, value of attrs
            obj = obj.attr attr, value
        obj
    
    mergeObj: (base, newObj) ->
        base = {} unless base?
        for key, value of newObj
            base[key] = value if value?
        base
    
    isEmpty: (obj) ->
        for prop, value of obj
            if obj.hasOwnProperty prop
                return no
        return yes
    
    mash: (properties) ->
        obj = {}
        obj[prop[0]] = prop[1] for prop in properties
        obj
        
    loadJSON: loadJSON = (url, onData, numRetries=3) ->
        return unless numRetries > 0
        
        d3.json url, (error, json) ->
            if error? or not json.success
                console.log error if error?
                console.log json.error if json?
                setTimeout (-> loadJSON(url, onData, numRetries-1)), 10
            else
                onData json.data

    property: (funcs) ->
        oldValue = undefined
        
        if typeof funcs is 'function' or not funcs.get?
            getter = (value) -> value
        else
            getter = funcs.get

        if typeof funcs is 'function'
            setter = funcs
        else
            if funcs.set?
                setter = funcs.set
            else
                setter = -> throw new Error('property is read-only')

        (value) ->
            if value?
                oldValue = setter value, oldValue)
                obj
            else
                getter oldValue

    degrees: (radians) -> radians/Math.PI*180
    radians: (degrees) -> Math.PI/180*degrees
    
    IntervalFunc: IntervalFunc
