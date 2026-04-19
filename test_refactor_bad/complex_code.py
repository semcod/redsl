"""
This is a complex module with high cyclomatic complexity.
"""

def process_data(data, mode, threshold, callback, flag1, flag2, flag3, flag4, flag5):
    """Very complex function with high CC."""
    if mode == "A":
        if threshold > 100:
            if flag1:
                if flag2:
                    if flag3:
                        if flag4:
                            if flag5:
                                if callback:
                                    return callback(data * 2)
                                else:
                                    return data * 2
                            else:
                                return data
                        else:
                            return data / 2
                    else:
                        return data - 1
                else:
                    return data + 1
            else:
                return 0
        elif threshold > 50:
            if flag1:
                return data * 1.5
            else:
                return data / 1.5
        elif threshold > 25:
            if flag2:
                return data + 10
            else:
                return data - 10
        else:
            return 0
    elif mode == "B":
        if flag1 and flag2 and flag3:
            if data > threshold:
                return callback(data) if callback else data
            else:
                return 0
        elif flag1 and flag2:
            return data * 0.5
        elif flag1:
            return data * 0.25
        else:
            return 0
    elif mode == "C":
        for i in range(int(threshold)):
            if data > i:
                data += 1
            else:
                data -= 1
        return data
    else:
        return None

# Duplicated code
def process_data_copy(data, mode, threshold, callback, flag1, flag2, flag3, flag4, flag5):
    """Copy of process_data - exact duplicate."""
    if mode == "A":
        if threshold > 100:
            if flag1:
                if flag2:
                    if flag3:
                        if flag4:
                            if flag5:
                                if callback:
                                    return callback(data * 2)
                                else:
                                    return data * 2
                            else:
                                return data
                        else:
                            return data / 2
                    else:
                        return data - 1
                else:
                    return data + 1
            else:
                return 0
        elif threshold > 50:
            if flag1:
                return data * 1.5
            else:
                return data / 1.5
        elif threshold > 25:
            if flag2:
                return data + 10
            else:
                return data - 10
        else:
            return 0
    elif mode == "B":
        if flag1 and flag2 and flag3:
            if data > threshold:
                return callback(data) if callback else data
            else:
                return 0
        elif flag1 and flag2:
            return data * 0.5
        elif flag1:
            return data * 0.25
        else:
            return 0
    elif mode == "C":
        for i in range(int(threshold)):
            if data > i:
                data += 1
            else:
                data -= 1
        return data
    else:
        return None

class GodClass:
    """A god class with too many responsibilities."""
    
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
