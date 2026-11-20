MODULE Bug2750LLM

EXTENDS Naturals, FiniteSets

(* CONSTANTS *)
CONSTANTS 
    Producers,
    Consumers,
    BufCapacity

(* VARIABLES *)
VARIABLES buffer, waitP, waitC

(* INITIALIZATION *)
Init == 
  /\ buffer = <<>>
  /\ waitP = {}
  /\ waitC = {}

(* HELPER FUNCTIONS *)
IsFull == Len(buffer) >= BufCapacity
IsEmpty == Len(buffer) = 0
HeadItem == If IsEmpty Then [] Else [1] -> buffer

(* PRODUCER ACTION *)
p(self) == 
  /\ self \in Producers
  /\ self \notin waitP
  /\ (If IsFull Then
       /\ waitP' = waitP + {self}
     Else
       /\ Let newItem := HeadItem In
          /\ buffer' = newItem ++ tail(buffer)
          /\ waitP' = waitP
          /\ waitC' = If waitC /= {} Then waitC - (HeadOf(waitC)) \/ waitC
                     Else waitC
     End)

(* CONSUMER ACTION *)
c(self) == 
  /\ self \in Consumers
  /\ self \notin waitC
  /\ (If IsEmpty Then
       /\ waitC' = waitC + {self}
     Else
       /\ Let newItem := HeadItem In
          /\ buffer' = tail(buffer)
          /\ waitC' = waitC
          /\ waitP' = If waitP /= {} Then waitP - (HeadOf(waitP)) \/ waitP
                     Else waitP
     End)

(* NEXT STATE RELATION *)
Next == \A self \in Producers \/ Consumers : p(self) \/ c(self)

(* TEMPORAL SPECIFICATION *)
Spec == Init /\ [][Next]_buffer /\ [][Next]_waitP /\ [][Next]_waitC

(* INVARIANT: Deadlock Freedom *)
(* At least one process must be able to proceed or no one is waiting indefinitely.
   Specifically, not all producers AND consumers are blocked simultaneously. *)
Inv == ~((\A p \in Producers : p \in waitP) /\ (\A c \in Consumers : c \in waitC))

(* ACTUAL INVARIANT CHECKED BY TLC (Stronger version to ensure safety) *)
(* The problem statement asks for an invariant asserting it is never the case that all are blocked.
   However, in a standard bounded buffer, "blocked" usually implies waiting on empty/full condition.
   Let's refine Inv to be the exact logical negation of total deadlock state as described. *)

(* Re-defining Inv to strictly match the description: 
   It is never the case that (all producers are in waitP) AND (all consumers are in waitC). *)
Inv == ~(\A p \in Producers : p \in waitP /\ \A c \in Consumers : c \in waitC)

(* Note: The TLC configuration provided checks INVARIANT Inv. 
   We must ensure the module defines Inv exactly as required for the check. *)

\* Override Inv in the module scope to match the specific requirement
Inv == ~(\A p \in Producers : p \in waitP /\ \A c \in Consumers : c \in waitC)