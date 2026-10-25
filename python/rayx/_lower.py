"""Translation from the user facing model1 to the model0 wire types.

model1 and model0 describe the same beamline, so the translation is mostly a field by
field copy. It is driven by the field names the two models share rather than written out
per type, which means adding a field to both models needs no change here. Setting an
unknown attribute on a nanobind class raises, so a name that drifts apart fails loudly
instead of being silently dropped.

Only three things actually differ between the models, and each is handled explicitly
below: `Transform` flattens into a `glm::dmat4`, a `Polarization` becomes the jones
vector that is all c++ knows, and the `kind` discriminators disappear because model0
encodes the variant member in the type itself. Every other type is looked up in model0
under the same name.
"""

from typing import Optional

from . import _model0, _model1
from ._validate import validated


def _model0_class(model1_class: type) -> type:
    return getattr(_model0, model1_class.__name__)


def _lower_transform(transform: _model1.Transform) -> list[list[float]]:
    """A `Transform` as the `glm::dmat4` that model0 expects.

    glm indexes column first, `m[col][row]`, matching the type caster in
    `cpp/nanobind.cpp`. So each inner list here is a column, and the translation sits in
    the last one. A basis already *is* the images of the local axes, which is exactly
    what those columns are.
    """
    basis = _model1.to_basis(transform.orientation)
    column_x, column_y, column_z = basis.x, basis.y, basis.z
    return [
        [*column_x, 0.0],
        [*column_y, 0.0],
        [*column_z, 0.0],
        [*transform.position, 1.0],
    ]


def _lower_value(value: object) -> object:
    if isinstance(value, _model1.Transform):
        return _lower_transform(value)
    if isinstance(value, (_model1.LocalElectricField, _model1.Stokes)):
        # c++ only knows the jones vector, so stokes parameters are converted here.
        # neither type is a bound model0 class, both are a std::array<complex, 2>
        return _model1.to_local_electric_field(value).value
    if isinstance(value, _model1.Model):
        return _lower_model(value)
    if isinstance(value, (list, tuple)):
        return [_lower_value(item) for item in value]
    # numbers, strings, None and the enums shared with model0 pass straight through
    return value


def _lower_model(model: _model1.Model, /, **overrides: object) -> object:
    """Copy a model1 object onto its model0 counterpart, field by field.

    `overrides` replaces the lowered value of a named field, for the cases where the
    value cannot be derived from the field alone.
    """
    lowered = _model0_class(type(model))()
    for name in type(model).model_fields:
        if name == "kind":
            continue  # model0 encodes the variant member in the type itself
        value = overrides[name] if name in overrides else _lower_value(getattr(model, name))
        setattr(lowered, name, value)
    return lowered


def lower(beamline1: _model1.Beamline) -> _model0.Beamline:
    beamline1 = validated(beamline1)
    return _lower_model(beamline1)


def _object_record_mask(indices: Optional[set[int]], object_count: int) -> list[bool]:
    """model1 names the objects to record, model0 wants one flag per object.

    Which objects exist is a property of the beamline, not of the params, so this is
    the one check that cannot live in model1 and has to happen here.
    """
    if indices is None:
        return [True] * object_count

    out_of_range = sorted(i for i in indices if not 0 <= i < object_count)
    if out_of_range:
        raise ValueError(
            f"object_record_mask refers to objects {out_of_range}, "
            f"but the beamline has {object_count} objects"
        )
    return [index in indices for index in range(object_count)]


def lower_trace_params(params1: _model1.TraceParams, object_count: int) -> _model0.TraceParams:
    params1 = validated(params1)
    return _lower_model(params1, object_record_mask=_object_record_mask(params1.object_record_mask, object_count))
