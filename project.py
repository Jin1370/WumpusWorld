import random
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
grid[9] = 'wumpus'
grid[28] = 'pit'
grid[22] = 'gold'

knowledge = {}  # (x, y): 'Safe', 'Wumpus', 'Pit', etc.

class Agent:
    def __init__(self, x, y, orientation):
        self.x = x
        self.y = y
        self.orientation = orientation
        self.has_gold = False
        self.arrow_count = 3
        self.scream = False

        # Initialize KB with starting position percept
        percepts = self.perceive(self.x, self.y)
        self.update_knowledge(self.x, self.y, percepts)

    # 매개변수로 x,y를 주면 해당 좌표의 index 반환, 안주면 현재 좌표의 index 반환
    def get_index(self, x=None, y=None):
        x = x if x is not None else self.x
        y = y if y is not None else self.y
        grid_y = GRID_SIZE - y - 1
        return grid_y * GRID_SIZE + x

    def perceive(self, x, y):
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

    def update_knowledge(self, x, y, percepts):
        stench, breeze, _, _, scream = percepts
        index = self.get_index(x, y)
        cell = grid[index]

        # 에이전트가 죽지 않았고, 해당 칸이 KB에 Safe로 저장되어 있지 않은 경우 해당 칸 Safe로 업데이트
        if (cell != 'wumpus') and (cell != 'pit') and (knowledge.get((x, y), 'Unknown') != 'Safe'):
            knowledge[(x, y)] = 'Safe'
        # stench와 breeze 모두 False이고, 인접한 칸들이 KB에 Safe로 저장되어 있지 않은 경우 인접한 칸 모두 Safe로 업데이트
        if not stench and not breeze:
            for dx, dy in MOVE_DELTA.values():
                nx, ny = x + dx, y + dy
                if 1 <= nx <= WORLD_SIZE and 1 <= ny <= WORLD_SIZE:
                    neighbor_status = knowledge.get((nx, ny), 'Unknown')
                    if neighbor_status != 'Safe':
                        knowledge[(nx, ny)] = 'Safe'
        else:
            for dx, dy in MOVE_DELTA.values():
                nx, ny = x + dx, y + dy
                if 1 <= nx <= WORLD_SIZE and 1 <= ny <= WORLD_SIZE:
                    neighbor_status = knowledge.get((nx, ny), 'Unknown')
                    # stench는 True, breeze는 False이고 인접한 칸들이 KB에 Unknown으로 저장되어 있는 경우 인접한 칸 모두 MaybeWumpus로 업데이트
                    if stench and not breeze:
                        if neighbor_status == 'Unknown':
                            knowledge[(nx, ny)] = 'MaybeWumpus'
                    # stench는 False, breeze는 True이고 인접한 칸들이 KB에 Unknown으로 저장되어 있는 경우 인접한 칸 모두 MaybePit으로 업데이트
                    elif breeze and not stench:
                        if neighbor_status == 'Unknown':
                            knowledge[(nx, ny)] = 'MaybePit'

        if scream and hasattr(self, 'wumpus_killed_pos'):
            wx, wy = self.wumpus_killed_pos
            if knowledge.get((wx, wy)) == 'Wumpus':
                knowledge[(wx, wy)] = 'Safe'
                print(f"Since Scream==True, update KB: ({wx},{wy}) -> Safe")
            self.scream = False
            self.wumpus_killed_pos = None

    def infer_cause_of_death(self, x, y):
        cause = knowledge.get((x, y), 'Unknown')
        if cause == 'MaybeWumpus':
            print(f"Agent likely died from Wumpus at ({x},{y}). Updating KB.")
            knowledge[(x, y)] = 'Wumpus'
            # KB의 모든 MaybeWumpus를 Unknown으로
            for key, value in knowledge.items():
                if value == 'MaybeWumpus':
                    knowledge[key] = 'Unknown'
        elif cause == 'MaybePit':
            print(f"Agent likely died from Pit at ({x},{y}). Updating KB.")
            knowledge[(x, y)] = 'Pit'
            # KB의 모든 MaybePit을 Unknown으로
            for key, value in knowledge.items():
                if value == 'MaybePit':
                    knowledge[key] = 'Unknown'
        else:
            print(f"Agent died at ({x},{y}), cause unknown.")

    def GoForward(self):
        dx, dy = MOVE_DELTA[self.orientation]
        new_x = self.x + dx
        new_y = self.y + dy
        bump = False

        # 다음 칸에 위험 표시가 되어 있는지 KB에서 확인
        danger = knowledge.get((new_x, new_y))
        if danger in ['Wumpus', 'Pit']:
            print(f"Knowledge says danger at ({new_x},{new_y}): {danger}. Changing direction!")
            if random.choice([True, False]):
                self.TurnLeft()
            else:
                self.TurnRight()

        elif 1 <= new_x <= WORLD_SIZE and 1 <= new_y <= WORLD_SIZE:
            self.x = new_x
            self.y = new_y
            print(f"Moved to ({self.x}, {self.y}) facing {self.orientation}")

            index = self.get_index()
            if grid[index] in ['wumpus', 'pit']:
                print(f"You encountered a {grid[index]} and died! Restart at (1,1)")
                self.infer_cause_of_death(self.x, self.y)  # 추가: 죽음 추론
                percepts = self.perceive(self.x, self.y)
                self.update_knowledge(self.x, self.y, percepts)
                # 죽으면 (1,1)로 초기화 (KB와 화살은 유지)
                self.x, self.y = 1, 1
                self.orientation = 'East'

        else:
            bump = True
            print("Bump! Hit a wall.")

        percepts = self.perceive(self.x, self.y)
        percepts[3] = bump  # Update bump
        self.update_knowledge(self.x, self.y, percepts)
        percepts[4] = self.scream # KB 업데이트시 scream==True였다면, 상태가 wumpus였던 좌표를 safe로, scream==False로 바꾸기 때문에 갱신 필요

        if (self.x, self.y) == (1, 1) and self.has_gold: # 좌표가 (1,1)이고 금을 가지고 있으면 climb
            self.Climb()
        elif percepts[2]:  # 금이 있으면 grab
            self.Grab()
        elif bump:  # 벽에 부딪히면 TurnLeft와 TurnRight 중 랜덤으로 선택해 수행
            if random.choice([True, False]):
                self.TurnLeft()
            else:
                self.TurnRight()
        elif self.arrow_count > 0:  # 화살이 남아있고, 에이전트가 바라보는 방향의 동일선상에 wumpus가 있으면 shoot
            dx, dy = MOVE_DELTA[self.orientation]
            x, y = self.x + dx, self.y + dy
            while 1 <= x <= WORLD_SIZE and 1 <= y <= WORLD_SIZE:
                if knowledge.get((x, y)) == 'Wumpus':
                    self.Shoot()
                    percepts[4] = self.scream # Shoot 실행시 wumpus를 제거하고 scream==True로 바꾸기 때문에 갱신 필요
                    break
                x += dx
                y += dy

        print_percepts(percepts)
        print_grid(grid)
        print_knowledge()

        return percepts

    def TurnLeft(self):
        idx = DIRECTIONS.index(self.orientation)
        self.orientation = DIRECTIONS[(idx - 1) % 4]
        print(f"Turned left. Now facing {self.orientation}")

    def TurnRight(self):
        idx = DIRECTIONS.index(self.orientation)
        self.orientation = DIRECTIONS[(idx + 1) % 4]
        print(f"Turned right. Now facing {self.orientation}")

    def Grab(self):
        index = self.get_index()
        print(grid[index])
        if grid[index] == 'gold':
            self.has_gold = True
            grid[index] = 'empty'
            print("Grabbed the gold!")
        else:
            print("No gold here.")

    def Shoot(self):
        if self.arrow_count <= 0:
            print("No arrows left.")
            return
        self.arrow_count -= 1
        print(f"Shot an arrow! Remaining arrows: {self.arrow_count}")
        dx, dy = MOVE_DELTA[self.orientation]
        x, y = self.x + dx, self.y + dy
        while 1 <= x <= WORLD_SIZE and 1 <= y <= WORLD_SIZE:
            idx = self.get_index(x, y)
            if grid[idx] == 'wumpus':
                grid[idx] = 'empty'
                self.scream = True
                self.wumpus_killed_pos = (x, y)
                print(f"You killed the wumpus at ({x},{y})!")
                break
            x += dx
            y += dy

    def Climb(self):
        if (self.x, self.y) == (1, 1):
            if self.has_gold:
                print("Climbed out with the gold!")
                exit()

# Initialize agent
agent = Agent(1, 1, 'East')

# Grid update function
def update_grid_with_agent():
    for i in range(len(grid)):
        if grid[i] == 'A':
            grid[i] = 'empty'
        grid[agent.get_index()] = 'A'

# Grid print function
def print_grid(grid):
    update_grid_with_agent()
    print("----------------------------------\n<Grid>")
    for y in range(GRID_SIZE):
        row = ""
        for x in range(GRID_SIZE):
            index = y * GRID_SIZE + x

            kb_x = x
            kb_y = GRID_SIZE - y - 1
            status = knowledge.get((kb_x, kb_y), 'Unknown')


            if grid[index] == 'wall':
                row += "#  "
            elif grid[index] == 'A':
                row += "A  "
            elif grid[index] == 'gold':
                row += "G  "
            elif grid[index] == 'wumpus':
                row += "W  "
            elif grid[index] == 'pit':
                row += "P  "
            else:
                if (1 <= kb_x <= WORLD_SIZE) and (1 <= kb_y <= WORLD_SIZE):
                    if status == 'Safe':
                        row += "S  "
                    elif status == 'Wumpus':
                        row += "W! "
                    elif status == 'Pit':
                        row += "P! "
                    elif status == 'MaybeWumpus':
                        row += "W? "
                    elif status == 'MaybePit':
                        row += "P? "
                    else:
                        row += "?  "
                else:
                    row += "?  "
        print(row)
    print("----------------------------------")

# Knowledge print function
def print_knowledge():
    print("----------------------------------\n<Knowledge Base>")
    for y in range(1, WORLD_SIZE + 1):
        for x in range(1, WORLD_SIZE + 1):
            status = knowledge.get((x, y), 'Unknown')
            print(f"[{x},{y}] : {status}")
    print("----------------------------------\n")

def print_percepts(percepts):
    stench, breeze, glitter, bump, scream = percepts
    print("----------------------------------\n<Percepts>")
    print(f"Stench: {stench}, Breeze: {breeze}, Glitter: {glitter}, Bump: {bump}, Scream: {scream}")
    print("----------------------------------")


print_grid(grid)
print_knowledge()
# 메인 루프
#while True:
#    agent.GoForward()

for _ in range(20):  # 20번만 실행
    agent.GoForward()