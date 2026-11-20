---- MODULE ConfigParamsAgainstConfigParamsLLM ----
EXTENDS ConfigParams

Model == INSTANCE ConfigParamsLLM WITH x <- x, y <- y, z <- z, w <- w
ModelSpec == Model!Init /\ [][Model!Next]_<<x, y, z, w>>
====
