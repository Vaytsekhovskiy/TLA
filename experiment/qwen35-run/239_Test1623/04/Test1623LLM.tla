MODULE Test1623LLM

CONSTANTS N

VARIABLE x

-- ASSUME N >= 0

(* Invariant: x is always non-negative *)
INV == x >= 0

(* Initial state: x equals N *)
Init == x = N

(* Next state relation: if x > 0 then decrement, else stay at 0 *)
Next == [][x]_
    IF x > 0 THEN
        x' = x - 1
    ELSE
        x' = x
    FI

-- The following specifications are required by the TLC configuration
SPECIFICATION
    INV
    Init
    Next

END