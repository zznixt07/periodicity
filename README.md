## limit execution of expensive function once every day or once every month.
For use in pythonanywhere.com where there is limited CPU time.

Note:
> the below script must run as frequently as the smallest unit of time in the
decorator func. A func wont run every 10 minute if the script containing it
only executes once every hour.
This decorator won't really work if the script continually runs without exiting. 


## Installation
`pip install --user git+https://github.com/zznixt07/periodicity.git`

## Usage

```
from periodicity import every, every_specific

@every(days=1)
def theory_of_everything(): 
    pass

# run this func on the day 2 of every month
@every_specific(day_of_month=2)
def expensive_af():
    pass

# run below func at the 15th of every month and then every 4 days until end of month
@every_specific(day_of_month=15, repeat_every_days=4)
def dodgy_fn():
    pass 

```
