from enum import IntEnum


class CategoryType(IntEnum):
    '''Category types for income or expense.'''
    INCOME = 1
    EXPENSE = 2

    def __str__(self):
        if self == CategoryType.INCOME:
            return "income"
        elif self == CategoryType.EXPENSE:
            return "expense"
        else:
            raise ValueError(f'Invalid category type {self}')
