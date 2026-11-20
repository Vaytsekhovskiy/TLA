---- MODULE Bug2750ControlAgainstBug2750 ----
EXTENDS Bug2750Control

Gold == INSTANCE Bug2750 WITH buffer <- buffer, waitP <- waitP, waitC <- waitC
GoldSpec == Gold!Spec
====
