from puzzle_ui import main_GUI
from puzzle import main_console

import sys

def main(argv):
    if len(argv) > 1 and argv[1] == '-c':
        main_console(argv)
    else:
        main_GUI(argv)

if __name__ == '__main__':
    main(sys.argv)
