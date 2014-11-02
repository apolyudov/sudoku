sudoku
======

Sudoku in Python

Pure Python implementation of Sudoku puzzle solver and generator;
GUI and console version;
Cross-plafrom;
Tested on MS Windows 7, but must work on Linux,
and anywhere else where python is ported.

1 Foreword

This was a project to help me learn python.
I decided to write something useful but fun.
My daughter's favorite puzzle is sudoku.
She solves them pretty well and I can not keep up.
So I thought: why don't I write the sudoku puzzle generator and solver?
That will let me understand the solving strategy and maybe improve my solving skills.
So I did.

First I wrote the data model, then applied classical rules.
The code is rather generic, so the rules may be easily changed, with the same data model and solver.

Initially I coded a brute force solver.
Not a really dumb one, means it does some checks and does not follow
obviously impossible paths, but is does use some guessing and goes
back-and-forth trying different alternatives.

Interestingly enough, this solver will eventually solve every correct puzzle,
even those that are not solvable by elimination technique (so-called "impossible" puzzles).
To say more, it will solve any incorrect puzzle for which multiple solutions are possible,
and it will obviously report impossibility to solve for any puzzle with no solutions.

This sounds pretty good, but there are obvious drawbacks as well.
It is terribly slow, and is not able to give a meaningful explanation of how it solved the puzzle.
Now, what does the ability to solve incorrect puzzle brings?
In fact, it lets us generate brand new puzzles.
Since empty set is an incorrect puzzle with multiple solutions it is "solvable".
Solver picks values at random (out of set of possible values),
so it will not generate the same puzzle twice in  a row.
But this is not a puzzle yet. It is a completely solved puzzle.
Now, we have to start the elimination process.
And this process must be rule-based to ensure that it is solvable by humans.
So I written the rule-based solver also.

Both solvers and generator, as well as some debugging code is what I call Sudoku Solver core.
Minimalistic Sudoku console is what I used for debugging and finally solving, both interactively and automatically.
Finally, I added some very simple GUI to make it look nice, and also learn pythonic
ways of dealing with graphics.

2 Installation

All you need is PY :)
simply make sure you have all the .py files in the same directory, and
python 2.7 is installed with standard packages.

3 How to use

there is more than one way to (skin the cat) run this toy.

Run 'main.py' to get GUI (requires python 'wx' extension to be installed;
see http://www.wxpython.org/ on how to install it)
another way to run is:
/path/to/python main.py
(if python is not on system path)
if there is no 'wx' extension found, it will fall back to console mode
See 4 for more detailed description of GUI mode

or

run 'main.py -c' to get console version of it
See 5 for more detailed description of console mode

4 GUI notes

It is very simple and (I hope) self-explanatory, but anyway:
there is an EDIT field for the puzzle, and set of buttons that control the
state of presentation and solver.
EDIT field consists of multiple cells, which can accept only one character each.
(1-9),for 3x3 sudoku,
(0-9,A-F) for 4x4 sudoku,
(A-Y) for 5x5 sudoku

Typically the 'puzzle' part (the initial set of populated cells) is "locked", so
that you can't edit them by  mistake. BUT: doing double-click on locked cell makes
it unlocked. double-click on unlocked cell, yeah, makes it locked.
All the possible alternatives allowed by the rules are shown as a tooltip.
Some obsious errors are marked in RED or YELLOW, and tooltip changes to explain
what happened.

buttons:

- New: erases the field (both locked and unlocked cells)

- Clear: erases all the unlocked cells

- Generate: takes 1-3 seconds to generate 3x3 puzzle on my machine.
Generating 4x4 puzzles takes a minute or two. I did not have paitience to see
how long does it take to generate 5x5 puzzle.
  generated results are immediately locked.
  generated puzzle is supposed to be solvable, and is supposed to have unique solution :)

- Solve: populates EDIT field with whatever solution it finds, and generates report
  which is supposed to explain to humans how was the soulution found
  in case of incorrect puzzles, it will not do a brute force, but give the partial solution.
  The reason why I don't give brute force option in GUI is: I can't generate explanation
  log for brute-force solver, and without explanation this is not very useful.
  Whoever cares about brute-force solver, it is available in console mode :)

 GUI version does not have a special command to give hints.
 Instead, whoat you could do is: click on 'Solve', and then click 'Clear'.
 complete solution will be printed in a separate window in a what I consider human-readable form.
 Use it as a cheatsheet if necessary.

- Validate: makes sure that all the values in the EDIT field are allowed by the rules.

- Load: reads the game state from predefined file.

- Save: writes the game state to predefined file.

5 Console commands

text console takes several commands, that let you generate and solve sudoku puzzles

- load predefined game #0: v 0

- show currently loaded game: t

- turn on 'show maybe' mode (t will display possible values for non-solved elements): m 1

- solve the game: s

- print the step-by-step explanation: p

- give a hint (next step): h

- generate new game: gen

- clear game buffer: clr

- set a value N at position (x,y): e <y> <x> <N>

e.g.: e 3 4 7 will set value '7' to cell in row 3, col 4

- clear value at position (x,y): e <y> <x> .

- export current state as a string: x

- import game as a string, exported by 'x': i <string>

6. Details on solver and generator

Currently there are 2 solvers (rule-based solver and random solver).
There is one generator, based on both solvers and random elimination approach.
random solver (I acall it hard solver) solves any puzzle that has solution(s)
rule-based solver only solves puzzle with a single solution, and only if the solution
is logically derivable (does not currently do any guesswork)

The plan is:

- improve rule-based solver to cover so-called impossible (guesswork) cases with a single solution

- to write rule-based generator, with ability to generate games of given complexity

- more?
