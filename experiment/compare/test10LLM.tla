--------------------------- MODULE test10LLM ---------------------------
EXTENDS Integers

VARIABLE x

Init == x = TRUE
Next == UNCHANGED x

f1[i \in Int] == i + 2
f2[i, j \in Int] == i + j
f4[i, j \in Int] == [a |-> i, b |-> j]
f5[i, j, k \in Int] == i + j + k

Inv ==
    /\ f1[3] = 5
    /\ f2[3, 4] = 7
    /\ f2[<<3, 4>>] = 7
    /\ f4[3, 4].a = 3
    /\ f4[3, 4].b = 4
    /\ f5[3, 4, 5] = 12
    /\ f5[<<3, 4, 5>>] = 12

Spec == Init /\ [][Next]_<<x>>
=============================================================================
