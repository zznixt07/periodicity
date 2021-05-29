import os
import json
import logging
import calendar
from datetime import datetime, timezone, timedelta
from typing import Tuple, Callable, Any, List
from functools import wraps

logger = logging.getLogger(__name__)

def get_datadir() -> str:
    import platform
    """
    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming
    """

    home = os.path.expanduser('~')
    platform_name = platform.system().lower()
    if 'windows' in platform_name:
        datadir = 'AppData/Roaming'
    if 'linux' in platform_name:
        datadir = '.local/share'
    elif 'darwin' in platform_name:
        datadir = 'Library/Application Support'
    # don think we can make the dir if for some strange reason its doesn't exists
    return os.path.join(home, datadir)

def get_default(key, value, overwrite=False):
    dir_path = os.path.join(get_datadir(), 'py_my_db', 'db')
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, 'fn_ts.json'), 'a+', encoding='UTF-8') as file:
        file.seek(0)
        contents = file.read()
        
        try:
            obj = json.loads(contents)
        except json.JSONDecodeError:
            obj = {}

        if (not overwrite) and (key in obj):
            return obj[key]
        obj[key] = value

        file.seek(0)
        file.truncate()
        file.write(json.dumps(obj))
        return value

def every_specific(func=None, *, day_of_month: int = 1, repeat_every_days: int = 31):
    '''only runs on day > day_of_month and a multiple of repeat_every_days that is < 31.
    Its main advantage is one can choose to run it at every start of a month which
    is not the same as running it every 30 days cuz of dynamic length of months.
    '''
    
    if repeat_every_days <= 0:
        raise ValueError('repeat_every_days must be > 0')
    if day_of_month not in range(-1, 32):
        raise ValueError('day_of_month must be > 0 and <= 31')

    if day_of_month == -1:
        utc_now = datetime.now(tz=timezone.utc)
        # get the last day of the current month of the current year
        day_of_month = calendar.monthrange(utc_now.year, utc_now.month)[1]

    def wrapper(fn):

        @wraps(fn)
        def call_fn_or_not(*args, **kwargs):
            allowed_days: List[int] = [
                (i * repeat_every_days) + day_of_month
                for i in range(0, ((31 - day_of_month) // repeat_every_days) + 1)
            ]
            logger.debug('runs on days: %s', allowed_days)
            utc_dt: datetime = datetime.now(tz=timezone.utc)
            today: datetime = utc_dt.replace(
                 hour=0, minute=0, second=0, microsecond=0
            )
            fn_name: Callable[[args, kwargs], Any] = fn.__name__
            # should only run on allowed_days days, and only once a day.
            for i, day in enumerate(allowed_days):
                if today.day == day:
                    # only <date> is enough. but <datetime> is used for extensiblity
                    today_ts: float  = today.timestamp()
                    succ_day: int
                    succ_ts: float
                    try:
                        succ_day = allowed_days[i + 1]
                        succ_ts = today.replace(day=succ_day).timestamp()
                    except IndexError:
                        # wrap around. get last day. add the succ_day to that to get ts.
                        succ_day = allowed_days[0]
                        last_day: int = calendar.monthrange(utc_dt.year, utc_dt.month)[1]
                        succ_ts = (
                            today.replace(day=last_day) + timedelta(days=succ_day)
                        ).timestamp()

                    signature: Tuple[int, int, float] = (day_of_month, repeat_every_days, succ_ts)
                    stored_sig: Tuple[int, int, float] = get_default(fn_name, signature)
                    stored_ts: float = stored_sig[-1]
                    # print(succ_day)
                    # print('today_ts', today_ts)

                    # will not run if entry is being stored for the first time in db.
                    # I think that is the expected behaviour.
                    if day_of_month != stored_sig[0] or repeat_every_days != stored_sig[1]:
                        # if signature is changed update db.
                        logger.info('func signature modified.')
                        stored_sig = get_default(fn_name, signature, overwrite=True)
                    if today_ts >= stored_ts:
                        # main condition is ==. '>' just to be safe
                        # expired
                        logger.info('expired. setting new time.')
                        get_default(fn_name, signature, overwrite=True)
                    else:
                        # today_ts <= stored_ts; hasn't expired
                        logger.info(
                            'skipping %s. expires in %.0f secs',
                            fn_name,
                            stored_ts - utc_dt.timestamp()
                        )
                        return

                    logger.info('running %s', fn_name)
                    return fn(*args, **kwargs)

            logger.info("skipping func <%s>.Unmatching Day.", fn_name)
            return
            
        return call_fn_or_not
    
    if func:
        return wrapper(func)

    return wrapper

def every(func=None, *, days=3):
    '''param::days also accepts float cuz timedelta supports float.
    timestamp is stored in UTC not local.
    '''

    def wrapper(fn):
        
        @wraps(fn)
        def call_fn_or_not(*args, **kwargs):
            fn_name = fn.__name__
            now_ts = datetime.now(tz=timezone.utc).timestamp()
            t_minus_days = now_ts + timedelta(days=days).total_seconds()
            stored_ts = get_default(fn_name, t_minus_days)
            # this is the obv way to check if value was written or not by above func.
            if stored_ts != t_minus_days:
                # if its a new entry, dont enter this loop.
                if now_ts > stored_ts:
                    # expired
                    logger.info('expired. setting new time.')
                    get_default(fn_name, t_minus_days, overwrite=True)
                else:
                    # now_ts <= stored_ts; hasn't expired
                    logger.info('skipping %s. expires in %.0f secs', fn_name, stored_ts - now_ts)
                    return
            logger.info('running %s', fn_name)
            return fn(*args, **kwargs)

        return call_fn_or_not

    if func:
        return wrapper(func)
    return wrapper


if __name__ == '__main__':
    logging.basicConfig(level=10)
    # @every
    # @every_specific
    # @every_specific(day_of_month=10)
    @every_specific(day_of_month=14, repeat_every_days=5)
    def net():
        print('=======================net=================')

    net()

