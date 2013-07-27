
module.exports = (grunt) ->
    debug = grunt.option 'debug'
    
    makeRequireJSTask = (main) ->
        options:
            findNestedDependencies: true
            mainConfigFile: 'build/js/requireConfig.js'
            baseUrl: 'build/js'
            name: main
            out: "deploy/js/#{main}.js"
            optimize: if debug then 'none' else 'uglify2'
            generateSourceMaps: debug
            paths:
                d3: 'empty:' # eclude from minifying
            wrap:
                startFile: "build/js/requireConfig.js"
        
    grunt.initConfig
        coffee:
            compile:
                expand: true
                cwd: 'src/js'
                src: '**/*.coffee'
                dest: 'build/js'
                ext: '.js'
        
        watch:
            coffee:
                files: ['src/js/**/*.coffee']
                tasks: 'coffee:compile'
        
        copy:
            js:
                expand: true
                cwd: 'src/js'
                src: '**/*.js'
                dest: 'build/js'
            jsLib:
                expand: true
                cwd: 'lib/js'
                src: '**/*.js'
                dest: 'deploy/js/lib'
            css:
                expand: true
                cwd: 'src/css'
                src: '**/*'
                dest: 'deploy/css'
            cssLib:
                expand: true
                cwd: 'lib/css'
                src: '**/*'
                dest: 'deploy/css/lib'
            html:
                expand: true
                cwd: 'src/html'
                src: '**/*'
                dest: 'deploy/html'
            htmlLib:
                expand: true
                cwd: 'lib/html'
                src: '**/*'
                dest: 'deploy/html/lib'
        
        clean:
            build: 'build'
            deploy: 'deploy'
                
        requirejs:
            channels: makeRequireJSTask "channels/main"
    
    for contrib in ['coffee', 'requirejs', 'concat', 'copy', 'watch', 'clean']
        grunt.loadNpmTasks "grunt-contrib-#{contrib}"
    
    
    grunt.registerTask 'jsModule', (name) ->
        grunt.task.run ['coffee', 'copy:js', "requirejs:#{name}"]
    
    grunt.registerTask 'full', ['clean', 'coffee', 'copy', 'requirejs']
    grunt.registerTask 'default', ['full']
