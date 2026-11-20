---- MODULE Bug2750LLM ----

CONSTANTS 
    Producers = {p1, p2},
    Consumers = {c1, c2},
    BufCapacity = 1

VARIABLES 
    buffer, waitP, waitC

Init == 
    buffer = << >> AND
    waitP = {} AND
    waitC = {}

Next == 
    /\ buffer' = buffer
    /\ waitP' = waitP
    /\ waitC' = waitC

p(self) ==
    /\ self \notin waitP
    /\ card(buffer) = BufCapacity
    /\ waitP' = waitP \cup {self}
    /\ waitC' = waitC

p(self) ==
    /\ self \notin waitP
    /\ card(buffer) < BufCapacity
    /\ buffer' = buffer \cup {self}
    /\ waitC' = waitC \cup {self}

c(self) ==
    /\ self \notin waitC
    /\ card(buffer) = 0
    /\ waitC' = waitC \cup {self}
    /\ waitP' = waitP

c(self) ==
    /\ self \notin waitC
    /\ card(buffer) > 0
    /\ buffer' = tail(buffer)
    /\ waitP' = waitP \cup {self}
    /\ waitC' = waitC

Spec == Init /\ [][Next]_vars

Inv == 
    /\ waitP \subseteq Producers
    /\ waitC \subseteq Consumers
    /\ NOT (waitP = Producers AND waitC = Consumers)

---- END MODULE Bug2750LLM ----