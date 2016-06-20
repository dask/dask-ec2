class Table():

    def __init__(self, data, tabletype=0):
        self.data = data
        tabletypes = ["standard", "boldHead", "headless"]
        if isinstance(tabletype, int) and ((tabletype >= 0) and (tabletype <= 2)):
            self.tabletype = tabletype
        else:
            ok = False
            for i, j in enumerate(tabletypes):
                if j == tabletype:
                    self.tabletype = i
                    ok = True
            if not ok:
                self.tabletype = 0
            #self.tabletype = tabletypes.index(tabletype)
    def formatRowBorder(self, colLengths):
        s = "+"
        # TODO: Simplify?
        for n in colLengths:
            s += "-" * (n + 2)
            s += "+"
        return s

    def formatRow(self, row, columns, colLengths):
        s = ""
        colsInRow = len(row)
        for n in range(columns):
            if n <= (colsInRow - 1):
                s += "| " + row[n] + (" " * ((colLengths[n] - len(row[n])) + 1))
            else:    # index out of bounds
                s += "|" + (" " * (colLengths[n] + 2))
        s += "|"
        return s

    def write(self):
        # Find maximum columns
        # TODO: Don't store local copy, use self.data
        data = self.data
        columns = 0
        for r in data:
            if len(r) > columns:
                columns = len(r)
        # Convert array to strings for printing
        for i, r in enumerate(data):
            for j, c in enumerate(r):
                data[i][j] = str(c)
        #DEBUG: print data
        # Find max length in each column
        maxColLengths = [0] * columns
        for i, r in enumerate(data):
            for j, c in enumerate(r):
                if (len(str(c)) > maxColLengths[j]):
                    maxColLengths[j] = len(str(c))
        #DEBUG: print maxColLengths
        # Print rable
        if self.tabletype == 0:
            border = self.formatRowBorder(maxColLengths)
            i = 0
            for r in data:
                if (i <= 1):
                    print(border)
                print(self.formatRow(r, columns, maxColLengths))
                i += 1
            print(border)
        elif self.tabletype == 1:
            border = self.formatRowBorder(maxColLengths)
            i = 0
            for r in data:
                if (i <= 1):
                    print(border if i == 0 else border.replace("-", "="))
                print(self.formatRow(r, columns, maxColLengths))
                i += 1
            print(border)
        elif self.tabletype == 2:
            border = self.formatRowBorder(maxColLengths)
            for r in data:
                print(border)
                print(self.formatRow(r, columns, maxColLengths))
            print(border)
