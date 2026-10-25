"""The result of a trace: one numpy array per ray attribute."""

from dataclasses import dataclass

import numpy as np

from ._model0 import RayAttrMask

__all__ = ["Rays"]


@dataclass(frozen=True)
class Rays:
    """Recorded ray events, one numpy array per attribute.

    `trace` returns the columns by value from C++, so each array is a writable view onto
    a buffer that numpy now owns. Nothing is copied on access, writes are visible to
    anything else holding the same column, and holding on to a single column lets the
    others be freed.

    `frozen` only stops the attributes being rebound; the arrays themselves stay
    mutable. The fields mirror `RAYX_RAY_ATTRS` in `cpp/model0.h`, in the same order.

    An attribute excluded by `TraceParams.ray_attr_record_mask` is a zero length array
    rather than None, so the type never varies. Compare `recorded` against the mask to
    tell "not recorded" from "recorded, but no events".
    """

    path_id: np.ndarray
    path_event_id: np.ndarray
    position_x: np.ndarray
    position_y: np.ndarray
    position_z: np.ndarray
    direction_x: np.ndarray
    direction_y: np.ndarray
    direction_z: np.ndarray
    local_electric_field_x: np.ndarray
    local_electric_field_y: np.ndarray
    optical_path_length: np.ndarray
    energy: np.ndarray
    order: np.ndarray
    object_id: np.ndarray
    source_id: np.ndarray
    event_type: np.ndarray
    rand_counter: np.ndarray

    # which attributes the trace was asked to record
    recorded: RayAttrMask
