---- MODULE ConfigParamsLLM ----

EXTENDS Integers, Strings, Seq, Set

(* 
 * Declare the configuration-provided constants.
 * These are expected to be bound to concrete values in the TLC/Alapche configuration file.
 *)
CONSTANTS MyInt, MyStr, MyModelValue1, MyModelValue2, MySet

(* 
 * Declare variables. 
 *)
VARIABLES x, y, z, w

(* 
 * Initialization predicate.
 * Binds variables to the configuration-provided constants.
 *)
Init == 
  x = MyInt /\
  y = MyStr /\
  z = MyModelValue1 /\
  w = MySet

(* 
 * Next predicate: state never changes (stuttering allowed).
 *)
Next == TRUE

(* 
 * Invariant predicate.
 * Asserts that variables hold the specific constant values and that the two model values are distinct.
 *)
Inv == 
  x = MyInt /\
  y = MyStr /\
  z = MyModelValue1 /\
  w = MySet /\
  MyModelValue1 != MyModelValue2

(* 
 * System specification.
 * Starts at Init, always satisfies Inv, and transitions via Next (which allows stuttering).
 *)
Spec == Init /\ [][Next]_<>CHOOSE x,y,z,w \/ \A s : INVARIANT(s) => Inv(s)

----