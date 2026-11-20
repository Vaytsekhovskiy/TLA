--------------------------- MODULE Bug2750LLM ---------------------------
EXTENDS Naturals, Sequences

CONSTANTS Producers, Consumers, BufCapacity
VARIABLES buffer, waitP, waitC

ProcSet == Producers \cup Consumers
vars == <<buffer, waitP, waitC>>

Init ==
    /\ buffer = << >>
    /\ waitP = {}
    /\ waitC = {}

isfull(b) == Len(b) = BufCapacity
isempty(b) == Len(b) = 0

Producer(self) ==
    /\ self \in Producers
    /\ self \notin waitP
    /\ IF isfull(buffer)
          THEN /\ waitP' = waitP \union {self}
               /\ UNCHANGED <<buffer, waitC>>
          ELSE /\ buffer' = Append(buffer, self)
               /\ waitP' = waitP
               /\ IF waitC # {}
                     THEN \E t \in waitC: waitC' = waitC \ {t}
                     ELSE waitC' = waitC

Consumer(self) ==
    /\ self \in Consumers
    /\ self \notin waitC
    /\ IF isempty(buffer)
          THEN /\ waitC' = waitC \union {self}
               /\ UNCHANGED <<buffer, waitP>>
          ELSE /\ buffer' = Tail(buffer)
               /\ waitC' = waitC
               /\ IF waitP # {}
                     THEN \E t \in waitP: waitP' = waitP \ {t}
                     ELSE waitP' = waitP

Next ==
    \/ \E p \in Producers: Producer(p)
    \/ \E c \in Consumers: Consumer(c)

Spec == Init /\ [][Next]_vars
Inv == ~(waitP = Producers /\ waitC = Consumers)
=============================================================================
