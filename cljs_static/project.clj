(defproject lsc-web "0.1.0-SNAPSHOT"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :license {:name "Eclipse Public License"
            :url "http://www.eclipse.org/legal/epl-v10.html"}
  :repositories {"sonatype-oss-public" "https://oss.sonatype.org/content/groups/public/"}
  :dependencies [[org.clojure/clojure "1.5.1"]
                 [org.clojure/core.async "0.1.0-SNAPSHOT"]
                 [jayq "2.4.0"]]
  :main lsc-web.core
  :plugins [[lein-cljsbuild "0.3.2"]]
  :cljsbuild {
    :builds {
        :coinc-dev {
          :source-paths ["src/lib" "src/apps/coinc"]
          :compiler {
            :output-to "../static/deploy/js/coinc.js"
            :optimizations :whitespace
            :externs ["lib/d3.v3.js" "lib/jquery.min.js" "lib/crossfilter.min.js"]
            :pretty-print true}}

        :coinc-prod {
          :source-paths ["src/lib" "src/apps/coinc"]
          :compiler {
            :output-to "../static/deploy/js/coinc.min.js"
            :optimizations :simple
            :externs ["lib/d3.v3.js" "lib/jquery.min.js" "lib/crossfilter.min.js"]
            :pretty-print false}}

        :coinc-cross-dev {
          :source-paths ["src/lib" "src/apps/coinc_cross"]
          :compiler {
            :output-to "../static/deploy/js/coinc-cross.js"
            :optimizations :whitespace
            :externs ["lib/d3.v3.js" "lib/jquery.min.js" "lib/crossfilter.min.js"]
            :pretty-print true}}

        :coinc-cross-prod {
          :source-paths ["src/lib" "src/apps/coinc_cross"]
          :compiler {
            :output-to "../static/deploy/js/coinc-cross.min.js"
            :optimizations :simple
            :externs ["lib/d3.v3.js" "lib/jquery.min.js" "lib/crossfilter.min.js"]
            :pretty-print false}}
        
        :coinc-time-series-dev {
          :source-paths ["src/lib" "src/apps/coinc_time_series"]
          :compiler {
            :output-to "../static/deploy/js/coinc-time-series.js"
            :optimizations :whitespace
            :externs ["lib/d3.v3.js" "lib/jquery.min.js"]
            :pretty-print true}}}
  })
