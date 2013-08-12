(ns lsc-web.cross
  (:require [cljs.core.async :as async]
            [lsc-web.utils :refer [floor to-map options->map pad-with]]
            [lsc-web.plots :as plots :refer [describe! style! d3 scale draw! 
                                             update!]])
  (:require-macros
    [cljs.core.async.macros :refer [go]]))

(defprotocol CrossFilter
  (dimension [this func])
  (add! [this records]))

(defprotocol Top
  (top [this k]))

(defprotocol Remove
  (remove! [this]))

(defprotocol Dimension
  (group [this func])
  (get-dim-value [this obj])
  (filter-value! [this value])
  (filter-exact! [this value])
  (filter-range! [this range])
  (filter-func! [this func])
  (filter-all! [this])
  (bottom [this k]))

(defprotocol ReduceGroup
  (reduce-group! [this add remove initial]))

(defprotocol GroupAll
  (group-all [this]))

(defprotocol AllGroup
  (get-value [this]))

(defprotocol Group
  (reduce-count! [this])
  (reduce-sum! [this value-func])
  (order! [this order-value-func])
  (order-natural! [this])
  (get-all [this]))

(defprotocol HasDimension
  (get-dimension [this]))

(defn make-all-group [dimension group-obj]
  (reify 
    AllGroup
    (get-value [_] (.value group-obj))

    ReduceGroup
    (reduce-group! [_ add remove initial] 
      (.reduce group-obj add remove initial))

    HasDimension
    (get-dimension [_] dimension)))

(defn- make-group [dimension group-obj]
  (reify
    ICounted
    (-count [_] (.size group-obj))

    ReduceGroup
    (reduce-group! [_ add remove initial]
      (.reduce group-obj add remove initial))

    Group
    (reduce-count! [_] (.reduceCount group-obj))
    (reduce-sum! [_ value-func] (.reduceSum group-obj value-func))
    (order! [_ order-value-func] (.order group-obj order-value-func))
    (order-natural! [_] (.orderNatural group-obj))
    (get-all [_] (.all group-obj))

    Top
    (top [_ k] (.top group-obj k))

    Remove
    (remove! [_] (.remove group-obj))

    HasDimension
    (get-dimension [_] dimension)))

(defn- make-dimension [dim-obj func]
  (reify 
    Dimension
    (get-dim-value [_ obj] (func obj))
    (group [this group-func] (make-group this (.group dim-obj group-func)))
    (filter-value! [_ value] (.filter dim-obj value))
    (filter-exact! [_ value] (.filterExact dim-obj value))
    (filter-range! [_ range] (.filterRange dim-obj (to-array range)))
    (filter-func! [_ func] (.filterFunction dim-obj func))
    (filter-all! [_] (.filterAll dim-obj))
    (bottom [_ k] (.bottom dim-obj k))

    GroupAll
    (group-all! [this] (make-all-group this (.groupAll dim-obj)))

    Top
    (top [_ k] (.top dim-obj k))

    Remove
    (remove! [_] (.remove dim-obj))))

(defn cross [data]
  (let [cross-obj (js/crossfilter (to-array data))]
    (reify 
      CrossFilter
      (dimension [_ func] (make-dimension (.dimension cross-obj func) func))
      (add! [_ records] (.add cross-obj (to-array records)))

      GroupAll 
      (group-all [_]  (make-all-group nil (.groupAll cross-obj)))

      ICounted
      (-count [_] (.size cross-obj)))))

(defprotocol Size
  (size [this]))

(defprotocol BarView
  (->group [this dimension])
  (ungroup [this x])
  (x-scale [this])
  (x-delta [this x]))

(defprotocol ColumnView
  (format-value [this value])
  (describe-elem [this elem value]))

(def sizes {:small {:x 250 :y 250}
            :medium {:x 500 :y 250}
            :large {:x 1000 :y 250}})

(defn data-set
  [cross & fields]
  {:cross cross 
   :fields (mapcat #(if (or (vector? %) (list? %)) % [%]) fields)})

(defn field
  [& {:keys [name dimension views]}]
  {:name name :dimension dimension :views views})

(defn time-bar-view
  [& {:keys [domain grouping ungrouping size] 
      :or {grouping :hour ungrouping identity size :medium}}]
  (reify
    Size
    (size [_] (size sizes))

    BarView
    (->group [_ dimension] 
      (group dimension (aget (.-time d3) (name grouping))))
    (ungroup [_ x] (ungrouping x))
    (x-scale [_] (scale domain :clamp true :type :time))
    (x-delta [_ x] 
      (new js/Date (+ (.getTime x)
                      (case grouping :second 1000
                                     :minute (* 60 1000)
                                     :hour (* 60 60 1000)
                                     :day (* 24 60 60 1000)))))))

(defn bar-view
  [& {:keys [domain bar-width size] 
      :or {bar-width 1 size :medium}}]
  (reify
    Size
    (size [_] (size sizes))

    BarView
    (->group [_ dimension] 
      (group dimension #(floor (/ (max (first domain) (min (second domain) %))
                                  bar-width))))
    (ungroup [_ x] (* x bar-width))
    (x-scale [_] (scale domain :clamp true))
    (x-delta [_ x] (+ x bar-width))))


(defn column-view
  [& {:keys [format width describe] 
      :or {format str width 50 describe (fn [_ _])}}]
  (reify
    Size
    (size [_] width)

    ColumnView
    (format-value [_ value] (format value))
    (describe-elem [_ elem value] (describe elem value))))

(defrecord BarPlot [scales view background]
  plots/Draw
  (draw! [this canvas data]
    (let [{:keys [x y]} (plots/expand-to-canvas-size scales canvas)
          rects (-> canvas (.selectAll "rect.bar") (.data (to-array data)))]
      (when (> (count data) 0)
        (describe! (-> rects .enter (.append "rect"))
                   {:class "bar"
                    :width (let [first-x (-> data first first)]
                              (- (x (x-delta view first-x))
                                 (x first-x)
                                 2))
                    :fill (if background "gray" "steelblue")
                    :opacity (if background 0.1 1.0)
                    :shape-rendering "crispEdge"})
        (describe! rects
                   {:x #(-> % first x inc)
                    :y #(-> % second y)
                    :height #(- (y 0) (y (second %)))}))
      (-> rects .exit .remove))))

(defn- make-bar-brush
  [canvas scales props]
  (let [expanded (plots/expand-to-canvas-size scales canvas)
        bar-group (.append canvas "g")

        brush (-> d3 .svg.brush (.x (:x expanded)) (.clamp true))
        redraw-brush! (fn []
          (brush bar-group)
          (describe! (.selectAll bar-group "rect")
                     {:height (.attr canvas "height")}))

        clear-link (-> canvas (.append "text") (.text "clear"))
        disable-clear! #(describe! clear-link 
                                   {:fill "gray" :cursor "default"})
        enable-clear! #(describe! clear-link 
                                  {:fill "blue" :cursor "pointer"})]
    (redraw-brush!)

    (.on brush "brush" (fn []
      (let [[x0 x1] (.extent brush)]
        (when #_(:round-extent view) false
          (.extent brush (array (.round js/Math x0) (.round js/Math x1)))
          (redraw-brush!))
        (if (.empty brush) (disable-clear!) (enable-clear!))

        (let [[x-min x-max] (-> expanded :x .domain)
              x0 (if (> 1e-4 (- x0 x-min)) (- js/Infinity) x0)
              x1 (if (> 1e-4 (- x-max x1)) js/Infinity x1)]
          (-> props :field :dimension (filter-range! [x0 x1])))
        (async/put! (:update props) true))))

    (describe! clear-link {:fill "gray" :x 5 :y -3 :cursor "default"})
    (.on clear-link "click" (fn []
      (.clear brush)
      (disable-clear!)
      (-> props :field :dimension  filter-all!)
      (async/put! (:update props) true)
      (redraw-brush!)))))

(defn- make-bar-view
  [canvas props]
  (let [grab-data (fn []
          (let [domain (-> props :view x-scale .domain)
                [lower-limit upper-limit] domain]
            (for [datum (-> props :group get-all)
                  :let [x (-> props :view (ungroup (.-key datum)))]
                  :when (and (<= lower-limit x) (< x upper-limit))]
              [x (.-value datum)])))
        data (grab-data)

        upper-value (apply max (map second data))
        scales {:x (-> props :view x-scale)
                :y (scale [0 (min 100 upper-value)] :clamp true)}

        labels (plots/LabeledCanvas. (-> props :field :name name) "" "Count")
        axes (plots/XYAxes. (:x scales) (:y scales) false)
        canvas (plots/prepare-all! canvas [labels axes])

        size (plots/get-size canvas)
        match-size #(describe! % {:width (:x size) :height (:y size)})
        background (match-size (.append canvas "g"))
        foreground (match-size (.append canvas "g"))

        plot (BarPlot. scales (:view props) false)
        update #(draw! plot foreground (grab-data))]
    (draw! (assoc plot :background true) background (grab-data))
    (update)
    (make-bar-brush canvas scales props)
    update))

(defn- find-views
  [filter-func data-set update include-group]
  (apply concat 
    (for [field (:fields data-set)
          :let [views (filter filter-func (:views field))]]
      (for [view views] 
        (merge {:view view :field field :update update}
          (if include-group {:group (->group view (:dimension field))}))))))

(defn- make-bar-views
  [data-set container update]
  (let [update-funcs (array)
        bar-views (find-views #(satisfies? BarView %) data-set update true)
        containers (-> container (.selectAll "svg.bar-view")
                                 (.data (to-array bar-views)))]
    (-> containers .enter (.append "svg")
                   (describe! {:class "bar-view"}))
    (describe! containers
               {:width #(-> % :view size :x)
                :height #(-> % :view size :y)})
    (-> containers .exit .remove)

    (.each containers #(this-as this 
      (.push update-funcs (make-bar-view (.select d3 this) %1))))

    (fn [] (doseq [func update-funcs] (func)))))

(defn- make-counter
  [data-set container num-rows]
  (let [text-box (-> container (.append "div")
                               (style! {:font-weight "bold"
                                        :font-size "14px"
                                        :padding "20px"}))
        update (fn []
          (.text text-box (str (-> data-set :cross group-all get-value) 
                               " of " 
                               (-> data-set :cross count) 
                               " selected. Showing " num-rows " rows")))]
    (update)
    update))

(defn- make-column-views
  [data-set container num-rows sort-field-name update]
  (let [col-views (find-views #(satisfies? ColumnView %) data-set update false)
        sort-field (first (filter #(= sort-field-name (:name %))
                                  (:fields data-set)))
        canvas (.append container "div")

        headers (-> canvas (.append "div")
                           (.classed "col-header" true)
                           (.selectAll "div")
                           (.data (to-array col-views))
                           .enter (.append "div")
                           (.text #(-> % :field :name))
                           (style! {:text-align "center"
                                    :font-weight "bold"
                                    :font-size "10px"
                                    :float "left"
                                    :width #(str (-> % :view size) "px")}))

        select-rows (fn []
          (-> canvas (.selectAll "div.col-row")
                                (.data (to-array (pad-with num-rows nil
                                  (top (sort-field :dimension) num-rows))))))
        rows (select-rows)

        select-entries (fn [rows]
          (-> rows (.selectAll "div.col-entry")
                   (.data (fn [coinc row-num] 
                     (to-array (for [view col-views] [coinc view row-num]))))))

        update-entries (fn []
          (-> (select-entries (select-rows))
              (style! {:background-color (fn [[_ _ row]] 
                         (if (even? row) "#AAAAFF" "#FFFFFF"))})
              (.text (fn [[coinc view _]]
                        (if (nil? coinc) ""
                            (format-value (:view view) 
                              (get-dim-value (-> view :field :dimension) 
                                             coinc)))))
              (.each #(this-as this 
                (-> % second :view (describe-elem (.select d3 this) %))))))]
    (-> rows .enter (.append "div")
             (.classed "col-row" true)
             (style! {:text-align "center" :clear "both"}))
    (-> (select-entries rows) 
        .enter (.append "div")
        (.classed "col-entry" true)
        (style! {:float "left" :font-size "12px"
                 :width #(-> % second :view size (str "px"))}))
    (update-entries)
    update-entries))

(defn show-views
  [data-set container num-rows sort-field-name]
  (let [update (async/chan 1)
        update-bar-views (make-bar-views data-set container update)
        update-counter (make-counter data-set container num-rows)
        update-column-views (make-column-views data-set container 
                             num-rows sort-field-name update)]
    (go (while true
      (when (async/<! update)
        (update-bar-views)
        (update-counter)
        (update-column-views))))))