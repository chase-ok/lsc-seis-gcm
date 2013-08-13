(ns lsc-app.coinc-time-series
  (:require [lsc-web.data :as data]
            [lsc-web.plots :as plots :refer [scale get-size select extent d3
                                             describe! prepare! translate!
                                             draw! style!]]
            [lsc-web.utils :refer [gps->unix unix->date floor]]
            [cljs.core.async :as async]
            [clojure.string :refer [join capitalize]]
            [jayq.core :as jq])
  (:require-macros
    [cljs.core.async.macros :refer [go]]))

(defn- load-time-series
  [group coinc]
  (let [url (str (.-webRoot js/definitions) "/coinc/group/" (:id group) 
                 "/time-series/" (:id coinc) "/all")
        out (async/chan 1)
        data-chan (data/unwrap-result (data/load-json-v2 url))]
    (go (let [data (async/<! data-chan)]
          (async/>! out {:raw (.-raw data) :bandpassed (.-bandpassed data)})
          (async/close! out)))
    out))

(defn- get-group [] (js->clj (.-group js/definitions) :keywordize-keys true))
(defn- get-coinc [] (js->clj (.-coinc js/definitions) :keywordize-keys true)) 

(defn- time-series-url
  [group coinc]
  (str (.-webRoot js/definitions) "/coinc/group/" (:id group) 
                                  "/time-series/" (:id coinc)))

(defn- gps->date [gps] (-> gps gps->unix unix->date))

(defn- get-time-range
  [coinc]
  (let [time-min (- (:time_min coinc) (.-sample_buffer js/definitions))
        time-max (+ time-min (.-sample_duration js/definitions))]
    [(gps->date time-min) (gps->date time-max)]))

(def horizon-size {:x 1300 :y 100})

(defn- get-time-scale
  [coinc]
  (scale (get-time-range coinc) :type :time
         :range [0 (:x horizon-size)]))

(defn- make-time-axes
  [container coinc]
  (let [time-scale (get-time-scale coinc)] 
    (-> container (.append "svg")
                  (describe! {:class "top axis"
                              :width (:x horizon-size)
                              :height 20})
                  (style! {:position "fixed" :top "0px" :z-index 4 
                           :background "#FFFFFF"
                           :padding-bottom "3px" })
                  (.append "g")
                  (translate! 0 20)
                  (.call (-> d3 .svg.axis (.scale time-scale)
                                          (.ticks 10)
                                          (.orient "top"))))
    (-> container (.append "svg")
                  (describe! {:class "bottom axis"
                              :height 20})
                  (style! {:position "fixed" :bottom "0px" :z-index 4
                           :background "#FFFFFF"
                           :padding-top "3px"})
                  (.call (-> d3 .svg.axis (.scale time-scale)
                                          (.ticks 10)
                                          (.orient "bottom"))))))

(defn- make-horizon []
  (-> d3 .horizon (.width (:x horizon-size)) (.height (:y horizon-size))
                  (.bands 3) (.mode "offset")
                  (.interpolate "basis")))

(defn channel->data
  [time-series channel index]
  (let [points (aget time-series index)
        [time-min time-max] (get-time-range (get-coinc))
        dt (/ (- time-max time-min) (count points))]
    (to-array (for [i (range (count points))]
      (array (-> i (* dt) (+ (.getTime time-min)) js/Date.) 
             (aget points i))))))

(defn- add-horizon-header
  [container title]
  (-> container 
      (.insert "div" ".bottom")
      (style! {:clear "both"})
      (.append "h3")
      (.text (capitalize title))))
                
(defn- freq-band
  [coinc]
  [(apply min (map first (:freq_bands coinc)))
   (apply max (map second (:freq_bands coinc)))])

(defn- make-horizons
  [container coinc time-series type update-ruler]
  (add-horizon-header container (name type))
  (let [time-scale (get-time-scale coinc)
        group (get-group)
        data (map-indexed (fn [i c] [c (channel->data (type time-series) c i)])
                          (:channels group)) 
        horizons (-> container (.selectAll (str ".horizon." (name type)))
                               (.data (to-array data)))
        vertical-line! (fn [time-func style] 
          (let [wrapped #(-> (time-func %1 %2) gps->date time-scale)]
            (-> horizons (.append "line")
                         (describe! {:y1 0 :y2 (:y horizon-size)
                                     :x1 wrapped :x2 wrapped})
                         (style! (assoc style :shape-rendering 
                                              "crispEdges")))))
        coinc-channel-index (fn [channel]
          (first (mapcat #(when (= (:id channel) %2) %1) 
                         (map-indexed vector (:channel_ids coinc)))))]
    (-> horizons .enter (.insert "svg" ".bottom")
                 (describe! {:class (str "horizon " (name type))
                             :height (:y horizon-size)})
                 (.append "g")
                 (.datum #(second %))
                 (.call (make-horizon)))
    
    (-> horizons (.append "text") 
                 (.text (fn [[channel _]]
                    (str (:subsystem channel) ":" (:name channel))))
                 (translate! 5 15)
                 (style! {:text-anchor "start" :font-size "10px"}))
    
    (when (= type :bandpassed)
      (-> horizons (.append "text")
                   (.text (fn [[channel _]] 
                      (let [index (coinc-channel-index channel)
                            [f-low f-high] (if index
                                               (get (:freq_bands coinc) index)
                                               (freq-band coinc)) 
                            format (.format d3 ".2f")]
                        (str (format f-low) " - " (format f-high) " Hz"))))
                   (translate! 5 (- (:y horizon-size) 5))
                   (style! {:text-anchor "start" :font-size "10px"}))) 

    (let [ruler-group (-> horizons (.append "g")
                                   (describe! {:class "ruler"})
                                   (translate! -100 (- (:y horizon-size) 5))
                                   (style! {:font-size "12px"}))]
      (-> ruler-group (.append "text")
                      (describe! {:class "ruler-value" :x -2})
                      (style! {:font-weight "bold" :text-anchor "end"}))
      (-> ruler-group (.append "text")
                      (describe! {:x 2})
                      (.text #(-> group :channels (nth %2) :units))))
   
    (vertical-line! (fn [_ _] (:time_min coinc))
                    {:stroke-width "2px" :stroke "black" 
                     :stroke-dasharray "3,1"})
    (vertical-line! #(-> coinc :times (get (coinc-channel-index (first %1)) 0))
                    {:stroke-width "2px" :stroke "black"})
    (vertical-line! #(-> coinc :weighted_times 
                         (get (coinc-channel-index (first %1)) 0 ))
                    {:stroke-width "3px" :stroke "green"})
    (vertical-line! (fn [_ _] (:time_max coinc))
                    {:stroke-width "2px" :stroke "black"})
    
    (go (while true (let [x (async/<! update-ruler) y (- (:y horizon-size) 5)
                          ruler (.select horizons "g.ruler")
                          format (.format d3 ".5g")]
      (if (pos? x)
          (do (-> ruler (translate! x y))
              (-> ruler (.select "text.ruler-value")
                        (.text (fn [_ i] (let [series (second (nth data i))
                                               ratio (/ (.-length series) 
                                                        (:x horizon-size))]
                          (-> series (aget (.floor js/Math (* x ratio))) 
                                     second format)))))) 
          (-> ruler (translate! -100 y))))))))

(defn- make-ruler
  [container coinc update-rulers]
  (let [line (-> container (.append "div")
                           (style! {:position "absolute"
                                    :top 0 :bottom 0
                                    :width "1px"
                                    :z-index 3
                                    :pointer-events "none"
                                    :display "none"
                                    :background "#000"}))
        horizon-svgs (-> container (.selectAll "svg.horizon"))]
    (.on horizon-svgs "mousemove" (fn []
      (let [[x _] (.mouse d3 (-> horizon-svgs (aget 0) (aget 0)))]
        (style! line {:display "block" :left (str x "px")})
        (doseq [chan update-rulers] (async/put! chan x))))) 
    (.on horizon-svgs "mouseout" (fn []
        (style! line {:display "none"})
        (doseq [chan update-rulers] (async/put! chan -1))))))

(defn run []
  (let [group (get-group)
        coinc (get-coinc)
        time-series-chan (load-time-series group coinc)
        container (select "body")]
    (go (let [time-series (async/<! time-series-chan)
              update-rulers (for [_ (range 2)] (async/chan))]
          (make-time-axes container coinc)
          (doseq [[i type] (map-indexed vector [:bandpassed :raw])]
            (.log js/console (array update-rulers i type))
            (make-horizons container coinc time-series type (nth update-rulers i)))
          (make-ruler container coinc update-rulers)))))
(jq/document-ready run)
