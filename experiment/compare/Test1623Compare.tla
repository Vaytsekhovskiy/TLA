--------------------------- MODULE Test1623Compare ---------------------------
EXTENDS Integers
CONSTANT N
VARIABLES gold_x, model_x

Gold == INSTANCE Test1623 WITH x <- gold_x
Model == INSTANCE Test1623LLM WITH x <- model_x

Init == Gold!Init /\ Model!Init
Next == Gold!Next /\ Model!Next
vars == <<gold_x, model_x>>
Spec == Init /\ [][Next]_vars
GoldSpec == Gold!Init /\ [][Gold!Next]_<<gold_x>>
=============================================================================
