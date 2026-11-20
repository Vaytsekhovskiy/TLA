---- MODULE ConfigParamsLLM ----

EXTENDS Integers, Strings, Seq, Set

(* Constants declared in the configuration file *)
CONSTANTS MyInt, MyStr, MyModelValue1, MyModelValue2, MySet

(* Variables to be initialized and checked *)
VARIABLES x, y, z, w

(* Initialization: bind variables to constants *)
Init == 
  x = MyInt /\
  y = MyStr /\
  z = MyModelValue1 /\
  w = MySet

(* Next: state never changes *)
Next == TRUE

(* Invariant: assert that variables hold the specific constant values *)
Inv == 
  x = MyInt /\
  y = MyStr /\
  z = MyModelValue1 /\
  w = MySet /\
  z != MyModelValue2

(* System specification: start at Init, always satisfy Inv, and transition via Next *)
Spec == Init /\ [][Next]_<>CHOOSE x,y,z,w \/ \A s : INVARIANT(s) => Inv(s)

----