from decimal import getcontext, ROUND_FLOOR


class DecimalAccuracy:
    getcontext().prec = 30
    getcontext().rounding = ROUND_FLOOR
