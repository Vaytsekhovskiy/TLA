---- MODULE Test1623LLM ----

CONSTANTS N

VARIABLES x

Init == x = N

Next == (x > 0) /\ (x' = x - 1) \/ (x = 0) /\ (x' = x)

Inv == x >= 0

Spec == Init /\ [][Next]_x /\ Inv

---- END MODULE ----