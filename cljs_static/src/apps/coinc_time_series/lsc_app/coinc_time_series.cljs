(ns lsc-app.coinc-time-series
  (:require [lsc-web.data :as data]
            [lsc-web.plots :as plots :refer [scale get-size select extent d3
                                             describe! prepare! translate!
                                             draw! style!]]
            [lsc-web.utils :refer [gps->unix floor]]
            [cljs.core.async :as async]
            [clojure.string :refer [join]]
            [jayq.core :as jq])
  (:require-macros
    [cljs.core.async.macros :refer [go]]))

(defn- load-time-series
  [group coinc]
  (let [url (str (.-webRoot js/definitions) "/coinc/group/" (:id group) 
                 "/time-series/" (:id coinc) "/all")
        out (async/chan 1)
        data-chan (data/unwrap-result (data/load-json url))]
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

(defn run []
  (let [group (get-group)
        coinc (get-coinc)
        time-series-chan (load-time-series group coinc)
        container (select "body")]
    (go (let [time-series (async/<! time-series-chan)]
          (.log js/console time-series)))))
(jq/document-ready run)
