import pygame
import random
import sys
import os
import traceback


def resource_path(relative_path):
    """获取资源的绝对路径 - 解决打包后路径问题"""
    try:
        # PyInstaller创建的临时文件夹
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    """主函数，包含完整的错误处理"""
    try:
        # 初始化pygame
        pygame.init()

        # 游戏常量
        WIDTH, HEIGHT = 600, 600
        GRID_SIZE = 20
        GRID_WIDTH = WIDTH // GRID_SIZE
        GRID_HEIGHT = HEIGHT // GRID_SIZE
        FPS = 10

        # 颜色定义
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        GREEN = (0, 255, 0)
        RED = (255, 0, 0)
        BLUE = (0, 120, 255)
        GRAY = (40, 40, 40)
        YELLOW = (255, 255, 0)

        # 方向常量
        UP = (0, -1)
        DOWN = (0, 1)
        LEFT = (-1, 0)
        RIGHT = (1, 0)

        class Snake:
            def __init__(self):
                self.reset()

            def reset(self):
                self.body = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
                self.direction = RIGHT
                self.grow_pending = 3
                self.score = 0

            def move(self):
                head_x, head_y = self.body[0]
                dx, dy = self.direction
                new_head = (head_x + dx, head_y + dy)

                # 检查撞墙
                if new_head[0] < 0 or new_head[0] >= GRID_WIDTH or new_head[1] < 0 or new_head[1] >= GRID_HEIGHT:
                    return False

                # 检查撞自己
                if new_head in self.body:
                    return False

                self.body.insert(0, new_head)

                if self.grow_pending > 0:
                    self.grow_pending -= 1
                else:
                    self.body.pop()

                return True

            def grow(self):
                self.grow_pending += 1
                self.score += 10

            def change_direction(self, new_direction):
                if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
                    self.direction = new_direction

        class Food:
            def __init__(self):
                self.position = (0, 0)
                self.randomize_position()

            def randomize_position(self):
                self.position = (random.randint(0, GRID_WIDTH - 1),
                                 random.randint(0, GRID_HEIGHT - 1))

            def check_collision(self, snake_body):
                return self.position in snake_body

        class Game:
            def __init__(self):
                # 安全的屏幕初始化
                try:
                    self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
                    pygame.display.set_caption("Snake Game")
                except Exception as e:
                    # 如果默认分辨率失败，尝试较低分辨率
                    try:
                        self.screen = pygame.display.set_mode((800, 600))
                    except:
                        # 最后尝试最小分辨率
                        self.screen = pygame.display.set_mode((400, 300))

                self.clock = pygame.time.Clock()

                # 安全的字体初始化 - 多种回退方案
                self.font = self.get_safe_font(36)
                self.small_font = self.get_safe_font(24)

                self.snake = Snake()
                self.food = Food()
                self.game_over = False
                self.ensure_food_valid()

                # 游戏结束菜单选项
                self.menu_options = ["Restart", "Quit"]
                self.selected_option = 0

                print("游戏初始化完成")

            def get_safe_font(self, size):
                """安全的字体获取函数，多重回退方案"""
                font_attempts = [
                    # 尝试1: 系统默认字体
                    lambda: pygame.font.Font(None, size),
                    # 尝试2: Arial字体
                    lambda: pygame.font.SysFont('arial', size),
                    # 尝试3: 无衬线字体
                    lambda: pygame.font.SysFont('sans-serif', size),
                    # 尝试4: 任何可用字体
                    lambda: pygame.font.SysFont(None, size),
                ]

                for attempt in font_attempts:
                    try:
                        font = attempt()
                        # 测试字体是否能正常渲染
                        test_surface = font.render("Test", True, WHITE)
                        if test_surface.get_width() > 0:
                            return font
                    except:
                        continue

                # 如果所有字体都失败，创建最简单的字体模拟
                print("警告: 使用回退字体方案")
                return self.create_fallback_font(size)

            def create_fallback_font(self, size):
                """创建图形回退字体"""

                class FallbackFont:
                    def __init__(self, font_size):
                        self.size = font_size
                        self.char_width = font_size // 2
                        self.char_height = font_size

                    def render(self, text, antialias, color):
                        width = len(text) * self.char_width
                        surface = pygame.Surface((width, self.char_height), pygame.SRCALPHA)
                        surface.fill((0, 0, 0, 0))  # 透明背景

                        # 用简单图形表示文字
                        for i, char in enumerate(text):
                            if char.isalnum():
                                rect = pygame.Rect(i * self.char_width, 0,
                                                   self.char_width - 2, self.char_height)
                                pygame.draw.rect(surface, color, rect, 1)
                        return surface

                return FallbackFont(size)

            def ensure_food_valid(self):
                while self.food.check_collision(self.snake.body):
                    self.food.randomize_position()

            def handle_events(self):
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False

                    if event.type == pygame.KEYDOWN:
                        if self.game_over:
                            # 游戏结束菜单导航
                            if event.key == pygame.K_UP:
                                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
                            elif event.key == pygame.K_DOWN:
                                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
                            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                                if self.selected_option == 0:  # Restart
                                    self.restart_game()
                                else:  # Quit
                                    return False
                            elif event.key == pygame.K_ESCAPE:
                                return False
                            elif event.key == pygame.K_r:  # R键也可以重新开始
                                self.restart_game()
                        else:
                            # 游戏进行中控制
                            if event.key == pygame.K_UP:
                                self.snake.change_direction(UP)
                            elif event.key == pygame.K_DOWN:
                                self.snake.change_direction(DOWN)
                            elif event.key == pygame.K_LEFT:
                                self.snake.change_direction(LEFT)
                            elif event.key == pygame.K_RIGHT:
                                self.snake.change_direction(RIGHT)
                            elif event.key == pygame.K_ESCAPE:
                                return False
                            elif event.key == pygame.K_r:  # 游戏中也可以按R重新开始
                                self.restart_game()

                return True

            def update(self):
                if not self.game_over:
                    if not self.snake.move():
                        self.game_over = True
                        return

                    if self.snake.body[0] == self.food.position:
                        self.snake.grow()
                        self.food.randomize_position()
                        self.ensure_food_valid()

            def draw_game(self):
                """绘制游戏画面"""
                self.screen.fill(BLACK)

                # 绘制网格
                for x in range(0, WIDTH, GRID_SIZE):
                    pygame.draw.line(self.screen, GRAY, (x, 0), (x, HEIGHT))
                for y in range(0, HEIGHT, GRID_SIZE):
                    pygame.draw.line(self.screen, GRAY, (0, y), (WIDTH, y))

                # 绘制蛇
                for i, (x, y) in enumerate(self.snake.body):
                    color = GREEN if i == 0 else BLUE
                    rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, BLACK, rect, 1)

                # 绘制食物
                food_rect = pygame.Rect(self.food.position[0] * GRID_SIZE,
                                        self.food.position[1] * GRID_SIZE,
                                        GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(self.screen, RED, food_rect)

                # 绘制分数 - 使用安全的文本绘制
                self.draw_text_safe(f"Score: {self.snake.score}", self.font, WHITE, 10, 10)

                # 绘制长度
                self.draw_text_safe(f"Length: {len(self.snake.body)}", self.small_font, WHITE, WIDTH - 150, 10)

                # 绘制墙壁边界
                pygame.draw.rect(self.screen, RED, (0, 0, WIDTH, HEIGHT), 3)

            def draw_text_safe(self, text, font, color, x, y):
                """安全的文本绘制函数"""
                try:
                    if hasattr(font, 'render'):
                        # 正常字体
                        text_surface = font.render(text, True, color)
                        self.screen.blit(text_surface, (x, y))
                    else:
                        # 回退字体
                        text_surface = font.render(text, True, color)
                        self.screen.blit(text_surface, (x, y))
                except Exception as e:
                    # 如果文本绘制失败，用图形表示
                    pygame.draw.rect(self.screen, color, (x, y, len(text) * 8, 30), 1)

            def draw_game_over_menu(self):
                """绘制游戏结束菜单"""
                # 半透明覆盖层
                overlay = pygame.Surface((WIDTH, HEIGHT))
                overlay.set_alpha(180)
                overlay.fill(BLACK)
                self.screen.blit(overlay, (0, 0))

                # 游戏结束标题
                self.draw_text_safe("Game Over", self.font, RED, WIDTH // 2 - 80, HEIGHT // 2 - 80)

                # 最终分数
                self.draw_text_safe(f"Final Score: {self.snake.score}", self.font, WHITE, WIDTH // 2 - 120,
                                    HEIGHT // 2 - 30)

                # 菜单选项
                menu_y = HEIGHT // 2 + 20
                for i, option in enumerate(self.menu_options):
                    color = YELLOW if i == self.selected_option else WHITE
                    self.draw_text_safe(option, self.font, color, WIDTH // 2 - 50, menu_y + i * 50)

                    # 添加选择指示器
                    if i == self.selected_option:
                        pygame.draw.polygon(self.screen, YELLOW, [
                            (WIDTH // 2 - 80, menu_y + i * 50 + 18),
                            (WIDTH // 2 - 60, menu_y + i * 50 + 8),
                            (WIDTH // 2 - 60, menu_y + i * 50 + 28)
                        ])

                # 操作说明
                self.draw_text_safe("UP/DOWN: Select  ENTER: Confirm", self.small_font, GRAY, WIDTH // 2 - 140,
                                    HEIGHT - 50)

            def draw(self):
                """绘制所有内容"""
                self.draw_game()

                if self.game_over:
                    self.draw_game_over_menu()

                pygame.display.flip()

            def restart_game(self):
                """重新开始游戏"""
                self.snake.reset()
                self.food.randomize_position()
                self.ensure_food_valid()
                self.game_over = False
                self.selected_option = 0

            def run(self):
                """运行游戏主循环"""
                running = True
                print("游戏开始! 控制说明:")
                print("方向键: 控制蛇移动")
                print("ESC: 退出游戏")
                print("R: 重新开始游戏")
                print("游戏结束后: 使用上下键选择菜单，回车确认")

                while running:
                    try:
                        running = self.handle_events()
                        self.update()
                        self.draw()
                        self.clock.tick(FPS)
                    except Exception as e:
                        print(f"游戏循环错误: {e}")
                        # 尝试继续运行
                        running = True

                pygame.quit()

        # 创建并运行游戏
        game = Game()
        game.run()

    except Exception as e:
        # 捕获所有未处理的异常
        error_msg = f"游戏发生错误:\n{type(e).__name__}: {e}"
        print(error_msg)
        traceback.print_exc()

        # 尝试显示错误信息
        try:
            pygame.init()
            screen = pygame.display.set_mode((600, 400))
            font = pygame.font.SysFont('arial', 24)

            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                        running = False

                screen.fill((0, 0, 0))
                lines = error_msg.split('\n')
                for i, line in enumerate(lines):
                    text = font.render(line, True, (255, 0, 0))
                    screen.blit(text, (50, 50 + i * 30))

                text = font.render("Press any key to exit", True, (255, 255, 255))
                screen.blit(text, (50, 200))
                pygame.display.flip()

            pygame.quit()
        except:
            pass

        input("按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()