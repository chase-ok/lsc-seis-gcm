
from numpy import dtype, uint32, float32, float64
    
def make_dtype(**fields):
    return dtype(fields.items())

trigger = make_dtype(time=float32,
                     time_min=float64,
                     time_max=float64,
                     freq=float32,
                     freq_min=float64,
                     freq_max=float64,
                     snr=float32,
                     amplitude=float64,
                     q=float32)

coincidence = make_dtype(dt=float64,
                         mean_time=float64,
                         mean_snr=float64,
                         mean_freq=float64,
                         trigger1=uint32,
                         trigger2=uint32)