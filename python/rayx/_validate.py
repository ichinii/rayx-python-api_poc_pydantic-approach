"""Validation of a model1 tree.

model1 checks itself wherever an object is complete: at construction and when loading
json. It deliberately does not check on assignment, because building a value up field
by field passes through states that are not yet valid. This module is the other half of
that bargain, re-checking a finished tree before anything is done with it.
"""

from typing import TypeVar

from . import _model1

T = TypeVar("T", bound=_model1.Model)


def validate(beamline1: _model1.Beamline) -> None:
    """Check a whole beamline, raising pydantic's ValidationError if anything is wrong.

    Since assignment is unchecked, this is the authoritative check. `trace` runs it for
    you; call it directly to check a beamline you are still assembling, without paying
    for a trace. The error lists every problem found, each with the path to the field it
    came from.
    """
    validated(beamline1)


def validated(model: T) -> T:
    """Re-check a model1 tree and return a revalidated, coerced copy.

    Assignment is unchecked, so a field may hold anything that was written to it since
    construction, including a value of the wrong type or one that breaks an invariant
    spanning several fields. Re-validating the dumped tree re-runs every validator in
    model1 over the final beamline, so each invariant stays written exactly once, next
    to the field it constrains, rather than being restated here.

    The copy is what callers should lower: revalidation also *coerces*, turning a
    `"10"` assigned after construction back into a `10.0` before it reaches a nanobind
    setter. `warnings=False` keeps such a value from emitting a serializer warning on
    the way out; it is still caught or coerced on the way back in.

    The caller's model is left untouched: one that fails should not be silently
    rewritten, and one that passes has nothing to rewrite.
    """
    return type(model).model_validate(model.model_dump(warnings=False))
