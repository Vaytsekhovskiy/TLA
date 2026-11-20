--------------------------- MODULE test10Compare ---------------------------
CONSTANTS dummy
VARIABLES gold_x, model_x

Gold == INSTANCE test10 WITH x <- gold_x
Model == INSTANCE test10LLM WITH x <- model_x

Init == Gold!Init /\ Model!Init
Next == Gold!Next /\ Model!Next
vars == <<gold_x, model_x>>
Spec == Init /\ [][Next]_vars
GoldSpec == Gold!Init /\ [][Gold!Next]_<<gold_x>>
=============================================================================
