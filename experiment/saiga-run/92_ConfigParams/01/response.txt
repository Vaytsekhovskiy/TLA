```module ConfigParamsLLM

(* Constants *)
CONSTANTS
  MyInt == 42
  MyStr == "hello"
  MyModelValue1 == Model1
  MyModelValue2 == Model2
  MySet == {1, 2, 3}

(* Types *)
ONE_TYPE
  MyType == TYPE

(* Model Values *)
CONSTANTS
  Model1 == MyModelValue1
  Model2 == MyModelValue2

(* Variables *)
VARIABLES
  x, y, z, w

(* Initial Predicate *)
PRED Init ==
  /\ x = MyInt
  /\ y = MyStr
  /\ z = MyModelValue1
  /\ w = MySet

(* Next Predicate *)
PRED Next == 
  /\ True

(* Invariant *)
PRED Inv ==
  /\ x = MyInt
  /\ y = MyStr
  /\ z = MyModelValue1
  /\ z /= MyModelValue2
  /\ w = MySet

END MODULE
```