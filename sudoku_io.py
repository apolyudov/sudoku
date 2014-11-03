#!/usr/bin/python

from sudoku import Sudoku

class SudokuDocument(object):
    def __init__(self, dim=3):
        self._notifiers = set([])
        self._doc = Sudoku(dim=dim)

    def ImportHex(self, text):
        try:
            val = int(text[-2:])
        except:
            return False
        if not self.setDim(val):
            return False
        self._doc.ImportHex(text[0:-2])
        return True

    def ExportHex(self):
        return '%s%02d' % (self._doc.ExportHex(), self._doc.dim)

    def open(self, change_notifier):
        t = (change_notifier, )
        self._notifiers.add(t)
        return t

    def close(self, t):
        self._notifiers.remove(t)

    def setDim(self, dim):
        if dim != self._doc.dim:
            self._update(Sudoku(dim=dim))
            return True
        return False

    def setval(self, idx, val, fixed=None):
        self._doc.data[idx].setval(val)

    def clear(self, force=None):
        for x in self._doc.data:
            if not x.fixed or force:
                x.setval(None);

    def _update(self, doc):
        self._doc = doc
        for t in self._notifiers:
            notifier = t[0]
            notifier()

    @property
    def doc(self):
        return self._doc

def stream_file_io(fname, open_mode, stream_func, *args):
    try:
        f = None
        f = open(fname, open_mode)
        results = stream_func(f, *args)
    except IOError, e:
        results = (False, 'IOError [%s]: %s' % (fname, e))
    finally:
        if f != None:
            f.close()
            f = None

    return results

# dim - is passed verbatim from client; not interpreted
# lines - is the number of lines in target file
# seed - string of arbitrary data, length must be divisible by lines
# fname - is output file name
def raw_write_stream(s_output, dim, lines, seed):
    total = len(seed)
    line_size = int(total / lines)

    if (line_size * lines) != total:
        raise ValueError('incorrect arguments to raw stream writer; lines=%d; total=%d' % (lines, total))

    print >> s_output, '# sudoku: file=%s; dim=%d; lines=%d; total=%d' % (s_output.name, dim, lines, total)
    print >> s_output, '%d,%d,%d' % (dim, lines, total)
    for i in xrange(lines):
        seg = seed[line_size*i:line_size*(i+1)]
        print >> s_output, seg

    return (True,)

# fname is input file name, created by raw_write
def raw_read_stream(s_input):
    dim = 0
    lines = 0
    total = 0
    seg_size = 0
    segs=[]
    for line in s_input:
        l = line.strip()
        if len(l) == 0 or l[0] == '#': continue
        if total == 0:
            dim, lines, total = (int(x) for x in l.split(','))
            seg_size = int(total / lines)
            continue
        segs.append(line.strip())
    seed = ''.join(seg for seg in segs)
    if total != len(seed) or lines != len(segs) or not reduce(lambda prev,seg: len(seg) == seg_size and prev, segs, True):
            raise ValueError('format mismatch in data structure')

    return (True, dim, lines, seed)

def doc_write_stream(s_output, doc):

    unknown_doc = doc
    doc = None
    
    if type(unknown_doc) == SudokuDocument:
        doc = unknown_doc.doc
    elif type(unknown_doc) == Sudoku:
        doc = unknown_doc
    else:
        raise TypeError(unknown_doc)

    s = '%d;%s;%s\n' % (
        doc.dim,
        ','.join('%d:%s' % (x.pos, x.val) for x in filter(lambda g: g.fixed, doc.data)),
        ','.join('%d:%s' % (x.pos, x.val) for x in filter(lambda g: not g.fixed and g.HasVal(), doc.data))
    )
    s_output.write(s)

    return (True,)

def doc_read_stream(stream, doc):
    unknown_doc = doc
    sudoku_doc = None
    doc = None

    if type(unknown_doc) == SudokuDocument:
        sudoku_doc = unknown_doc
        doc = sudoku_doc.doc
    elif type(unknown_doc) == Sudoku:
        doc = unknown_doc
    else:
        raise TypeError(unknown_doc)

    text = stream.readline()
    dim,locked,unlocked=text.split(';')
    dim = int(dim)
    
    if dim != doc.dim:
        if  sudoku_doc == None:
            raise ValueError('Sudoku object does not support dynamic change of dimension: doc.dim=%d; dim=%d' % (doc.dim, dim))
        else:
            sudoku_doc.setDim(dim)
            doc = sudoku_doc.doc
    else:
        doc.Populate()

    for x in locked.split(','):
        a = x.split(':')
        if len(a) < 2: continue
        idx,val = a
        idx = int(idx)
        doc.data[idx].setval(val, True)
    for x in unlocked.split(','):
        a= x.split(':')
        if len(a) < 2: continue
        idx,val = a
        idx = int(idx)
        doc.data[idx].setval(val)

    return (True,)
