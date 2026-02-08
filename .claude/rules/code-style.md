# Python Code Style Guide

This document defines Python best practices and code patterns for this codebase.

## Formatting

- Follow PEP 8 style guide
- Use **4 spaces** for indentation (no tabs)
- Max file length: **500 lines**. Refactor if approaching this limit.

## Type Hints

Use PEP 484 type hints with modern lowercase generics (Python 3.9+):

```python
# Correct
def process(items: list[str]) -> dict[str, int]:
    ...

# Avoid (legacy typing module)
from typing import List, Dict
def process(items: List[str]) -> Dict[str, int]:
    ...
```

## Module Organization

- Organize code into clearly separated modules by feature or responsibility
- Every module must have a concise docstring explaining its purpose
- Keep related functionality together; split when modules grow too large
- Modules are `.py` files in the project directory
- If there are more than 10-20 modules, consider grouping them into folders

## Imports

Imports go at the top of the file, separated into three sections with comments:

```python
# Standard library
import os
from dataclasses import dataclass

# Third-party libraries
import flask
from dotenv import load_dotenv

# Local imports
from .utils import get_user_choice
```

## Documentation

### Module Docstrings

Every module starts with a brief docstring:

```python
[utils.py]
"""A place to put generally useful functions and classes."""
```

### Function/Class Docstrings

Use Google-style docstrings for public functions and classes:

```python
def get_potential_points(game_state: GameState, square: Square) -> int:
    """Calculate points for placing current dice in a square.

    Args:
        game_state: Current game state with dice on table.
        square: The scoring category to evaluate.

    Returns:
        Points that would be scored, accounting for joker rules.

    Raises:
        ValueError: If the square is already filled.
    """
```

### Inline Comments

Use comments to add extra information that is needed for code clarity, but not contained in the code itself - such as units for numerical quantities, and explanations of what complex logic achieves. Don't just reiterate what the code already says.

Before adding a comment to explain what a variable/function/etc means, try putting that information in the variable or function name.

Comments are also useful to prevent misunderstandings among humans or AI coding agents where confusing code is unavoidable, and the likelihood of misunderstanding is high - for example in the below example where the 0th element represents the number of '1' dice. Another example is Fourier analysis, where multiple conflicting conventions for the definition of the Fourier transform and its inverse are in common use. In code that uses the Fourier transform, at least one docstring and/or comment should document which convention is used.

```python
# BAD EXAMPLE:
def add(a: float, b: float) -> float:  # function called add takes float arguments a and b
    '''Add a and b'''
    c = a + b  # assign sum of a and b to c
    return c  # function returns c, a float

# BETTER EXAMPLE:
def add_prices(price_a: float, price_b: float) -> float:
    '''Get the sum of price_a and price_b'''
    # Prices are in GBP
    total_price = price_a + price_b
    return total_price
```

```python
# BAD EXAMPLE:
# store the number of times that each of 1 to 6 appears in the dice list
dice_counts = [game_state.dice_on_table.count(n) for n in range(1, 7)]
# ^ comment just reiterates what the code says to anyone familiar with Python

# BETTER EXAMPLE:
# dice_counts[i] = count of (i+1)s, e.g. dice_counts[0] = count of 1s
dice_counts = [game_state.dice_on_table.count(n) for n in range(1, 7)]
# ^ comment suggests how to use dice_counts in subsequent code

# EVEN BETTER EXAMPLE:
# Precalculate how many of each number is on the table
dice_counts = {n: game_state.dice_on_table.count(n) for n in range(1, 7)}
# ^ off-by-one confusion is eliminated by using a dict, and
#   the comment explains the context & design intent behind this line of code
```

Remember, comments are intended for people who are fluent in the programming language, but not necessarily familiar with the application domain, or project-specific design choices and conventions.

### Variable naming

Variable names should aim to be specific and descriptive, but limit them to around 3 words unless absolutely necessary. Don't over-specify: names should align with the application-specificity of a particular bit of code.

For example, a function that can sort any container should just be called "sort", but a class method that sorts `Listing`'s by price should be called "Listing.sort_by_price".

All variable names should be descriptive, but an important exception is loop counters: in simple loops or list comprehensions, these can just be called `i`, `j`, `k` in the order of nesting.

```python
# Example where using `i` as a loop counter doesn't make sense:
# Graphics rendering loop: complex and unusual logic
# Each loop iteration represents something specific: a frame
# Use a descriptive variable name for the loop counter
#*******************************
timestep: float = ...  # seconds
is_realtime: bool = ...
for frame_counter in range(num_frames):
    # Advance the simulation
    world.step(timestep)
    # Render the next frame
    frame = graphics.render(world)
    # Show the frame counter in the corner
    show_frame_counter(frame, frame_counter)
    # Update the display
    display.blit(frame)
    display.update()
    # Pause until the next frame
    if is_realtime:
        wait(timestep)
#*******************************

# Example where using `i` as a loop counter makes sense:
# Iterating over a list is a common code pattern
# The loop counter doesn't mean anything other than being a
# throwaway index into the list
# In this case, we also can't use the `for request in current_requests`
# syntax, because the list is modified inside the loop
#*******************************
# Delete expired requests
i = 0
while i < len(current_requests):
    if is_expired(current_requests[i]):
        current_requests.pop(i)
    else:
        i += 1
```

## Section Separators (Optional)

For longer files, use 80-character section separators with centered titles:

```python
# --------------------------------- CONSTANTS ----------------------------------

# ------------------------------ HELPER FUNCTIONS ------------------------------

# -------------------------------- PUBLIC API ----------------------------------
```

## Important notes

- Never assume of guess - When in doubt, ask for clarification
- Always verify file paths and module names before use
- Keep CLAUDE.md updated when adding new patterns or dependencies
- Test your code - No feature is complete without tests
- Document your decisions - Future developers (including yourself) will thank you
