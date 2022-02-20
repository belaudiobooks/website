"""Pluralization filter for books count in templates"""

from atexit import register
from django import template

import re

register = template.Library()


@register.filter
def by_plural(value, variants):
    variants = variants.split(',')
    value = abs(int(value))

    if value % 10 == 1 and value % 100 != 11:
        variant = 0
    elif value % 10 >= 2 and value % 10 <= 4 and (value % 100 < 10 or value % 100 >= 20):
        variant = 1
    else:
        variant = 2
    
    return variants[variant]

@register.filter
def gender(value, variants):
    variants = variants.split(',')

    if value and value=='FEMALE':
        variant = 0
    else: 
        variant = 1
    
    return variants[variant]

@register.filter
def duration(value):
    day, seconds = value.days, value.seconds
   
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    
    #check if more than 24 horus and assign correct spelling for values
    hours = by_plural(hrs,'гадзіна,гадзіны,гадін')
    minutes = by_plural(mins,'мінута,мінуты,мінут')
    seconds = by_plural(secs,'сякунда,сякунды,сякунд')

    if day:
        days = by_plural(day,'дзень,дня,дней')
        #return values with spelling in Belarussian if more than 24 hours
        return f'{day} {days} {hrs} {hours} {mins} {minutes} {secs} {seconds}'
    
    #return values with spelling in Belarussian
    return f'{hrs} {hours} {mins} {minutes} {secs} {seconds}'


        
    