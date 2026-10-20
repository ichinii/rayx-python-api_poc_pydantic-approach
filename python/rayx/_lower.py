from . import _model0, _model1

def lower(beamline1: _model1.Beamline):
    return _model0.Beamline()

def trace(beamline1: _model1.Beamline):
    trace_params = _model0.TraceParams()
    trace_params.seed = 42
    trace_params.object_record_mask = []
    trace_params.ray_attr_record_mask = _model0.RayAttrMask.ALL
    trace_params.max_events = None
    trace_params.max_batch_size = None
    return _model0.trace(lower(beamline1), trace_params)
