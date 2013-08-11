(ns lsc-app.coinc-cross
  (:require [lsc-web.data :as data]
            [lsc-web.plots :as plots :refer [scale get-size select extent d3
                                             describe! prepare! translate!
                                             draw! style!]]
            [lsc-web.utils :refer [gps->unix floor]]
            [lsc-web.cross :as cross :refer [data-set field dimension 
                                             time-bar-view column-view 
                                             bar-view]]
            [cljs.core.async :as async]
            [clojure.string :refer [join]]
            [jayq.core :as jq])
  (:require-macros
    [cljs.core.async.macros :refer [go]]))

(defn- load-coincs
  [group]
  (let [url (str (.-webRoot js/definitions) "/coinc/group/" (:id group) "/all")
        out (async/chan 1)
        data-chan (data/unwrap-result (data/load-json url))]
    (go (let [data (async/<! data-chan)]
          (async/>! out (.-coincs data))
          (async/close! out)))
    out))

(defn- get-group [] (js->clj (.-group js/definitions) :keywordize-keys true))

(defn- map-over-values
  [f m] (into {} (for [[key value] m] [key (f value)])))

(defn- map-over-key-values
  [f m] (into {} (for [[key value] m] [key (f key value)])))

(defn- mean [xs] (/ (apply + xs) (count xs)))

(defn- time-series-url
  [group coinc]
  (str (.-webRoot js/definitions) "/coinc/group/" (:id group) 
                                  "/time-series/" (.-id coinc)))

(defn- make-data-set
  [group coincs]
  (let [cross (cross/cross coincs)
        get-date #(new js/Date (-> % .-times first gps->unix (* 1000)))
        channel-ids (to-array (map :id (:channels group)))
        array-dim (fn [name array-func format width]
          (apply vector (for [chan (:channels group)]
            (field :name (str "#" (:id chan) " " name)
                   :dimension (dimension cross (fn [coinc]
                     (let [index (.indexOf (.-channel_ids coinc) (:id chan))]
                       (if (= index -1) -1
                           (aget (array-func coinc) index)))))
                   :views [(column-view :format #(if (= % -1) "---"
                                                     (format %))
                                        :width width)]))))]
    (data-set cross
      (field :name "Time [UTC]" 
             :dimension (dimension cross get-date)
             :views [(time-bar-view :domain [(get-date (first coincs))
                                             (get-date (last coincs))]
                                    :grouping :hour
                                    :size :medium)
                      (column-view :format (.time.format.utc d3 "%H:%M:%S.%L")
                                   :width 80)])
      (field :name "Duration [s]" 
             :dimension (dimension cross #(- (.-time_max %) (.-time_min %)))
             :views [(bar-view :domain [0 100]
                               :grouping floor
                               :size :medium)
                      (column-view :format (.format d3 ".2f")
                                   :width 60)])
      (field :name "Max SNR" 
             :dimension (dimension cross #(apply max (.-snrs %)))
             :views [(bar-view :domain [6 25] 
                               :bar-width 0.25
                               :size :medium)
                      (column-view :format (.format d3 ".1f")
                                   :width 50)])
      (field :name "SNR Ratio" 
             :dimension (dimension cross (fn [coinc]
                 (let [first-snr (-> coinc .-snrs first)
                       last-snr (-> coinc .-snrs last)]
                    (if (> first-snr 0) (/ last-snr first-snr) 1.2))))
             :views [(bar-view :domain [0.8 1.2] 
                               :bar-width 0.01
                               :size :medium)
                      (column-view :format (.format d3 ".2f")
                                   :width 50)])
      (field :name "Chain Length" 
             :dimension (dimension cross #(.-length %))
             :views [(bar-view :domain [2 (-> group :channels count)] 
                               :size :small)
                      (column-view :width 50)])
      (field :name "Start Channel"
             :dimension (dimension cross 
                #(.indexOf channel-ids (-> % .-channel_ids first)))
             :views [(bar-view :domain [0 (-> group :channels count dec)]
                               :size :small)
                     (column-view :width 50)])
      (field :name "Weighted Peak Frequency [Hz]" 
             :dimension (dimension cross #(mean (.-weighted_freqs %)))
             :views [(bar-view :domain [0 16] 
                               :bar-width 0.25
                               :size :medium)
                      (column-view :format (.format d3 ".1f")
                                   :width 90)])
      (field :name "Mean (Peak Time - Start Time)  [s]" 
             :dimension (dimension cross #(- (mean (.-weighted_times %))
                                             (.-time_min %)))
             :views [(bar-view :domain [0 60] 
                               :grouping floor
                               :size :medium)])
      (field :name "Mean Delay [s]" 
             :dimension (dimension cross (fn [coinc]
                (let [t0 (-> coinc .-times first)]
                  (mean (for [t (-> coinc .-times next)] (- t t0))))))
             :views [(bar-view :domain [0 0.5]
                               :bar-width 0.01
                               :size :medium)
                     (column-view :format (.format d3 ".3f")
                                  :width 60)])
      (field :name "Mean Frequency Bandwidth [Hz]" 
             :dimension (dimension cross (fn [coinc]
                (mean (for [[f-low f-high] (.-freq_bands coinc)] 
                        (- f-high f-low)))))
             :views [(bar-view :domain [0 16]
                               :bar-width 0.25
                               :size :medium)
                     (column-view :format (.format d3 ".1f")
                                  :width 90)])

      (array-dim "Frequency [Hz]" #(.-weighted_freqs %) (.format d3 ".2f") 70)
      (array-dim "SNR" #(.-snrs %) (.format d3 ".2f") 50)

      (field :name "Time Series" 
             :dimension (dimension cross #(.-id %))
             :views [(column-view :format (fn [] "") :width 60
                        :describe (fn [elem [coinc _ _]] (when coinc
                          (-> elem (.append "a")
                                   (.attr "href" (time-series-url group coinc))
                                   (.attr "target" "_blank")
                                   (.text "View")))))]))))

(defn- add-label
  [group container]
  (-> container (.append "div")
                  (style! {:font-weight "bold"
                           :font-size "18px"})
                  (.text (:name group)))
  (-> container (.append "div")
                (style! {:clear "both"})
                (.selectAll "div.channel-info")
                (.data (-> group :channels to-array))
                .enter (.append "div")
                (.classed "channel-info" true)
                (.text #(str "#" %2 " " (:subsystem %1) ":" (:name %1)))
                (style! {:font-size "10px"
                         :padding "8px"
                         :float "left"})))

(defn run []
  (let [group (get-group)
        coinc-chan (load-coincs group)
        container (select "body")]
    (add-label group container)
    (go (let [coincs (async/<! coinc-chan)
              data-set (make-data-set group coincs)]
          (cross/show-views data-set (select "body") 30 "Max SNR")))))
(jq/document-ready run)