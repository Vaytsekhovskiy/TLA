---- MODULE Test1623AgainstTest1623Control ----
EXTENDS Test1623

Candidate == INSTANCE Test1623Control WITH x <- x
CandidateSpec == Candidate!Init /\ [][Candidate!Next]_<<x>>
====
