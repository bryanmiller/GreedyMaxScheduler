# Copyright (c) 2016-2022 Association of Universities for Research in Astronomy, Inc. (AURA)
# For license information see LICENSE or https://opensource.org/licenses/BSD-3-Clause

import asyncio
import json
from datetime import datetime
from typing import List
import strawberry # noqa
from strawberry.file_uploads import Upload
from astropy.time import Time
from lucupy.minimodel import Site

from scheduler.core.builder import SchedulerBuilder
from scheduler.core.service.service import build_scheduler
from scheduler.core.sources import Origins
from scheduler.process_manager import setup_manager, TaskType
from scheduler.db.planmanager import PlanManager


from .types import (SPlans, NewScheduleResponse,
                    NewScheduleError, NewScheduleSuccess,
                    NewNightPlans, ChangeOriginSuccess)
from .inputs import CreateNewScheduleInput
from .scalars import SOrigin


builder = SchedulerBuilder()

# TODO: All times need to be in UTC. This is done here but converted from the Optimizer plans, where it should be done.
@strawberry.type
class Mutation:
    '''
    @strawberry.mutation
    def change_mode():
        pass

    '''

    @strawberry.mutation
    async def load_sources_files(self, files: List[Upload], service: str) -> List[str]:
        source_to_change = Services[service]
        builder.sources.use_file(source_to_change, files)
        contents = []
        for file in files:
            content = (await file.read()).decode("utf-8")
            contents.append(content)
        return contents

    @strawberry.mutation
    def change_origin(new_origin: SOrigin) -> ChangeOriginSuccess:
        old = str(builder.sources.origin)
        builder.sources.set_origin(new_origin)
        return ChangeOriginSuccess(from_origin=old, to_origin=str(new_origin))


@strawberry.type
class Query:
    all_plans: List[SPlans] = strawberry.field(resolver=lambda: PlanManager.get_plans())

    @strawberry.field
    def plans(self) -> List[SPlans]:
        return PlanManager.get_plans()

    @strawberry.field
    def site_plans(self, site: Site) -> List[SPlans]:
        return [plans.for_site(site) for plans in PlanManager.get_plans()]

    @strawberry.field
    def current_origin(self) -> SOrigin:
        return builder.sources.origin

    @strawberry.field
    def schedule(self, new_schedule_input: CreateNewScheduleInput) -> NewNightPlans:
        plans = PlanManager.get_plans_by_input(new_schedule_input.start_time,
                                               new_schedule_input.end_time,
                                               new_schedule_input.site)
        plans_summary = {}
        if not plans:
            start, end = Time(new_schedule_input.start_time, format='iso', scale='utc'), \
                    Time(new_schedule_input.end_time, format='iso', scale='utc')
            scheduler = build_scheduler(start, end, new_schedule_input.site, builder)
            plans, plans_summary = scheduler()
        splans = [SPlans.from_computed_plans(p, new_schedule_input.site) for p in plans]
        # json_summary = json.dumps(plans_summary)
        return NewNightPlans(night_plans=splans, plans_summary=plans_summary)
