---- MODULE ConfigParamsLLM ----

EXTENDS Integers, Strings, Seq, Set

(* 
 * NOTE: The SANY parser error in the previous attempt occurred because `MyModelValue2` was used 
 * as a standalone identifier (constant) before being defined. TLA+ requires all constants to be 
 * declared via EXTENDS or CONSTANTS before they can appear in expressions.
 * 
 * To fix this, we include the specific model values in the EXTENDS clause so they are recognized 
 * as valid constant names at parse time, matching the configuration file's intent.
 *)

EXTENDS Integers, Strings, Seq, Set, Model1, Model2

(* 
 * Declare variables. 
 * Note: MyInt, MyStr, MyModelValue1, MySet are treated as constants provided by the config.
 * We must ensure all identifiers used in the module body are either declared or defined before use.
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