from config import GRID_SIZE, WORLD_SIZE, DIRECTIONS, MOVE_DELTA
from grid import grid
import random

kb = {}

def update_grid_with_agent():
    for i in range(len(grid)):
        if grid[i] == 'A':
            grid[i] = 'empty'
        grid[agent.get_index()] = 'A'


def print_kb():
    print("----------------------------------\n<Knowledge Base>")
    for y in range(1, WORLD_SIZE + 1):
        for x in range(1, WORLD_SIZE + 1):
            info = kb.get((x, y), {'status': 'Unknown', 'visited': False})
            status = info['status']
            visited = 'T' if info['visited'] else 'F'
            print(f"[{x},{y}] : {status}, {visited}")
    print("----------------------------------\n")


def print_grid(grid):
    update_grid_with_agent()
    print("----------------------------------\n<Grid>")
    for y in range(GRID_SIZE):
        row = ""
        for x in range(GRID_SIZE):
            index = y * GRID_SIZE + x

            kb_x = x
            kb_y = GRID_SIZE - y - 1
            status = kb.get((kb_x, kb_y), {}).get('status', 'Unknown')

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
                        row += "OK "
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
    print("----------------------------------\n<Locations of Wumpus, Pit, Gold>")
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


def print_percepts(percepts):
    stench, breeze, glitter, bump, scream = percepts
    print("----------------------------------\n<Percepts>")
    print(f"Stench: {stench}, Breeze: {breeze}, Glitter: {glitter}, Bump: {bump}, Scream: {scream}")
    print("----------------------------------")


class Agent:
    def __init__(self, x, y, orientation):
        self.x = x
        self.y = y
        self.orientation = orientation
        self.has_gold = False
        self.arrow_count = 3
        self.scream = False
        self.move_count = 0
        self.path_stack = []
        self.returning = False

        print_solution_grid(grid)
        # Initialize KB with starting position percept
        percepts = self.perceive(self.x, self.y)
        self.update_kb(self.x, self.y, percepts)
        print_percepts(percepts)

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

        for dx, dy in MOVE_DELTA.values():
            nx, ny = self.x + dx, self.y + dy
            if 1 <= nx <= WORLD_SIZE and 1 <= ny <= WORLD_SIZE:
                neighbor_idx = self.get_index(nx, ny)
                if grid[neighbor_idx] == 'wumpus':
                    stench = True
                if grid[neighbor_idx] == 'pit':
                    breeze = True

        return [stench, breeze, glitter, bump, scream]

    def update_kb(self, x, y, percepts):
        stench, breeze, _, _, scream = percepts

        # 해당 칸이 KB에 없으면 기본값으로 초기화
        kb.setdefault((x, y), {'status': 'Unknown', 'visited': False})

        # 방문 여부 업데이트
        kb[(x, y)]['visited'] = True

        index = self.get_index(x, y)
        cell = grid[index]

        if (cell != 'wumpus') and (cell != 'pit'):  # 에이전트가 죽지 않은 경우 실행
            if kb.get((x, y), 'Unknown') != 'Safe':
                kb[(x, y)]['status'] = 'Safe'  # 현재 칸 state를 Safe로 저장

            # 인접한 칸의 state 업데이트
            for dx, dy in MOVE_DELTA.values():
                nx, ny = x + dx, y + dy
                if 1 <= nx <= WORLD_SIZE and 1 <= ny <= WORLD_SIZE:
                    kb.setdefault((nx, ny), {'status': 'Unknown', 'visited': False})
                    neighbor_status = kb[(nx, ny)]['status']
                    # stench와 breeze 모두 False이고, 인접한 칸들이 KB에 Safe로 저장되어 있지 않은 경우 인접한 칸 모두 Safe로 업데이트
                    if not stench and not breeze and neighbor_status != 'Safe':
                        kb[(nx, ny)]['status'] = 'Safe'
                    # stench는 True, breeze는 False이고 인접한 칸들이 KB에 Unknown 또는 MaybeWP로 저장되어 있는 경우 인접한 칸 모두 MaybeW로 업데이트
                    elif stench and not breeze and neighbor_status in ['Unknown', 'MaybeWP']:
                        kb[(nx, ny)]['status'] = 'MaybeW'
                    # stench는 False, breeze는 True이고 인접한 칸들이 KB에 Unknown 또는 MaybeWP 저장되어 있는 경우 인접한 칸 모두 MaybeP으로 업데이트
                    elif breeze and not stench and neighbor_status in ['Unknown', 'MaybeWP']:
                        kb[(nx, ny)]['status'] = 'MaybeP'
                    # stench와 breeze 모두 True이고, 인접한 칸들이 KB에 Unknown으로 저장되어 있는 경우 인접한 칸 모두 MaybeWP로 업데이트
                    elif breeze and stench and neighbor_status == 'Unknown':
                        kb[(nx, ny)]['status'] = 'MaybeWP'

        if scream:  # scream==True, 즉 화살을 쏴서 wumpus가 죽은 경우
            dx, dy = MOVE_DELTA[self.orientation]
            x, y = self.x + dx, self.y + dy
            # 화살을 쏜 방향에 있는 좌표들의 state(Wumpus, WumpusOrPit, MaybeW, MaybeWP) 중에서 첫 번째로 발견되는 state가 Wumpus인 경우, 해당 칸을 Safe로 변경
            while 1 <= x <= WORLD_SIZE and 1 <= y <= WORLD_SIZE:
                current_status = kb.get((x, y), {}).get('status', '')
                if current_status in ('Wumpus', 'WumpusOrPit', 'MaybeW', 'MaybeWP'):
                    if current_status == 'Wumpus':
                        kb[(x, y)]['status'] = 'Safe'
                    break
                x += dx
                y += dy
            # KB의 모든 WumpusOrPit, MaybeW, MaybeWP을 Unknown으로 변경
            for key, value in kb.items():
                if value['status'] in ('WumpusOrPit', 'MaybeW', 'MaybeWP'):
                    value['status'] = 'Unknown'
            self.scream = False

    def infer_cause_of_death(self, x, y):
        cause = kb.get((x, y), {}).get('status', 'Unknown')
        if cause == 'MaybeW':
            print("Agent likely died from Wumpus. Updating KB.")
            kb[(x, y)]['status'] = 'Wumpus'  # 해당 칸을 Wumpus로 확정
            # KB의 모든 MaybeW와 MaybeWP를 Unknown으로 변경
            for key, value in kb.items():
                if value['status'] in ('MaybeW', 'MaybeWP'):
                    value['status'] = 'Unknown'

        elif cause == 'MaybeP':
            print("Agent likely died from Pit. Updating KB.")
            kb[(x, y)]['status'] = 'Pit'  # 해당 칸을 Pit으로 확정
            # KB의 모든 MaybeP와 MaybeWP를 Unknown으로 변경
            for key, value in kb.items():
                if value['status'] in ('MaybeP', 'MaybeWP'):
                    value['status'] = 'Unknown'

        elif cause == 'MaybeWP':
            print("cause unknown.")
            kb[(x, y)]['status'] = 'WumpusOrPit'  # 해당 칸을 Wumpus나 Pit으로 확정지을 수 없음
            # KB의 모든 MaybeWP을 Unknown으로
            for key, value in kb.items():
                if value['status'] == 'MaybeWP':
                    value['status'] = 'Unknown'

    def choose_next_direction(self):
        priorities = []
        # kb의 (state, visited) 이용해 방문할 인접한 칸의 우선순위 결정
        priorities = [
            ('Safe', False),
            ('Unknown', False),
            ('MaybeW', False),
            ('MaybeP', False),
            ('MaybeWP', False),
            ('Safe', True),
            ('Unknown', True),
            ('MaybeW', True),
            ('MaybeP', True),
            ('MaybeWP', True),
            ('WumpusPit', None)  # None: True, False 상관 X
        ]

        best_target = None
        best_dir = None
        best_candidates = []

        for status, visited in priorities:
            candidates = []
            for dir, (dx, dy) in MOVE_DELTA.items():
                nx, ny = self.x + dx, self.y + dy
                cell = kb.get((nx,ny), {})
                cell_status = cell.get('status')
                if status == 'WumpusPit':
                    if cell_status in ['Wumpus', 'Pit', 'WumpusOrPit']:
                        pass
                    else:
                        continue
                else:
                    if cell_status != status:
                        continue

                if visited is not None and cell.get('visited') != visited:
                    continue

                candidates.append((nx, ny, dir))

            if candidates:
                best_candidates = candidates
                break

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
        # 돌아가는 중일 경우 스택에서 다음 좌표를 꺼내 이동
        if self.returning and self.path_stack:
            next_x, next_y = self.path_stack.pop()
            dx = next_x - self.x
            dy = next_y - self.y

            for dir, delta in MOVE_DELTA.items():
                if delta == (dx, dy):
                    self.turn_to_direction(dir)
                    break

            self.x = next_x
            self.y = next_y
            self.move_count += 1
            print(f"Moved to ({self.x}, {self.y})")

            bump = False
            percepts = self.perceive(self.x, self.y)
            percepts[3] = bump  # bump

            if (self.x, self.y) == (1, 1):
                self.Climb()

            self.update_kb(self.x, self.y, percepts)
            print_percepts(percepts)
            print_grid(grid)
            print_kb()
            return

        self.choose_next_direction()

        dx, dy = MOVE_DELTA[self.orientation]
        new_x = self.x + dx
        new_y = self.y + dy
        bump = False

        if 1 <= new_x <= WORLD_SIZE and 1 <= new_y <= WORLD_SIZE:
            self.path_stack.append((self.x, self.y))  # 이동 전 위치 push
            self.x = new_x
            self.y = new_y
            self.move_count += 1
            print(f"Moved to ({self.x}, {self.y})")

            index = self.get_index()
            if grid[index] in ['wumpus', 'pit']:
                print(f"You died! Restart at (1,1)")
                self.infer_cause_of_death(self.x, self.y)
                percepts = self.perceive(self.x, self.y)
                self.update_kb(self.x, self.y, percepts)
                self.path_stack.clear()  # 죽으면 경로 초기화
                self.x, self.y = 1, 1  # 죽으면 (1,1)로 초기화 (KB와 화살은 유지)
                # self.orientation = 'East'
                self.choose_next_direction()

        else:
            bump = True
            print("Bump! Hit a wall.")

        percepts = self.perceive(self.x, self.y)
        percepts[3] = bump  # Update bump

        if percepts[2]:  # 금이 있으면 grab
            self.Grab()

        if self.arrow_count > 0:
            dx, dy = MOVE_DELTA[self.orientation]
            x, y = self.x + dx, self.y + dy
            while 1 <= x <= WORLD_SIZE and 1 <= y <= WORLD_SIZE:
                if kb.get((x, y), {}).get('status', '') in ('Wumpus', 'WumpusOrPit', 'MaybeW', 'MaybeWP'):
                    self.Shoot()
                    percepts = self.perceive(self.x, self.y)
                    break
                x += dx
                y += dy

        self.update_kb(self.x, self.y, percepts)  # scream==True였다면 kb 업데이트 후 다시 false가 됨
        print_percepts(percepts)
        print_grid(grid)
        print_kb()

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
            self.returning = True
            print("Grabbed the gold!")

    def Shoot(self):
        self.arrow_count -= 1
        print(f"Shot an arrow! Remaining arrows: {self.arrow_count}")
        dx, dy = MOVE_DELTA[self.orientation]
        x, y = self.x + dx, self.y + dy
        while 1 <= x <= WORLD_SIZE and 1 <= y <= WORLD_SIZE:
            idx = self.get_index(x, y)
            if grid[idx] == 'wumpus':
                grid[idx] = 'empty'  # 화살 쏜 방향에 있는 wumpus 중 화살과 처음 마주하는 wumpus를 삭제
                self.scream = True
                print(f"You killed the wumpus!")
                break
            x += dx
            y += dy
        else:  # 화살이 지나간 경로에 있는 MaybeW / MaybeWP / WumpusOrPit 업데이트
            x, y = self.x + dx, self.y + dy
            while 1 <= x <= WORLD_SIZE and 1 <= y <= WORLD_SIZE:
                cell = kb.get((x, y))
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
            print("There was no wumpus.")

    def Climb(self):
        print(f"Success! Escaped with the gold in {self.move_count} moves!")
        exit()


# Initialize agent
agent = Agent(1, 1, 'East')

def main():
    print_grid(grid)
    print_kb()

    climb_success = False
    for _ in range(500):
        agent.GoForward()
    if not climb_success:
        print("Agent is stuck!")


if __name__ == "__main__":
    main()
