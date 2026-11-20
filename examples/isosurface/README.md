# Quadratic form isohypersurface sampler

This package serves as an example, and also integration test for the RBA framework.
It demonstrates simple problem,
that is not too dummy (uses meaningfully all data structures),
but is not greatly optimized to ease the reading.

## Problem
We are given a real-valued quadratic form and wish to find an isohypersurface
where the form evaluates to a given value (*threshold*).

## Solution
Let us spawn multiple tasks and each of them will undertake an iterative algorithm to refine the form variables.
We hold a *lower* variable assignment that evaluates the form to a value lower than the *threshold*.
And similarly, *upper*. Then we iterate the *bisection method*.

### Sampling
To differentiate solutions a bit, we introduce an *exceptional variable* that changes differently than the midpoint between *lower* and *upper*.

## Initialization
We need to start the process in a valid state, i.e., provide valid assignments that evaluate above and below the threshold.
This can be easily achieved by properly preparing the input data,
because, unlike in reality, we do not care about solving any significant problem.
