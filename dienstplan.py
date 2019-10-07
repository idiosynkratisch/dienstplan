import os
import math
import statistics
import time
import copy
import locale
import calendar
import datetime
import itertools

locale.setlocale(locale.LC_ALL, '')
cal = calendar.Calendar()

days = [locale.ABDAY_2, locale.ABDAY_3, locale.ABDAY_4, locale.ABDAY_5,
        locale.ABDAY_6]
days = [locale.nl_langinfo(day) for day in days]

#Enter the available time slots in this list.
times = ['10-12', '12-14', '14-16', '16-18']

shifts = 20 #Enter total number of shifts per week here.

def create_indexed_list(d):
    """Creates an indexed list which is less costly to copy."""
    l = []
    index = {}
    for name in d:
        l.append(d[name])
        index[name] = len(l) - 1
    return index, l

def prepare_limits(prefs, limit, personal_limits):
    """Computes the dict giving the maximum number of shifts for each p."""

    limits = {}
    sum = 0

    for name in prefs:
        if name in personal_limits:
            limits[name] = personal_limits[name]
        else: limits[name] = limit

        #check that limit is less than times someone is actually available.
        available = 0
        for pref in prefs[name]:
            if pref: available += 1
        if available < limits[name]: limits[name] = available

        sum += limits[name]

    empty_limit = shifts - sum
    if empty_limit > 0:
        prefs['---'] = shifts*[-1]
        limits['---'] = empty_limit

    return limits

def find_best_plans(prefs, limit, personal_limits = {}):
    """Finds the best plans given the constraints.

    The constraints are given in form of preferences (prefs),
    the general limit on number of shifts (limit),
    and personal limits of individual people (personal_limits),
    which should be a dict assigning the limit to their name."""

    limits = prepare_limits(prefs, limit, personal_limits)

    highscore = 0
    best_plans = []
    i = 0

    for plan in possible_plans(prefs, limits):
        i += 1
        score = value(plan, prefs)
        if score < highscore:
            continue
        elif score > highscore:
            highscore = score
            best_plans = [plan]
        elif score == highscore: 
            best_plans.append(plan)

    print(i)

    best_plans.sort(key=lambda x: 
                    statistics.pvariance(
                    [prefs[name][time] for time, name in enumerate(x)]))

    return best_plans

def value(plan, prefs):
    """Returns the score of a plan based on the prefs"""
    scores = [prefs[name][time] for time, name in enumerate(plan)]
    return sum(scores)

def generate_possibilities(prefs, verbose = False):
    """Gives a list of possible entries for each slot.

    If verbose is set, it outputs this list in a readable format."""

    poss = []
    for i in range(shifts):
        l = []
        for name in prefs:
            if prefs[name][i] == 0: continue
            else:
                l.append(name)
        poss.append(l)

    if verbose:
        strs = []
        # sorting the orginal lists may decrease performance
        for time, li in enumerate(copy.deepcopy(poss)):
            li.sort(key = lambda x: prefs[x][time], reverse=True)
            l = ['{0} ({1})'.format(name, prefs[name][time]) for name in li]
            strs.append(', '.join(l))
        grid = list(zip(*zip(*[iter(strs)]*5)))
        for i, day in enumerate(days):
            for j, time in enumerate(times):
                print('{0} {1}: {2}'.format(day, time, grid[i][j]))

    return poss


def possible_plans(prefs, limits):
    """Generates all possible plans compatible with prefs and limits.

    Plans have entries out of the people who have prefs.
    Plans are lists of people of length 20 (line after line)."""

    poss = generate_possibilities(prefs)
    
    limits = create_indexed_list(limits)

    max = 1
    for l in poss:
        max *= len(l)
    global quarter, half, three_quarter, milestones
    quarter, half, three_quarter = int(max/4), int(max/2), int(3*max/4)
    milestones = {quarter, half, three_quarter}
    global it_counter, start_time
    it_counter = 0
    start_time = time.time()

    for plan in generate_plans(poss, *limits, shifts):
        yield plan
   
def generate_plans(poss, index, lim, len):
    """Recursive generator for possible plans given poss."""

    global it_counter

    for name in poss[shifts - len]:
        it_counter += 1
        if it_counter in milestones:
            elapsed = int(time.time() - start_time)
            min, sec = elapsed // 60, elapsed % 60
            time_str = 'after {0}:{1} min, '.format(min, sec)
            output = time_str + str(it_counter)
            if it_counter == quarter: print('25% ' + output)
            elif it_counter == half: print('50% '  + output)
            elif it_counter == three_quarter: print('75% ' + output)

        limits = lim[:]  #store a copy of limits to reset to later
        lim[index[name]] -= 1
        if lim[index[name]] < 0: continue
        if len == 1:
            yield [name]
        else:
            for rest in generate_plans(poss, index, lim, len - 1):
                yield [name] + rest
        lim = limits

def unpack_preferences(folder=os.getcwd()):
    """Goes through the forms in folder and reads the preferences.
    
    Default for folder is the current working directory."""

    filelist = os.listdir(folder)

    try:
        filelist.remove('.DS_Store')
    except ValueError:
        pass

    print(filelist)

    prefs_list = [get_prefs(folder + '/' + file) for file in filelist]
    return dict(prefs_list)   

def get_prefs(file):
    """Reads in preferences from a file (as path)."""

    print('Reading file ' + file)
    data = open(file)
    name = data.readline().split()[1]

    pref = []

    for line in data:
        line = line.strip()
        if line == '': continue
        else:
            cells = [cell.strip() for cell in line.split('|')]
            if cells[0].strip('-') == '': continue
            elif cells[0] not in times: continue
            else:
                pref.extend([float(i) for i in cells[1:]])

    return name, pref
                
def format_plan(plan):
    """Outputs the plan in a human-readable format."""

    width = max([len(name) for name in plan]) + 2
    plan = list(zip(*[iter(plan)]*5))
    header = (7*' ' + ''.join(
    ['|{:^{width}}'.format(day, width=width) for day in days]) + '\r\n')
    separator = 7*'-' + 5*('|' + width*'-') + '\r\n'
    output = header
    for time, line in enumerate(plan):
        output += separator
        cells = ['|{:^{width}}'.format(name, width=width) for name in line]
        output += ' '+times[time]+' ' + ''.join(cells) + '\r\n'

    output += '\r\n'
    return output

def isInDateRange(start_date, end_date, date):
    """Checks whether a given date is in a given range of dates.

    start_date and end_date have to be lists of the form [day, month]
    date must be a datetime.date
    """
    
    c = lambda x: \
            ((x.month == start_date[1] and x.day >= start_date[0]) or \
            (start_date[1] < x.month < end_date[1]) or \
            (x.month == end_date[1] and x.day <= end_date[0])) 
    return c(date)

def removeDuplicateItems(l):
    """Changes a list in place so that each item occurs only once."""

    for i, item in enumerate(l):
        for j in range(i):
            if l[j] == item: l.remove(item)

def generate_form(span = (), free = [], names = []):
    """Generates the preferences form.

    span is a 2-tuple of strings indicating the time-span
    for which preferences can be given. Must be in format (d)d.(m)m.(yyyy)
    free is a list of either 2-tuples of strings, indicating periods or
    single days for which no preference is needed.
    If no span is given, a form for a weekly plan is returned.
    """

    output = 'Name: ' + 2*'\r\n'
    if not span == ():
        #This generates a form for more than one week
        start_date, end_date = \
            [list(map(int, date.split('.')[:2])) for date in span]
        months = []
        year = datetime.date.today().year
        for month in range(start_date[1], end_date[1]+1):
            months.extend(cal.monthdatescalendar(year,
                          month))

        removeDuplicateItems(months)

        freeset = set()
        for item in free:
            if type(item) is str:
                day, month = list(map(int, item.split('.')[:2]))
                freeset.add(datetime.date(year, month, day))
            if type(item) is tuple:
                s,e = [list(map(int, date.split('.')[:2])) for date in item]
                daylist = []
                for week in months:
                    d = filter(lambda x: isInDateRange(s, e, x), week) 
                    daylist.extend(d)
                freeset = freeset | set(daylist)
        
        free = freeset
        width = max([len(name) for name in names]) + 2

        for week in months:
            c = lambda x: isInDateRange(start_date, end_date, x) and \
                    x.weekday() < 5 and x not in free
            weekdays = list(filter(c, week))
            if weekdays == []:
                continue
            else:
                d = ['{:%d.%m.}'.format(day) for day in weekdays]
                header = 7*' ' + \
                ''.join(['|{:^{width}}'.format(day, width=width) \
                for day in d]) + '\r\n'
                output += header
                cells = len(weekdays)*('|'+ width*' ') + '\r\n'
                separator = 7*'-'+len(weekdays)*('|'+width*'-') + '\r\n'
                for time in times:
                    output += separator + ' '+time+' ' + cells
                output += '\r\n'
    else:
        #This generates the form for one week
        width = max([len(day) for day in days]) + 2
        header = 7*' ' +\
        ''.join(['|{:^{width}}'.format(day, width=width) for day in days])+\
        '\r\n'
        output += header
        cells = len(days)*('|'+ width*' ') + '\r\n'
        separator = 7*'-'+len(days)*('|'+width*'-') + '\r\n'
        for time in times:
            output += separator + ' '+time+' ' + cells
        output += '\r\n'
        
    output += '0 = Kann nicht, 1 = Kann, 2 = Möchte Gerne'
    return output

def calculate_shifts(span = (), free = []):
    """Returns the number of shifts in the given time period."""

    start_date, end_date = \
             [list(map(int, date.split('.')[:2])) for date in span]
    months = []
    year = datetime.date.today().year
    for month in range(start_date[1], end_date[1]+1):
        months.extend(cal.monthdatescalendar(year,
                      month))

    removeDuplicateItems(months)

    freeset = set()
    for item in free:
        if type(item) is str:
            day, month = list(map(int, item.split('.')[:2]))
            freeset.add(datetime.date(year, month, day))
        if type(item) is tuple:
            s,e = [list(map(int, date.split('.')[:2])) for date in item]
            daylist = []
            for week in months:
                days = filter(lambda x: isInDateRange(s, e, x), week) 
                daylist.extend(days)
            freeset = freeset | set(daylist)
    
    free = freeset
    
    c = lambda x: isInDateRange(start_date, end_date, x) and \
                    x.weekday() < 5 and x not in free

    days = [list(filter(c, week)) for week in months]
    days = list(filter(lambda x: x != [], days))

    dates = itertools.chain.from_iterable(months)
    dates = list(filter(c, dates))
    shifts = len(dates) * len(times)

    return days, shifts
