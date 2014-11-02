#!/usr/bin/python
class Sudoku(object):
    def __init__(self, dim=3,alfa=None,seed=None):
        self.dim=d=int(dim)
        if d < 2 or d > 99 or int(dim) != dim: raise ValueError("dimension must be positive integer [2..99], but %r is given" % dim)
        self.sq_dim = sq_dim = d * d
        self.total = sq_dim * sq_dim
        self.grp={} # closed group lookup table
        self.defval='.'
        self.all_alfa = {
        2: '1234',
        3: '123456789',
        4: '0123456789ABCDEF',
        5: 'ABCDEFGHIJKLMNOPQRSTUVWXY',
        6: '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        }
        if alfa:
            alfa = tuple(alfa)
            self.all_alfa[dim] = alfa[1:]
            self.defval = alfa[0]
        self.alfabet = self.all_alfa[dim]
        self.sep=''
        if not self.alfabet:
            raise ValueError('custom alphabet (iterable) for dim=%d with size %d must be defined' % (d, sq_dim))
        self.set_all = set(self.alfabet)
        if not len(self.set_all) == self.sq_dim:
            raise ValueError('custom alphabet size for dim=%d must have size %d, but %d is given' % (d, sq_dim, len(self.set_all)))
        self.data = tuple(Elem(self,i) for i in xrange(self.total))
        self.InitRand()
        self.check = False
        self.Setup()
        self.SetSync(True)
        self.Populate(seed)
        self.check = True

    def PrintSolution(self, solution, stream):
        sq_dim = self.sq_dim
        def pos(x): return "y:%2d,x:%2d" % (x/sq_dim+1,x%sq_dim+1)
        def eset_pos(x):
            if len(x) == 1:
                return "# %2d" % (int(x[0])+1)
            else:
                return "# <x:%d, y:%d>" % (x[0]+1,x[1]+1)
        def eset(obj): return '%s%s' % (obj.name,eset_pos(obj.pos))
        def esets(objs): return '{%s}' % ', '.join(eset(obj) for obj in objs)
        def vals(x): return "[%s]" % ", ".join(v for v in x)
        def cell(c): return "C#[%s]" % pos(c.pos)
        def cells(cl): return "{%s}" % ", ".join(cell(c) for c in cl)
        def diff_cell(dc): return "%s:%s" % (cell(dc[0]),dc[1])
        def diff_cells(dcl): return '{%s}' % ', '.join(diff_cell(dc) for dc in dcl)
        for step in solution:
            mode=step[0]
            if mode == "group":
                print >>stream, "Group: %s @ %s; reduction: %s in %s" % (
                    vals(step[1]), cells(step[2]), cells(step[3]), eset(step[4])
                    )
            elif mode == "cross":
                cr=step[1]
                delta=step[2]
                apply_list=step[3]
                print >>stream, "cross of",eset(cr.a_obj),"and",eset(cr.b_obj),"must have",delta,"=> reducing in cells",diff_cells(apply_list)
            elif mode == "tuple1":
                item = step[1]
                val = step[2]
                print >>stream, "%s: '%s' ; last on crossing of %s" % (cell(item), val, esets(item.bindings))
            else:
                item =step[0]
                val = step[1]
                e = step[2]
                print >>stream, "%s: '%s' ; last in %s" % (cell(item), val, eset(e))

    def Export(self):
        return self.sep.join(str(x.val) if x.val != None else self.defval for x in self.data)

    def ExportHex(self):
        order = self.sq_dim+1
        res = 0
        for e in self.data:
            idx = self.alfabet.find(e.val) + 1 if e.HasVal() else 0
            res *= order
            res += idx
        return '%X' % res

    def ImportHex(self, s):
        res = int(s, 16)
        seed = bytearray(self.total)
        order = self.sw_dim + 1

        for i in xrange(self.total):
            idx = res % order
            seed[i] = (self.alfabet[idx-1] if idx > 0 else self.defval)
            res -= idx
            res /= order
        self.Populate(str(seed))

    def InitRand(self):
        from random import Random
        self.rand=Random()

    def Setup(self):
        self.squares = tuple(Square(self,n) for n in xrange(self.sq_dim))
        self.rows = tuple(Row(self,n) for n in xrange(self.sq_dim))
        self.cols = tuple(Col(self,n) for n in xrange(self.sq_dim))

        self.all_esets = (self.squares, self.rows, self.cols)

        plain_sets = []
        for esets in self.all_esets:
            plain_sets.extend(esets)
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

    def Validate(self):
        invalid_list = []
        for e in self.data:
            if not e.IsValid():
                invalid_list.append(e)
        return invalid_list

    def Hint(self,n=None):
        if n == None: n = 1
        sav=self.Export()
        path=[]
        _ =self.Solve(path, n)
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
            if dbg:
                print "Puzzle is not valid"
            return False
        try:
            self.check = False
            self.SetSync(False)
            res = True
            i=0
            for x in self.data: x.fixed = x.HasVal()
            while i < self.total:
                x = self.data[i]
                if dbg:
                    print "load: x[%d]=%s; maybe=%s; failed=%s; fixed=%s" % (x.pos,x.val,x.maybe,x.failed,x.fixed)
                if x.fixed:
                    i=i+1
                    continue
                x.update()
                t=tuple(x.maybe-x.failed)
                if len(t) == 0:
                    x.failed=set([])
                    if i == 0:
                        if dbg:
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
                    if dbg:
                        print "assign: x[%d]=%s; maybe=%s; failed=%s; fixed=%s" % (x.pos,x.val,x.maybe,x.failed,x.fixed)
                    i=i+1
                        
        except AttributeError, e:
            print "Error in Elem:", x.pos
            raise
        except ValueError, e:
            print e
            raise
            res = False
        finally:
            self.SetSync(True)
            self.check=True
        return res

    # Generating with a "SolveHard",
    # reducing randomly,
    # verifying with "Solve"
    def GenHard(self,init=True,seed=None, full=False):
        def can_remove(pos):
            gen=self.Export()
            new_gen = gen
            res = False
            # all path manipulations are for debugging only
            good_path=[]
            try:
                self.data[pos].setval(None)
                new_gen = self.Export()
                self.Populate()
                self.Populate(new_gen)
                path=[]
                res= self.Solve(path)
                if res:
                    good_path=path
            except Exception, e:
                print 'exception while solving:', e
                print pos
                raise
                res = False
            finally:
                self.Populate()
                self.Populate(gen)
            return res, good_path

        def reduce_random():
            cnt=0
            good_path = []
            while(True):
                pos = self.rand.randint(0,self.total-1)
                if not self.data[pos].HasVal(): continue
                res, path = can_remove(pos)
                if res:
                    self.data[pos].setval(None)
                    cnt+=1
                    good_path = path
                else:
                    return cnt, good_path

        if init:
            self.Populate(seed)
            if not seed or full:
                self.SolveHard()

        stable=0
        good_path = []
        while(True):
            res, path = reduce_random()
            if not res:
                stable += 1
            else:
                stable=0
                good_path = path
            if stable == self.sq_dim: break
        Done=False
        while(not Done):
            for x in self.data:
                if not x.HasVal(): continue
                res, path = can_remove(x.pos)
                if res:
                    x.setval(None)
                    good_path = path
                    break
            else:
                Done=True
        return self.Export().count(self.defval), good_path

    def SolveSimple(self,solution):
        res = False
        for pos,(e,val) in self.FindUniques():
            item=self.data[pos]
            item.setval(val)
            if solution != None:
                solution.append((item,val,e))
            res = True
        for pos,val in self.FindTuples(1):
            item=self.data[pos]
            item.setval(val[0])
            if solution != None:
                solution.append(('tuple1',item,val[0]))
            res = True
        return res

    def SolveGroups(self,solution):
        res = False
        self.UpdateClosedGroups()
        for g in self.grp.values():
            modified=g.Apply()
            if modified:
                res = True
                if solution != None:
                    step = ('group',
                            tuple(g.val), # values in the group
                            tuple(g.data),  # cells of the group
                            tuple(modified),# modified cell list
                            g.eset) # eset to which the group belongs
                    solution.append(step)
        return res

    def Groups(self):
        self.UpdateClosedGroups()
        return self.grp

    def SolveCrossings(self, solution):
        res = False
        for cr in self.crossings:
            cm = set.union(*[set(x.maybe) if x.maybe != None else set([]) for x in cr.data])
            if cr.check_crossing(cm,cr.a_set,cr.a_obj,cr.b_set,cr.b_obj, solution): res = True
            if cr.check_crossing(cm,cr.b_set,cr.b_obj,cr.a_set,cr.a_obj, solution): res = True

        return res

    def Solve(self, solution=None, steps=None):
        self.check=True
        if not self.sync:
            self.SetSync(True)
        complete = True
        if steps != None:
            complete = False
        res = True
        while res:
            if(steps != None and solution != None and len(solution) >= steps):
                solution = solution[0:steps]
                res = True
                break
            res = self.SolveSimple(solution)
            if res: continue
            res = self.SolveCrossings(solution)
            if res: continue
            res = self.SolveGroups(solution)

        if complete:
            todo = filter(lambda x: not x.HasVal(), self.data)
            if len(todo):
                res = False
            else:
                res = True

        return res

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
        self.grp={}
        for esets in self.all_esets:
            for eset in esets:
                eset.UpdateClosedGroups()

    def AddGrp(self,grp):
        key=(grp.eset,grp.val)
        g=self.grp.get(key,None)
        if g: return g
        self.grp[key] = grp
        for x in grp.data:
            x.addgrp(grp)
        return grp

class Move(object):
    def __init__(self, pos, val, explain):
        pass

class Group(object):
    def __init__(self,owner,eset,val,lst):
        self.owner = owner
        self.eset = eset
        self.val = tuple(val)  # set of values in the group
        self.data = lst # list of items in the group
        self.applied = False
    def Apply(self):
        if self.applied: return None
        self.applied = True
        val = set(self.val)
        modified=set([])
        for x in self.eset.data:
            if x not in self.data:
                tmp=x.alt_size()
                x.remove(val)
                if tmp != x.alt_size():
                    modified.add(x)
        return modified
            
    def remove(self,e):
        self.data = self.data - set([e])
        self.applied=True
        if len(self.data) > 1:
            val = tuple(x.val for x in self.data)
            self.owner.AddGrp(Group(self.owner,self.eset,val,self.data))
        else:
            for x in self.data:
                x.remgrp(self)
                
    def __repr__(self):
        return '{Group: %s; cells: %s in %s}' % (self.val, self.data, self.eset.Name())

class Crossing(object):
    def __init__(self,parent,cross,a,b):
        self.parent=parent
        self.data = set(cross)
        self.a_set = set(a.data) - set(cross)
        self.b_set = set(b.data) - set(cross)
        self.a_obj = a
        self.b_obj = b
    def check_crossing(self,cm, a_set, a_obj, b_set, b_obj, solution):
        applied = []
        delta = cm - set.union(*[set(x.maybe) if x.maybe != None else set([]) for x in a_set])
        if len(delta):
            for x in b_set:
                if not x.maybe: continue
                old = x.maybe
                l = len(old)
                new = x.maybe - delta
                l -= len(new)
                if l:
                    x.maybe = new
                    diff = old - new
                    applied.append((x, diff))
            if len(applied) > 0 and solution != None:
                solution.append(('cross', self, delta, applied))
        return len(applied) > 0
    def __repr__(self):
        return 'Crossing: [%s]' % (self.data,)

class ElemSet(object):
    name = "eset"
    def __init__(self,puzzle,pos):
        self.parent = puzzle
        self.pos = pos
        self.data = None
        
    def Name(self):
        return '%s[%s]' % (self.name, ",".join(str(int(x)+1) for x in self.pos))

    def __repr__(self):
        return '%s: {%s}' % (self.Name(), self.data)

    def _make_maybe_set(self):
        return set(filter(lambda x:x.maybe != None and x.val == None,(x for x in self.data)))

    def _add_elem_to_grp(self, grps, key, val):
        grp = grps.get(key, None)
        if grp == None:
            grp = set([])
            grps[key] = val
            changed = True
        elif not val.issubset(grp):
            grp.update(val)
            changed = True
        else:
            changed = False
        
        return changed

    # find all the cells in the set with exactly
    # same maybe list
    def _find_exact_groups(self, maybe_set):
        grps = {}
        # build the set of cells with the same maybe set
        for x in maybe_set:
            self._add_elem_to_grp(grps, frozenset(x.alt_tuple()), set([x]))
        return grps

    def _add_groups(self, grps, maybe_set):
        added=[]
        for grpval, eset in grps.items():
            if len(eset) == 1 or len(eset) == len(maybe_set):
                # groups containing 1 element or all elements
                # are trivial (do not bring new info for analysis)
                continue
            if len(grpval) == len(eset):
                # add group to parent set
                self.parent.AddGrp(Group(self.parent,self,grpval,eset))
                # remove group members from maybe_set
                added.append(eset)
        return added

    # if size of group matches size of maybe list for the group,
    # this is a closed group  
    def UpdateClosedGroups(self):
        self.UpdateClosedGroupsOverlap()

    # this is simplified implementation:
    # requires that all N cells in group have exactly
    #  the same N-tuple of maybe elements 
    def UpdateClosedGroupsExact(self):
        maybe_set = self._make_maybe_set()
        grps = self._find_exact_groups(maybe_set)
        return grps, maybe_set, self._add_groups(grps, maybe_set)
        
    # this is generic implementation:
    # looks for any N-cell combination,
    # that has overlapped maybe of size N 
    def UpdateClosedGroupsOverlap(self):
        # 1-st stage: looking for exact matches of 'maybe' sets
        grps, maybe_set, added = self.UpdateClosedGroupsExact()
        found = len(added)
        for eset in added:
            for e in eset:
                maybe_set.discard(e)
        if found > 0:
            # rebuild groups from remaining cells only
            grps = self._find_exact_groups(maybe_set)
        # 2-nd stage: looking for matches of combinations of 'maybe' sets
        if len(grps) > 3:
            # with len == 3 group can only be pair
            # pairs are guaranteed to be discovered by
            # first stage
            while True:
                changed = False
                for eset_maybe, eset in grps.items():
                    # eset is set of cells that forms this combined eset_maybe set
                    for e in maybe_set - eset:
                        key_set = set(eset_maybe)
                        key_set.update(set(e.alt_tuple()))
                        val_set = set([])
                        val_set.update(eset)
                        val_set.add(e)
                        if self._add_elem_to_grp(grps, frozenset(key_set), val_set):
                            changed=True
                if not changed: break
            found = len(self._add_groups(grps, maybe_set))

        return found

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

class Row(ElemSet):
    name = "row"
    def __init__(self,parent,ypos):
        ElemSet.__init__(self,parent,(ypos,))
        self.data=tuple(parent.data[parent.sq_dim*ypos:parent.sq_dim*(ypos+1)])

class Col(ElemSet):
    name = "col"
    def __init__(self,parent,xpos):
        ElemSet.__init__(self,parent,(xpos,))
        self.data=tuple(parent.data[xpos::parent.sq_dim])

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
            if self.parent.check and val not in self.parent.alfabet:
                raise ValueError('Incorrect input: %s' % val)
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
        self.maybe=set([])
        self.maybe.update(self.parent.set_all)

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
        return self.val != None and self.val != self.parent.defval

#    def IsValid(self):
#        return reduce(lambda x,y:x and y, tuple(e._IsValid() for e in self.all_affected),True)

    def IsValid(self): return (self.val != None and self.Unique()) or (self.maybe != None and len(self.maybe) > 0)

    def __repr__(self):
        return "[%d: %s]" % (self.pos, self.val if self.HasVal() else (list(self.maybe) if self.maybe != None else None))
