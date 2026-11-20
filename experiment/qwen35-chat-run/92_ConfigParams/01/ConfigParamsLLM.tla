MODULE ConfigParamsLLM

(* Constants defined via configuration *)
CONSTANTS MyInt, MyStr, MyModelValue1, MyModelValue2, MySet

(* Variables to be initialized and checked *)
VARIABLE x, y, z, w

(* Initialization: bind variables to their corresponding constants *)
Init ==
  x = MyInt /\
  y = MyStr /\
  z = MyModelValue1 /\
  w = MySet

(* Transition relation: state is immutable *)
Next == TRUE

(* Invariant: assert that variables hold the specific constant values *)
Inv ==
  x = MyInt /\
  y = MyStr /\
  z = MyModelValue1 /\
  z <> MyModelValue2 /\
  w = MySet

(* Main specification combining Init, Next, and Inv *)
Spec ==
  Init /\ [][Next]_<x,y,z,w> /\
    \A s : [TRUE -> TRUE] |%s|
      (Init \/ (Inv /\ Next))

(* Optional: Explicitly declare the module as a simple state machine for TLC *)
ASSUME True

ENDMODULE