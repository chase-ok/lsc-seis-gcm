(ns lsc-app.coinc
  (:require [lsc-web.data :as data]
            [lsc-web.plots :as plots :refer [scale get-size select extent
                                             describe! prepare! translate!
                                             draw!]]
            [lsc-web.utils :refer [gps->unix]]
            [cljs.core.async :as async]
            [clojure.string :refer [join]]
            [jayq.core :as jq])
  (:require-macros
    [cljs.core.async.macros :refer [go]]))

(defn- load-coincs
  [group]
  (let [url (str "/coinc/group/" (:id group) "/all")
        out (async/chan 1)
        data-chan (data/unwrap-result (data/load-json url))]
    (go (let [data (async/<! data-chan)]
          (async/>! out (.-coincs data))
          (async/close! out)))
    out))

(defn- get-group [] (js->clj (.-group js/definitions) :keywordize-keys true))

(defn- bar-spacing
  [canvas group]
  {:x (/ (:x (get-size canvas))
         (dec (count (:channels group))))
   :y 5})

(defn- bar-size
  [canvas group]
  {:x 10
   :y (- (/ (:y (get-size canvas))
            (count (:channels group)))
         (:y (bar-spacing canvas group)))})

(defn- make-channel-scales
  [context]
  (let [bar-size (:bar-size context)
        bar-spacing (:bar-spacing context)
        group (:group context)
        num-channels (count (:channels group))
        channel-ids (map :id (:channels group))]
    {:channel-color (scale channel-ids :type :category20)
     :chain-position (scale (range num-channels)
                            :type :ordinal
                            :range (for [i (range num-channels)]
                                     (* i (:x bar-spacing))))
     :channel-position (scale channel-ids
                              :range (for [i (range num-channels)]
                                       (* i (+ (:y bar-spacing)
                                               (:y bar-size)))))}))

(defn- make-coinc-scales
  [context]
  (let [coincs (:coincs context)
        snrs (map #(apply max (.-snrs %)) coincs)]
    {:time (scale [(-> coincs first .-times first)
                   (-> coincs last .-times last)]
                  :range [(-> context :bar-size :y) 0])
     :snr (scale [(max 1 (apply min snrs)) (apply max snrs)]
                 :type :log :range [0.5 6] :clamp true)
     :snr-ratio (scale [0.5 1.5] :range [-1 1] :clamp true)}))

(defn- prepare-legend!
  [y-offset context info]
  (let [spacing 5
        size {:x (-> info get-size :x) :y 20}
        channel-color (-> context :scales :channel-color)
        channels (-> context :group :channels)
        legend (-> info (.append "g")
                        (.selectAll ".legend")
                        (.data (to-array channels))
                        .enter (.append "g"))]
    (describe! legend
               {:class "legend"
                :transform (fn [_ i]
                 (str "translate(0," (* i (+ (:y size) spacing)) ")"))})
    (describe! (.append legend "rect")
               {:x 0 :y 0
                :width (:x size) :height (:y size)
                :stroke "none"
                :fill #(channel-color (:id %))})

    (describe! (-> legend (.append "text")
                          (.text #(str (:subsystem %) ":" (:name %))))
               {:x 3
                :y (- (:y size) 5)
                :text-anchor "start"
                :font-size (- (:y size) 8)
                :font-weight "bold"
                :fill "white"})

    (.on legend "mouseover" (fn [channel]
      (async/put! (-> context :chans :highlight-chains)
                  (fn [coinc] (some #{(:id channel)} (.-channel_ids coinc))))))
    (.on legend "mouseout"
      #(async/put! (-> context :chans :clear-highlight) true))

    (* (count channels) (+ (:y size) spacing))))

(def histogram-scales
  {:x (scale [6 30] :clamp true)
   :y (scale [1 10] :clamp true)
   :z (plots/make-color-scale (scale [1e-5 1] :type :log)
                              (.rgb plots/d3 255 255 255)
                              (.rgb plots/d3 127 0 0))})

(defn- prepare-histogram!
  [y-offset context info]
  (let [size {:x (-> info get-size :x) :y 250}
        labels (plots/LabeledCanvas. "Percentage of Coincidences"
                                     "SNR" "Frequency")

        xy-axes (plots/XYAxes. (:x histogram-scales) (:y histogram-scales)
                               false)
        z-axis (plots/ZColorAxis. (:z histogram-scales))
        canvas (describe! (.append info "g")
                          {:width (:x size) :height (:y size)})]
    (translate! canvas 0 y-offset)
    (let [canvas (plots/prepare-all! canvas [labels z-axis xy-axes])]
      (.attr canvas "id" "histogram-canvas")
      (+ y-offset (:y size)))))

(defn- draw-histogram!
  [canvas-context coincs]
  (let [snr-freq-pairs (map #(array (apply max (.-snrs %))
                                    (first (.-freqs %)))
                            coincs)
        histogram (plots/Histogram2D. histogram-scales
                                      (range 6 (inc 30))
                                      (range 1 (inc 10)))
        canvas (.select plots/d3 "#histogram-canvas")

        expanded (plots/expand-to-canvas-size histogram-scales canvas)
        brush (-> plots/d3 .svg.brush
                           (.clamp (array true true))
                           (.x (:x expanded))
                           (.y (:y expanded)))]
    (draw! histogram canvas snr-freq-pairs)

    (.on brush "brushend" (fn []
       (let [[[snr-low freq-low] [snr-high freq-high]] (.extent brush)
             include-above #(if (> 1 (- (aget (.domain %2) 1) %1))
                                (/ 1 0) %1)
             snr-high (include-above snr-high (:x expanded))
             freq-high (include-above freq-high (:y expanded))
             filter-chan (-> canvas-context :context :chans :filter-chains)]
         (async/put! filter-chan (fn [chain]
           (and (some true? (map #(< freq-low % freq-high)
                                 (.-freqs chain)))
                (some true? (map #(< snr-low % snr-high)
                                 (.-snrs chain)))))))))
    (brush canvas)))

(defn- prepare-chain-info!
  [y-offset context info]
  (let [height 250
        text-height 12
        spacing 5
        text-group (.append info "g")]
    (describe! text-group
               {:width (:x (get-size info))
                :height height})
    (translate! text-group 0 y-offset)
    (go (while true
          (let [lines (async/<! (-> context :chans :show-info))
                texts (-> text-group (.selectAll "text.info")
                                     (.data (to-array lines)))]
            (describe! (-> texts .enter (.append "text"))
                       {:class "info"
                        :x 3
                        :y (fn [_ i] (+ (* (inc i) text-height)
                                        (* i spacing)))
                        :text-anchor "start"
                        :font-size text-height
                        :font-weight "bold"})
            (.text texts identity)
            (-> texts .exit .remove))))
    (+ y-offset height spacing)))

(defrecord CoincInfo [context]
  plots/PrepareCanvas
  (prepare! [this container]
    (let [container-size (get-size container)
          {width :x height :y} (:info-size context)
          canvas (describe! (.append container "g")
                            {:width width :height height})]
      (translate! canvas (- (:x container-size) width) 0)
      (-> 0 (prepare-legend! context canvas)
            (prepare-histogram! context canvas)
            (prepare-chain-info! context canvas))
      canvas)))

(defn- prepare-bars!
  [context canvas]
  (let [channels (-> context :group :channels)
        bar-data (for [pos (range (count channels)) channel channels]
                   [pos (:id channel)])
        bars (-> canvas (.selectAll "rect.hive-bar")
                        (.data (to-array bar-data))
                        .enter (.append "rect"))
        {:keys [chain-position
                channel-position
                channel-color]} (:scales context)
        bar-size (:bar-size context)]
    (describe! bars
               {:class "hive-bar"
                :x #(- (chain-position (first %)) (/ (:x bar-size) 2))
                :y #(channel-position (second %))
                :width (:x bar-size)
                :height (:y bar-size)
                :stroke "none"
                :fill #(channel-color (second %))})
    (.on bars "mouseover" (fn [[pos channel-id]]
      (async/put! (-> context :chans :highlight-chains)
                  (fn [coinc] (= channel-id
                                 (aget (.-channel_ids coinc) pos))))))
    (.on bars "mouseout"
      #(async/put! (-> context :chans :clear-highlight) true))))

(defn- make-snr-ratio-color-map
  [snr-ratio]
  (let [good (.rgb plots/d3 0 255 0)
        neutral (.rgb plots/d3 100 100 100)
        bad (.rgb plots/d3 255 0 0)

        good-interp (.interpolateRgb plots/d3 neutral good)
        bad-interp (.interpolateRgb plots/d3 neutral bad)]
    (fn [ratio]
      (let [mapped (snr-ratio ratio)]
        (if (pos? mapped)
            (bad-interp mapped)
            (good-interp (- mapped)))))))

(defn- draw-links!
  [context canvas]
  (let [coincs (:coincs context)
        links (for [coinc coincs
                    pos (range (dec (.-length coinc)))
                    :let [time #(aget (.-times coinc) %)
                          snr #(aget (.-snrs coinc) %)
                          channel-id #(aget (.-channel_ids coinc) %)]]
                {:coinc coinc
                 :pos pos
                 :time (time pos)
                 :dt (- (time (inc pos)) (time pos))
                 :snr (snr 0)
                 :freq (aget (.-freqs coinc) pos)
                 :amplitude (aget (.-amplitudes coinc) pos)
                 :snr-ratio (/ (snr (inc pos)) (snr pos))
                 :start-id (channel-id pos)
                 :end-id (channel-id (inc pos))})

        {:keys [time snr channel-color chain-position channel-position
                snr-ratio]} (:scales context)
        snr-ratio (make-snr-ratio-color-map snr-ratio)

        link-group (.select plots/d3 "g#link-group")
        ; we NOTE! We need to flip x and y for diag to be horizontal!
        line (-> plots/d3 .svg.diagonal (.projection #(array (.-y %) (.-x %))))
        path (-> link-group (.selectAll "path.link")
                            (.data (to-array links))
                            .enter (.append "path"))]
    (.log js/console link-group)
    (describe! path
               {:class "link"
                :fill "none"
                :stroke #(snr-ratio (:snr-ratio %))
                :stroke-width #(snr (:snr %))
                :stroke-opacity 0.5
                :stroke-dasharray #(if (> (:dt %) 1e-5) "15,3" "none")
                :d (fn [link]
                     (let [make-coord #(js-obj "y" (chain-position %1)
                                               "x" (+ (channel-position %2)
                                                      (time (:time link))))]
                       (line (js-obj "source" (make-coord (:pos link)
                                                          (:start-id link))
                                     "target" (make-coord (inc (:pos link))
                                                          (:end-id link))))))})

    (.on path "mouseover" (fn [link]
      (let [time-format #((.time.format.utc plots/d3 %2)
                          (new js/Date (* 1000 (gps->unix %1))))
            snr-format (.format plots/d3 ".1f")
            freq-format (.format plots/d3 ".3f")
            ampl-format (.format plots/d3 ".3f")
            format-list #(join ", " (map %1 %2))
            coinc (:coinc link)]
        (async/put! (-> context :chans :show-info)
          [(str "Time: " (time-format (:time link) "%Y-%m-%d %H:%M:%S.%L"))
          (str "SNR: " (snr-format (:snr link)))
          (str "Frequency: " (freq-format (:freq link)))
          (str "Amplitude:" (ampl-format (:amplitude link)))
          ""
          (str "All Times: "
               (format-list #(time-format % "%S.%L") (.-times coinc)))
          (str "All SNRs: " (format-list snr-format (.-snrs coinc)))
          (str "All Frequncies: "
               (format-list freq-format (.-freqs coinc)))
          (str "All Amplitudes: " 
               (format-list ampl-format (.-amplitudes coinc)))])

        (async/put! (-> context :chans :highlight-chains)
                    (fn [coinc-match] (= (.-id coinc) (.-id coinc-match)))))))

    (.on path "mouseout" (fn []
      ;(async/put! (-> context :chans :show-info) [])
      (async/put! (-> context :chans :clear-highlight) true)))))

(defn- launch-highlight-queue!
  [context canvas]
  (let [num-links (apply + (map #(dec (.-length %)) (:coincs context)))
        chunk-size 1000
        max-chunks (.ceil js/Math (/ num-links chunk-size))
        render-queue (async/chan (async/sliding-buffer max-chunks))
        partition-chunks #(partition chunk-size chunk-size nil %)
        chunk-paths (fn [] (-> plots/d3 (.selectAll "path.link")
                                        (aget 0)
                                        partition-chunks))]
    (go (while true
          (let [match (async/<! (-> context :chans :highlight-chains))
                snr (-> context :scales :snr)]
            (doseq [chunk (chunk-paths)]
              (async/put! render-queue [chunk (fn [selection]
                (describe! selection
                           {:stroke-opacity #(if (match (:coinc %)) 1.0 0.05)
                            :stroke-width (fn [link]
                              (let [base (snr (:snr link))]
                                (if (match (:coinc link))
                                    (* 2 base)
                                    (/ base 2))))}))])))))
    (go (while true
          (let [should-clear (async/<! (-> context :chans :clear-highlight))
                snr (-> context :scales :snr)]
            (doseq [chunk (chunk-paths)]
              (async/put! render-queue [chunk (fn [selection]
                (describe! selection
                           {:stroke-opacity 0.5
                            :stroke-width #(snr (:snr %))}))])))))
    (let [sleep-time 50 ; ns 
          process-chunk (fn []
            (go (let [[chunk render-func] (async/<! render-queue)
                       selection (.selectAll plots/d3 (to-array chunk))]
                  (render-func selection))))]
          (js/setInterval process-chunk sleep-time))))

(defn- launch-filter-queue!
  [context canvas]
  (go (while true
        (let [filter-fn (async/<! (-> context :chans :filter-chains))]
          (describe! (.selectAll plots/d3 "path.link")
                     {:display #(if (filter-fn (:coinc %)) "true" "none")})))))

(defrecord ChainPlot [group]
  plots/PrepareCanvas
  (prepare! [this container]
     (let [labels (plots/LabeledCanvas. (:name group)
                                        "Coincidence Chain"
                                        "Start")
           container (prepare! labels container)
           container-size (get-size container)
           info-size {:x 350 :y (:y container-size)}

           canvas (describe! (.append container "g")
                             {:width (- (:x container-size) (:x info-size) 15)
                              :height (:y container-size)})

           context {:group group
                    :labels labels
                    :canvas canvas
                    :info-size info-size
                    :bar-size (bar-size canvas group)
                    :bar-spacing (bar-spacing canvas group)
                    :chans {:highlight-chains (async/chan 1)
                            :clear-highlight (async/chan 1)
                            :filter-chains (async/chan 1)
                            :show-info (async/chan 1)}}
           context (assoc context :scales (make-channel-scales context))
           context (assoc context :info (CoincInfo. context))]
       (prepare! (:info context) container)
       (describe! (.append canvas "g") {:id "link-group"}) ; for z-ordering
       (prepare-bars! context canvas)
       {:context context
        :canvas (describe! (.append canvas "g")
                           {:width (- (:x container-size) (:x info-size))
                            :height (:y container-size)})}))

  plots/Draw
  (draw! [this canvas-context coincs]
    (let [{:keys [canvas context]} canvas-context
          context (assoc context :coincs coincs)
          context (update-in context [:scales]
                             merge (make-coinc-scales context))]
      (draw-links! context canvas)
      (launch-highlight-queue! context canvas)
      (launch-filter-queue! context canvas))))

(defn run []
  (let [group (get-group)
        plot (ChainPlot. group)
        canvas-context (prepare! plot (select :#container))
        coinc-chan (load-coincs group)]
    (go (let [coincs (async/<! coinc-chan)]
          (draw-histogram! canvas-context coincs)
          (draw! plot canvas-context coincs)))))
(js/document-ready run)
