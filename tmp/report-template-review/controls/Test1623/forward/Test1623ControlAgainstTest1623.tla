---- MODULE Test1623ControlAgainstTest1623 ----
EXTENDS Test1623Control

Gold == INSTANCE Test1623 WITH x <- x
GoldSpec == Gold!Init /\ [][Gold!Next]_<<x>>
====
