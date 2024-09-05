from settle.pojo.case.CaseAction import CaseAction

"""
一个taker是一个case
"""


class Case:

    def __init__(self, data=None):
        self.id = None
        self.tag = None
        self.type = None
        self.case_actions: list[CaseAction] = None
        if data:
            self.__dict__.update(data)
