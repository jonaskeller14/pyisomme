from pyisomme.channel import Channel, time_intersect

import numpy as np
import logging


logger = logging.getLogger(__name__)


class Correlation_ISO18571:
    def __init__(self, reference_channel: Channel, comparison_channel: Channel, *args, **kwargs):

        from objective_rating_metrics.rating import ISO18571

        time = time_intersect(reference_channel, comparison_channel)
        if not np.all(np.abs(np.diff(time) - 0.0001) < 10e-6):
            logger.warning("Time resolution of 10 kHz required. Channel Data will be adjusted by interpolation.")
            t_start = time[0]
            t_end = time[-1]
            time = np.arange(t_start, t_end, 0.0001)

        reference_curve = np.vstack((time, reference_channel.get_data(t=time))).T
        comparison_curve = np.vstack((time, comparison_channel.get_data(t=time, unit=reference_channel.unit))).T

        self.iso18571 = ISO18571(reference_curve=reference_curve, comparison_curve=comparison_curve, *args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self.iso18571, attr)
