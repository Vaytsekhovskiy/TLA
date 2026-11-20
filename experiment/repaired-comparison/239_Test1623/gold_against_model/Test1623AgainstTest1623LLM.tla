---- MODULE Test1623AgainstTest1623LLM ----
EXTENDS Test1623

Model == INSTANCE Test1623LLM WITH x <- x
ModelSpec == Model!Init /\ [][Model!Next]_<<x>>
====
