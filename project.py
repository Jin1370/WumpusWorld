# Constants
GRID_SIZE = 6
WORLD_SIZE = 4
DIRECTIONS = ['North', 'East', 'South', 'West']
MOVE_DELTA = {
    'North': (0, 1),
    'East': (1, 0),
    'South': (0, -1),
    'West': (-1, 0)
}

# Initialize the grid
grid = ['wall'] * (GRID_SIZE * GRID_SIZE)
for y in range(1, WORLD_SIZE + 1):
    for x in range(1, WORLD_SIZE + 1):
        grid_y = GRID_SIZE - y - 1
        index = grid_y * GRID_SIZE + x
        grid[index] = 'empty'

# Add wumpus and pit for testing
grid[15] = 'wumpus'  # (3,2)
grid[16] = 'pit'     # (4,2)
grid[27] = 'gold'    # (3,1)

# Knowledge base to store state: 'Unknown', 'Safe', 'Wumpus', 'Pit'
knowledge = [['Unknown' for _ in range(WORLD_SIZE + 2)] for _ in range(WORLD_SIZE + 2)]

class Agent:
    def __init__(self, x, y, orientation):
        self.x = x
        self.y = y
        self.orientation = orientation
        self.has_gold = False
        self.has_arrow = True
        self.alive = True
        self.scream = False

    def get_index(self, x=None, y=None):
        x = x if x is not None else self.x
        y = y if y is not None else self.y
        grid_y = GRID_SIZE - y - 1
        return grid_y * GRID_SIZE + x

    def perceive(self):
        index = self.get_index()
        stench = False
        breeze = False
        glitter = (grid[index] == 'gold')
        bump = False
        scream = self.scream

        # Check adjacent cells
        for dx, dy in MOVE_DELTA.values():
            nx, ny = self.x + dx, self.y + dy
            if 1 <= nx <= WORLD_SIZE and 1 <= ny <= WORLD_SIZE:
                neighbor_idx = self.get_index(nx, ny)
                if grid[neighbor_idx] == 'wumpus':
                    stench = True
                if grid[neighbor_idx] == 'pit':
                    breeze = True

        return [stench, breeze, glitter, bump, scream]

    def update_knowledge(self, percepts):
        stench, breeze, _, _, _ = percepts
        if not stench and not breeze:
            knowledge[self.y][self.x] = 'Safe'
            for dx, dy in MOVE_DELTA.values():
                nx, ny = self.x + dx, self.y + dy
                if 1 <= nx <= WORLD_SIZE and 1 <= ny <= WORLD_SIZE:
                    if knowledge[ny][nx] == 'Unknown':
                        knowledge[ny][nx] = 'Safe'
        elif not self.alive:
            index = self.get_index()
            if grid[index] == 'wumpus':
                knowledge[self.y][self.x] = 'Wumpus'
            elif grid[index] == 'pit':
                knowledge[self.y][self.x] = 'Pit'

    def GoForward(self):
        dx, dy = MOVE_DELTA[self.orientation]
        new_x = self.x + dx
        new_y = self.y + dy
        bump = False

        if 1 <= new_x <= WORLD_SIZE and 1 <= new_y <= WORLD_SIZE:
            self.x = new_x
            self.y = new_y
            index = self.get_index()
            if grid[index] in ['wumpus', 'pit']:
                self.alive = False
                print(f"You encountered a {grid[index]} and died!")
        else:
            bump = True
            print("Bump! Hit a wall.")

        percepts = self.perceive()
        percepts[3] = bump  # Update bump
        self.update_knowledge(percepts)
        return percepts

    def TurnLeft(self):
        idx = DIRECTIONS.index(self.orientation)
        self.orientation = DIRECTIONS[(idx - 1) % 4]

    def TurnRight(self):
        idx = DIRECTIONS.index(self.orientation)
        self.orientation = DIRECTIONS[(idx + 1) % 4]

    def Grab(self):
        index = self.get_index()
        if grid[index] == 'gold':
            self.has_gold = True
            grid[index] = 'empty'
            print("Grabbed the gold!")
        else:
            print("No gold here.")

    def Shoot(self):
        if not self.has_arrow:
            print("No arrows left.")
            return
        self.has_arrow = False
        dx, dy = MOVE_DELTA[self.orientation]
        x, y = self.x + dx, self.y + dy
        while 1 <= x <= WORLD_SIZE and 1 <= y <= WORLD_SIZE:
            idx = self.get_index(x, y)
            if grid[idx] == 'wumpus':
                grid[idx] = 'empty'
                self.scream = True
                print("You killed the wumpus!")
                break
            x += dx
            y += dy

    def Climb(self):
        if (self.x, self.y) == (1, 1):
            if self.has_gold:
                print("Climbed out with the gold!")
            else:
                print("Climbed out empty-handed.")
        else:
            print("Can't climb here.")

# Initialize agent
agent = Agent(1, 1, 'East')

# Grid update function
def update_grid_with_agent():
    for i in range(len(grid)):
        if grid[i] == 'A':
            grid[i] = 'empty'
    if agent.alive:
        grid[agent.get_index()] = 'A'

# Grid print function
def print_grid(grid):
    update_grid_with_agent()
    for y in range(GRID_SIZE):
        row = ""
        for x in range(GRID_SIZE):
            index = y * GRID_SIZE + x
            cell = grid[index]
            if cell == 'wall':
                row += "#  "
            elif cell == 'A':
                row += "A  "
            elif cell == 'gold':
                row += "G  "
            else:
                row += "?  "
        print(row)
    print()

# Knowledge print function
def print_knowledge():
    print("Agent Knowledge:")
    for y in range(WORLD_SIZE + 1, 0, -1):
        print(' '.join(f"{knowledge[y][x][0]}" if knowledge[y][x] != 'Unknown' else 'U' for x in range(1, WORLD_SIZE + 1)))
    print()

print_grid(grid)
print_knowledge()

agent.GoForward()
print_grid(grid)
print_knowledge()

agent.GoForward()  # gold 있는 위치로 이동
agent.Grab()
print_grid(grid)
print_knowledge()
