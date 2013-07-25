
from numpy import dtype, int32, float32, float64
    
def make_dtype(**fields):
    return dtype(fields.items())

trigger_dtype = make_dtype(time=float32,
                           time_min=float64,
                           time_max=float64,
                           freq=float32,
                           freq_min=float64,
                           freq_max=float64,
                           snr=float32,
                           amplitude=float64,
                           q=float32)
