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

        if index == 25:  # (1,1)에는 아무것도 생성되지 않음
            continue
        has_wumpus = random.random() < 0.1
        has_pit = random.random() < 0.1

        if has_pit:  # 둘 다 True일 경우 Pit 우선으로 처리
            grid[index] = 'pit'
        elif has_wumpus:
            grid[index] = 'wumpus'
        else:
            grid[index] = 'empty'

# Gold 배치: Wumpus, Pit이 없는 곳 중 하나
safe_indices = [i for i in range(GRID_SIZE * GRID_SIZE) if grid[i] == 'empty' and i != 25]
if safe_indices:
    gold_index = random.choice(safe_indices)
    grid[gold_index] = 'gold'
'''
#grid[19] = 'wumpus'
grid[26] = 'wumpus'
grid[15] = 'pit'
grid[8] = 'gold'
'''

knowledge = {}  # (x, y): 'Safe', 'Wumpus', 'Pit', etc.

class Agent:
    def __init__(self, x, y, orientation):
        self.x = x
        self.y = y
        self.orientation = orientation
        self.has_gold = False
        self.arrow_count = 3
        self.scream = False
        self.move_count = 0

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
        index = self.get_index(x, y)
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

        # 해당 칸이 KB에 없으면 기본값으로 초기화
        knowledge.setdefault((x, y), {'status': 'Unknown', 'visited': False})

        # 방문 여부 업데이트
        knowledge[(x, y)]['visited'] = True

        index = self.get_index(x, y)
        cell = grid[index]

        if (cell != 'wumpus') and (cell != 'pit'):  # 에이전트가 죽지 않은 경우
            if knowledge.get((x, y), 'Unknown') != 'Safe':
                knowledge[(x, y)]['status'] = 'Safe'
            # 인접한 칸 state 업데이트
            for dx, dy in MOVE_DELTA.values():
                nx, ny = x + dx, y + dy
                if 1 <= nx <= WORLD_SIZE and 1 <= ny <= WORLD_SIZE:
                    knowledge.setdefault((nx, ny), {'status': 'Unknown', 'visited': False})
                    neighbor_status = knowledge[(nx, ny)]['status']
                    # stench와 breeze 모두 False이고, 인접한 칸들이 KB에 Safe로 저장되어 있지 않은 경우 인접한 칸 모두 Safe로 업데이트
                    if not stench and not breeze and neighbor_status != 'Safe':
                        knowledge[(nx, ny)]['status'] = 'Safe'
                    # stench는 True, breeze는 False이고 인접한 칸들이 KB에 Unknown 또는 MaybeWP로 저장되어 있는 경우 인접한 칸 모두 MaybeW로 업데이트
                    elif stench and not breeze and neighbor_status in ['Unknown', 'MaybeWP']:
                        knowledge[(nx, ny)]['status'] = 'MaybeW'
                    # stench는 False, breeze는 True이고 인접한 칸들이 KB에 Unknown 또는 MaybeWP 저장되어 있는 경우 인접한 칸 모두 MaybeP으로 업데이트
                    elif breeze and not stench and neighbor_status in ['Unknown', 'MaybeWP']:
                        knowledge[(nx, ny)]['status'] = 'MaybeP'
                    # stench와 breeze 모두 True이고, 인접한 칸들이 KB에 Unknown으로 저장되어 있는 경우 인접한 칸 모두 MaybeWP로 업데이트
                    elif breeze and stench and neighbor_status == 'Unknown':
                        knowledge[(nx, ny)]['status'] = 'MaybeWP'

        if scream and hasattr(self, 'wumpus_killed_pos'):
            wx, wy = self.wumpus_killed_pos
            if knowledge.get((wx, wy), {}).get('status') in ('Wumpus', 'WumpusOrPit', 'MaybeW', 'MaybeWP'):
                knowledge[(wx, wy)]['status'] = 'Safe'
                # KB의 모든 MaybeW, MaybeWP를 Unknown으로
                for key, value in knowledge.items():
                    if value['status'] in ('MaybeW', 'MaybeWP'):
                        value['status'] = 'Unknown'
                print(f"Since Scream==True, update KB")
            self.scream = False
            self.wumpus_killed_pos = None

    def infer_cause_of_death(self, x, y):
        cause = knowledge.get((x, y), {}).get('status', 'Unknown')
        if cause == 'MaybeW':
            print("Agent likely died from Wumpus. Updating KB.")
            knowledge[(x, y)]['status'] = 'Wumpus'
            # KB의 모든 MaybeW와 MaybeWP를 Unknown으로
            for key, value in knowledge.items():
                if value['status'] in ('MaybeW', 'MaybeWP'):
                    value['status'] = 'Unknown'
        elif cause == 'MaybeP':
            print("Agent likely died from Pit. Updating KB.")
            knowledge[(x, y)]['status'] = 'Pit'
            # KB의 모든 MaybeP와 MaybeWP를 Unknown으로
            for key, value in knowledge.items():
                if value['status'] in ('MaybeP', 'MaybeWP'):
                    value['status'] = 'Unknown'
        elif cause == 'MaybeWP':
            print("cause unknown.")
            knowledge[(x, y)]['status'] = 'WumpusOrPit'
            # KB의 모든 MaybeWP을 Unknown으로
            for key, value in knowledge.items():
                if value['status'] == 'MaybeWP':
                    value['status'] = 'Unknown'

    def choose_next_direction(self):
        priorities = []

        # 우선순위 정의
        if not self.has_gold:
            priorities = [
                ('Safe', False),
                ('MaybeW', False),
                ('MaybeP', False),
                ('MaybeWP', False),
                ('Safe', True),
                ('WumpusPit', True)
            ]
        else:
            priorities = [
                ('Safe', True),  # True or False 모두 포함
                ('Safe', False),
                ('MaybeW', False),
                ('MaybeP', False),
                ('MaybeWP', False),
                ('WumpusPit', True)
            ]

        best_target = None
        best_dir = None
        best_candidates = []  # 후보를 저장할 리스트

        for status, visited in priorities:
            candidates = []  # 각 레벨별 후보 리스트
            for dir, (dx, dy) in MOVE_DELTA.items():
                nx, ny = self.x + dx, self.y + dy
                cell = knowledge.get((nx,ny), {})
                # Status 체크
                cell_status = cell.get('status')
                if status == 'WumpusPit':
                    if cell_status in ['Wumpus', 'Pit', 'WumpusOrPit']:
                        pass
                    else:
                        continue
                else:
                    if cell_status != status:
                        continue

                # Visited 체크
                if visited is not None and cell.get('visited') != visited:
                    continue

                candidates.append((nx, ny, dir))

            if candidates:
                best_candidates = candidates
                break  # 우선순위 레벨에서 후보 찾았으면 종료

        # 후보 중 랜덤 선택
        if best_candidates:
            # for Bump test
            # for dir, (dx, dy) in MOVE_DELTA.items():
            #    nx, ny = self.x + dx, self.y + dy
            #    if not (1 <= nx <= WORLD_SIZE and 1 <= ny <= WORLD_SIZE):
            #        best_candidates.append((nx, ny, dir))
            target = random.choice(best_candidates)
            target_x, target_y, best_dir = target
            print(f"select direction: {best_dir}")
            self.turn_to_direction(best_dir)

        else:
            print("움직일 칸을 찾지 못함 (모두 방문했거나 위험)")

    def turn_to_direction(self, target_dir):
        # 현재 방향과 target_dir 비교해서 방향 회전
        current_idx = DIRECTIONS.index(self.orientation)
        target_idx = DIRECTIONS.index(target_dir)

        diff = (target_idx - current_idx) % 4
        if diff == 0:
            pass  # 이미 바라보고 있음
        elif diff == 1:
            self.TurnRight()
        elif diff == 2:
            self.TurnRight()
            self.TurnRight()
        elif diff == 3:
            self.TurnLeft()

    def GoForward(self):
        #next_status = knowledge.get((new_x, new_y), {}).get('status', 'Unknown')
        #if next_status != 'Safe':
        self.choose_next_direction()

        dx, dy = MOVE_DELTA[self.orientation]
        new_x = self.x + dx
        new_y = self.y + dy
        bump = False

        if 1 <= new_x <= WORLD_SIZE and 1 <= new_y <= WORLD_SIZE:
            self.x = new_x
            self.y = new_y
            self.move_count += 1
            print(f"Moved to ({self.x}, {self.y})")

            index = self.get_index()
            if grid[index] in ['wumpus', 'pit']:
                print(f"You died! Restart at (1,1)")
                self.infer_cause_of_death(self.x, self.y)  # 추가: 죽음 추론
                percepts = self.perceive(self.x, self.y)
                self.update_knowledge(self.x, self.y, percepts)
                # 죽으면 (1,1)로 초기화 (KB와 화살은 유지)
                self.x, self.y = 1, 1
                self.choose_next_direction()

        else:
            bump = True
            print("Bump! Hit a wall.")

        percepts = self.perceive(self.x, self.y)
        percepts[3] = bump  # Update bump

        if (self.x, self.y) == (1, 1) and self.has_gold: # 좌표가 (1,1)이고 금을 가지고 있으면 climb
            self.Climb()
        elif percepts[2]:  # 금이 있으면 grab
            self.Grab()

        #self.update_knowledge(self.x, self.y, percepts)
        #percepts[4] = self.scream # KB 업데이트시 scream==True였다면 상태를 업데이트하고 scream==False로 바꾸기 때문에 갱신 필요

        if self.arrow_count > 0:  # 화살이 남아있고, 에이전트가 바라보는 방향의 동일선상에 'Wumpus', 'WumpusOrPit', 'MaybeW', 'MaybeWP'가 있으면 shoot
            dx, dy = MOVE_DELTA[self.orientation]
            x, y = self.x + dx, self.y + dy
            while 1 <= x <= WORLD_SIZE and 1 <= y <= WORLD_SIZE:
                if knowledge.get((x, y), {}).get('status', '') in ('Wumpus', 'WumpusOrPit', 'MaybeW', 'MaybeWP'):
                    self.Shoot()
                    percepts = self.perceive(self.x, self.y)
                    percepts[4] = self.scream # Shoot 실행시 wumpus를 제거하면 scream==True로 바꾸기 때문에 갱신 필요
                    break
                x += dx
                y += dy
        self.update_knowledge(self.x, self.y, percepts)
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
        if grid[index] == 'gold':
            self.has_gold = True
            grid[index] = 'empty'
            print("Grabbed the gold!")
        else:
            print("No gold here.")

    def Shoot(self):
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
        else:  # 화살이 지나간 경로에 있는 MaybeW / MaybeWP / WumpusOrPit을 업데이트
            x, y = self.x + dx, self.y + dy
            while 1 <= x <= WORLD_SIZE and 1 <= y <= WORLD_SIZE:
                cell = knowledge.get((x, y))
                if cell:
                    status = cell.get('status')
                    if status == 'MaybeW':
                        cell['status'] = 'Safe'
                    elif status == 'MaybeWP':
                        cell['status'] = 'MaybeP'
                    elif status == 'WumpusOrPit':
                        cell['status'] = 'Pit'
                x += dx
                y += dy
            print("There was no wumpus. Updated KB")

    def Climb(self):
        print(f"Success! Escaped with the gold in {self.move_count} moves!")
        exit()

# Initialize agent
agent = Agent(1, 1, 'East')

# Grid update function
def update_grid_with_agent():
    for i in range(len(grid)):
        if grid[i] == 'A':
            grid[i] = 'empty'
        grid[agent.get_index()] = 'A'

# Knowledge print function
def print_knowledge():
    print("----------------------------------\n<Knowledge Base>")
    for y in range(1, WORLD_SIZE + 1):
        for x in range(1, WORLD_SIZE + 1):
            info = knowledge.get((x, y), {'status': 'Unknown', 'visited': False})
            status = info['status']
            visited = 'T' if info['visited'] else 'F'
            print(f"[{x},{y}] : {status}, {visited}")
    print("----------------------------------\n")

def print_percepts(percepts):
    stench, breeze, glitter, bump, scream = percepts
    print("----------------------------------\n<Percepts>")
    print(f"Stench: {stench}, Breeze: {breeze}, Glitter: {glitter}, Bump: {bump}, Scream: {scream}")
    print("----------------------------------")

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
            status = knowledge.get((kb_x, kb_y), {}).get('status', 'Unknown')

            if grid[index] == 'wall':
                row += "#  "
            elif grid[index] == 'A':
                row += "A  "
            # elif grid[index] == 'wumpus':
            #    row += "W  "
            # elif grid[index] == 'pit':
            #    row += "P  "
            else:
                if (1 <= kb_x <= WORLD_SIZE) and (1 <= kb_y <= WORLD_SIZE):
                    if status == 'Safe':
                        row += "S  "
                    elif status == 'Wumpus':
                        row += "W! "
                    elif status == 'Pit':
                        row += "P! "
                    elif status == 'WumpusOrPit':
                        row += "WP!"
                    elif status == 'MaybeW':
                        row += "W? "
                    elif status == 'MaybeP':
                        row += "P? "
                    elif status == 'MaybeWP':
                        row += "WP?"
                    else:
                        row += "?  "
                else:
                    row += "?  "
        print(row)

def print_solution_grid(grid):
    print("----------------------------------\n<Solution Grid>")
    for y in range(GRID_SIZE):
        row = ""
        for x in range(GRID_SIZE):
            index = y * GRID_SIZE + x
            if grid[index] == 'wall':
                row += "#  "
            elif grid[index] == 'gold':
                row += "G  "
            elif grid[index] == 'wumpus':
                row += "W  "
            elif grid[index] == 'pit':
                row += "P  "
            else:
                row += "-  "
        print(row)

def main():
    print_solution_grid(grid)

    print_grid(grid)
    print_knowledge()

    climb_success = False
    for _ in range(200):  # 20번만 실행
        agent.GoForward()
    if not climb_success: print("Agent is stuck!")

if __name__ == "__main__":
    main()
