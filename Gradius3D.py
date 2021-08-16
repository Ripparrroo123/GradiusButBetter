import pygame, sys, pickle
from pygame.locals import *
from random import *
from math import *

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import pywavefront

from gamestates import Gamestate
import objects as obj2D
import objects3D as obj3D

#-------------#global variables
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
BASE_ATTACK = 5
frame_limit = pygame.time.Clock()
inputs = set([])
bullets = [] #active bullets
enemies = [] #active enemies
player = None #the current player so that it is accessible globally 
scores = [] #the text elements for the scoreboard
muted = False
power_ups = []
gamestate = Gamestate.MENU #gamestate, defaults to the start menu
player_score = 0
delta_time = 1
active_boss = False
player_dead = False

#-------------#configs
pygame.init()
display = (SCREEN_WIDTH, SCREEN_HEIGHT)
screen = pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
pygame.display.set_caption(str(gamestate).split('.')[-1])

#render configs
glEnable(GL_LIGHTING)
glEnable(GL_DEPTH_TEST)
glShadeModel(GL_SMOOTH)

#camera
gluPerspective(40, (display[0]/display[1]), 0.1, 50.0)

#light settings
#light 0
glEnable(GL_LIGHT0)
glLight(GL_LIGHT0, GL_POSITION,  (3, 3, 3, 1)) # point light from the left, top, front
glLightfv(GL_LIGHT0, GL_AMBIENT, (0, 0, 0, 1))
glLightfv(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))

glTranslatef(0.0, 0.0, -5)
#-------------#functions
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

    player = Player(600, 300, 50, 0.6, player_model ,bullet_model)

    objects.append(player)
    
    objects.append(EnemyManager(3000))

    game_manager = GameManager(objects)

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

def check_collision2D(hitbox1, hitbox2):
    return hitbox1.colliderect(hitbox2)

def check_collision3D(boundbox1, boundbox2):
    return 

def quit():
    """
    shuts down the game and saves the scores
    """
    pygame.quit
    sys.exit()

#-------------#classes

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
                if event.type == KEYDOWN:
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
        self.velocity = pygame.Vector2(0, 0)
        self.model = model
        self.do_draw = True
        self.model.position = (position_x, position_y, 0)

    # @property
    # def hitbox(self):
    #     hitbox = self.model.get_rect()
    #     hitbox.x = self.position.x
    #     hitbox.y = self.position.y
    #     return hitbox

    def set_sprite(self, new_model):
        self.model = new_model

    # Moves the gameobject
    def update(self, events):
        self.model.translate(self.velocity[0], self.velocity[1], 0)

    def draw(self):
        self.model.draw()

    def destroy(self):
        objects.remove(self)

class Entity(GameObject):

    def __init__(self, position_x, position_y, maxHP, model):

        super().__init__(position_x, position_y, model)

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

    def __init__(self, position_x, position_y, maxHP, move_speed,player_model, bullet_model):

        super().__init__(position_x, position_y, maxHP, model = player_model)

        self._bullet_manager = BulletManager(bullet_model)

        self.move_speed = move_speed

        self._start_shooting_time = None

        self.power = 1

        self._shooting = False

        self._animation_last_time = 0

        self._i = 1

        self._death_time = None

        # self._pulse = False #Set to True for alternate indicator for when big_shoot() is ready

        #Animations
        # self._exp = [explosion_1, explosion_2, explosion_3, explosion_4, explosion_5]

        # self._pulse = [pulse_1, pulse_2, pulse_3, pulse_4, pulse_5, pulse_6, pulse_7, pulse_8, pulse_9, pulse_10, pulse_11, pulse_12, pulse_13, pulse_14]


    def update(self, events):
        super().update(events)

        self._shooting = False

        global player_HP
        player_HP = self._hp/50

        time = pygame.time.get_ticks()
            
        #Alternate shooting types
        for event in events:
            if event.type == KEYDOWN and event.key == K_SPACE:
                self._start_shooting_time = time
                self._bullet_manager.tap_shoot(self.model.position[0], self.model.position[1], self.power)
                self._shooting = True
                self._i = 0
            if event.type == KEYUP:
                if event.key == K_SPACE and self._start_shooting_time:
                    if time - self._start_shooting_time > 1000:
                        self._bullet_manager.big_shoot(self.model.position[0], self.model.position[1], self.power)
                        self._shooting = True
                    self._start_shooting_time = None

        #Regular shoot
        if K_SPACE in keys and not self._shooting:
            self._bullet_manager.shoot(self.model.position[0] + 60, self.model.position[1] + 30, 1, self.power, 1)
            self._shooting = True

        #Visual indicator for when big_shoot() is ready
        # if self._start_shooting_time != None and time - self._start_shooting_time > 1000:
            #Alternate indicator
            # if self._pulse == True:
            #     if time - self._animation_last_time > 20:
            #         self._i += 1
            #         if self._i == 14:
            #             self._i = 0
            #         self._animation_last_time = time
        #         self.sprite = pygame.transform.scale(self._pulse[self._i], (70, 35))

        #     #Standard indicator
        #     else:
        #         self.sprite = pygame.transform.scale(red_player_sprite, (70, 35))
        
        # #Standard appearance
        # else:
        #     self.sprite = pygame.transform.scale(player_sprite, (70, 35))

        #Damage for when you run into an enemy
        # for enemy in enemies:
        #     if check_collision2D(self.hitbox, enemy.hitbox) > 0:
        #         if time - self._last_time > 500:
        #             self.take_damage(1)
        #             self._last_time = time
        
        #Check for and apply powerups
        for power in power_ups:
            if check_collision2D(self.hitbox, power.hitbox) > 0:
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
                quit()

        #render
        if self.do_draw:
            super().draw()

        #If the player just took damage, don't draw them
        elif time - self.last_damage > 50:
            self.do_draw = True

class Enemy(Entity):

    def __init__(self, position_x, position_y, model, bullet_model, points, difficulty):
        
        #The difficulty is slightly randomized for variety
        self._difficulty = difficulty + randint(1, 3)

        super().__init__(position_x, position_y, maxHP = 50 + self._difficulty * 30, model = model)

        self._bullet_manager = BulletManager(bullet_model)

        self._move_speed = 0.1 * self._difficulty

        #Which direction, up or down?
        self._cycle = choice([1, -1])

        self.points = floor(points + difficulty)

        self._last_shot = 0

        self._death_time = None

        self._time = 0

        #Death animation
        # self._exp = [explosion_1, explosion_2, explosion_3, explosion_4, explosion_5]


    def update(self, events):
        super().update(events)

        self._time = pygame.time.get_ticks()

        #spawn behaviour
        if self.model.position[0] > SCREEN_WIDTH*0.8 and self._hp > 0:
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
        if self.model.position[1] > SCREEN_HEIGHT * 0.8:
            self._cycle = -1

        #Getting close to the top of the screen, better turn around
        if self.model.position[1] < SCREEN_HEIGHT * 0.1:
            self._cycle = 1

        #When the enemy is off-screen, destroy them
        if self.model.position[0] < -100:
            enemies.remove(self)
            self.destroy()
        
        #Shoot
        if self._time - self._last_shot > 800 and self._death_time == None:
            self._bullet_manager.shoot(self.model.position[0], self.model.position[1] + 50, direction = -0.5, multiplier = 1 , size = 1)
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
        # self._exp = [explosion_1, explosion_2, explosion_3, explosion_4, explosion_5]

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
                    new_enemy = Enemy(SCREEN_WIDTH, SCREEN_HEIGHT * randint(3, 7) / 10, enemy_model, bullet_model, 5, self._difficulty)
                    enemies.append(new_enemy)
                    objects.append(new_enemy)
                    self._last_time = time
                    self._boss_count += 1
                    self._difficulty += 0.1
                    self.total_count += 1
                elif enemies == []:
                    new_enemy = Boss(SCREEN_WIDTH, SCREEN_HEIGHT * randint(3, 7) / 10, pygame.transform.scale(boss_model, (17 * 5, 40 * 5)), pygame.transform.scale(bullet_model, (10, 5)), floor(randint(1, 3) + self._difficulty))
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
                # if check_collision2D(self.hitbox, enemy.hitbox) > 0 :
                #     if time - self._last_time > 500:
                #         enemy.take_damage(self._damage)
                #         self._last_time = time

                    if self in bullets:
                        bullets.remove(self)
                        super().destroy()

        #self._direction is less than 0 when an enemy or boss fired the bullet
        elif self._direction < 0:

            #Check for collision with player, deal damage, destroy bullet
            # if check_collision2D(self.hitbox, player.hitbox) != 0:
            #     player.take_damage(1)
            #     self._last_time = time

                if self in bullets:
                    bullets.remove(self)
                    super().destroy()

        #If a player bullet goes off-screen, it is deleted
        if self.model.position[0] >= SCREEN_WIDTH + 200:
            bullets.remove(self)
            super().destroy()

        #If an enemy bullet goes off-screen, it is deleted
        if self.model.position[1] < -100:
            bullets.remove(self)
            super().destroy()
        
class BulletManager:
    
    def __init__(self, model):
        self._last_time = pygame.time.get_ticks()
        self.model = model

    #Function that can be called by either the player or an enemy/boss
    def shoot(self, origin_x, origin_y, direction, multiplier, size):
        time = pygame.time.get_ticks()

        if time > self._last_time + 150:
            if not muted:    
                shoot_sound.play()

            model = self.model
                
            temp = Bullet(origin_x, origin_y, direction, model, multiplier)

            bullets.append(temp)
            objects.append(temp)
            self._last_time = time
    
    def tap_shoot(self, origin_x, origin_y, multiplier):
        time = pygame.time.get_ticks()

        if not muted:    
            shoot_sound.play()

        model = self.model
        damage = 2 * multiplier
            
        temp = Bullet(origin_x + 60, origin_y + 30, 1, model, damage)

        bullets.append(temp)
        objects.append(temp)
        self._last_time = time

    def big_shoot(self, origin_x, origin_y, multiplier):
        if not muted:    
            shoot_sound.play()

        model = self.model
        damage = 5 * multiplier
            
        temp = Bullet(origin_x, origin_y + 30, 1, model, damage)

        bullets.append(temp)
        objects.append(temp)

class PowerUp(GameObject):
    def __init__(self, origin_x, origin_y):
        self.type = choice(["Speed", "Power"])
        if self.type == "Power":
            super().__init__(origin_x, origin_y, pygame.transform.scale(power_up_model, (18 * 5, 9 * 5)))
        elif self.type == "Speed":
            super().__init__(origin_x, origin_y, pygame.transform.scale(speed_up_model, (18 * 5, 9 * 5)))
    
    def update(self, events):
        self.draw()


#-------------#assets
try: 
    #models
    player_model = obj3D.Open(pywavefront.Wavefront('./Models/ship.obj', parse=True))
    print(player_model)
    bullet_model = obj3D.Open(pywavefront.Wavefront('./Models/bullet.obj', parse=True))
    power_up_model = obj3D.Open(pywavefront.Wavefront('./Models/power_up.obj', parse=True))
    speed_up_model = obj3D.Open(pywavefront.Wavefront('./Models/speed_up.obj', parse=True))
    enemy_model = obj3D.Open(pywavefront.Wavefront('./Models/enemy.obj', parse=True))
    boss_model = obj3D.Open(pywavefront.Wavefront('./Models/boss.obj', parse=True))

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

#managers
game_manager = None

while True:
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    
    events = pygame.event.get()
   
    #if currently playing
    if game_manager:
        game_manager.update(events)
        # #stat displays that need live updating
        # obj2D.Text(20, 20, screen, f'Score:{player_score}', font_joystix, 20, pygame.Color(255,255,255)).render()
        # obj2D.Text(20, 60, screen, 'Power:{:.1f}'.format(player.power), font_joystix, 20, pygame.Color(255,255,255)).render()
        # obj2D.Text(200, 60, screen, 'Speed:{:.1f}'.format(player.move_speed), font_joystix, 20, pygame.Color(255,255,255)).render()
        
        # #Healthbar
        # pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(18, 118, 204, 29))
        # pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(20, 120, 200, 25))
        # pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(20, 120, 100 * player_HP*2, 25))

    else:
        start_game()

    pygame.display.flip()

    frame_limit.tick(60)


