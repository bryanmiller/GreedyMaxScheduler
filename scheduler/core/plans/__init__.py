# Copyright (c) 2016-2022 Association of Universities for Research in Astronomy, Inc. (AURA)
# For license information see LICENSE or https://opensource.org/licenses/BSD-3-Clause

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import ceil
from typing import List, Mapping, Optional

from lucupy.minimodel import Observation, ObservationID, Site, Conditions, Band, Resource

from scheduler.core.calculations.nightevents import NightEvents


@dataclass(order=True, frozen=True)
class Visit:
    start_time: datetime  # Unsure if this or something else
    obs_id: ObservationID
    atom_start_idx: int
    atom_end_idx: int
    start_time_slot: int
    time_slots: int
    score: float
    instrument: Optional[Resource]

@dataclass(frozen=True)
class NightStats:
    timeloss: str
    plan_score: float
    plan_conditions: Conditions
    n_toos: int
    completion_fraction: Mapping[Band,int]


@dataclass
class Plan:
    """
    Nightly plan for a specific Site.

    night_stats are supposed to be calculated at the end when plans are already generated.
    """
    start: datetime
    end: datetime
    time_slot_length: timedelta
    site: Site
    _time_slots_left: int

    def __post_init__(self):
        self.visits: List[Visit] = []
        self.is_full = False
        self.night_stats: Optional[NightStats] = None
        self.alt_degs: List[List[float]] = []

    @staticmethod
    def time2slots(time_slot_length: timedelta, time: timedelta) -> int:
        # return ceil((time.total_seconds() / self.time_slot_length.total_seconds()) / 60)
        # return ceil((time.total_seconds() / self.time_slot_length.total_seconds()))
        return ceil(time / time_slot_length)

    def add(self,
            obs: Observation,
            start: datetime,
            start_time_slot: int,
            time_slots: int,
            score: float,
            atom_start_idx: int,
            atom_end_idx: int) -> None:
        visit = Visit(start,
                      obs.id,
                      atom_start_idx,
                      atom_end_idx,
                      start_time_slot,
                      time_slots,
                      score,
                      obs.instrument())
        self.visits.append(visit)
        self._time_slots_left -= time_slots

    def __contains__(self, obs: Observation) -> bool:
        return any(visit.obs_id == obs.id for visit in self.visits)

    def time_left(self) -> int:
        return self._time_slots_left


class Plans:
    """
    A collection of Plan from all sites for a specific night
    """

    def __init__(self, night_events: Mapping[Site, NightEvents], night_idx: int):
        self.plans = {}
        self.night = night_idx
        for site, ne in night_events.items():
            if ne is not None:
                self.plans[site] = Plan(ne.local_times[night_idx][0],
                                        ne.local_times[night_idx][-1],
                                        ne.time_slot_length.to_datetime(),
                                        site,
                                        len(ne.times[night_idx]))

    def __getitem__(self, site: Site) -> Plan:
        return self.plans[site]

    def __iter__(self):
        return iter(self.plans.values())

    def all_done(self) -> bool:
        """
        Check if all plans for all sites are done in a night
        """
        return all(plan.is_full for plan in self.plans.values())
