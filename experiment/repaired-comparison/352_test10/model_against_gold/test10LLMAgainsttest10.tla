---- MODULE test10LLMAgainsttest10 ----
EXTENDS test10LLM

Gold == INSTANCE test10 WITH x <- x
GoldSpec == Gold!Init /\ [][Gold!Next]_<<x>>
====
