(ns lsc-web.utils)

(def leaps #{46828800, 78364801, 109900802, 173059203, 252028804, 315187205, 346723206, 393984007, 425520008, 457056009, 504489610, 551750411, 599184012, 820108813, 914803214, 1025136015})

(defn- count-leaps
  [gps-time]
  (count (filter #(>= gps-time %) leaps)))

(defn gps->unix
  [gps-time]
  (+ gps-time 315964800 (count-leaps gps-time) (if (leaps gps-time) 0.5 0)))

(defn floor [x] (.floor js/Math x))

(defn to-map [f coll] (into {} (for [x coll] [x (f x)])))

(defn options->map
  [options]
  (into {} (vec (map vec (partition 2 options)))))

(defn pad-with 
  [length value col] 
  (first (partition length length (repeat value) col)))