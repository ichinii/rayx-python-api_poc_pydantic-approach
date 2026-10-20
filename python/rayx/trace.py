from ._model1 import Beamline
from ._lower import trace as lower_trace

def trace(beamline: Beamline):
    return lower_trace(beamline)
