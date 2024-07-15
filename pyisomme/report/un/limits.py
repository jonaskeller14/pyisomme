from pyisomme.limits import Limit


class Limit_Pass(Limit):
    name = "Pass"
    color = "green"
    rating = True


class Limit_Fail(Limit):
    name = "Fail"
    color = "red"
    rating = False
