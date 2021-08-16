#imports and constants
import pygame, sys, pickle
from pygame.locals import *
from random import *
from math import *

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import pywavefront

from pygame.time import Clock
from gamestates import Gamestate
import objects as obj

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
BASE_ATTACK = 5

#Lists for global management
scores = [] #the text elements for the scoreboard
player_score = 0 #the current score the player has achieved 
player_HP = 1 
objects = [] #All active objects. Everything that gets updated each frame
keys = set([]) #a set for the input keys, stops duplicate entries
bullets = [] #active bullets
enemies = [] #active enemies
power_ups = [] #power-up hitboxes
gamestate = Gamestate.MENU #gamestate, defaults to the start menu
delta_time = 1 #default delta
frame_limit = Clock()
muted = False
stop = False
name = ''
player = None #the current player so that it is accessible globally 
active_boss = False
player_dead = False #stops the game as the player dies

#--------------------
#classes, functions, gameobjects and methods

def start_game():
    """
    initiates the elements needed for the game to launch and then changes the gamestate into running
    also resets the elements for a clean run
    """
    global player_score
    global game_manager
    global objects
    global keys
    global bullets
    global enemies
    global stop
    global player
    global active_boss
    global player_dead
    
    player_dead = False
    active_boss = False
    player_score = 0
    stop = False
    objects = []
    keys = set([])
    bullets = []
    enemies = []
    pygame.mixer.music.stop()

    if not muted:
        pygame.mixer.music.play(-1,0.0)

    player = Player(600, 300, 50, 0.6, bullet_sprite)

    objects.append(player)
    
    objects.append(EnemyManager(3000))

    game_manager = GameManager(objects)

    #objects.append(EnvironmentManager(60, 30))

    pass

def stop_game():
    """
    resets the game variables and objects
    """
    global objects
    global keys
    global bullets
    global enemies
    global power_ups
    global game_manager
    global stop

    stop = True
    objects = []
    keys = set([])
    bullets = []
    enemies = []
    power_ups = []
    game_manager = None
    pygame.mixer.music.stop()

    pass

def render_scores(da_screen, scores, positions):
    """
    creates an array of renderable text objects
    """
    score_render = []
    for index in range(10):
        #creates a new text element in set positions based on score 
        score_render.append(obj.Text(positions[index][0], positions[index][1], da_screen, '{findex}. {name} - {score}'.format(findex = index, name = scores[index]["name"], score = scores[index]["score"]), font_joystix, 24), )

    return score_render

def if_highscore():
    """
    checks if the score achieved is worth displaying or not
    """
    global scores
    global player_score
    global name

    for i, entry in enumerate(scores):
        if player_score >= int(entry['score']):
            return True

    return False

def update_score():
    """
    checks if the player scored higher than any of the current scores and then puts them on the scoreboard
    """
    global scores
    global player_score
    global name
    
    for i, entry in enumerate(scores):
        #if current achieved score is larger than a stored score
        if player_score >= int(entry['score']):
            #insert the current score in front of the score as it is larger or equal
            scores.insert(i,{'name': name, 'score': player_score})
            scores.pop(len(scores)-1)
            name = ''
            return

def load_scores():
    """
    unpacks the scores from the pickle file, if no score has been saved it creates a new scoreboard and a new pickle file with that scoreboard
    """
    
    try:
        #checks if the save file is here
        with open('save.pickle', 'rb') as save:
            scores = pickle.load(save)

    except:
        #creates a save file in the case of no save file
        with open('save.pickle', 'wb') as file:

            #creates 10 of the scoreboard values 
            initial_scores = [{'name': 'ABC', 'score': '0'} for x in range(10)]

            pickle.dump(initial_scores, file)
            scores = initial_scores

    return scores

def save_scores():
    """
    writes the current scores down into the pickle file
    """
    global scores

    with open('save.pickle', 'wb') as file:
        #saves whatever is in the scores into the file
        pickle.dump(scores, file)

def check_collision(hitbox1, hitbox2):
    return hitbox1.colliderect(hitbox2)

def change_gamestate(new_state):
    """
    changes the gamestate and window caption
    """
    global gamestate
    pygame.display.set_caption(str(new_state).split('.')[-1])
    gamestate = new_state

def quit():
    """
    shuts down the game and saves the scores
    """
    save_scores()
    pygame.quit
    sys.exit()

class MenuManager:
    """
    manage menu assets and assets, button functions and rendering 
    """
    def __init__(self, buttons, images, labels):
        self._buttons = buttons
        self._images = images
        self.labels = labels

    #player control
    def update(self, events):
        for event in events:
            if event.type == MOUSEBUTTONUP:
                #checks if the mouse clicked a button
                for button in self._buttons:
                    if button.is_clicked(event.pos):
                        button.click()
                continue

        for buttons in self._buttons:
            buttons.render()

        for image in self._images:
            image.render()
            
        for label in self.labels:
            label.render()

class GameManager:
    """
    manages game assets such as the player and the enemies 
    """
    def __init__(self, objects):
        global stop

        self._objects = objects
        self._last_time = pygame.time.get_ticks()


    #player control
    def update(self, events):
        global keys

        if player_dead == False:
            
            for event in events:
                if event.type == KEYDOWN and event.key not in keys:
                    keys.add(event.key)
                    continue 
                elif event.type == KEYUP and event.key in keys:
                    keys.remove(event.key)
                    
            for object in self._objects:
                object.update(events)
                if stop:
                    return True
                    
        else:
            #this stops the explosion from the player dying from moving 
            keys = set([])
            player.update(events)
        
        #delta_time is the amount of time that the last frame took to compute, it is used to make movement consistent despite any changes in framrate
        global delta_time
        delta_time = (pygame.time.get_ticks() - self._last_time)
        self._last_time = pygame.time.get_ticks()

class GameObject:
    
    def __init__(self, position_x, position_y, model):
        self.position = pygame.Vector2(position_x, position_y)
        self.velocity = pygame.Vector2(0, 0)
        self.model = model
        self.do_draw = True

    @property
    def hitbox(self):
        hitbox = self.model.get_rect()
        hitbox.x = self.position.x
        hitbox.y = self.position.y
        return hitbox

    def set_sprite(self, new_sprite):
        self.model = new_sprite

    # Moves the gameobject
    def update(self, events):
        self.position += self.velocity

    def draw(self):
        global screen
        screen.blit(self.model,self.position)

    def destroy(self):
        objects.remove(self)

class Entity(GameObject):

    def __init__(self, position_x, position_y, maxHP, sprite):

        super().__init__(position_x, position_y, sprite)

        self._maxHP = maxHP
        self._hp = maxHP

        self._last_time = 0

        self.last_damage = 0


    def take_damage(self, damage):
        self._hp = max(0, self._hp - (randint(1, 10) + BASE_ATTACK) * damage)

        #Used for the damage effect
        self.last_damage = pygame.time.get_ticks()
        self.do_draw = False


    def heal(self):
        self._hp = min(self._maxHP, self._hp + randint(5, 10))

class Player(Entity):

    def __init__(self, position_x, position_y, maxHP, move_speed, bullet_model):

        super().__init__(position_x, position_y, maxHP, sprite = player_model)

        self._bullet_manager = BulletManager(bullet_model)

        self.move_speed = move_speed

        self._start_shooting_time = None

        self.power = 1

        self._shooting = False

        self._animation_last_time = 0

        self._i = 1

        self._death_time = None

        self._pulse = False #Set to True for alternate indicator for when big_shoot() is ready

        #Animations
        # self._exp = [explosion_1, explosion_2, explosion_3, explosion_4, explosion_5]

        # self._pulse = [pulse_1, pulse_2, pulse_3, pulse_4, pulse_5, pulse_6, pulse_7, pulse_8, pulse_9, pulse_10, pulse_11, pulse_12, pulse_13, pulse_14]


    def update(self, events):
        super().update(events)

        self._shooting = False

        global player_HP
        player_HP = self._hp/50

        time = pygame.time.get_ticks()

        #up
        if keys & {K_UP, K_w}:
            self.model.translate(0, 0.1, 0)
        #left
        if keys & {K_LEFT, K_a}:
            self.model.translate(-0.1, 0, 0)
        #down
        if keys & {K_DOWN, K_s}:
            self.model.translate(0, -0.1, 0)
        #right
        if keys & {K_RIGHT, K_d}:
            self.model.translate(0.1, 0, 0)
            
        #Alternate shooting types
        for event in events:
            if event.type == KEYDOWN and event.key == K_SPACE:
                self._start_shooting_time = time
                self._bullet_manager.tap_shoot(self.position.x, self.position.y, self.power)
                self._shooting = True
                self._i = 0
            if event.type == KEYUP:
                if event.key == K_SPACE and self._start_shooting_time:
                    if time - self._start_shooting_time > 1000:
                        self._bullet_manager.big_shoot(self.position.x, self.position.y, self.power)
                        self._shooting = True
                    self._start_shooting_time = None

        #Regular shoot
        if K_SPACE in keys and not self._shooting:
            self._bullet_manager.shoot(self.position.x + 60, self.position.y + 30, 1, self.power, 1)
            self._shooting = True

        #Visual indicator for when big_shoot() is ready
        if self._start_shooting_time != None and time - self._start_shooting_time > 1000:
            #Alternate indicator
            if self._pulse == True:
                if time - self._animation_last_time > 20:
                    self._i += 1
                    if self._i == 14:
                        self._i = 0
                    self._animation_last_time = time
                self.sprite = pygame.transform.scale(self._pulse[self._i], (70, 35))

            #Standard indicator
            else:
                self.sprite = pygame.transform.scale(red_player_sprite, (70, 35))
        
        #Standard appearance
        else:
            self.sprite = pygame.transform.scale(player_sprite, (70, 35))

        #Damage for when you run into an enemy
        for enemy in enemies:
            if check_collision(self.hitbox, enemy.hitbox) > 0:
                if time - self._last_time > 500:
                    self.take_damage(1)
                    self._last_time = time
        
        #Check for and apply powerups
        for power in power_ups:
            if check_collision(self.hitbox, power.hitbox) > 0:
                if power.type == "Speed":
                    self.move_speed += 0.1
                if power.type == "Power":
                    self.power += 0.2
                if not muted:
                    player_power.play()
                power.destroy()
                power_ups.remove(power)
                self.heal()

        #player die
        if self._hp < 1:
            global player_dead
            player_dead = True

            #Only happens the first frame after the player dies
            if self._death_time == None:
                self._death_time = time

            #Death animation
            if time - self._death_time < 600:
                stage = min((time - self._death_time) // 100, 4)
                self.sprite = self._exp[stage]
            
            #Actual end of the run
            else:
                #check if score is able to be put on scoreboard
                if if_highscore():
                    change_gamestate(Gamestate.GAME_OVER)            
                else:
                    change_gamestate(Gamestate.SCOREBOARD)            
                stop_game()

                return True

        #render
        if self.do_draw:
            super().draw()

        #If the player just took damage, don't draw them
        elif time - self.last_damage > 50:
            self.do_draw = True

class Enemy(Entity):

    def __init__(self, position_x, position_y, sprite, bullet_sprite, points, difficulty):
        
        #The difficulty is slightly randomized for variety
        self._difficulty = difficulty + randint(1, 3)

        super().__init__(position_x, position_y, maxHP = 50 + self._difficulty * 30, sprite = sprite)

        self._bullet_manager = BulletManager(bullet_sprite)

        self._move_speed = 0.1 * self._difficulty

        #Which direction, up or down?
        self._cycle = choice([1, -1])

        self.points = floor(points + difficulty)

        self._last_shot = 0

        self._death_time = None

        self._time = 0

        #Death animation
        self._exp = [explosion_1, explosion_2, explosion_3, explosion_4, explosion_5]


    def update(self, events):
        super().update(events)

        self._time = pygame.time.get_ticks()

        #spawn behaviour
        if self.position.x > SCREEN_WIDTH*0.8 and self._hp > 0:
            self.velocity.x = -1 * self._move_speed * delta_time
            self.velocity.y = self._move_speed * self._cycle / 2 * delta_time

        #live behaviour
        elif self._hp > 0:
            self.velocity.x = -0.4 * self._move_speed * delta_time
            self.velocity.y = self._move_speed * self._cycle / 2 * delta_time

        #die
        else:
            self.velocity = pygame.Vector2(0, 0)
            #Explosion
            global player_score
            player_score += self.points
            if self._death_time == None:
                self._death_time = self._time
                if not muted:
                    enemy_explode.play()
                self._bullet_manager = None
                enemies.remove(self)
            self.die()

        #Getting close to the bottom of the screen, better turn around
        if self.position.y > SCREEN_HEIGHT * 0.8:
            self._cycle = -1

        #Getting close to the top of the screen, better turn around
        if self.position.y < SCREEN_HEIGHT * 0.1:
            self._cycle = 1

        #When the enemy is off-screen, destroy them
        if self.position.x < -100:
            enemies.remove(self)
            self.destroy()
        
        #Shoot
        if self._time - self._last_shot > 800 and self._death_time == None:
            self._bullet_manager.shoot(self.position.x, self.position.y + 50, direction = -0.5, multiplier = 1 , size = 1)
            self._last_shot =self._time

        #Render
        if self.do_draw:
            super().draw()

        #If the enemy just took damage, don't draw them
        elif self._time - self.last_damage > 50:
            self.do_draw = True

    #Death animation, then destruction
    def die(self):
        stage = min((self._time - self._death_time) // 100, 4)
        if self._time - self._death_time < 600:
            self.sprite = self._exp[stage]
        else:
            if randint(1, 100) < 10:
                temp = PowerUp(self.position.x, self.position.y)
                objects.append(temp)
                power_ups.append(temp)
            super().destroy()

class Boss(Entity):
    def __init__(self, position_x, position_y, sprite, bullet_sprite, difficulty):
        super().__init__(position_x, position_y, maxHP = 300 * difficulty, sprite = sprite)

        self.bullet_sprite = bullet_sprite

        self._bullet_manager = BulletManager(bullet_sprite)

        self._difficulty = difficulty

        self.points = 10 * self._difficulty
        
        self._move_speed = self._difficulty / 10

        self._last_shot = 0

        self._death_time = None

        self._time = 0

        self._shoot_speed = 1500  / self._difficulty

        #Death animation
        self._exp = [explosion_1, explosion_2, explosion_3, explosion_4, explosion_5]

    def update(self, events):
        super().update(events)

        self._time = pygame.time.get_ticks()

        #spawn behaviour
        if self.position.x > SCREEN_WIDTH*0.8 and self._hp > 0:
            self.velocity.x = -1 * self._move_speed * delta_time
            #y position uses linear interpolation. Just pretend we remembered the syntax for Pygame's Lerp thing and didn't write it ourself!
            self.velocity.y = self._move_speed * (player.position.y - 60 - self.position.y) / 300 / self._difficulty * delta_time
        
        #live behaviour
        elif self._hp > 0:
            self.velocity.x = 0
            #y position uses linear interpolation. Just pretend we remembered the syntax for Pygame's Lerp thing and didn't write it ourself!
            self.velocity.y = self._move_speed * (player.position.y - 75 - self.position.y) / 100 / self._difficulty * delta_time
        
        #die
        else:
            self.velocity = pygame.Vector2(0, 0)
            global player_score
            player_score += self.points
            if self._death_time == None:
                self._death_time = self._time
                if not muted:
                    enemy_explode.play()
                self._bullet_manager = None
                enemies.remove(self)
            self.die()
        
        #Shoot
        if self._time - self._last_shot > self._shoot_speed and self._death_time == None:
            self._bullet_manager.shoot(self.position.x-100, self.position.y + 100, -0.75, self._difficulty, 3)
            self._last_shot =self._time

        #Render
        if self.do_draw:
            super().draw()

        #If the boss just took damage, don't draw them
        elif self._time - self.last_damage > 50:
            self.do_draw = True
    
    #Death animation, then destroy
    def die(self):
        stage = min((self._time - self._death_time) // 100, 4)
        if self._time - self._death_time < 600:
            self.sprite = self._exp[stage]
        else:
            if randint(1, 100) < 90:
                temp = PowerUp(self.position.x, self.position.y)
                objects.append(temp)
                power_ups.append(temp)
            global active_boss
            active_boss = False
            super().destroy()

class EnemyManager:

    def __init__(self, interval):

        #The spawn interval can be randomized. We don't though...
        if interval == 'random':
            self._interval = randint(1000, 20000)
        else:
            self._interval = interval

        self._last_time = 0

        self.total_count = 0

        self._difficulty = 0

        #How many enemies since the last boss?
        self._boss_count = 0

        #How many enemies between each boss?
        self._boss_interval = 10


    def update(self, events):
        global enemies
        global active_boss
        time = pygame.time.get_ticks()

        if not active_boss:    
            if time - self._last_time > self._interval:
                if self._boss_count != self._boss_interval:
                    new_enemy = Enemy(SCREEN_WIDTH, SCREEN_HEIGHT * randint(3, 7) / 10, pygame.transform.scale(enemy_sprite, (100, 100)), pygame.transform.scale(bullet_sprite, (10, 5)), 5, self._difficulty)
                    enemies.append(new_enemy)
                    objects.append(new_enemy)
                    self._last_time = time
                    self._boss_count += 1
                    self._difficulty += 0.1
                    self.total_count += 1
                elif enemies == []:
                    new_enemy = Boss(SCREEN_WIDTH, SCREEN_HEIGHT * randint(3, 7) / 10, pygame.transform.scale(boss_sprite, (17 * 5, 40 * 5)), pygame.transform.scale(bullet_sprite, (10, 5)), floor(randint(1, 3) + self._difficulty))
                    enemies.append(new_enemy)
                    objects.append(new_enemy)
                    self._last_time = time
                    active_boss = True
                    self._boss_count = 0
                    self._boss_interval = randint(5, 15)
                    self._difficulty += 1
                    self.total_count += 1

class Bullet(GameObject):

    def __init__(self, position_x, position_y, direction, sprite, damage):
        super().__init__(position_x, position_y, sprite)

        self._direction = direction

        self._damage = damage

        self._last_time = 0


    def update(self, events):
        super().update(events)
        super().draw()
        global enemies
        time = pygame.time.get_ticks()
        self.velocity.x = self._direction * 3 * delta_time

        #self._direction is 1 when the player fired the bullet
        if self._direction == 1:

            #Check for colliding enemies, deal damage, destroy bullet
            for enemy in enemies:
                if check_collision(self.hitbox, enemy.hitbox) > 0 :
                    if time - self._last_time > 500:
                        enemy.take_damage(self._damage)
                        self._last_time = time

                    if self in bullets:
                        bullets.remove(self)
                        super().destroy()

        #self._direction is less than 0 when an enemy or boss fired the bullet
        elif self._direction < 0:

            #Check for collision with player, deal damage, destroy bullet
            if check_collision(self.hitbox, player.hitbox) != 0:
                player.take_damage(1)
                self._last_time = time

                if self in bullets:
                    bullets.remove(self)
                    super().destroy()

        #If a player bullet goes off-screen, it is deleted
        if self.position.x >= SCREEN_WIDTH + 200:
            bullets.remove(self)
            super().destroy()

        #If an enemy bullet goes off-screen, it is deleted
        if self.position.x < -100:
            bullets.remove(self)
            super().destroy()
        
class BulletManager:
    
    def __init__(self, sprite):
        self._last_time = pygame.time.get_ticks()
        self.sprite = sprite

    #Function that can be called by either the player or an enemy/boss
    def shoot(self, origin_x, origin_y, direction, multiplier, size):
        time = pygame.time.get_ticks()

        if time > self._last_time + 150:
            if not muted:    
                shoot_sound.play()

            sprite = pygame.transform.scale(self.sprite, (10 * size, 5 * size))
                
            temp = Bullet(origin_x, origin_y, direction, sprite, multiplier)

            bullets.append(temp)
            objects.append(temp)
            self._last_time = time
    
    def tap_shoot(self, origin_x, origin_y, multiplier):
        time = pygame.time.get_ticks()

        if not muted:    
            shoot_sound.play()

        sprite = pygame.transform.scale(self.sprite, (20, 10))
        damage = 2 * multiplier
            
        temp = Bullet(origin_x + 60, origin_y + 30, 1, sprite, damage)

        bullets.append(temp)
        objects.append(temp)
        self._last_time = time

    def big_shoot(self, origin_x, origin_y, multiplier):
        if not muted:    
            shoot_sound.play()

        sprite = pygame.transform.scale(self.sprite, (50, 25))
        damage = 5 * multiplier
            
        temp = Bullet(origin_x, origin_y + 30, 1, sprite, damage)

        bullets.append(temp)
        objects.append(temp)

class PowerUp(GameObject):
    def __init__(self, origin_x, origin_y):
        self.type = choice(["Speed", "Power"])
        if self.type == "Power":
            super().__init__(origin_x, origin_y, pygame.transform.scale(power_up_sprite, (18 * 5, 9 * 5)))
        elif self.type == "Speed":
            super().__init__(origin_x, origin_y, pygame.transform.scale(speed_up_sprite, (18 * 5, 9 * 5)))
    
    def update(self, events):
        self.draw()

#--------------------
#gameloops and assembly

#Initializing
pygame.init()

#Screen options
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(str(gamestate).split('.')[-1])

## game assets
try:
    #sprite for the bullet
    bullet_sprite = pywavefront.Wavefront('./Models/bullet.obj').parse()

    #player sprite and assembly
    player_model = pywavefront.Wavefront('./Models/ship.obj').parse()
    #use coloring
    # red_player_sprite = pygame.image.load('Sprites/Red_Player.png').convert_alpha()

    # #Pulse animation for alternate indicator for big_shoot() being ready
    # pulse_1 = pygame.image.load('Sprites/Pulse1.png').convert_alpha()
    # pulse_2 = pygame.image.load('Sprites/Pulse2.png').convert_alpha()
    # pulse_3 = pygame.image.load('Sprites/Pulse3.png').convert_alpha()
    # pulse_4 = pygame.image.load('Sprites/Pulse4.png').convert_alpha()
    # pulse_5 = pygame.image.load('Sprites/Pulse5.png').convert_alpha()
    # pulse_6 = pygame.image.load('Sprites/Pulse6.png').convert_alpha()
    # pulse_7 = pygame.image.load('Sprites/Pulse7.png').convert_alpha()
    # pulse_8 = pygame.image.load('Sprites/Pulse8.png').convert_alpha()
    # pulse_9 = pygame.image.load('Sprites/Pulse9.png').convert_alpha()
    # pulse_10 = pygame.image.load('Sprites/Pulse10.png').convert_alpha()
    # pulse_11 = pygame.image.load('Sprites/Pulse11.png').convert_alpha()
    # pulse_12 = pygame.image.load('Sprites/Pulse12.png').convert_alpha()
    # pulse_13 = pygame.image.load('Sprites/Pulse13.png').convert_alpha()
    # pulse_14 = pygame.image.load('Sprites/Pulse14.png').convert_alpha()

    #Powerup sprites. Originally, both types were going to have the same sprite, that's why the first one is just calle PowerUp
    power_up_sprite = pywavefront.Wavefront('./Models/power_up.obj').parse()
    speed_up_sprite = pywavefront.Wavefront('./Models/speed_up.obj').parse()

    #enemy sprites
    enemy_sprite = pywavefront.Wavefront('./Models/enemy.obj').parse()
    boss_sprite = pywavefront.Wavefront('./Models/boss.obj').parse()

    # #explosion stages
    # explosion_1 = pygame.transform.scale(pygame.image.load('Sprites/Exp1.png').convert_alpha(), (4 * 5, 3 * 5))
    # explosion_2 = pygame.transform.scale(pygame.image.load('Sprites/Exp2.png').convert_alpha(), (6 * 5, 5 * 5))
    # explosion_3 = pygame.transform.scale(pygame.image.load('Sprites/Exp3.png').convert_alpha(), (8 * 5, 7 * 5))
    # explosion_4 = pygame.transform.scale(pygame.image.load('Sprites/Exp4.png').convert_alpha(), (20 * 5, 20 * 5))
    # explosion_5 = pygame.transform.scale(pygame.image.load('Sprites/Exp5.png').convert_alpha(), (20 * 5, 20 * 5))

    #audio
    shoot_sound = pygame.mixer.Sound('audio/player_shoot.wav')
    shoot_sound.set_volume(0.1)
    player_power = pygame.mixer.Sound('audio/power.wav')
    player_power.set_volume(0.5)
    enemy_explode = pygame.mixer.Sound('audio/enemy_explosion.wav')
    enemy_explode.set_volume(0.1)
    pygame.mixer.music.load('audio/Concert_Of_The_Aerogami.wav')

    #fonts
    font_joystix = 'fonts/joystix monospace.ttf'
    font_gomarice = 'fonts/gomarice_no_continue.ttf'

except Exception as e:
    print('Not all assets could be loaded: ' + str(e) + ' at line ' + str(e.__traceback__.tb_lineno))


## menu assets
menu_buttons = []
menu_buttons.append(obj.Button(lambda:change_gamestate(Gamestate.RUNNING),(SCREEN_WIDTH//2)-100,250,screen, ' Start! ', font_gomarice, 80, pygame.Color(255,255,255), pygame.Color(120,120,120))) # button to start the game
menu_buttons.append(obj.Button(quit,(SCREEN_WIDTH//2)-80,470,screen, ' QUIT ', font_gomarice, 80, pygame.Color(255,255,255), pygame.Color(120,120,120))) # button to shut down the game
menu_buttons.append(obj.Button(lambda:change_gamestate(Gamestate.SCOREBOARD),(SCREEN_WIDTH//2)-100,360,screen, ' Score ', font_gomarice, 80, pygame.Color(255,255,255), pygame.Color(120,120,120))) # button to shut down the game
menu_images = []
menu_labels = []
menu_labels.append(obj.Text(200,50,screen,'The paper plane that could!', font_joystix,40,pygame.Color(255,255,255)))

##scoreboard assets
scoreboard_buttons = []
scoreboard_buttons.append(obj.Button(lambda:change_gamestate(Gamestate.MENU), 380, 500, screen, ' Menu ', font_gomarice, 80, pygame.Color(255,255,255),pygame.Color(120,120,120)))
scoreboard_buttons.append(obj.Button(lambda:change_gamestate(Gamestate.RUNNING), 680, 500, screen, ' Play ', font_gomarice, 80, pygame.Color(255,255,255),pygame.Color(120,120,120)))

scoreboard_images = []
#no images :(

scoreboard_label_positions = [(290,100), (290,150), (290,200), (290,250), (290,300), (660,100), (660,150), (660,200), (660,250), (660,300)]
scores = load_scores()
scoreboard_labels = render_scores(screen, scores, scoreboard_label_positions)

#managers
main_menu = MenuManager(menu_buttons, menu_images, menu_labels)
scoreboard_menu = MenuManager(scoreboard_buttons, scoreboard_images, scoreboard_labels)
game_manager = None


#Game Loop
while True:
    #fills the screen with black to clean it
    screen.fill((0, 0, 0))
    events = pygame.event.get()

    if gamestate == Gamestate.MENU:
        main_menu.update(events)

    elif gamestate == Gamestate.GAME_OVER:
        #display name on the screen
        obj.Text(300, 80, screen, f'FINAL SCORE:{player_score}', font_gomarice, 100, pygame.Color(255,255,255)).render()
        obj.Text(480,300,screen,f'Name:{name}', font_gomarice, 50, pygame.Color(255,255,255)).render()

    elif gamestate == Gamestate.SCOREBOARD:

        scoreboard_menu.labels = render_scores(screen, scores, scoreboard_label_positions)

        scoreboard_menu.update(events)
    
    #if currently playing
    elif gamestate == Gamestate.RUNNING:
        if game_manager:
            game_manager.update(events)
            #stat displays that need live updating
            obj.Text(20, 20, screen, f'Score:{player_score}', font_joystix, 20, pygame.Color(255,255,255)).render()
            obj.Text(20, 60, screen, 'Power:{:.1f}'.format(player.power), font_joystix, 20, pygame.Color(255,255,255)).render()
            obj.Text(200, 60, screen, 'Speed:{:.1f}'.format(player.move_speed), font_joystix, 20, pygame.Color(255,255,255)).render()
            
            #Healthbar
            pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(18, 118, 204, 29))
            pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(20, 120, 200, 25))
            pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(20, 120, 100 * player_HP*2, 25))

        else:
            start_game()


    #global events
    for event in events:

        #closes the game
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE and gamestate == Gamestate.MENU):
            quit()


        if event.type == KEYDOWN:

            #global mute, except for in the name entry
            if event.key == K_m and gamestate != Gamestate.GAME_OVER:
                muted = not muted
                if muted:
                    pygame.mixer.music.stop()
                else:
                    pygame.mixer.music.play(-1,0.0)

            #if currently viewing the main menu
            elif gamestate == Gamestate.MENU :
                #get into the game from the menu
                if event.key == K_RETURN:
                    change_gamestate(Gamestate.RUNNING)

            #if the game is running
            elif gamestate == Gamestate.RUNNING:
                if event.type == KEYDOWN:
                    #restart game when playing
                    if  event.key == K_r:
                        start_game()
                    
                    #quit game mid game
                    if event.key == K_ESCAPE:
                        stop_game()
                        change_gamestate(Gamestate.MENU)

                    #turn off audio
                    if event.key == K_m:
                        muted = not muted
                        if muted:
                            pygame.mixer.music.stop()
                        else:
                            pygame.mixer.music.play(-1,0.0)

            #currently viewing the scoreboard
            elif gamestate == Gamestate.SCOREBOARD:
                #go to menu from scoreboard
                if event.key == K_ESCAPE:
                    change_gamestate(Gamestate.MENU)
                
                #launches the game from the scoreboard
                if event.key == K_RETURN:
                    change_gamestate(Gamestate.RUNNING)
            
            #currently at the name entry
            elif gamestate == Gamestate.GAME_OVER:
                #accept the name and go to scoreboard
                if event.key == K_RETURN and len(name.strip()) > 2:
                    name = name.strip()
                    change_gamestate(Gamestate.SCOREBOARD)
                    update_score()
                    
                #backspace function
                elif event.key == K_BACKSPACE:
                    name = name[:-1]
                    
                #add key to name
                elif len(name) < 6:
                    #print(event.unicode)
                    name += event.unicode
            
    frame_limit.tick(60)
                          
    pygame.display.update()