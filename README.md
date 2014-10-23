sudoku
======

sudoku in python

Core sudoku solver and puzzle generator;

This was a project to help me learn python.
I decided to write something useful but fun. My daughter's favorite puzzle is sudoku. She solves them pretty well and I can not keep up. So I thought: why don't I write the sugoku puzzle generator and solver? That will let me understand the solving strategy and maybe improve my solving skills. So I did.

First I wrote the data model, then applied classical rules. The code is rather generic, so the rules may be easily changed, with the same data model and solver.

Initially I coded a brute force solver. Not a really dumb one, means it does some checks and does not follow obviously impossible paths, but is does use some guessing and goes back-and-forth trying different alternatives.

Interestingly enough, this solver will eventually solve every correct puzzle, even those that are not solvable by elimination technique (so-called "impossible" puzzles).
To say more, it will solve any incorrect puzzle for which multiple solutions are possible, and it will obviously report impossibility to solve for any puzzle with no solutions. This sounds pretty good, but there are obvious drawbacks as well. It is terribly slow, and is not able to give a meaningful explanation of how it solved the puzzle.
Now, what does the ability to solve incorrect puzzle brings? In fact, it lets us generate brand new puzzles. Since empty set is an incorrect puzzle with multiple solutions it is "solvable". Solver picks values at random (out of set of possible values), so it will not generate the same puzzle twice in  a row. But this is not a puzzle yet. It is a completely solved puzzle.
Now, we have to start the elimination process. And this process must be rule-based to ensure that it is solvable by humans.
So I written the rule-based solver also.
Both solvers and generator, as well as some debugging code is what I call Sudoku Solver core.
Minimalistic Sudoku console is what I used for debugging and finally solving, both interactively and automatically.
