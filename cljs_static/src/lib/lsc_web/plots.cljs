(ns lsc-web.plots
  (:require [clojure.string :as string]))

(def d3 js/d3)

(defn describe!
  [obj properties]
  (doseq [prop-name (keys properties)]
    (.attr obj (name prop-name) (prop-name properties)))
  obj)

(defn style!
  [obj properties]
  (doseq [prop-name (keys properties)]
    (.style obj (name prop-name) (prop-name properties)))
  obj)

(defn select [selection] (.select d3 (name selection)))

(defn translate!
  [selection x y]
  (describe! selection {:transform (str "translate(" x "," y ")")}))

(defn- half [x] (/ x 2))

(defn get-size
  [selection]
  {:x (int (.attr selection "width")) :y (int (.attr selection "height"))})

(defn extent [xs] (.extent d3 (to-array xs)))

(defn scale
  [domain & {:keys [type range clamp]
             :or {type :linear range nil clamp false}}]
  (let [scale (if (= (name type) "time")
                  (.time.scale d3)
                  ((aget (.-scale d3) (name type))))]
    (when domain (.domain scale (to-array domain)))
    (when range (.range scale (to-array range)))
    (when clamp (.clamp scale clamp))
    scale))

(defprotocol PrepareCanvas
  (prepare! [this container]))

(defn prepare-all!
  [container preparers]
  (reduce #(prepare! %2 %1) container preparers))

(defprotocol UpdateCanvas
  (update! [this canvas]))

(defprotocol Draw
  (draw! [this canvas data]))


(defrecord LabeledCanvas [title x-label y-label]
  PrepareCanvas
  (prepare! [this container]
    (let [margins {:left 60 :top 40 :right 40 :bottom 60}
          font-heights {:title 20 :x-label 18 :y-label 18}

          container-size (get-size container)
          size {:x (- (:x container-size) (:left margins) (:right margins))
                :y (- (:y container-size) (:top margins) (:bottom margins))}

          canvas (describe! (.append container "g")
                            {:class "canvas"
                             :width (:x size)
                             :height (:y size)})]
      (translate! canvas (:left margins) (:top margins))

      (describe! (-> (.append canvas "text") (.text title))
                 {:x (half (:x size))
                  :y (- (* 1.1 (:title font-heights)) (:top margins))
                  :text-anchor "middle"
                  :font-size (:title font-heights)
                  :class "title label"})

      (describe! (-> (.append canvas "text") (.text x-label))
                 {:x (half (:x size))
                  :y (+ (:y size) (:bottom margins)
                        (* -1.1 (:x-label font-heights)))
                  :text-anchor "middle"
                  :font-size (:x-label font-heights)
                  :class "x label"})

      (describe! (-> (.append canvas "g")
                     (.attr "transform" "rotate(-90)")
                     (.append "text")
                     (.text y-label))
                 {:x (- (half (:y size)))
                  :y (- (* 1.1 (:y-label font-heights)) (:left margins))
                  :text-anchor "middle"
                  :font-size (:y-label font-heights)
                  :class "y label"})
      canvas))

  UpdateCanvas
  (update! [this canvas]
    (let [title (.select canvas "text.title.label")
          x-label (.select canvas "text.x.label")
          y-label (.select canvas "text.y.label")]
      (.text title (:title this))
      (.text x-label (:x-label this))
      (.text y-label (:y-label this))
      canvas)))

(defn make-axis
  [scale orientation]
  (-> (.svg.axis d3) (.scale scale) (.orient orientation)))

(defn- make-x-axis [axes] (make-axis (:x-scale axes) "bottom"))
(defn- make-y-axis [axes] (make-axis (:y-scale axes) "left"))
(defn- make-grid-axis [axis length]
  (-> axis (.tickSize (- length) 0 0) (.tickFormat "")))

(defn expand-to-canvas-size
  [scales canvas]
  (let [{width :x height :y} (get-size canvas)
        {:keys [x y]} scales]
    {:x (-> x .copy (.range (to-array [0 width])))
     :y (-> y .copy (.range (to-array [height 0])))}))

(defn expand-axes-to-canvas-size
  [axes canvas]
  (let [{:keys [x y]} (expand-to-canvas-size {:x (:x-scale axes)
                                              :y (:y-scale axes)}
                                             canvas)]
    (assoc axes :x-scale x :y-scale y)))

(defrecord XYAxes [x-scale y-scale show-grid]
  PrepareCanvas
  (prepare! [this canvas]
    (let [this (expand-axes-to-canvas-size this canvas)
          size (get-size canvas)
          x-grid-group (describe! (.append canvas "g") {:class "x grid"})
          y-grid-group (describe! (.append canvas "g") {:class "y grid"})
          x-group (describe! (.append canvas "g") {:class "x axis"})
          y-group (describe! (.append canvas "g") {:class "y axis"})]
      (doseq [group [x-grid-group x-group]]
        (translate! group 0 (:y size)))
      (update! this canvas)))

  UpdateCanvas
  (update! [this canvas]
    (let [this (expand-axes-to-canvas-size this canvas)
          size (get-size canvas)
          x-axis (make-x-axis this)
          y-axis (make-y-axis this)
          x-grid-axis (make-grid-axis (make-x-axis this) (:y size))
          y-grid-axis (make-grid-axis (make-y-axis this) (:x size))]
      (x-grid-axis (.select canvas ".x.grid"))
      (y-grid-axis (.select canvas ".y.grid"))
      (describe! (.selectAll canvas ".grid")
                 {:display (if (:show-grid this) "true" "none")})

      (x-axis (.select canvas ".x.axis"))
      (y-axis (.select canvas ".y.axis"))
      canvas)))

(defn make-color-scale
  [scale low-color high-color]
  (let [scale (-> scale .copy (.range (array 0 1)))
        interp (.interpolateRgb d3 low-color high-color)]
    (with-meta #(-> % scale interp) {:low-color low-color
                                     :high-color high-color
                                     :scale scale})))

(defrecord ZColorAxis [color-scale]
  PrepareCanvas
  (prepare! [this container]
    (let [size (get-size container)
          width 30 bar-width 20
          defs (.append container "defs")
          group (describe! (.append container "g") {:class "z axis"})]
      (let [gradient (.append defs "linearGradient")
            make-stop #(describe! (.append gradient "stop")
                                  {:offset %1
                                   :stop-color %2
                                   :stop-opacity 1})]
        (describe! gradient
                   {:id "z-gradient"
                    :x1 "0%" :y1 "100%"
                    :x2 "0%" :y2 "0%"})
        (make-stop "0%" (:low-color (meta color-scale)))
        (make-stop "100%" (:high-color (meta color-scale))))

      (translate! group (- (:x size) (- width bar-width)) 0)
      (describe! (.append group "rect")
                 {:x (- bar-width) :y 0
                  :width bar-width :height (:y size)
                  :fill "url(#z-gradient)"})

      (update! this container)
      (describe! (.append container "g")
                 {:width (- (:x size) width bar-width 5)
                  :height (:y size)})))


  UpdateCanvas
  (update! [this canvas]
    (let [size (get-size canvas)
          axis (make-axis (-> color-scale meta :scale
                              .copy (.range (array (:y size) 0)))
                          "right")
          defs (.select canvas "defs")]
      (-> defs (.select "#z-gradient") .remove)
      (let [gradient (.append defs "linearGradient")
            make-stop #(describe! (.append gradient "stop")
                                  {:offset %1
                                   :stop-color %2
                                   :stop-opacity 1})]
        (describe! gradient
                   {:id "z-gradient"
                    :x1 "0%" :y1 "100%"
                    :x2 "0%" :y2 "0%"})
        (make-stop "0%" (:low-color (meta color-scale)))
        (make-stop "100%" (:high-color (meta color-scale)))
        (axis (.select canvas ".z.axis")))
      canvas)))

(def default-data-set
  {:label nil :color "black" :marker-size 2})

(defrecord ScatterPlot [axes legend data-sets]
  UpdateCanvas
  (update! [this canvas]
    (let [legend-pos (get this :legend :top-right)
          canvas-size (get-size canvas)
          size {:x 100 :y 20}]
      (when (not= legend-pos :no-legend)
        (let [data-sets (filter :label (-> this :data-sets vals))
              legend (-> canvas (.selectAll ".legend")
                                (.data (to-array data-sets)))
              position (fn [_ i]
                (let [[x y]
                      (case legend-pos
                         :top-right [(- (:x canvas-size) (:x size))
                                     (* i (+ (:y size) 5))])]
                  (str "translate(" x "," y ")")))
              legend-group (-> legend .enter
                                      (.append "g")
                                      (describe! {:class "legend"
                                                  :transform position}))]
          (describe! (.append legend-group "rect")
                     {:x 0 :y 0
                      :width (:x size) :height (:y size)
                      :stroke "none"
                      :fill #(get % :color "black")})
          (describe! (-> legend-group (.append "text") (.text #(:label %)))
                     {:x 3
                      :y (- (:y size) 5)
                      :text-anchor "start"
                      :font-size (- (:y size) 8)
                      :font-weight "bold"
                      :fill "white"})
          (-> legend .exit .remove)))
      canvas))

  Draw
  (draw! [this canvas data]
     (let [with-keys (fn [key] (map (fn [v] {:key key :value v}) (key data)))
           combined (mapcat with-keys (keys data))

           {:keys [x-scale y-scale]} (expand-axes-to-canvas-size axes canvas)
           get-data-set #(get (:data-sets this) % default-data-set)]

       (doseq [key (keys data)]
         (let [data-set (key (:data-sets this))
               class #(string/join % ["scatter-point" (name key)])
               circles (-> (.selectAll canvas (str "." (class ".")))
                           (.data (to-array (key data))))]
           (describe! (-> circles .enter (.append "circle"))
                      {:class (class " ")})
           (describe! (-> circles .transition (.duration 500))
                     {:cx #(-> % first x-scale)
                      :cy #(-> % second y-scale)
                      :r (get data-set :marker-size 2)
                      :stroke "none"
                      :fill (get data-set :color "black")})
           (-> circles .exit .remove)))
       (update! this canvas))))

(defn make-histogram
  ([bins] (-> d3 .layout.histogram
                 (.bins (to-array bins))
                 (.frequency false)))
  ([bins accessor] (.value (make-histogram bins) accessor)))

(defn- get-hist-length
  [datum scale]
  (.abs js/Math (- (scale (+ (.-x datum) (.-dx datum)))
                   (scale (.-x datum)))))

(defrecord Histogram2D [scales x-bins y-bins]
  Draw
  (draw! [this canvas data]
     (let [{x-scale :x y-scale :y} (expand-to-canvas-size scales canvas)
           z-scale (:z scales)
           x-hist (make-histogram x-bins first)
           y-hist (make-histogram y-bins second)
           x-data (x-hist (to-array data))
           x-groups (-> canvas (.selectAll "g.histogram") (.data x-data))]
       (describe! (-> x-groups .enter (.append "g"))
                  {:class "histogram"})
       (-> x-groups .exit .remove)
       (describe! x-groups
                  {:transform #(str "translate("
                                    (.floor js/Math (-> % .-x x-scale))
                                    ",0)")
                   :width #(get-hist-length % x-scale)})

       (let [rects (-> x-groups (.selectAll "rect.histogram") (.data y-hist))]
         (describe! (-> rects .enter (.append "rect"))
                    {:class "histogram"
                     :x 0
                     :stroke "none"})
         (-> rects .exit .remove)
         (describe! rects
                    {:y #(-> % .-x y-scale (- (get-hist-length % y-scale)))
                     :height #(get-hist-length % y-scale)
                     :width #(this-as this
                               (-> d3 (.select (.-parentNode this))
                                      (.attr "width")))
                     :fill #(this-as this
                              (-> % .-y (* (-> d3 (.select (.-parentNode this))
                                                  .datum .-y))
                                    z-scale))})))))

;(testing)
