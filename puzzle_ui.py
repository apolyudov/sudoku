#!/usr/bin/python
from sudoku import Sudoku
import wx
from puzzle import PrintSolution

class SudokuDocument(Sudoku):
    def __init__(self, dim=3):
        self._notifiers = set([])
        self._doc = Sudoku(dim=dim)

    def ImportHex(self, text):
        try:
            val = int(text,16) % 100
        except:
            return False
        if not self.setDim(val):
            return False
        self._doc.ImportHex(text)
        return True

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

    def _update(self, doc):
        self._doc = doc
        for t in self._notifiers:
            notifier = t[0]
            notifier()

    @property
    def doc(self):
        return self._doc

class SudokuEditItem(wx.TextCtrl):
    [E_OK,E_IMPOSSIBLE,E_NO_SOLUTION] = xrange(3)
    def __init__(self, parent, data, pos, size):

        self.data = data
        self.pos = pos
        self.size = size

        wx.TextCtrl.__init__(
        self,
        parent = parent,
        pos = pos,
        size = size,
        style = 0,
        value = '')

        self.SetMaxLength(1)
        font = self.GetFont()
        font.SetPointSize(int(size.height*9/16))
        self.SetFont(font)
        self.Bind(wx.EVT_TEXT, self.on_text)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_mouse_dbl_left)
        self.fixed = False
        self.error = self.E_OK

    def clear(self, force=False):
        if not self.fixed or force:
            self.data.setval(None)
            self.fixed = False
            self.error = self.E_OK

    def update(self, fixed = None):
        if fixed == None:
            fixed = self.fixed
        if fixed == True and self.data.HasVal():
            self.Enable(False)
            self.fixed = True
        else:
            self.Enable(True)
            if fixed != None:
                self.fixed = False

        if self.data.HasVal():
            self.SetValue(self.data.val)
            self.SetToolTipString('')
        else:
            self.SetValue('')
            maybe = list(self.data.maybe)
            maybe.sort()
            tip = ','.join(str(x) for x in maybe)
            self.SetToolTipString(tip)

        if not self.fixed:
            if self.error == self.E_IMPOSSIBLE:
                self.BackgroundColour = (255,0,0,0)
            elif self.error == self.E_NO_SOLUTION:
                self.BackgroundColour = (255,255,0,0)
            else:
                self.BackgroundColour = (255,255,255,255)
        self.Refresh()

    def on_mouse_dbl_left(self, event):
        self.update(not self.fixed)
        event.Skip()

    def on_text(self, event):
        new_val = self.GetValue()
        if len(new_val) == 0:
            new_val = None
        old_val = self.data.val
        if old_val == new_val:
            return
        try:
            self.data.setval(new_val)
            self.error = self.E_OK if self.data.IsValid() else self.E_IMPOSSIBLE
        except ValueError, err:
            msg = 'Can\'t set the value: %s: %s' % (new_val, err)
            # rules do not prohibit this value for this cell,
            # but some other cell(s) will become invalid
            if new_val != '?':
                self.error = self.E_NO_SOLUTION
                self.SetToolTipString(msg)
            else:
                self.error = self.E_OK
                self.SetToolTipString(str(self.data))
        finally:
            result = self.data.val
            if result != new_val:
                if result != None:
                    self.ChangeValue(result)
                else:
                    self.ChangeValue('')
        self.update()
        self.Parent.on_item_text(self, event)

class SudokuEditPanel(wx.Panel):
    def __init__(self, parent, pos, sudoku_doc, cell_size):
        self.sudoku = sudoku_doc
        self.parent = parent
        self.cell_size = cell_size
        wx.Panel.__init__(self, parent = parent, pos = pos)
        self.setup()

    def destroy(self):
        for e in self.lines:
            e.Destroy()
        for e in self.grid:
            e.Destroy()

    def setup(self):
        self.grid = []
        self.lines = []
        doc = self.sudoku.doc
        n_lines = doc.dim-1

        offset = wx.Point(self.cell_size.x, self.cell_size.y)
        size = self.cell_size
        width = int(offset.x/10)
        extra_width = int(offset.x/10)
        self.do_lines = True

        length = wx.Point(doc.sq_dim*size.x+n_lines*(width+extra_width),
                          doc.sq_dim*size.y+n_lines*(width+extra_width))

        self.SetClientRect(wx.Rect(0,0,length.x + offset.x*2, length.y + offset.y*2))            
        style = wx.NO_BORDER
        if self.do_lines:
            for i in xrange(1,doc.dim):
                line = wx.StaticLine(
                  parent=self, pos=wx.Point(offset.x + i*doc.dim*size.x+(i-1)*(width+extra_width) + extra_width/2, offset.y),
                  size=wx.Size(width, length.y),
                  style=style)
                self.lines.append(line)

                line = wx.StaticLine(
                      parent=self, pos=wx.Point(offset.x, offset.y + i*doc.dim*size.y+(i-1)*(width+extra_width) + extra_width/2),
                      size=wx.Size(length.x, width),
                      style=style)
                self.lines.append(line)

        for e in doc.data:
            x = e.pos % doc.sq_dim
            y = (e.pos - x) / doc.sq_dim
            elem_pos = wx.Point(size.x*x + int(x/doc.dim)*(width+extra_width),
                                size.y*y + int(y/doc.dim)*(width+extra_width))
            item = SudokuEditItem(self, e, offset + elem_pos, size)
            self.grid.append(item)

        self.Bind(wx.EVT_LEFT_DCLICK, self.on_mouse_dbl_left)

    def update_doc(self):
        self.destroy()
        self.setup()

    def Import(self, text):
        dim,locked,unlocked=text.split(';')
        if not self.sudoku.setDim(int(dim)):
            self.clear(True)
        for x in locked.split(','):
            idx,val = x.split(':')
            item = self.grid[int(idx)]
            item.SetValue(val)
        self.update(fixed=True)
        for x in unlocked.split(','):
            idx,val = x.split(':')
            item = self.grid[int(idx)]
            item.SetValue(val)
        self.update()
    def Export(self):
        return '%d;%s;%s' % (
            self.sudoku.doc.dim,
            ','.join('%d:%s' % (x.data.pos, x.data.val) for x in filter(lambda g: g.fixed, self.grid)),
            ','.join('%d:%s' % (x.data.pos, x.data.val) for x in filter(lambda g: not g.fixed and g.data.HasVal(), self.grid))
        )

    def on_mouse_dbl_left(self, event):
        print 'panel_dblclick', event.x, event.y
        event.Skip()

    def mark_invalid(self, lst):
        for item in self.grid:
            item.error = item.E_OK
        for e in lst:
            item = self.grid[e.pos]
            if not item.fixed:
                item.error = item.E_IMPOSSIBLE
        self.update()

    def clear(self, force=None):
        for e in self.grid:
            e.clear(force)

    def update(self, fixed = None):
        for e in self.grid:
            e.update(fixed)

    def on_item_text(self, child, event):
        self.Parent.update()


class ButtonPanel(wx.Panel):
    def __init__(self, parent, pos, size):
        wx.Panel.__init__(self, parent=parent, pos = pos, size=size)
        self.buttons=[]
    def add_button(self, label, evt_func):
        idx = len(self.buttons)
        btn = wx.Button(self, label=label, pos=wx.Point(0,40+idx*30))
        btn.Bind(wx.EVT_BUTTON, evt_func)
        self.buttons.append(btn)
        return btn

class MainFrame(wx.Frame):
    def __init__(self, doc):
        wx.Frame.__init__(
            self,
            parent=None,
            style=wx.DEFAULT_FRAME_STYLE,
            title='Sudoku')

        self.ID = self.GetId()
        self.sudoku = doc
        self.sudoku.open(self.update_doc)
        self.file_name = 'sudoku_game.txt'

        self.sudoku_edit = SudokuEditPanel(self, pos = wx.Point(0,0),
                                           sudoku_doc = self.sudoku,
                                           cell_size = wx.Size(40,40))
        sz = self.sudoku_edit.GetSize()
        self.buttons = ButtonPanel(self, pos = wx.Point(sz.x, 0), size=wx.Size(100,sz.y))

        self.btnLock = self.buttons.add_button('', self.on_btn_lock_unlock)
        self.buttons.add_button('Clear', self.on_btn_clear)
        self.buttons.add_button('Generate', self.on_btn_generate)
        self.buttons.add_button('Solve', self.on_btn_solve)
        self.buttons.add_button('Validate', self.on_btn_validate)
        self.buttons.add_button('Load', self.on_btn_load)
        self.buttons.add_button('Save', self.on_btn_save)

        self.export = wx.TextCtrl(parent=self, pos=wx.Point(0,sz.y),size=wx.Size(sz.x+100,100))
        self.export.Bind(wx.EVT_TEXT, self.on_text_export)
        self.SetClientSize(wx.Size(sz.x+100,sz.y+100))
        self.SetLockedState(False)

        self.load_game(self.file_name)

    def on_btn_load(self, event):
        self.load_game(self.file_name)

    def on_btn_save(self, evt):
        self.save_game(self.file_name)

    def load_game(self, name):
        try:
            f= open(name,'r')
            self.sudoku_edit.Import(f.read())
            f.close()
        except Exception, e:
            print e
            self.sudoku_edit.clear()
            return False

        return True

    def save_game(self, name):
        try:
            f= open(name,'w')
            f.write(self.sudoku_edit.Export())
            f.close()
        except Exception, e:
            print e
            raise
            return False

        return True

    def SetLockedState(self, locked):
        self.locked = locked
        if self.locked:
            self.btnLock.SetLabel('Unlock')
        else:
            self.btnLock.SetLabel('Lock')
        self.update(self.locked)

    def on_text_export(self, evt):
        self.sudoku.ImportHex(self.export.GetValue())
        self.SetLockedState(True)
        self.update()

    def on_btn_validate(self, evt):
        invalid_list = self.sudoku.doc.Validate()
        self.sudoku_edit.mark_invalid(invalid_list)
        self.update()

    def on_btn_lock_unlock(self, evt):
        self.SetLockedState(not self.locked)
        self.update()

    def on_btn_clear(self, evt):
        self.sudoku_edit.clear()
        self.update()

    def on_btn_solve(self, evt):
        print 'Solving'
        res, solution = self.sudoku.doc.Solve(explain=True)
        self.update()
        PrintSolution(solution)
        print res

    def on_btn_generate(self, evt):
        print 'Generating'
        doc = self.sudoku.doc
        seed = doc.Export() if not self.locked else None
        doc.GenHard(init=True, seed=seed, full=True)
        self.SetLockedState(True)
        self.update()
        print doc.Export()

    def update(self, fixed=None):
        self.sudoku_edit.update(fixed)
        self.export.ChangeValue(self.sudoku.doc.ExportHex())

    def save(self):
        pass

    def update_doc(self):
        self.Freeze()
        self.sudoku_edit.update_doc()
        size = self.sudoku_edit.GetSize()
        self.export.SetPosition((0,size.y))
        self.buttons.SetPosition((size.x,0))
        btn_size = self.buttons.GetSize()
        exp_size = self.export.GetSize()
        self.buttons.SetSize((btn_size.x,size.y))
        self.export.SetSize((size.x+btn_size.x,exp_size.y))
        self.SetClientSize((size.x+btn_size.x,size.y+exp_size.y))
        self.Thaw()
        print 'update doc in frame'

def main_GUI(argv):
    app = wx.App(redirect=True)
    doc = SudokuDocument()
    frame = MainFrame(doc)
    frame.update()
    frame.Show(True)
    app.MainLoop()
    return 0

