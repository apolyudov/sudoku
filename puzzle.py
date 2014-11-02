import sys
from sudoku import Sudoku, Row, Col

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
        self.rows = tuple(RowView(self,r) for r in filter(lambda x: type(x[0]) is Row, (ds for ds in doc.all_esets))[0])
        self.cols = filter(lambda x: type(x[0]) is Col, (ds for ds in doc.all_esets))[0]

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

    def edit(self, interactive=True, read=None):
        shared = {
            "solution": [],
            # turn 'possible values' hint on/ off for each cell
            "maybe":False,
            "quit": False,

            # some predefined puzzles for debugging, the 'simple', 'medium', 'hard' are logically derivable,
            # 'impossible' require guesswork
            # impossible still must have single solution 
            "games": [('..3.849.1...7....62.....4....5..6..9..49.16..9..5..8....2.....57....2...4.819.7..', 3, 'medium'),
                      ('.61.....5...74......4.9....8.......7.7.3..1....58.....42.....18...96..52.3.......', 3, 'hard'),
                      ('18.3.6......8............658.9.3..1..7.....2..3..4.7.652............3......5.7.39', 3, 'hard'),
                      ('.12.....83...46........2.5...3......6...1...4..72..9.....63.74.73.42.........753.', 3, 'impossible'),
                      ('36...AF072E4..5.9.......5...E3........2B9.6..4..542.E8....D...1.A09D.B.......7.C.'
                       '.....6.......F..8..A..E..C..9.54...C.3.D.5...8B...1...F.0A..8.D.A.....4..3......E'
                       '.7....4FB.....B...1.....8E.....3F....6A7..02.9.DB4F0......C.7..7.C.ED..B...6.11.E'
                       '......50....4', 4, 'hard'),
                      ('6..8..2......9.AC.9.6...4.....5......4....A.3.....5.01...8D3..2E....B..A01...4.84'
                       '...E.93B.F......0.347..92.6...5..C..2...3.7.0.925..7B.E......0C.8..A...7F..1.E...'
                       '318......CB.......3..1..0..7..........A5.2.68....D.C8............A..4B8..D2.F.32.'
                       '....5C7.4...D', 4, 'hard'),
                     ]
        }
        if read == None:
            def _read():
                return raw_input('# ')
            read = _read
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
                    res,_=doc.Solve()
                    if not res:
                        print "This change leads to multiple possible solutions"
                    doc.Populate(new)
                except ValueError:
                    doc.Populate(sav)
                    print "This is unsolvable combination. Reverted"
        def _solve(steps=None,ns=shared):
            print "Solving:",
            s = ns["solution"] = []
            res = self.doc.Solve(solution=s,steps=steps)
            return res
        def _asn(var,val,ns=shared):
            ns[var] = val
            print var,'=',ns[var]
        def _new_dim(dim):
            self.update(Sudoku(dim))
            self.notify_change()
        def _print_solution(ns):
            doc=self.doc
            doc.PrintSolution(ns['solution'], sys.stdout)
            ns['solution']=[]
        def _solve_cross():
            doc=self.doc
            lst=[]
            res=doc.SolveCrossings(lst)
            doc.PrintSolution(lst, sys.stdout)
            return res
        def _solve_groups():
            lst=[]
            res=doc.SolveGroups(lst)
            doc.PrintSolution(lst, sys.stdout)
            return res
        def _solve_simple():
            lst=[]
            res=doc.SolveSimple(lst)
            doc.PrintSolution(lst, sys.stdout)
            return res
        def _show_groups():
            for g in doc.grp.values():
                print g
                
        def _test_solver(ns, steps):
            while steps > 0:
                steps -= 1
                _, path = doc.GenHard(init = True)
                self.Show(ns['maybe'])
                gen = doc.Export()
                print gen
                doc.Populate()
                doc.Populate(gen)
                if not _solve():
                    print 'Test failed: steps=%d' % steps
                    print 'Solution from generator'
                    doc.PrintSolution(path, sys.stdout)
                    break
                doc.PrintSolution(ns['solution'], sys.stdout)
            else:
                print 'Test passed'
        def _verify_solver(ns, idx):
            doc = self.doc
            games = ns['games']
            if idx < 0 or idx >= len(games):
                idx = 0
                print "only %d validation games defined, selected 0" % len(games)
            game_data, game_dim, game_complexity = games[idx]
            if doc.dim != game_dim:
                _new_dim(game_dim)
                doc = self.doc
            doc.Populate(game_data)
            self.Show(ns['maybe'])
            print 'New Game: dimension: %d; complexity: %s; total %d populated cells of %d' % (
                   game_dim, game_complexity, len(filter(lambda c: c != '.', game_data)), len(game_data))
            
        while(not shared['quit']):
            cmd=read().split()
            if len(cmd) == 0: continue
            try:
                doc=self.doc
                e=None
                v={
                'v': lambda ns: _verify_solver(ns, int(cmd[1]) if len(cmd) > 1 else 0),
                'd': lambda ns: _new_dim(int(cmd[1]) if len(cmd) > 1 else 3),
                'e': lambda ns: _edit_pt(int(cmd[1])-1,int(cmd[2])-1,cmd[3]),
                'clr': lambda ns: doc.Populate(),
                't': lambda ns: self.Show(ns['maybe']),
                'm': lambda ns: _asn('maybe',bool(eval(cmd[1])) if len(cmd) > 1 else ns['maybe']),
                'h': lambda ns: doc.PrintSolution(doc.Hint(int(cmd[1],sys.stdout) if len(cmd) > 1 else None)),
                'x': lambda ns: doc.Export(),
                'i': lambda ns: doc.Populate(cmd[1]),
                'gen': lambda ns: reduce(lambda x,y: 'reduced: '+str(x)+', remain:'+str(doc.total-x),(doc.GenHard(init = True, seed = cmd[1] if len(cmd) > 1 else None)[0],self.Show(ns['maybe']))),
                'grp': lambda ns: _show_groups(),
                'p': lambda ns: _print_solution(ns),
                's': lambda ns: _solve(int(cmd[1]) if len(cmd) > 1 else None),
                'sc': lambda ns: _solve_cross(),
                'sg': lambda ns: _solve_groups(),
                'ss': lambda ns: _solve_simple(),
                'sh': lambda ns: doc.SolveHard(),
                'u': lambda ns: _test_solver(ns, int(cmd[1]) if len(cmd) > 1 else 1000),
                'q': lambda ns: _asn('quit',True),
                }[cmd[0]](shared)
                if v != None: print v
            except KeyError,e:
                print e
                raise
            except IndexError,e:
                print e
                raise
            except ValueError,e:
                print e
                raise
            finally:
                if e != None:
                    print "invalid command [%s]: '%s'" % (e," ".join(cmd))

class SudokuPuzzle(object):
    def __init__(self,size=3):
        self.doc  = Sudoku(size)
        self.view = SudokuView(self,self.doc)
        self.debug = True

    def notify_change(self,view,doc):
        if self.view != view: return
        if self.doc == doc: return
        self.doc = doc

    def size(self):
        return self.doc.dim

    def run(self):
        self.view.edit()

def main_console(argv):
    sd=SudokuPuzzle(3)
    sd.run()
    return sd
