--------------------------- MODULE Test1623LLM ---------------------------
EXTENDS Integers

CONSTANT N
VARIABLE x

Init == x = N

Next ==
    \/ x > 0 /\ x' = x - 1
    \/ x = 0 /\ UNCHANGED x

Inv == x >= 0

Spec == Init /\ [][Next]_<<x>>
=============================================================================
