define [], ->
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