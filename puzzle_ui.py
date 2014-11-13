#!/usr/bin/python
from sudoku_io import SudokuDocument, doc_read_stream, doc_write_stream, stream_file_io
import wx, sys

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
        self.tip = None

    def clear(self, force=False):
        if not self.fixed or force:
            self.data.setval(None)
            self.fixed = False
            self.error = self.E_OK

    def update(self):
        # propagates changes from document to view
        fixed = self.data.fixed
        self.Enable(not fixed)
        self.fixed = fixed

        if self.data.HasVal():
            self.ChangeValue(self.data.val)
            self.tip = None
        elif self.error == self.E_OK:
            self.ChangeValue('')
            maybe = list(self.data.maybe)
            maybe.sort()
            self.tip = ','.join(str(x) for x in maybe)

        if not self.fixed:
            if self.error == self.E_IMPOSSIBLE:
                self.BackgroundColour = (255,0,0,0)
                self.tip = 'Duplicate value'
            elif self.error == self.E_NO_SOLUTION:
                self.BackgroundColour = (255,255,0,0)
            else:
                self.BackgroundColour = (255,255,255,255)

        if self.tip != None:
            self.SetToolTipString(self.tip)
        else:
            self.SetToolTip(None)
        self.Refresh()

    def load(self, val):
        self.data.setval(val)
        if (self.data.HasVal()):
            self.ChangeValue(self.data.val)
        else:
            self.ChangeValue('')

    def on_mouse_dbl_left(self, event):
        if not self.data.fixed:
            if self.data.HasVal():
                self.data.fixed = True
        else:
            self.data.fixed = False
        self.update()

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
            self.error = self.E_NO_SOLUTION
            self.tip = msg
            self.SetToolTipString(msg)
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

        k = { 5:1, 4: 1.25, 3:1.5, 2:2 }

        size = wx.Size(int(self.cell_size.x*k[doc.dim]), int(self.cell_size.y*k[doc.dim]))
        offset = wx.Point(size.x, size.y)
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

    def on_mouse_dbl_left(self, event):
        x,y = event.GetPositionTuple()
        print 'mouse event',x,y
        for g in self.grid:
            rect = wx.Rect()
            rect.SetPosition(g.GetPosition())
            rect.SetSize(g.GetSize())
            if rect.ContainsXY(x,y):
                if g.data.fixed:
                    g.data.fixed = False
                else:
                    if g.data.HasVal():
                        g.data.fixed = True
                g.update()

    def mark_invalid(self, lst):
        for item in self.grid:
            item.error = item.E_OK
        for e in lst:
            item = self.grid[e.pos]
            if not item.fixed:
                item.error = item.E_IMPOSSIBLE
        self.update()

    def clear(self, force=None):
        self.sudoku.clear(force)

    def update(self):
        for e in self.grid:
            e.update()

    def on_item_text(self, child, event):
        self.Parent.update()

class ButtonPanel(wx.Panel):
    def __init__(self, parent, pos, size, offset):
        wx.Panel.__init__(self, parent=parent, pos = pos, size=size)
        self.buttons=[]
        self.offset = offset
    def add_button(self, label, evt_func):
        idx = len(self.buttons)
        btn = wx.Button(self, label=label, pos=wx.Point(0, self.offset + idx*30))
        btn.Bind(wx.EVT_BUTTON, evt_func)
        self.buttons.append(btn)
        return btn

class MainFrame(wx.Frame):
    def __init__(self, doc):
        wx.Frame.__init__(
            self,
            parent=None,
            style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX,
            title='Sudoku')

        self.ID = self.GetId()
        self.sudoku = doc
        self.sudoku.open(self.update_doc)
        self.file_name = 'sudoku_game_%d.txt'

        self.ref_size = size = 25

        self.sudoku_edit = SudokuEditPanel(self, pos = wx.Point(0,0),
                                           sudoku_doc = self.sudoku,
                                           cell_size = wx.Size(size,size))
        sz = self.sudoku_edit.GetSize()
        self.controls = ButtonPanel(self, pos = wx.Point(sz.x, 0), size=wx.Size(100,sz.y), offset=size)

        self.controls.add_button('New', self.on_btn_new)
        self.controls.add_button('Clear', self.on_btn_clear)
        self.controls.add_button('Generate', self.on_btn_generate)
        self.controls.add_button('Solve', self.on_btn_solve)
        self.controls.add_button('Validate', self.on_btn_validate)
        self.controls.add_button('Load', self.on_btn_load)
        self.controls.add_button('Save', self.on_btn_save)

        self.cmbSelDim = wx.ComboBox(choices=['2x2', '3x3', '4x4', '5x5'],
              parent=self.controls,
              pos=wx.Point(30, 250),
              size=wx.Size(60, size),
              style=0, value='3x3')
        self.cmbSelDim.Bind(wx.EVT_COMBOBOX, self.on_dim_combo)
        wx.StaticText(
              label='Size', parent=self.controls,
              pos=wx.Point(0, 252), size=wx.Size(30, 12), style=0)

        self.update_doc()

    def on_dim_combo(self, event):
        dim = int(self.cmbSelDim.Selection) + 2
        self.sudoku.setDim(dim)

    def on_btn_load(self, event):
        self.Freeze()
        self.load_game(self.file_name % self.sudoku.doc.dim)
        self.Thaw()

    def on_btn_save(self, evt):
        self.save_game(self.file_name % self.sudoku.doc.dim)

    def load_game(self, fname, quiet=False):
        res_list = stream_file_io(fname, 'r', doc_read_stream, self.sudoku)
        res = res_list[0]
        if not res:
            if not quiet:
                # TODO: show message box here
                print res_list[1]
        else:
            self.update()
        return res

    def save_game(self, fname, quiet=False):
        res_list = stream_file_io(fname, 'w', doc_write_stream, self.sudoku)
        res = res_list[0]
        if not res:
            if not quiet:
                # TODO: show message box here
                print res_list[1]
        return res

    def on_btn_validate(self, evt):
        invalid_list = self.sudoku.doc.Validate()
        self.sudoku_edit.mark_invalid(invalid_list)
        self.update()

    def on_btn_new(self, evt):
        self.Freeze()
        self.sudoku.clear(force=True)
        self.update()
        self.Thaw()

    def on_btn_clear(self, evt):
        self.sudoku.clear()
        self.update()

    def on_btn_solve(self, evt):
        print 'Solving'
        solution=[]
        res = self.sudoku.doc.Solve(solution)
        self.update()
        self.sudoku.doc.PrintSolution(solution, sys.stdout)
        print res

    def on_btn_generate(self, evt):
        doc = self.sudoku.doc
        doc.GenHard(init=True)
        self.update()

    def update(self):
        self.sudoku_edit.update()
        self.update_title()

    def save(self):
        pass

    def update_title(self):
        try:
            _, populated = self.sudoku.items()
            kind  = self.cmbSelDim.GetValue()
            title = 'Sudoku: %s [%d items]' % (kind, populated)
        except Exception, e:
            title = 'Sudoku'
            print e
        self.SetTitle(title)

    def update_doc(self):
        load = False
        self.Freeze()
        self.sudoku_edit.update_doc()
        size = self.sudoku_edit.GetSize()
        self.controls.SetPosition((size.x,0))
        ctl_size = self.controls.GetBestSize()
        self.controls.SetSize((ctl_size.x,max(size.y,ctl_size.y)))
        y_diff = size.y - ctl_size.y
        y_inc = 0
        if y_diff < self.ref_size:
            y_inc = self.ref_size - y_diff
        self.SetClientSize((size.x+ctl_size.x+self.ref_size, size.y + y_inc))
        self.load_game(self.file_name % self.sudoku.doc.dim, True)
        self.update()
        self.Thaw()

def main_GUI(argv):
    app = wx.App(redirect=False)
    doc = SudokuDocument()
    frame = MainFrame(doc)
    frame.update()
    frame.Show(True)
    app.MainLoop()
    return 0

