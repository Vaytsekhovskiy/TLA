---- MODULE Bug2750AgainstBug2750Control ----
EXTENDS Bug2750

Candidate == INSTANCE Bug2750Control WITH buffer <- buffer, waitP <- waitP, waitC <- waitC
CandidateSpec == Candidate!Spec
====
