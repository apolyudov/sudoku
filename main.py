#!/usr/bin/python
import sys

def main(argv):
    gui = True
    if len(argv) > 1 and argv[1] == '-c':
        gui = False
        print 'CMD option selected'

    if gui:
        try:
            from puzzle_ui import main_GUI
        except Exception, e:
            gui = False
            print 'GUI init failed:', e

    if not gui:
        from puzzle import main_console

    if gui:
        main_GUI(argv)
    else:
        main_console(argv)

if __name__ == '__main__':
    main(sys.argv)
