---- MODULE Test1623LLMAgainstTest1623 ----
EXTENDS Test1623LLM

Gold == INSTANCE Test1623 WITH x <- x
GoldSpec == Gold!Init /\ [][Gold!Next]_<<x>>
====
