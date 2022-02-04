import sys
import pygame as pg
from fighter import *

pg.init()

width = 1600
height = 900

s = pg.display.set_mode((width, height))

f = fight()
f.add_platform(pg.Rect(-500, 400, 1000, 100))
f.add_fighter(pg.Rect(0, 0, 25, 75))
print(f.fighters[0].stand)

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

	f.update()

	print("Rendering...")
	s.fill((0, 0, 0))
	cam.render(f)
	pg.display.flip()
