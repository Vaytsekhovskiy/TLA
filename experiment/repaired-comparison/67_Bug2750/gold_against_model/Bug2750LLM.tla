---- MODULE Bug2750LLM ----
CONSTANTS Producers, Consumers, BufCapacity
VARIABLES buffer, waitP, waitC
vars == <<buffer, waitP, waitC>>
Init == /\ buffer = <<>>
        /\ waitP = {}
        /\ waitC = {}
Next == UNCHANGED vars
Spec == Init /\ [][Next]_vars
Inv == /\ waitP \subseteq Producers
       /\ waitC \subseteq Consumers
       /\ ~(waitP = Producers /\ waitC = Consumers)
====
