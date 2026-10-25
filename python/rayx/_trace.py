"""The trace entry point: lower a beamline, run the tracer, wrap the result."""

from . import _model0, _model1
from ._lower import lower, lower_trace_params
from ._rays import Rays


def trace(beamline: _model1.Beamline, params: _model1.TraceParams | None = None) -> Rays:
    if params is None:
        params = _model1.TraceParams()
    # the splat is also the drift check: if `RAYX_RAY_ATTRS` and the `Rays` fields ever
    # disagree, this fails on a missing or unexpected keyword rather than losing a column
    columns = _model0.trace(
        lower(beamline), lower_trace_params(params, len(beamline.objects))
    )
    return Rays(recorded=params.ray_attr_record_mask, **columns)
