class Boggle:

    def __init__(self, grid, dictionary):
        # Normalize the grid to lowercase via helper,
        # then store dictionary and prepare solutions set.
        self.grid = self.setGrid(grid)
        self.dictionary = dictionary
        self.solutions = set()

    # Used to set the grid and convert all grid elements into lower case.
    def setGrid(self, grid):
        self.grid = grid
        for i in range(len(self.grid)):
            for j in range(len(self.grid[i])):
                self.grid[i][j] = self.grid[i][j].lower()
        # Return the processed grid so __init__ can assign it safely.
        return self.grid

    def setDictionary(self, dictionary):
        self.dictionary = dictionary

    # Build a set of all prefixes from the dictionary
    # Idea: if a partial string isn't a prefix of any word,
    # we can stop exploring that path.
    def build_Hashmap(self):
        prefix_table = set()
        for word in self.dictionary:
            for j in range(1, len(word) + 1):
                prefix_table.add(word[:j])
        return prefix_table

    # Turn dictionary words to lowercase and
    # make sure there's at least one word of length >= 3,
    # since shorter ones aren't valid Boggle words.
    def dictionary_wordLength(self):
        for i in range(len(self.dictionary)):
            self.dictionary[i] = self.dictionary[i].lower()
        ok = False
        for word in self.dictionary:
            if len(word) >= 3:
                ok = True
                break
        return ok

    # Validate NxN shape, alphabetic cells, special rules, and edge cases:
    # - Grid must be square (N x N).
    # - All cells must be alphabetic.
    # - Allow only specific multi-letter tiles ("qu", "st", "ie").
    # - If any special multi-letter tile appears, forbid raw "q", "s",
    # or "i" tiles.
    def gridValidate(self):
        n = len(self.grid)
        allowed_multi = {"qu", "st", "ie"}
        prohibited_raw = {"q", "s", "i"}
        for i in range(len(self.grid)):
            if len(self.grid[i]) != n:
                return False
            for j in range(len(self.grid[i])):
                cell = self.grid[i][j]
                # Multi-letter tiles must be from our allowed set.
                if len(cell) >= 2:
                    if cell not in allowed_multi:
                        return False
                # Single-letter versions of q/s/i are forbidden
                # when we're using special tiles.
                elif cell in prohibited_raw:
                    return False
                # Everything should be alphabetic characters.
                elif not self.grid[i][j].isalpha():
                    return False
        return True

    # Depth-first search from every cell to find all valid words.
    # We use:
    # - prefix_table to prune branches early
    # - set_dict for O(1) membership tests when a full word is formed.
    def searching_Algo(self, prefix_table, set_dict):
        # 8 directions: horizontal, vertical, and diagonal neighbors.
        directions = [
            (0, 1), (0, -1),
            (-1, 0), (1, 0),
            (-1, 1), (-1, -1),
            (1, 1), (1, -1)
        ]

        def find(row, col, string, used):
            # If current string isn't a prefix of any dictionary word,
            # stop exploring this path.
            if string not in prefix_table:
                return

            # If we've got a valid word (length >= 3 and in the dictionary),
            # record it.
            if (len(string) >= 3) and (string in set_dict):
                self.solutions.add(string)

            # Try extending the current string in all 8 directions.
            for dir_row, dir_col in directions:
                n_row, n_col = (row + dir_row), (col + dir_col)
                # Stay inside the grid and avoid revisiting
                # the same cell in this path.
                if (
                    0 <= n_row < len(self.grid)
                    and 0 <= n_col < len(self.grid[0])
                    and (n_row, n_col) not in used
                ):
                    used.add((n_row, n_col))
                    find(n_row, n_col, string + self.grid[n_row][n_col], used)
                    # Unmark the cell so it can be used in other paths.
                    used.remove((n_row, n_col))

        # Start a DFS from every cell on the board.
        for i in range(len(self.grid)):
            for j in range(len(self.grid[i])):
                find(i, j, self.grid[i][j], {(i, j)})

    def getSolution(self):
        # Early-out for empty inputs.
        if len(self.grid) == 0 or len(self.dictionary) == 0:
            return self.solutions

        # If dictionary or grid are invalid, don't bother searching.
        if not (self.dictionary_wordLength() and self.gridValidate()):
            return self.solutions
        else:
            # Precompute prefix table and dictionary set once, then run DFS.
            prefix_table = self.build_Hashmap()
            set_dict = set(self.dictionary)
            self.searching_Algo(prefix_table, set_dict)
            return sorted(self.solutions)


def main():
    grid = [["T", "W", "Y", "R"], ["E", "N", "P", "H"],
            ["G", "Z", "Qu", "R"], ["O", "N", "T", "A"]]
    dictionary = ["art", "ego", "gent", "get", "net", "new", "newt", "prat",
                  "pry", "qua", "quart", "quartz", "rat", "tar", "tarp",
                  "ten", "went", "wet", "arty", "rhr", "not", "quar"]

    mygame = Boggle(grid, dictionary)
    print(mygame.getSolution())


if __name__ == "__main__":
    main()