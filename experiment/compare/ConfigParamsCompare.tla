--------------------------- MODULE ConfigParamsCompare ---------------------------
CONSTANTS MyInt, MyStr, MyModelValue1, MyModelValue2, MySet
VARIABLES gold_x, gold_y, gold_z, gold_w, model_x, model_y, model_z, model_w

Gold == INSTANCE ConfigParams WITH
  x <- gold_x, y <- gold_y, z <- gold_z, w <- gold_w
Model == INSTANCE ConfigParamsLLM WITH
  x <- model_x, y <- model_y, z <- model_z, w <- model_w

Init == Gold!Init /\ Model!Init
Next == Gold!Next /\ Model!Next
vars == <<gold_x, gold_y, gold_z, gold_w, model_x, model_y, model_z, model_w>>
Spec == Init /\ [][Next]_vars
GoldSpec == Gold!Init /\ [][Gold!Next]_<<gold_x, gold_y, gold_z, gold_w>>
=============================================================================
