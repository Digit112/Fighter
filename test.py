import sys
import pygame as pg
from fighter import *

pg.init()

width = 1600
height = 900

s = pg.display.set_mode((width, height))

# Define Hitboxes, Stances, Attacks, & Connections
standing_hb = Hitbox(Rectangle(-12, -75, 12, 0))

Standing = stance(standing_hb)
Jab1 = stance(standing_hb, Standing, 6)
Jab2 = stance(standing_hb, Standing, 6)

atk_anim1 = collider_anim()
atk_anim1.add_col(Rectangle(12, -55, 22, -45), 4, 0)
atk_anim1.add_col(Rectangle(12, -55, 42, -45), 4, 2)
atk_anim1.add_col(Rectangle(12, -55, 42, -45), 4, 4)

atk_anim2 = collider_anim()
atk_anim2.add_col(Rectangle(12, -45, 22, -35), 4, 0)
atk_anim2.add_col(Rectangle(12, -45, 42, -35), 4, 2)
atk_anim2.add_col(Rectangle(12, -45, 42, -35), 4, 4)

atk_anim3 = collider_anim()
atk_anim3.add_col(Rectangle(12, -50, 12, -40), 8, 4)
atk_anim3.add_col(Rectangle(12, -50, 47, -40), 8, 7)
atk_anim3.add_col(Rectangle(12, -50, 47, -40), 8, 10)

atk1 = attack(4)
atk1.add_anim(atk_anim1)

atk2 = attack(4)
atk2.add_anim(atk_anim2)

atk3 = attack(10)
atk3.add_anim(atk_anim3)

Standing.add_connection(Jab1, fighter.BASIC, transition_time=4, time_in=3, time_out=None, atk=atk1)
Jab1.add_connection(Jab2, fighter.BASIC, transition_time=4, time_in=3, time_out=None, atk=atk2)
Jab2.add_connection(Standing, fighter.BASIC, transition_time=10, time_in=3, time_out=None, atk=atk3)

f = fight()
f.add_platform(pg.Rect(-500, 300, 1000, 20))
f.add_platform(pg.Rect(-400, 150, 200, 20))
f.add_platform(pg.Rect(200, 150, 200, 20))

f.add_fighter(pg.Rect(-12, -75, 24, 75), Standing, team=0)
f.add_fighter(pg.Rect(-12, -75, 24, 75), Standing, team=1)
f.fighters[0].pos.x = -300
f.fighters[1].pos.x = 300

cam = camera((-width//2, -height//2, width, height), s)

clk = pg.time.Clock()

while True:
	clk.tick(30)

	for event in pg.event.get():
		if event.type == pg.QUIT:
			sys.exit()
	
	k = pg.key.get_pressed()

	f.fighters[0].set_control(fighter.JUMP, k[pg.K_UP])
	f.fighters[0].set_control(fighter.DOWN, k[pg.K_DOWN])
	f.fighters[0].set_control(fighter.LEFT, k[pg.K_LEFT])
	f.fighters[0].set_control(fighter.RIGHT, k[pg.K_RIGHT])
	f.fighters[0].set_control(fighter.BASIC, k[pg.K_a])

	f.update()

	s.fill((0, 0, 0))
	cam.render(f, debug=True)
	pg.display.flip()
