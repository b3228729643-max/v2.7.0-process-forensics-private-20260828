# FIG-P580-01 mathematical / textual consistency

- Source and adjacent text define the common domain [0,5], p(x)=6x(5-x)/125, q_L=(2/5)1_[0,5/2], q_R=1/5.
- Integral check: integral p=1, integral q_L=1, integral q_R=1.
- q_L=0 on (5/2,5) while p>0 there, so p is not absolutely continuous with respect to q_L; a finite weighted sample cannot restore arbitrary missing-support contribution.
- q_R>0 on [0,5], hence p<<q_R. The source/adjacent text correctly stops at support coverage and explicitly does not claim low variance or estimator reliability.
- Recomputed ratio card: w(1)=0.96, w(5/2)=1.50, w(4)=0.96.
- B44 conflict: its current caption is support coverage, but its stored unique-reading conclusion and modification plan describe an accept-reject budget flow. The frozen source, rendered figure, caption, and adjacent text all support the former; the latter is a task-card cross-contamination and must not control review.

RESULT: PASS
