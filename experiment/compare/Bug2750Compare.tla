--------------------------- MODULE Bug2750Compare ---------------------------
EXTENDS Naturals, Sequences
CONSTANTS Producers, Consumers, BufCapacity
VARIABLES gold_buffer, gold_waitP, gold_waitC, model_buffer, model_waitP, model_waitC

Gold == INSTANCE Bug2750 WITH
  buffer <- gold_buffer, waitP <- gold_waitP, waitC <- gold_waitC
Model == INSTANCE Bug2750LLM WITH
  buffer <- model_buffer, waitP <- model_waitP, waitC <- model_waitC

Init == Gold!Init /\ Model!Init
Next == Gold!Next /\ Model!Next
vars == <<gold_buffer, gold_waitP, gold_waitC, model_buffer, model_waitP, model_waitC>>
Spec == Init /\ [][Next]_vars
GoldSpec == Gold!Init /\ [][Gold!Next]_<<gold_buffer, gold_waitP, gold_waitC>>
=============================================================================
