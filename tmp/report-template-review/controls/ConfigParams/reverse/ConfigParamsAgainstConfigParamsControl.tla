---- MODULE ConfigParamsAgainstConfigParamsControl ----
EXTENDS ConfigParams

Candidate == INSTANCE ConfigParamsControl WITH x <- x, y <- y, z <- z, w <- w
CandidateSpec == Candidate!Init /\ [][Candidate!Next]_<<x, y, z, w>>
====
