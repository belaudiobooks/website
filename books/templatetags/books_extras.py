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

    minutes = by_plural(mins,'хвіліна,хвіліны,хвілін')

    if day:
        hrs = hrs + (day * 24)
    
    if hrs:
        hours = by_plural(hrs,'гадзіна,гадзіны,гадзін')
        return f'{hrs} {hours} {mins} {minutes}'
    
    return f'{mins} {minutes}'

@register.filter
def colors(value):
    """getting quotient of the ASCII code of the first sympol of uuid, 
    where 0 is 0, 1-3 are 1, 4-6 are 2, 7-9 are 3, a-c are 4 and d-f are 5
    """
    first = str(value)[0]
    if first.isdigit():
        if int(first) == 0:
            key = 0
        elif int(first) in range(1, 4):
            key = 1
        elif int(first) in range(4, 7):
            key = 1
        elif int(first) in range(7, 10):
            key = 2  
    else:
        if first in ['a','b','c']:
            key = 3
        else: key = 4

    colors = {
        0:'/static/cover_templates/cover_templates_blue.jpeg',
        1:'/static/cover_templates/cover_templates_green.jpeg',
        2:'/static/cover_templates/cover_templates_grey.jpeg',
        3:'/static/cover_templates/cover_templates_purple.jpeg',
        4:'/static/cover_templates/cover_templates_red.jpeg',
        5:'/static/cover_templates/cover_templates_yellow.jpeg'
    }

    result = colors.setdefault(key,0)

    return result