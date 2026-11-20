---- MODULE test10Againsttest10LLM ----
EXTENDS test10

Model == INSTANCE test10LLM WITH x <- x
ModelSpec == Model!Init /\ [][Model!Next]_<<x>>
====
