---- MODULE ConfigParamsControlAgainstConfigParams ----
EXTENDS ConfigParamsControl

Gold == INSTANCE ConfigParams WITH x <- x, y <- y, z <- z, w <- w
GoldSpec == Gold!Init /\ [][Gold!Next]_<<x, y, z, w>>
====
