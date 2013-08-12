(ns lsc-web.windows
  (:require [lsc-web.data :as data]
            [lsc-web.plots :as plots]
            [cljs.core.async :as async])
  (:require-macros
    [cljs.core.async.macros :refer [go]]))

(defrecord Field [name accessor])

(def fields
  (map #(apply ->Field %)
       [["Number of Coincidences" #(.-num.overall_coincs %)]
        ["Coincidence Rate [1/s]" #(.-rates.overall_coincs %)]
        ["Mean dt [s]" #(.-dts.mean %)]]))

(defn- add-selector
  ([] (add-selector "body"))
  ([container]
    (let [field-selected (async/chan)
         selector (-> js/d3 (.select container) (.append "select"))
         options (-> selector (.selectAll "option")
                              (.data (to-array fields))
                              .enter
                              (.append "option"))]
      (.text options #(:name %))
      (.on selector "change" (fn []
        (let [index (.-selectedIndex (.node selector))]
          (async/put! field-selected (nth fields index)))))
      (async/put! field-selected (first fields))
      field-selected)))

(defn- setup-plot [group]
  (let [labels (plots/LabeledCanvas. (:name group) "Window [s]" "")
        canvas (plots/prepare! labels (plots/select :#container))

        axes (plots/XYAxes. (plots/scale [0 1]) (plots/scale [0 1]) true)
        scatter (plots/ScatterPlot. axes :top-right
                                    {:actual {:label "Actual"
                                              :marker-size 4}
                                     :time-offset {:label "Time-Offset"
                                                   :marker-size 3
                                                   :color "#777777"}})]
    (plots/prepare! axes canvas)
    (plots/update! scatter canvas)
    {:labels labels :axes axes :scatter scatter :canvas canvas}))

(defn- plot-field
  [plot data field]
  (let [canvas (:canvas plot)

        labels (assoc (:labels plot) :y-label (:name field))
        accessor (:accessor field)

        actual-vals (map (fn [datum] [(.-window datum)
                                      (accessor (.-actual datum))])
                            data)
        get-offset-vals (fn [datum]
          (map (fn [offset] [(.-window datum)
                             (accessor offset)])
                  (.-rand datum)))
        offset-vals (mapcat get-offset-vals data)

        y-limits (plots/extent (concat (map second offset-vals)
                                       (map second actual-vals)))
        axes (assoc (:axes plot) :y-scale (plots/scale y-limits))
        scatter (assoc (:scatter plot) :axes axes)]
    (plots/update! labels canvas)
    (plots/update! axes canvas)
    (plots/draw! scatter canvas {:actual actual-vals
                                 :time-offset offset-vals})))

(defn run
  [group]
  (let [plot (setup-plot group)
        field-selected (add-selector)]
    (.log js/console plot)
    (go (let [data (async/<! (data/load-json "windows-0.json"))]
          (.log js/console data)
          (plot-field plot data (first fields))
          (go (while true
                (plot-field plot data (async/<! field-selected))))))))
;(run {:name "H1-ETMY" :id 0})
