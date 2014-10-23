#!/usr/bin/python
class Sudoku(object):
    def __init__(self, dim=3,seed=None):
        self.dim=d=int(dim)
        if d < 2 or d > 6 or type(dim) is not int: raise ValueError("dimention must be positive integer [2..6], but %r is given" % dim)
        self.sq_dim = sq_dim = d * d
        self.total = sq_dim * sq_dim
        self.grp={} # closed group lookup table
        self.defval='.'
        self.alfabet = (
        '1234' if dim == 2
        else ('123456789' if dim == 3
        else ('0123456789ABCDEF' if dim == 4
        else ('ABCDEFGHIJKLMNOPQRSTUVWXY' if dim == 5
        else ('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ' if dim == 6
        else   None)))))
        if not self.alfabet: raise ValueError('custom alfabet (iterable) for dim=%d with size %d must be defined' % (d, sq_dim))
        self.set_all = set(self.alfabet)
        self.data = tuple(Elem(self,i) for i in xrange(self.total))
        self.InitRand()
        self.check = False
        self.Setup()
        self.SetSync(True)
        self.Populate(seed)

    def Export(self):
        return "".join(x.val if x.val != None else self.defval for x in self.data)

    def InitRand(self):
        from random import Random
        self.rand=Random()

    def Setup(self):
        squares = tuple(Square(self,n) for n in xrange(self.sq_dim))
        rows = tuple(Row(self,n) for n in xrange(self.sq_dim))
        cols = tuple(Col(self,n) for n in xrange(self.sq_dim))

        self.sets = (squares,rows,cols)

        plain_sets = []
        for es in self.sets:
            plain_sets.extend(es)
        self.plain_sets = tuple(plain_sets)

        # now that we have sets defined, let's find crossings
        crossings=[]
        for i,e in enumerate(self.plain_sets[:-1]):
            for g in self.plain_sets[i+1:]:
                cross=set.intersection(set(e.data),set(g.data))
                if len(cross) <= 1: continue # either no crossing, or a single element => not interesting
                crossings.append(Crossing(self,cross,e,g))

        self.crossings = tuple(crossings)

        for cr in self.crossings:
            for x in cr.data:
                x.BindCrossing(cr)

        for e in self.plain_sets:
           for x in e.data:
               x.Bind(e)

        for x in self.data: x.BindComplete()

    def IsValidAlfabet(self,alfabet):
        return len(set(alfabet.upper())) == self.sq_dim

    def IsValid(self):
        return reduce(lambda x,y: x and y, tuple(e.IsValid() for e in self.data), True)

    def Hint(self,n=None):
        if n == None: n = 1
        sav=self.Export()
        res,path=self.Solve(steps=n)
        self.Populate(sav)
        return path

    def Populate(self,initial=None):
        for x in self.data:
            x.reset()
        
        if initial:
            if len(initial) != self.total:
                raise ValueError("Incorrect initial set size; must be %d" % self.total)
            for i in xrange(self.total):
                x = self.data[i]
                c = initial[i]
                fixed = c in self.alfabet
                x.setval(c if fixed else None, fixed)

    def SetSync(self,sync):
        self.grp={}
        for x in self.data:
            x.SetSync(sync)
        if sync: self.Update()
        self.sync=sync

    def Update(self):
        for x in self.data:
            x.update()

    def SolveHard(self,dbg=False):
        if not self.IsValid():
            print "Puzzle is not valid"
            return False
        try:
            self.check = False
            self.SetSync(False)
            res = True
            i=0
            imax=0
            for x in self.data: x.fixed = x.HasVal()
            while i < self.total:
                x = self.data[i]
                if(dbg): print "load: x[%d]=%s; maybe=%s; failed=%s; fixed=%s" % (x.pos,x.val,x.maybe,x.failed,x.fixed)
                if x.fixed:
                    i=i+1
                    continue
                x.update()
                t=tuple(x.maybe-x.failed)
                if len(t) == 0:
                    x.failed=set([])
                    if i == 0:
                        print "Puzzle is not solvable"
                        res = False
                        break
                    while i > 0:
                        i=i-1
                        x=self.data[i]
                        if not x.fixed: break
                    x=self.data[i]
                    x.failed.add(x.val)
                    x.setval(None)
                else:
                    v=t[self.rand.randint(0,len(t)-1)]
                    x.setval(v)
                    if(dbg): print "assign: x[%d]=%s; maybe=%s; failed=%s; fixed=%s" % (x.pos,x.val,x.maybe,x.failed,x.fixed)
                    i=i+1
                        
        except AttributeError, e:
            print "Error in Elem:", x.pos
            raise
        except ValueError, e:
            print e
            res = False
        finally:
            self.SetSync(True)
            self.check=True
        return res

    # Generating with a "SolveHard", reducing with "Solve"
    def GenHard(self,init=True):
        def can_remove(pos):
            try:
                gen=self.Export()
                self.data[pos].setval(None)
                res,path=self.Solve()
            except:
                res=False
            finally:
                self.Populate(gen)
            return res

        def reduce_random():
            cnt=0
            while(True):
                pos = self.rand.randint(0,self.total-1)
                if not self.data[pos].HasVal(): continue
                if can_remove(pos):
                    self.data[pos].setval(None)
                    cnt+=1
                else:
                    return cnt

        if init:
            self.Populate()
            self.SolveHard()

        stable=0
        while(True):
            if not reduce_random():
                stable += 1
            else:
                stable=0
            if stable == self.sq_dim: break
        Done=False
        while(not Done):
            for x in self.data:
                if not x.HasVal(): continue
                if can_remove(x):
                    x.setval(None)
                    break
            else:
                Done=True
        return self.Export().count(self.defval)

    def SolveSimple(self,explain,solution):
        res = False
        for pos,(e,val) in self.FindUniques():
            self.data[pos].setval(val)
            if explain:
                solution.append((pos,val,e.name))
            res = True
        for pos,val in self.FindTuples(1):
            self.data[pos].setval(val[0])
            if explain: solution.append(('tuples',pos,val[0]))
            res = True
        return res

    def SolveGroups(self,explain,solution):
        res = False
        self.UpdateClosedGroups()
        for g in self.grp.values():
            if not g.applied:
                modified=g.Apply(explain)
                if modified:
                    res = True
                    if explain: solution.append(('group',
                                     tuple(g.data)[0].alt_tuple(), # values in the group
                                     tuple(x.pos for x in g.data),  # cell numbers of the group
                                     tuple(m.pos for m in modified),# modified cell list, number of remaining alternatives
                                     g.eset.name,g.eset.pos))       # dataset position and name (row, col, sq)
        return res

    def SolveCrossings(self, explain, solution):
        res = False
        for cr in self.crossings:
            cm = set.union(*[set(x.maybe) if x.maybe != None else set([]) for x in cr.data])
            if cr.check_crossing(cm,cr.a_set,cr.a_obj,cr.b_set,cr.b_obj,explain,solution): res = True
            if cr.check_crossing(cm,cr.b_set,cr.b_obj,cr.a_set,cr.a_obj,explain,solution): res = True

        return res

    def Solve(self,explain=False,steps=None):
        self.check=True
        if steps != None: explain=True
        res = True
        solution=[]
        while res:
            if(steps != None and len(solution) >= steps): return True, solution[:steps]
            res = self.SolveSimple(explain,solution)
            if not res:
                res = self.SolveCrossings(explain,solution)
            if not res:
                res = self.SolveGroups(explain,solution)

        for x in self.data:
            if x.val is None: return False, solution
        return True,solution

    def FindTuples(self,size=1):
        tuples=[]
        for x in self.data:
            if x.val: continue
            if x.alt_size() == size:
                tuples.append((x.pos,x.alt_tuple()))
        return tuples

    def FindUniques(self):
        uniques=[]
        for x in self.data:
            if x.HasVal(): continue
            u = x.MaybeUnique()
            if u:
                uniques.append((x.pos,u))
        return uniques

    def UpdateClosedGroups(self):
        for se in self.sets:
            for e in se:
                e.UpdateClosedGroups()

    def AddGrp(self,grp):
        key=(grp.eset,grp.val)
        g=self.grp.get(key,None)
        if g: return g
        self.grp[key] = grp
        for x in grp.data:
            x.addgrp(grp)
        return grp

class Group(object):
    def __init__(self,owner,eset,val,lst):
        self.owner = owner
        self.eset = eset
        self.val = tuple(val)  # set of values in the group
        self.data = lst # list of items in the group
        self.applied = False
    def Apply(self,explain=False):
        if self.applied: return None
        self.applied = True
        val = set(self.val)
        if explain:
            modified=set([])
            for x in self.eset.data:
                if x not in self.data:
                    tmp=x.alt_size()
                    x.remove(val)
                    if tmp != x.alt_size():
                        modified.add(x)
            return modified
        else:
            for x in self.eset.data:
                if x not in self.data:
                    x.remove(val)
            return True
            
    def remove(self,e):
        self.data = self.data - set([e])
        self.applied=True
        if len(self.data) > 1:
           val = tuple(x.val for x in self.data)
           self.owner.AddGrp(Group(self.owner,self.eset,val,self.data))
        else:
           for x in self.data:
               x.remgrp(self)

class Crossing(object):
    def __init__(self,parent,cross,a,b):
        self.parent=parent
        self.data = set(cross)
        self.a_set = set(a.data) - set(cross)
        self.b_set = set(b.data) - set(cross)
        self.a_obj = a
        self.b_obj = b
    def check_crossing(self,cm,a_set,a_obj,b_set,b_obj,explain,solution):
        applied = False
        delta = cm - set.union(*[set(x.maybe) if x.maybe != None else set([]) for x in a_set])
        if len(delta):
            for x in b_set:
                if not x.maybe: continue
                l=len(x.maybe)
                x.maybe -= delta
                l-=len(x.maybe)
                if l:
                    applied = True
            if applied and explain:
                solution.append(('cross',delta,self,b_obj))
        return applied

class ElemSet(object):
    name = "eset"
    def __init__(self,puzzle,pos):
        self.parent = puzzle
        self.pos = pos
        self.data = None

    def UpdateClosedGroups(self):
        sz={}
        for x in self.data:
            if x.HasVal(): continue
            xm=x.alt_tuple()
            grp=sz.get(xm,None)
            if not grp:
                sz[xm]=set([x])
            else:
                grp.add(x)
        for grpval,eset in sz.items():
            if len(grpval) == len(eset):
                self.parent.AddGrp(Group(self.parent,self,grpval,eset))

    def UpdateClosedGroupsNew(self):
        sz={}
        mx=filter(lambda x:x.maybe != None and x.val == None,(x for x in self.data))
        lmx=len(mx)
        #this is the optimization which is only good to look for pairs
        for x in mx:
            key=x.alt_tuple()
            val=set([x])
            grp=sz.get(key,None)
            if not grp:
                sz[key]=val
            else:
                grp.update(val)
        if(lmx > 4):
            lmx2=lmx/2
            # now, the n-tuples search (but not pairs)
            for j in xrange(lmx-1):
                for i,x in enumerate(mx[j:lmx2+j]):
                    pfx=mx[j:i+j+1]
                    for y in mx[i+1:]:
                        m = pfx + [y]
                        # m is a current subset to test for possible subgroup
                        u=set([])
                        for e in m: u.update(e.maybe)
                        key=tuple(u)
                        if len(key) == lmx: continue # skip group of maximum size => not interesting
                        val=set(m)
                        grp=sz.get(key,None)
                        if not grp:
                            sz[key]=val
                        else:
                            grp.update(val)
        # check all the keys (possible value sets) to be same size as group of referenced places: this will give us closed group
        for grpval,eset in sz.items():
            if len(grpval) == len(eset):
                self.parent.AddGrp(Group(self.parent,self,grpval,eset))

    def Unique(self,x):
        if x.val == None: return True
        for e in self.data:
            if e == x: continue
            if x.val == e.val: return False
        return True

    def MaybeUnique(self,x):
        if x.maybe == None: return
        maybe=x.maybe
        for e in self.data:
            if e.pos == x.pos or e.HasVal(): continue
            maybe = maybe - set(e.maybe)
            if(len(maybe) == 0): return None
        if len(maybe) != 1:
            raise ValueError("maybe='%r'" % maybe)
        return tuple(maybe)[0]

class Square(ElemSet):
    name = "sq"
    def __init__(self,parent,pos):
        dim = parent.dim
        sq_dim = parent.sq_dim
        xpos = pos % dim
        ypos = pos / dim
        ElemSet.__init__(self,parent,(xpos,ypos))
        sq=[]
        for n in xrange(dim):
            base = (ypos * dim + n) * sq_dim + xpos * dim
            sq.extend(parent.data[base:base + dim])
        self.data=tuple(sq)
    def __repr__(self):
        return "Square %r: %s\n" % (self.pos, self.data)

class Row(ElemSet):
    name = "row"
    def __init__(self,parent,ypos):
        ElemSet.__init__(self,parent,(ypos,))
        self.data=tuple(parent.data[parent.sq_dim*ypos:parent.sq_dim*(ypos+1)])
    def __repr__(self):
        return "Row %d: %s\n" % (self.pos[0], self.data)

class Col(ElemSet):
    name = "col"
    def __init__(self,parent,xpos):
        ElemSet.__init__(self,parent,(xpos,))
        self.data=tuple(parent.data[xpos::parent.sq_dim])
    def __repr__(self):
        return "Col %d: %s\n" % (self.pos[0], self.data)

class Elem(object):
    def __init__(self,parent,pos,val=None,fixed=False):
        self.sync = False
        self.pos = pos
        self.parent = parent
        self.bound = False
        self.maybe=None
        self.neighbours=None
        self.all_affected=None
        self.bindings=set([])
        self.crossings=set([])
        self.reset(val,fixed)

    def alt_size(self):
        return len(self.maybe) if self.bound and self.val == None else 0

    def alt_tuple(self):
        return tuple(self.maybe) if self.bound else ()

    def Bind(self,eset):
        self.bindings.add(eset)
        self.bound = False

    def BindCrossing(self,cr):
        self.crossings.add(cr)
        self.bound = False

    def BindComplete(self):
        self.all_affected = set([])
        for e in self.bindings:
            self.all_affected = set.union(self.all_affected,set(e.data))
        self.neighbours = self.all_affected - set([self])
        self.bound = True
        self.update()

    def Unique(self):
        if not self.bound: return
        for e in self.bindings: # for all containers (row,col,sq, ... )
            if not e.Unique(self): return False
        return True
        
    def MaybeUnique(self):
        if not self.bound: return
        for e in self.bindings: # for all containers (row,col,sq, ... )
            u=e.MaybeUnique(self)
            if u: return (e,u)
        return None

    def setval(self,val,fixed=False):
        if not self.bound: return
        if self.val == val:
            self.fixed = fixed
            return

        if self.HasVal():
            self.val = None
            self.fixed = False
            if self.sync: self.update_set(self.all_affected)

        if val != None:
            self.val = val
            self.fixed = fixed
            self.maybe = None
            if self.sync: self.remove_set(val,self.neighbours)

        if self.sync: self.ClearGroups()

    def ClearGroups(self):
        if self.grp != None:
            for g in self.grp:
                self.remgrp(g)
        self.grp=None

    def SetSync(self,sync):
        self.sync = sync
        self.ClearGroups()

    def update_set(self,eset):
        if not self.bound: return
        for e in eset:
            e.update()

    def remove_set(self,val,eset):
        if not self.bound: return
        for e in eset:
            e.remove(val)

    def reset(self,val=None,fixed=False):
        self.val=val
        self.fixed=fixed
        self.failed=set([])
        self.grp=None
        self.maybe=self.parent.set_all

    def addgrp(self,grp):
        if self.grp == None:
            self.grp = set([grp])
        else:
            self.grp.add(grp)

    def remgrp(self,grp):
        self.grp = self.grp - set([grp])
        grp.remove(self)

    def remove(self,val):
        if not self.bound: return
        if self.HasVal():
            self.maybe = None
        else:
            v = val if type (val) in [list,set,tuple] else [val]
            self.maybe = self.maybe - set(v)
            if not len(self.maybe) and self.parent.check:
                raise ValueError("no more choices. situation is unsolvable: %s" % self)

    def update(self):
        if not self.bound: return
        if self.val == None:
            self.maybe = self.parent.set_all - set(e.val for e in self.all_affected)
            if not len(self.maybe) and self.parent.check:
                raise ValueError("no more choices. situation is unsolvable: %s" % self)
        else:
            self.maybe = None

    def HasVal(self):
        return self.val != None

    def IsValid(self):
        return reduce(lambda x,y:x and y, tuple(e._IsValid() for e in self.all_affected),True)

    def _IsValid(self): return (self.val != None and self.Unique()) or (self.maybe != None and len(self.maybe) > 0)

    def __repr__(self):
        return "[%d: %s]" % (self.pos, self.val if self.HasVal() else (list(self.maybe) if self.maybe != None else None))
