# Catch Ingredients & Cook It!!
# CircuitPython 10.x Game for Xiao ESP32C3

import time
import board
import busio
import digitalio
import neopixel
import displayio
import terminalio
import random
import i2cdisplaybus
import adafruit_displayio_ssd1306
import adafruit_adxl34x
from adafruit_display_text import label

# ============================================
# HARDWARE SETUP
# ============================================
displayio.release_displays()
time.sleep(0.5)  # Wait for display release

# I2C - using board.SCL and board.SDA
i2c = busio.I2C(board.SCL, board.SDA)

# Wait for I2C to be ready
while not i2c.try_lock():
    pass
i2c.unlock()

# OLED Display with retry
display = None
for _ in range(3):
    try:
        display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
        display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)
        break
    except ValueError:
        time.sleep(0.3)

if display is None:
    print("ERROR: Cannot find OLED display!")
    while True:
        pass

# Accelerometer
accelerometer = adafruit_adxl34x.ADXL345(i2c)

# NeoPixels
NUM_PIXELS = 8
pixels = neopixel.NeoPixel(board.D3, NUM_PIXELS, brightness=0.3, auto_write=False)

# Rotary Encoder (manual - no rotaryio on ESP32-C3)
encoder_clk = digitalio.DigitalInOut(board.D0)
encoder_clk.direction = digitalio.Direction.INPUT
encoder_clk.pull = digitalio.Pull.UP

encoder_dt = digitalio.DigitalInOut(board.D1)
encoder_dt.direction = digitalio.Direction.INPUT
encoder_dt.pull = digitalio.Pull.UP

encoder_sw = digitalio.DigitalInOut(board.D6)
encoder_sw.direction = digitalio.Direction.INPUT
encoder_sw.pull = digitalio.Pull.UP

# ============================================
# INGREDIENT ICONS (8x8 bitmaps)
# ============================================
# 1 = white pixel, 0 = black pixel
ICON_DATA = {
    "egg": [  # 蛋形
        0b00111100,
        0b01111110,
        0b11111111,
        0b11111111,
        0b11111111,
        0b11111111,
        0b01111110,
        0b00111100,
    ],
    "milk": [  # 奶瓶
        0b00111100,
        0b00100100,
        0b00111100,
        0b01111110,
        0b01111110,
        0b01111110,
        0b01111110,
        0b00111100,
    ],
    "wheat": [  # 麦穗
        0b00010000,
        0b00111000,
        0b00010000,
        0b00111000,
        0b00010000,
        0b00111000,
        0b00010000,
        0b00010000,
    ],
    "bacon": [  # 培根条纹
        0b11111111,
        0b00000000,
        0b11111111,
        0b00000000,
        0b11111111,
        0b00000000,
        0b11111111,
        0b00000000,
    ],
    "tomato": [  # 番茄
        0b00011000,
        0b01111110,
        0b11111111,
        0b11111111,
        0b11111111,
        0b11111111,
        0b01111110,
        0b00111100,
    ],
    "chicken": [  # 鸡
        0b01100000,
        0b11110000,
        0b01111110,
        0b01111111,
        0b00111110,
        0b00011100,
        0b00100010,
        0b00100010,
    ],
    "duck": [  # 鸭
        0b01100000,
        0b11111000,
        0b01111110,
        0b00111111,
        0b00011110,
        0b00001100,
        0b00010010,
        0b00010010,
    ],
    "fish": [  # 鱼
        0b00000000,
        0b00011000,
        0b01111110,
        0b11111111,
        0b11111111,
        0b01111110,
        0b00011000,
        0b00000000,
    ],
    "carrot": [  # 胡萝卜
        0b00001100,
        0b00011110,
        0b00001100,
        0b00011000,
        0b00110000,
        0b01100000,
        0b11000000,
        0b10000000,
    ],
    "potato": [  # 土豆
        0b00111100,
        0b01111110,
        0b11111111,
        0b11111111,
        0b11111111,
        0b01111110,
        0b00111100,
        0b00000000,
    ],
    "pork": [  # 猪
        0b00000000,
        0b01100110,
        0b11111111,
        0b11111111,
        0b01111110,
        0b00111100,
        0b01000010,
        0b00000000,
    ],
    "yogurt": [  # 酸奶杯
        0b01111110,
        0b01000010,
        0b00111100,
        0b00111100,
        0b00111100,
        0b00111100,
        0b00111100,
        0b00011000,
    ],
    "fruit": [  # 水果/苹果
        0b00010000,
        0b00111000,
        0b01111110,
        0b11111111,
        0b11111111,
        0b11111111,
        0b01111110,
        0b00111100,
    ],
    "honey": [  # 蜂蜜罐
        0b00111100,
        0b01111110,
        0b01111110,
        0b00111100,
        0b01111110,
        0b01111110,
        0b01111110,
        0b00111100,
    ],
    "lemon": [  # 柠檬
        0b00011100,
        0b00111110,
        0b01111111,
        0b01111111,
        0b01111111,
        0b00111110,
        0b00011100,
        0b00000000,
    ],
    "cheese": [  # 奶酪三角
        0b00000001,
        0b00000111,
        0b00011111,
        0b01111111,
        0b11111111,
        0b11111111,
        0b11111111,
        0b00000000,
    ],
    "turkey": [  # 火鸡
        0b00110000,
        0b01111100,
        0b00111110,
        0b00011111,
        0b00001110,
        0b00000100,
        0b00001010,
        0b00001010,
    ],
    "cranberry": [  # 蔓越莓
        0b00000000,
        0b01100110,
        0b11111111,
        0b11111111,
        0b01111110,
        0b00111100,
        0b00000000,
        0b00000000,
    ],
    "shell": [  # 贝壳
        0b00011000,
        0b00111100,
        0b01111110,
        0b11111111,
        0b11111111,
        0b01010101,
        0b00101010,
        0b00000000,
    ],
    "seaweed": [  # 海草
        0b10010010,
        0b01001001,
        0b10010010,
        0b01001001,
        0b10010010,
        0b01001001,
        0b10010010,
        0b01001001,
    ],
    "lamb": [  # 羊
        0b01100110,
        0b11111111,
        0b11111111,
        0b01111110,
        0b00111100,
        0b00111100,
        0b01000010,
        0b01000010,
    ],
    "herbs": [  # 香草
        0b00100100,
        0b01011010,
        0b00100100,
        0b01011010,
        0b00100100,
        0b00011000,
        0b00011000,
        0b00011000,
    ],
    "grapes": [  # 葡萄
        0b00010000,
        0b01101100,
        0b11111110,
        0b11111110,
        0b01111100,
        0b00111000,
        0b00010000,
        0b00000000,
    ],
    "meat": [  # 肉
        0b00111100,
        0b01111110,
        0b11111111,
        0b11111111,
        0b11100111,
        0b11000011,
        0b01100110,
        0b00111100,
    ],
    "veggie": [  # 蔬菜
        0b00011000,
        0b00111100,
        0b01111110,
        0b00011000,
        0b00011000,
        0b00111100,
        0b01111110,
        0b00111100,
    ],
    "grain": [  # 谷物
        0b10101010,
        0b01010101,
        0b10101010,
        0b01010101,
        0b10101010,
        0b01010101,
        0b10101010,
        0b01010101,
    ],
    "default": [  # 默认方块
        0b11111111,
        0b10000001,
        0b10000001,
        0b10000001,
        0b10000001,
        0b10000001,
        0b10000001,
        0b11111111,
    ],
}

def make_icon(name):
    """Create an 8x8 icon bitmap for ingredient"""
    data = ICON_DATA.get(name, ICON_DATA["default"])
    bmp = displayio.Bitmap(8, 8, 2)
    pal = displayio.Palette(2)
    pal[0] = 0x000000
    pal[1] = 0xFFFFFF
    
    for y in range(8):
        row = data[y]
        for x in range(8):
            if row & (1 << (7 - x)):
                bmp[x, y] = 1
    
    return bmp, pal
COLOR_OFF = (0, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_PURPLE = (128, 0, 128)

TILT_THRESHOLD = 4.0
SHAKE_THRESHOLD = 18.0  # Lower threshold for easier shake detection
MOVE_DEBOUNCE = 0.15

DIFFICULTY = {
    "EASY": (90, 1),
    "MEDIUM": (60, 2),
    "HARD": (45, 3)
}

LEVELS = [
    {"name": "Sunny Morning", "view": "side", "ingredients": [("egg", 2), ("milk", 2)], "dish": "Fried Egg+Milk", "cooking": False},
    {"name": "Pancake Prep", "view": "side", "ingredients": [("egg", 2), ("wheat", 2)], "dish": "Pancakes", "cooking": False},
    {"name": "Full Breakfast", "view": "topdown", "ingredients": [("bacon", 2), ("egg", 2), ("tomato", 2)], "dish": "Bacon&Eggs", "cooking": False},
    {"name": "Healthy Bowl", "view": "topdown", "ingredients": [("yogurt", 2), ("fruit", 2), ("honey", 2)], "dish": "Yogurt Bowl", "cooking": False},
    {"name": "Poultry Chase", "view": "topdown", "ingredients": [("duck", 3), ("chicken", 3)], "dish": "Roast Bird", "cooking": False},
    {"name": "Lakeside", "view": "topdown", "ingredients": [("fish", 3), ("lemon", 2)], "dish": "Fish+Lemon", "cooking": False},
    {"name": "Hearty Stew", "view": "topdown", "ingredients": [("pork", 2), ("carrot", 2), ("potato", 2)], "dish": "Pork Stew", "cooking": False},
    {"name": "Pizza Time", "view": "topdown", "ingredients": [("cheese", 2), ("tomato", 2), ("wheat", 2)], "dish": "Pizza", "cooking": True},
    {"name": "Thanksgiving", "view": "topdown", "ingredients": [("turkey", 2), ("cranberry", 2), ("potato", 2)], "dish": "Turkey", "cooking": False},
    {"name": "Ocean Bounty", "view": "topdown", "ingredients": [("fish", 2), ("shell", 2), ("seaweed", 2)], "dish": "Seafood", "cooking": False},
    {"name": "Gourmet", "view": "topdown", "ingredients": [("lamb", 2), ("herbs", 2), ("grapes", 2)], "dish": "Lamb+Wine", "cooking": True},
    {"name": "Grand Feast", "view": "topdown", "ingredients": [("meat", 3), ("veggie", 3), ("grain", 3)], "dish": "Festival!", "cooking": True},
]

# ============================================
# GAME STATE
# ============================================
class Game:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.screen = "title"
        self.difficulty = "EASY"
        self.diff_idx = 0
        self.level = 0
        self.time_left = 90
        self.px = 64
        self.py = 32
        self.collected = {}
        self.needed = {}
        self.items = []
        self.cook_progress = 0
        self.last_move = 0

game = Game()
last_clk = True
last_btn = True
enc_pos = 0

# ============================================
# INPUT
# ============================================
def read_accel():
    x, y, z = accelerometer.acceleration
    total = (x**2 + y**2 + z**2) ** 0.5
    
    if total > SHAKE_THRESHOLD:
        return "SHAKE"
    if abs(x) > TILT_THRESHOLD and abs(x) > abs(y):
        return "RIGHT" if x > 0 else "LEFT"
    if abs(y) > TILT_THRESHOLD and abs(y) > abs(x):
        return "FWD" if y > 0 else "BACK"
    return None

def read_encoder():
    global last_clk, last_btn, enc_pos
    rot = 0
    btn = False
    
    clk = encoder_clk.value
    if clk != last_clk:
        rot = 1 if encoder_dt.value != clk else -1
        last_clk = clk
    
    b = encoder_sw.value
    if not b and last_btn:
        btn = True
    last_btn = b
    
    return rot, btn

# ============================================
# DISPLAY
# ============================================
def show_title():
    g = displayio.Group()
    g.append(label.Label(terminalio.FONT, text="CATCH & COOK!", color=0xFFFFFF, x=20, y=15))
    g.append(label.Label(terminalio.FONT, text="Catch ingredients", color=0xFFFFFF, x=10, y=32))
    g.append(label.Label(terminalio.FONT, text="[Press to Start]", color=0xFFFFFF, x=15, y=55))
    display.root_group = g

def show_mode():
    g = displayio.Group()
    g.append(label.Label(terminalio.FONT, text="SELECT MODE", color=0xFFFFFF, x=30, y=10))
    modes = ["EASY 90s", "MEDIUM 60s", "HARD 45s"]
    for i, m in enumerate(modes):
        pre = "> " if i == game.diff_idx else "  "
        g.append(label.Label(terminalio.FONT, text=pre + m, color=0xFFFFFF, x=20, y=28 + i*12))
    g.append(label.Label(terminalio.FONT, text="[Rotate & Press]", color=0xFFFFFF, x=12, y=60))
    display.root_group = g

def show_intro():
    lv = LEVELS[game.level]
    g = displayio.Group()
    g.append(label.Label(terminalio.FONT, text=f"LEVEL {game.level+1}", color=0xFFFFFF, x=40, y=12))
    g.append(label.Label(terminalio.FONT, text=lv["name"], color=0xFFFFFF, x=10, y=28))
    view = "Side" if lv["view"] == "side" else "Top-Down"
    g.append(label.Label(terminalio.FONT, text=f"View: {view}", color=0xFFFFFF, x=10, y=42))
    g.append(label.Label(terminalio.FONT, text="[Press to Start]", color=0xFFFFFF, x=15, y=58))
    display.root_group = g

def make_rect(w, h, fill=True):
    bmp = displayio.Bitmap(w, h, 2)
    pal = displayio.Palette(2)
    pal[0] = 0x000000
    pal[1] = 0xFFFFFF
    if fill:
        for x in range(w):
            for y in range(h):
                bmp[x, y] = 1
    else:
        for x in range(w):
            bmp[x, 0] = 1
            bmp[x, h-1] = 1
        for y in range(h):
            bmp[0, y] = 1
            bmp[w-1, y] = 1
    return bmp, pal

def show_game():
    lv = LEVELS[game.level]
    g = displayio.Group()
    
    # Status
    g.append(label.Label(terminalio.FONT, text=f"L{game.level+1} {int(game.time_left)}s", color=0xFFFFFF, x=0, y=6))
    
    if lv["view"] == "side":
        # Ground
        bmp, pal = make_rect(128, 2)
        g.append(displayio.TileGrid(bmp, pixel_shader=pal, x=0, y=52))
        # Player
        bmp, pal = make_rect(5, 8)
        g.append(displayio.TileGrid(bmp, pixel_shader=pal, x=game.px-2, y=44))
    else:
        # Border
        bmp, pal = make_rect(128, 42, False)
        g.append(displayio.TileGrid(bmp, pixel_shader=pal, x=0, y=10))
        # Player
        if 5 < game.px < 123 and 14 < game.py < 48:
            bmp, pal = make_rect(7, 3)
            g.append(displayio.TileGrid(bmp, pixel_shader=pal, x=game.px-3, y=game.py-1))
            bmp2, pal2 = make_rect(3, 7)
            g.append(displayio.TileGrid(bmp2, pixel_shader=pal2, x=game.px-1, y=game.py-3))
    
    # Items with ingredient icons
    for item in game.items:
        ix, iy = int(item["x"]), int(item["y"])
        icon_bmp, icon_pal = make_icon(item["name"])
        g.append(displayio.TileGrid(icon_bmp, pixel_shader=icon_pal, x=ix-4, y=iy-4))
    
    # Progress with ingredient icons
    x = 0
    for ing, need in list(game.needed.items())[:3]:
        got = game.collected.get(ing, 0)
        # Small 8x8 icon
        icon_bmp, icon_pal = make_icon(ing)
        g.append(displayio.TileGrid(icon_bmp, pixel_shader=icon_pal, x=x, y=55))
        # Count text
        g.append(label.Label(terminalio.FONT, text=f"{got}/{need}", color=0xFFFFFF, x=x+10, y=60))
        x += 42
    
    display.root_group = g

def show_cooking():
    g = displayio.Group()
    g.append(label.Label(terminalio.FONT, text="COOKING!", color=0xFFFFFF, x=40, y=12))
    g.append(label.Label(terminalio.FONT, text="Rotate encoder!", color=0xFFFFFF, x=20, y=28))
    
    # Bar
    bmp, pal = make_rect(100, 12, False)
    g.append(displayio.TileGrid(bmp, pixel_shader=pal, x=14, y=38))
    
    fw = int((game.cook_progress / 100) * 96)
    if fw > 2:
        bmp2, pal2 = make_rect(fw, 8)
        g.append(displayio.TileGrid(bmp2, pixel_shader=pal2, x=16, y=40))
    
    g.append(label.Label(terminalio.FONT, text=f"{game.cook_progress}%", color=0xFFFFFF, x=52, y=58))
    display.root_group = g

def show_clear():
    lv = LEVELS[game.level]
    g = displayio.Group()
    g.append(label.Label(terminalio.FONT, text="LEVEL CLEAR!", color=0xFFFFFF, x=25, y=18))
    g.append(label.Label(terminalio.FONT, text=f"Made: {lv['dish']}", color=0xFFFFFF, x=10, y=38))
    g.append(label.Label(terminalio.FONT, text="[Press Next]", color=0xFFFFFF, x=25, y=55))
    display.root_group = g

def show_over():
    g = displayio.Group()
    g.append(label.Label(terminalio.FONT, text="GAME OVER", color=0xFFFFFF, x=35, y=22))
    g.append(label.Label(terminalio.FONT, text=f"Level {game.level+1}", color=0xFFFFFF, x=40, y=38))
    g.append(label.Label(terminalio.FONT, text="[Press Retry]", color=0xFFFFFF, x=25, y=55))
    display.root_group = g

def show_win():
    g = displayio.Group()
    g.append(label.Label(terminalio.FONT, text="YOU WIN!", color=0xFFFFFF, x=40, y=18))
    g.append(label.Label(terminalio.FONT, text="MASTER CHEF!", color=0xFFFFFF, x=28, y=35))
    g.append(label.Label(terminalio.FONT, text="[Press Restart]", color=0xFFFFFF, x=20, y=55))
    display.root_group = g

# ============================================
# NEOPIXEL
# ============================================
def px_off():
    pixels.fill(COLOR_OFF)
    pixels.show()

def px_success():
    pixels.fill(COLOR_GREEN)
    pixels.show()
    time.sleep(0.1)
    pixels.fill(COLOR_OFF)
    pixels.show()

def px_fail():
    pixels.fill(COLOR_RED)
    pixels.show()
    time.sleep(0.2)
    pixels.fill(COLOR_OFF)
    pixels.show()

def px_spawn():
    pixels.fill(COLOR_YELLOW)
    pixels.show()
    time.sleep(0.05)
    pixels.fill(COLOR_OFF)
    pixels.show()

def px_complete():
    for c in [COLOR_RED, COLOR_YELLOW, COLOR_GREEN, COLOR_BLUE, COLOR_PURPLE]:
        pixels.fill(c)
        pixels.show()
        time.sleep(0.12)
    pixels.fill(COLOR_OFF)
    pixels.show()

def px_cooking(p):
    n = int((p / 100) * NUM_PIXELS)
    for i in range(NUM_PIXELS):
        pixels[i] = COLOR_BLUE if i < n else COLOR_OFF
    pixels.show()

# ============================================
# GAME LOGIC
# ============================================
def spawn(lv):
    ing, _ = random.choice(lv["ingredients"])
    if lv["view"] == "side":
        x, y = random.choice([15, 113]), 45
    else:
        x = random.randint(15, 113)
        y = random.randint(18, 48)
    
    spd = DIFFICULTY[game.difficulty][1]
    game.items.append({
        "name": ing,
        "x": x, "y": y,
        "vx": random.uniform(-1, 1) * spd,
        "vy": random.uniform(-1, 1) * spd if lv["view"] == "topdown" else 0
    })
    px_spawn()

def update_items(lv):
    for it in game.items:
        it["x"] += it["vx"] * 0.5
        if lv["view"] == "topdown":
            it["y"] += it["vy"] * 0.5
        
        if it["x"] < 10 or it["x"] > 118:
            it["vx"] *= -1
        if lv["view"] == "topdown" and (it["y"] < 15 or it["y"] > 48):
            it["vy"] *= -1

def check_catch():
    caught = []
    for it in game.items:
        if abs(game.px - it["x"]) < 12 and abs(game.py - it["y"]) < 12:
            caught.append(it)
    
    for it in caught:
        game.items.remove(it)
        game.collected[it["name"]] = game.collected.get(it["name"], 0) + 1
        px_success()

def is_complete():
    for ing, need in game.needed.items():
        if game.collected.get(ing, 0) < need:
            return False
    return True

def init_level():
    lv = LEVELS[game.level]
    game.time_left = DIFFICULTY[game.difficulty][0]
    game.px = 64
    game.py = 32 if lv["view"] == "topdown" else 45
    game.collected = {}
    game.needed = {ing: cnt for ing, cnt in lv["ingredients"]}
    game.items = []
    game.cook_progress = 0
    
    for _ in range(3):
        spawn(lv)

def move(m, lv):
    now = time.monotonic()
    if now - game.last_move < MOVE_DEBOUNCE:
        return
    game.last_move = now
    
    spd = 8
    if lv["view"] == "side":
        if m == "LEFT": game.px = max(10, game.px - spd)
        elif m == "RIGHT": game.px = min(118, game.px + spd)
        elif m == "SHAKE": check_catch()
    else:
        if m == "LEFT": game.px = max(10, game.px - spd)
        elif m == "RIGHT": game.px = min(118, game.px + spd)
        elif m == "FWD": game.py = max(15, game.py - spd)
        elif m == "BACK": game.py = min(48, game.py + spd)
        elif m == "SHAKE": check_catch()

# ============================================
# MAIN LOOP
# ============================================
def main():
    print("Catch & Cook Starting...")
    px_off()
    
    spawn_t = 0
    last_t = time.monotonic()
    
    while True:
        now = time.monotonic()
        dt = now - last_t
        last_t = now
        
        rot, btn = read_encoder()
        accel = read_accel()
        
        if game.screen == "title":
            show_title()
            if btn:
                game.screen = "mode"
                time.sleep(0.2)
        
        elif game.screen == "mode":
            if rot:
                game.diff_idx = (game.diff_idx + rot) % 3
            game.difficulty = ["EASY", "MEDIUM", "HARD"][game.diff_idx]
            show_mode()
            if btn:
                game.level = 0
                game.screen = "intro"
                time.sleep(0.2)
        
        elif game.screen == "intro":
            show_intro()
            if btn:
                init_level()
                game.screen = "play"
                spawn_t = 0
                time.sleep(0.2)
        
        elif game.screen == "play":
            lv = LEVELS[game.level]
            game.time_left -= dt
            
            if game.time_left <= 0:
                game.screen = "over"
                px_fail()
                continue
            
            if accel:
                move(accel, lv)
            
            # Auto-catch for side-view levels OR when close enough
            if lv["view"] == "side":
                check_catch()
            # Top-down: need to shake OR auto-catch when very close
            else:
                for it in game.items:
                    if abs(game.px - it["x"]) < 6 and abs(game.py - it["y"]) < 6:
                        check_catch()
                        break
            
            spawn_t += dt
            if spawn_t > 2.0 and len(game.items) < 5:
                spawn(lv)
                spawn_t = 0
            
            update_items(lv)
            show_game()
            
            if is_complete():
                game.screen = "cooking" if lv["cooking"] else "clear"
                if not lv["cooking"]:
                    px_complete()
        
        elif game.screen == "cooking":
            if rot:
                game.cook_progress = min(100, game.cook_progress + abs(rot) * 5)
            px_cooking(game.cook_progress)
            show_cooking()
            if game.cook_progress >= 100:
                game.screen = "clear"
                px_complete()
                time.sleep(0.3)
        
        elif game.screen == "clear":
            show_clear()
            if btn:
                game.level += 1
                game.screen = "win" if game.level >= 12 else "intro"
                time.sleep(0.2)
        
        elif game.screen == "over":
            show_over()
            if btn:
                game.reset()
                time.sleep(0.2)
        
        elif game.screen == "win":
            show_win()
            if btn:
                game.reset()
                time.sleep(0.2)
        
        time.sleep(0.02)

main()
