---- MODULE Bug2750AgainstBug2750LLM ----
EXTENDS Bug2750

Model == INSTANCE Bug2750LLM WITH buffer <- buffer, waitP <- waitP, waitC <- waitC
ModelSpec == Model!Spec
====
