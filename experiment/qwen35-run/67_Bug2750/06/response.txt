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

LetHead == \A x \in Set: [x] -> head(x)
LetTail == \A x \in Set: [x] -> tail(x)

(* PRODUCER ACTION *)
p(self) == 
  /\ self \in Producers
  /\ self \notin waitP
  /\ (If IsFull Then
       /\ waitP' = waitP + {self}
     Else
       Let newItem := [1] -> buffer In
       /\ buffer' = newItem ++ tail(buffer)
       /\ waitP' = waitP
       /\ waitC' = If waitC /= {} Then waitC - {HeadOf(waitC)} \/ waitC
                  Else waitC
     End)

(* CONSUMER ACTION *)
c(self) == 
  /\ self \in Consumers
  /\ self \notin waitC
  /\ (If IsEmpty Then
       /\ waitC' = waitC + {self}
     Else
       Let newItem := [1] -> buffer In
       /\ buffer' = tail(buffer)
       /\ waitC' = waitC
       /\ waitP' = If waitP /= {} Then waitP - {HeadOf(waitP)} \/ waitP
                  Else waitP
     End)

(* NEXT STATE RELATION *)
Next == \A self \in Producers \/ Consumers : p(self) \/ c(self)

(* TEMPORAL SPECIFICATION *)
Spec == Init /\ [][Next]_buffer /\ [][Next]_waitP /\ [][Next]_waitC

(* INVARIANT: Deadlock Freedom *)
Inv == ~(\A p \in Producers : p \in waitP /\ \A c \in Consumers : c \in waitC)