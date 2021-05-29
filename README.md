## limit execution of expensive function once every day or once every month.
For use in pythonanywhere.com where there is limited CPU time.

Assume the below script runs every 40 minutes
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
def dodgy_fn():
    pass 

```
