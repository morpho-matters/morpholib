# Provides a class of stopwatch objects.
import time

'''
Stopwatch object. Measures the duration between a .tic() call
and a .toc() call in units of seconds.'''
class Timer(object):
    # Constructor. Initializes startTime to
    # the time of construction.
    def __init__(self):
        self.startTime = time.perf_counter()

    # Resets the timer.
    def tic(self):
        self.startTime = time.perf_counter()

    # Returns time elapsed (in seconds) since the last
    # .tic() was called.
    def toc(self):
        return time.perf_counter() - self.startTime

# Function waits for the condition specified by cond to be True.
# cond is an expression given using lambda.
# e.g. waitfor(lambda: fileExists("someFile.txt"))
# "until" is the maximum amount of time to wait for cond to be True
# Defaults to infinity.
# "period" is how many seconds to wait before checking again if cond is True
# Defaults to 1 second.
# waitfor() returns True if cond becomes True
# waitfor() returns False if until exceeded, and so waitfor() gave up.
# NOTE: cond is evaluated lazily. waitfor() uses the variable names:
# cond, __waitfor_timer, until, time, period
# If you use the same names in your cond, waitfor() may act badly.
# Hopefully, your expression for cond doesn't use any of these names,
# but just to be safe, the correct way to provide input into cond is to
# explicitly declare your variables like so:
#
# lambda x=x, y=y, z=z: your_expression_containing_xyz
#
# That way, when cond is evaluated, x, y, and z will be YOUR x, y, and z.
def waitfor(cond, until=float("inf"), period=1):
    if type(cond) is str:
        cond = lambda cond=cond: eval(cond)
    __waitfor_timer = Timer()
    while not cond() and __waitfor_timer.toc() < until:
        time.sleep(period)
    return cond()

# Object used for the tic() and toc() functions that can
# be used in the global scope.
masterTimer = Timer()

# Resets the master timer
def tic():
    masterTimer.tic()

# Returns seconds elapsed since last tic() was called.
def toc():
    return masterTimer.toc()
