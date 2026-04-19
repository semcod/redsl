def calculate(x,y,z):
    if x>0:
        if y>0:
            if z>0:
                return x+y+z
            else:
                return 0
        else:
            return 0
    else:
        return 0

class BadClass:
    def method1(self,a,b,c,d,e,f):
        result=a+b+c+d+e+f
        if result>100:
            print("big")
        elif result>50:
            print("medium")
        elif result>10:
            print("small")
        else:
            print("tiny")
        return result
