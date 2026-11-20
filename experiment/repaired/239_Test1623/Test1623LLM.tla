---- MODULE Test1623LLM ----
EXTENDS Naturals

CONSTANTS N
ASSUME N \in Nat

VARIABLES x

Init ==
  x = N

Next ==
  IF x > 0 THEN
    x' = x - 1
  ELSE
    x' = x

Inv ==
  x >= 0

====
