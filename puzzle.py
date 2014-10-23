import sudoku

class RowView(object):
    def __init__(self,parent,row):
        self.parent=parent
        self.row=row
    def Show(self, wl=None):
        row=self.row
        width=wl if wl != None else list(5 for i in row.data)
        i=0
        for x in row.data:
            c=None
            if x.val:
                v = "'%s'" % x.val if wl else x.val
            elif wl:
                c="["
                v=""
                l=list(x.alt_tuple())
                l.sort()
                for e in l:
                    v = v + "%s%s" % (c,e)
                    c = ","
                v +="]"
            else:
                v='.'
            d = width[i] - len(v)
            if d > 0:
                d = d/2
                v = " "*d + v +" "*d
            print v,
            i = i + 1
            if i in range(row.parent.dim,row.parent.sq_dim,row.parent.dim):
                print "|",
        print

class SudokuView(object):
    def __init__(self,parent,doc):
        self.parent=parent
        self.update(doc)

    def notify_change(self):
        self.parent.notify_change(self,self.doc)

    def update(self,doc):
        self.doc=doc
        self.rows = tuple(RowView(self,r) for r in filter(lambda x: type(x[0]) is sudoku.Row, (ds for ds in doc.sets))[0])
        self.cols = filter(lambda x: type(x[0]) is sudoku.Col, (ds for ds in doc.sets))[0]

    def PrintSolution(self,solution):
        sq_dim=self.doc.sq_dim
        def pos(x): return "y:%2d,x:%2d" % (x/sq_dim+1,x%sq_dim+1)
        def eset_pos(x):
            if len(x) == 1:
                return "# %2d" % (int(x[0])+1)
            else:
                return "# <y:%d, x:%d>" % (x[0]+1,x[1]+1)
        def vals(x): return "[%s]" % ", ".join(v for v in x)
        def cells(c): return "{C#[%s]}" % "], C#[".join(pos(x) for x in c)
        for step in solution:
            mode=step[0]
            if mode == "group":
                print "Group: %s @ %s; reduction: %s in %s %s" % (
                    vals(step[1]), cells(step[2]), cells(step[3]), step[4], eset_pos(step[5]))
            elif mode == "cross":
                delta=step[1]
                cr=step[2]
                e=step[3]
                print "cross: reducing:",delta,"on cross of",cr.a_obj.name,cr.a_obj.pos,cr.b_obj.name,cr.b_obj.pos,"reduction at",e.name,e.pos
            elif mode == "tuples":
                print "C#[%s]: '%s' ; last on crossing" % (pos(step[1]),step[2])
            else:
                print "C#[%s]: '%s' ; last alternative in %s" % (pos(step[0]), step[1], step[2])

    def Show(self,show_maybe=True):
        cw=[]
        print "  ",
        i = 1
        doc = self.doc
        for c in self.cols:
            max_w = 5
            if show_maybe:
                for x in c.data:
                    n = x.alt_size()
                    if n == 0: n = 1
                    w = 2*n+1
                    if w > max_w: max_w = w
            cw.append(max_w)
            print ((max_w-5)/2)*" ", "%2d" % i,(max_w-(max_w-5)/2-4)*" ",
            if i in range(doc.dim,doc.sq_dim,doc.dim): print " ",
            i = i + 1
        print
        i=0
        w = sum(cw)+len(cw)-1+2*(doc.dim-1)
        for rv in self.rows:
            if i in range(0,doc.sq_dim,doc.dim):
                print "  ", w*"-"
            print "%2d" % (i+1),
            rv.Show(cw if show_maybe else None)
            i = i + 1
        print "  ", w*"-"

    def edit(self):
        shared = {
            "solution": [],
            "maybe":False,
            "quit": False,
        }
        def _edit_pt(y,x,s):
            doc=self.doc
            sav=doc.Export()
            try:
                doc.data[y*doc.sq_dim+x].setval(s if s in doc.alfabet else None)
                new=doc.Export()
            except:
                print "Argument error"
                return
            if not doc.IsValid():
                doc.Populate(sav)
                print "This will invalidate puzzle if applied. Reverted"
            else:
                try:
                    res,path=doc.Solve()
                    if not res:
                        print "This change leads to multiple possible solutions"
                    doc.Populate(new)
                except ValueError, e:
                    doc.Populate(sav)
                    print "This is unsolvable combination. Reverted"
        def _solve(steps=None,ns=shared):
            print "Solving:",
            ns["solution"]=None
            res, s = self.doc.Solve(explain=True,steps=steps)
            ns["solution"]=s
            return res
        def _asn(var,val,ns=shared):
            ns[var] = val
            print var,'=',ns[var]
        def _new_dim(dim):
            self.update(sudoku.Sudoku(dim))
            self.notify_change()
        def _print_solution(ns):
            self.PrintSolution(ns['solution'])
            ns['solution']=[]
        def _solve_cross():
            res=doc.SolveCrossings(True,[])
            return res
        def _solve_groups():
            lst=[]
            res=doc.SolveGroups(True,lst)
            self.PrintSolution(lst)
            return res
        def _solve_simple():
            lst=[]
            res=doc.SolveSimple(True,lst)
            self.PrintSolution(lst)
            return res
        while(not shared['quit']):
            cmd=raw_input("# ").split()
            if len(cmd) == 0: continue
            try:
                doc=self.doc
                e=None
                v={
                'v': lambda ns: doc.Populate('.12.....83...46........2.5...3......6...1...4..72..9.....63.74.73.42.........753.'),
                'd': lambda ns: _new_dim(int(cmd[1]) if len(cmd) > 1 else 3),
                'e': lambda ns: _edit_pt(int(cmd[1])-1,int(cmd[2])-1,cmd[3]),
                'clr': lambda ns: doc.Populate(),
                't': lambda ns: self.Show(ns['maybe']),
                'm': lambda ns: _asn('maybe',bool(eval(cmd[1])) if len(cmd) > 1 else ns['maybe']),
                'h': lambda ns: self.PrintSolution(doc.Hint(int(cmd[1]) if len(cmd) > 1 else None)),
                'x': lambda ns: doc.Export(),
                'i': lambda ns: doc.Populate(cmd[1]),
                'g': lambda ns: reduce(lambda x,y: 'reduced: '+str(x)+', remain:'+str(doc.total-x),(doc.GenHard(),self.Show(ns['maybe']))),
                'p': lambda ns: _print_solution(ns),
                's': lambda ns: _solve(int(cmd[1]) if len(cmd) > 1 else None),
                'sc': lambda ns: _solve_cross(),
                'sg': lambda ns: _solve_groups(),
                'ss': lambda ns: _solve_simple(),
                'sh': lambda ns: doc.SolveHard(),
                'q': lambda ns: _asn('quit',True),
                }[cmd[0]](shared)
                if v != None: print v
            except KeyError,e:
                pass
            except IndexError,e:
                pass
            except ValueError,e:
                pass
            finally:
                if e != None:
                    print "invalid command [%s]: '%s'" % (e," ".join(cmd))

class SudokuPuzzle(object):
    def __init__(self,size=3):
        self.doc  = sudoku.Sudoku(size)
        self.view = SudokuView(self,self.doc)

    def notify_change(self,view,doc):
        if self.view != view: return
        if self.doc == doc: return
        self.doc = doc

    def size(self):
        return self.doc.dim

    def run(self):
        self.view.edit()

def main(argv):
    sd=SudokuPuzzle(3)
    sd.run()
    return sd

if __name__ == "__main__": sd=main([])
