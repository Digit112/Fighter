import sys
import pygame as pg
import socket as sk
from fighter import *

# Start or connect to server.
def p_help():
	print("Usage:")
	print("To start a server:")
	print("py main.py")
	print("py main.py <port>")
	print("")
	print("To connect to a server:")
	print("py main.py <ip> <port>")

port = 42069
if len(sys.argv) == 1:
	print("Starting server on default port %d..." % port)
	ip = "192.168.1.23"
	iam = "server"
elif len(sys.argv) == 2:
	try:
		port = int(sys.argv[1])
	except ValueError:
		print("Provided port \"%s\" is not a number." % sys.argv[1])
		p_help()
		exit()

	if port < 0 or port > 65535:
		print("Provided port \"%d\" is not valid. (Must be between 0 and 65535, inclusive)" % port)
		p_help()
		exit()

	print("Starting server on port %d..." % port)
	ip = "192.168.1.23"
	iam = "server"
elif len(sys.argv) == 3:
	ip = sys.argv[1]
	try:
		sk.inet_aton(ip)
	except sk.error:
		print("Provided ip \"%s\" is not valid." % sys.argv[1])
		p_help()
		exit()
	
	try:
		port = int(sys.argv[2])
	except ValueError:
		print("Provided port \"%s\" is not a number." % sys.argv[2])
		p_help()
		exit()

	if port < 0 or port > 65535:
		print("Provided port \"%d\" is not valid. (Must be between 0 and 65535, inclusive)" % port)
		p_help()
		exit()
	
	print("Connecting to server at %s:%d..." % (sys.argv[1], port))
	iam = "client"

# Create or Connect to server
if iam == "server":
	s = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
	s.bind((ip, port))
	s.listen()
	conn, addr = s.accept()
elif iam == "client":
	s = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
	s.connect((ip, port))
	conn = s
else:
	print("What?")
	print("No.")
	exit()

#conn.setblocking(0)

print("Connection Formed.")

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
if iam == "server":
	f.fighters[0].pos.x = -300
	f.fighters[1].pos.x = 300
else:
	f.fighters[0].pos.x = 300
	f.fighters[1].pos.x = -300

cam = camera((-width//2, -height//2, width, height), s)

clk = pg.time.Clock()

fn = 0
while True:
	fn += 1

	clk.tick(30)

	for event in pg.event.get():
		if event.type == pg.QUIT:
			conn.close()
			sys.exit()

	if fn % 2 == 0:
		k = pg.key.get_pressed()

		k_e = [False]*5
		k_e[fighter.JUMP]  = k[pg.K_UP]
		k_e[fighter.DOWN]  = k[pg.K_DOWN]
		k_e[fighter.LEFT]  = k[pg.K_LEFT]
		k_e[fighter.RIGHT] = k[pg.K_RIGHT]
		k_e[fighter.BASIC] = k[pg.K_a]

		conn.send(bytes(k_e))

#		try:
		l_e = list(conn.recv(5))
#		except BlockingIOError:
#			l_e = None
		print(l_e)

		for i in range(len(k_e)):
			f.fighters[0].set_control(i, k_e[i])
			f.fighters[1].set_control(i, l_e[i])

	f.update()

	s.fill((0, 0, 0))
	cam.set_target_from_fight(f)
	cam.render(f, debug=True)
	pg.draw.rect(s, (200, 20, 20), (0, 0, (f.fighters[0].health/100)*(width/2), 15))
	pg.draw.rect(s, (200, 20, 20), (width - (f.fighters[1].health/100)*(width/2), 0, width/2, 15))
	pg.display.flip()

