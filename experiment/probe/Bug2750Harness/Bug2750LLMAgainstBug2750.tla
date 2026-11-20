---- MODULE Bug2750LLMAgainstBug2750 ----
EXTENDS Bug2750LLM

Gold == INSTANCE Bug2750 WITH buffer <- buffer, waitP <- waitP, waitC <- waitC
GoldSpec == Gold!Spec
====
