import os

import pytz

local_tz = pytz.timezone(os.environ.get("LOCAL_TZ", "US/Eastern"))