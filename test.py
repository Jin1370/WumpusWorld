import random

# Constants
GRID_SIZE = 4
ARROWS = 3
DIRECTIONS = ['EAST', 'NORTH', 'WEST', 'SOUTH']
DX = [1, 0, -1, 0]
DY = [0, 1, 0, -1]

# Elements on the grid
WUMPUS = (2, 0)
PIT = (3, 2)
GOLD = (3, 3)

# Agent class with reflex and state
class Agent:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x, self.y = 0, 0
        self.direction = 0  # 0: East, 1: North, 2: West, 3: South
        self.state = [['Unknown' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.safe = set()
        self.visited = set()
        self.arrows = ARROWS
        self.has_gold = False
        self.path = [(0, 0)]
        self.state[0][0] = 'Safe'
        self.safe.update([(0, 1), (1, 0)])
        self.visited.add((0, 0))

    def get_percepts(self):
        percepts = {'Stench': False, 'Breeze': False, 'Glitter': False, 'Bump': False, 'Scream': False}
        if (self.x, self.y) == WUMPUS:
            percepts['Stench'] = True
        if (self.x, self.y) == PIT:
            percepts['Breeze'] = True
        if (self.x, self.y) == GOLD:
            percepts['Glitter'] = True
        return percepts

    def infer_and_update(self, percepts):
        x, y = self.x, self.y
        adj = [(x + dx, y + dy) for dx, dy in zip(DX, DY)
               if 0 <= x + dx < GRID_SIZE and 0 <= y + dy < GRID_SIZE]

        if not percepts['Stench'] and not percepts['Breeze']:
            for nx, ny in adj:
                self.state[ny][nx] = 'Safe'
                self.safe.add((nx, ny))
        if percepts['Stench']:
            for nx, ny in adj:
                if self.state[ny][nx] == 'Unknown':
                    self.state[ny][nx] = 'Danger'
        if percepts['Glitter']:
            self.has_gold = True

    def decide_move(self):
        for dx, dy in zip(DX, DY):
            nx, ny = self.x + dx, self.y + dy
            if (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and
                    (nx, ny) in self.safe and (nx, ny) not in self.visited):
                return nx, ny
        return None

    def move_to(self, nx, ny):
        self.x, self.y = nx, ny
        self.visited.add((nx, ny))
        self.path.append((nx, ny))

    def climb_out(self):
        print("Agent climbed out with gold!")
        return True

    def display_grid(self):
        print("\nAgent State Grid:")
        for y in reversed(range(GRID_SIZE)):
            row = ''
            for x in range(GRID_SIZE):
                if (x, y) == (self.x, self.y):
                    row += ' A '
                elif self.state[y][x] == 'Safe':
                    row += ' . '
                elif self.state[y][x] == 'Danger':
                    row += ' D '
                else:
                    row += ' ? '
            print(row)
        print()

# Simulation
def run_simulation():
    agent = Agent()
    steps = 0
    max_steps = 50
    while steps < max_steps:
        percepts = agent.get_percepts()
        agent.infer_and_update(percepts)
        agent.display_grid()

        if agent.has_gold and (agent.x, agent.y) == (0, 0):
            agent.climb_out()
            break

        next_move = agent.decide_move()
        if next_move:
            agent.move_to(*next_move)
        else:
            # Return to start if stuck or has gold
            if agent.x != 0 or agent.y != 0:
                agent.move_to(0, 0)
            else:
                print("Agent is stuck. Restarting with known state.")
                agent.reset()
        steps += 1

run_simulation()

