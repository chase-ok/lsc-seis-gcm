(ns lsc-web.data
  (:require
    [cljs.core.async :as async :refer [chan close! put! <! >!]])
  (:require-macros
    [cljs.core.async.macros :refer [go]]))

(defn- do-load-json
  [url out on-error num-retries]
  (when (pos? num-retries)
        (.json js/d3 url (fn [error json]
          (if error
              (do (on-error url error)
                  (do-load-json url out on-error (dec num-retries)))
              (do (put! out json)
                  (close! out)))))))

(defn- log-error
  [url error]
  (.log js/console (str "Could not load " url ": " error)))

(defn load-json
    [url & {:keys [on-error num-retries] :or {on-error log-error, num-retries 3}}]
    (let [out (chan 1)]
      (go (do-load-json url out on-error num-retries))
      out))

(defn unwrap-result
  [data-chan & {:keys [on-error] :or {on-error log-error}}]
  (let [out (chan 1)]
    (go (let [json (<! data-chan)]
          (if (.-success json)
            (>! out (.-data json))
            (on-error (.-error json)))
          (close! out)))
    out))
;(go (.log js/console (<! (load-json "coinc.json"))))
