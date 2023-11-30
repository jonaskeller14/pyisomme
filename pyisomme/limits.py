import fnmatch
import re


class Limits:
    def __init__(self, name: str = None, limits: list = None):
        self.name = name
        self.limits = [] if limits is None else limits

    def get_limits(self, code: str) -> list:
        """
        Returns list of limits matching given code.
        :param code: Channel code (pattern not allowed)
        :return:
        """
        output = []
        for limit in self.limits:
            for code_pattern in limit.code_patterns:
                if fnmatch.fnmatch(code, code_pattern):
                    output.append(limit)
                try:
                    if re.match(code_pattern, code):
                        output.append(limit)
                except re.error:
                    continue
        return output

    def read(self, *paths):
        pass

    def write(self, path):
        pass


class Limit:
    def __init__(self, code_patterns: list, points: tuple, color="black", linestyle="-", name: str = None):
        self.code_patterns = code_patterns
        self.points = points  # tuple of x,y --> represent not only constants but also lines with corner
        self.color = color
        self.linestyle = linestyle
        self.name = name
