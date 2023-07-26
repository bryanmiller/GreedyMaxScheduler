# Copyright (c) 2016-2023 Association of Universities for Research in Astronomy, Inc. (AURA)
# For license information see LICENSE or https://opensource.org/licenses/BSD-3-Clause

from abc import ABC


# TODO: Perhaps makes SchedulerComponent a Singleton since we only need one instance of each during each execution.
class SchedulerComponent(ABC):
    """
    Base class for all Scheduler components involved in the pipeline.
    """
    ...
