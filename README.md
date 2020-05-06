# Uncontrolled Manifold Research App
## Background
This app demonstrates a toy example for the uncontrolled manifold (UCM) hypothesis (Scholz & Schöner, 1999).
In its basic form there is one performance criterion for a task, but two degrees of freedom (df) to fulfill that goal.

target = x1 + x2  | target = const  
x1 and x2 are two uncoupled state variables.

This creates a subspace of df configurations that is redundant for successful task performance.

[//]: # (Todo: Is that really a vector SUBSPACE with all its properties?)

Final state variability in df configurations should be elongated along the task-irrelevant direction and be less in the
task-relevant direction orthogonal to it.

This is a toy example as it doesn't really explore the variability in the underlying biomechanical system and only
captures results of the control signals. I assume, there's no measurable effect of control-dependent noise either.

Since optimal feedback control is related to UCM theory in the sense that the optimal control law may not act along
certain dimensions (the UCM), one prediction made for optimal feedback control in the presence of control-dependent
noise is that if more control is asserted in the redundant direction (e.g. no optimal control law) the reduced variance
in that direction comes at the expense of increased variance in the task-relevant direction (Todorov, 2004).

To demonstrate one possible operationalization for testing that prediction, there's one task condition that tries to
limit the variability compared to the redundant direction of the unconstrained task by introducing a second performance
criterion that relies on one of the degrees of freedom.
As mentioned, due to suppositional absence of measurable effects of control-dependent noise, no increased error in the
first performance criterion is expected.

## References
John P. Scholz; Gregor Schöner (1999).
"The uncontrolled manifold concept: identifying control variables for a functional task".
Experimental Brain Research. 126 (3): 289–306.

Todorov, Emmanuel (2004). "Optimality principles in sensorimotor control". Nature Neuroscience. 7 (9): 907–915.


## Installation
- compile using buildozer
- Install apk to Android device
