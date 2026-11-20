---- MODULE ConfigParamsLLMAgainstConfigParams ----
EXTENDS ConfigParamsLLM

Gold == INSTANCE ConfigParams WITH x <- x, y <- y, z <- z, w <- w
GoldSpec == Gold!Init /\ [][Gold!Next]_<<x, y, z, w>>
====
