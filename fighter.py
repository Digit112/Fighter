import pygame as pg
from collision import *

# Super handy functions for drawing rects with names in lieu of images.
def debug_rect(surf, color, rect, name=""):
	pg.draw.rect(surf, color, rect, width=1)
	
	dbg_fnt = pg.font.SysFont(["couriernew", "ubuntumono"], 11)

	# Code to draw the name
	if name != "":
		# The text of "name" will be drawn horizontally if the rect is wide, 
		# or vertically if the rect is tall.
		if rect.w + 2 > rect.h:
			max_text_width = rect.w - 2
			max_text_height = rect.h - 2
		else:
			max_text_width = rect.h - 2
			max_text_height = rect.w - 2
		
		if dbg_fnt.size(name)[1] > max_text_height:
			# Not enough vertical space to render text.
			return
		
		# Should probably implement a faster algorithm for
		# Trimming down strings that don't fit in the rect
		while dbg_fnt.size(name)[0] > max_text_width:
			name = name[:-1]
		
		# Render text
		text_surface = dbg_fnt.render(name, False, color)
		
		# Rotate if necessary
		if rect.h > rect.w + 2:
			text_surface = pg.transform.rotate(text_surface, -90)
		
		# Blit text into the rect.
		surf.blit(text_surface, (rect.left+2, rect.top+2))

# Class for holding an animation of a single value
# Each animation has a certain number of frames and is split into segments
# Each segment runs from the value at the end of the previous segment to the value at the beginning of the next
# Using the chosen form of interpolation.
class animation:
	# Constants for types of interpolation
	LINEAR = 0

	def __init__(self, val):
		self.points = [val]

# Class for storing an attack
class attack:
	def __init__(self, h, n):
		self.hb = h
		self.frames = n
		self.frame = 0
	
	def copy(self):
		return attack(self.hb, self.frames)

# Class for holding a platform.
class platform(pg.sprite.Sprite):
	def __init__(self, rect, surf=None):
		pg.sprite.Sprite.__init__(self)
		self.rect = pg.Rect(rect)
		self.image = surf
		self.collider = Hitbox(Rectangle(rect.left, rect.top, rect.right, rect.bottom))

# Stores a connection between two stances
# Connections have time-ins and time-outs, which define a range of frames after the most recent transition after which this connection is viable.
# Connections have a "trigger" value. When this value is passed to the stance object containing this connection via the event() function, a valid connection with that trigger is followed if it exists.
class connection:
	def __init__(self, srce, dest, trigger, time_in=0, time_out=None, atk=None):
		self.srce = srce
		self.dest = dest
		self.trigger = trigger

		# Time since last transition must be between ti and to for this connection to be followed.
		self.ti = time_in
		self.to = time_out

		# Attack that starts when this connection is followed.
		self.atk = atk

	# Returns whether this connection is valid and can be followed
	def is_valid(self, t):
		return self.ti < t and (self.to == None or t < self.to)

# Stores a stance, which is a state in the state machine that each fighter has.
# Stances transition to other stances in response to events which are passed to the state machine via function call.
# Stances have degradation targets, which define which stance it'll switch too after a certain amount of time has passed.
class stance:
	def __init__(self, hitbox, deg=None, deg_t=None):
		# List of connection instances. Connections are one-way and a stance only holds its outgoing connections.
		self.connections = []

		# Character's collider in this stance
		self.hb = hitbox

		# Stance to switch to after deg_t frames pass
		self.deg = deg
		self.deg_t = deg_t

	# Returns True if this stance should degrade or False otherwise
	def is_degraded(self, t):
		return self.deg_t is not None and t > self.deg_t
	
	# Create a connection and add it to this stance
	def add_connection(self, dest, trigger, time_in=0, time_out=None, atk=None):
		self.connections.append(connection(self, dest, trigger, time_in, time_out, atk))
	
	# Returns the valid connection that should be followed in response to this event, if it exists. Return None otherwise.
	def event(self, trigger, t):
		for c in self.connections:
			if trigger == c.trigger and c.is_valid(t):
				return c
		return None

# Class for holding a fighter.
class fighter(pg.sprite.Sprite):
	JUMP = 0
	LEFT = 1
	RIGHT = 2
	DOWN = 3

	BASIC = 4

	def __init__(self, rect, surf, fight, stance):
		pg.sprite.Sprite.__init__(self)
		self.rect = pg.Rect(rect)
		self.image = surf

		# The current stance. The passed variable is usually cookie-cutter, but may link, through its connections, to a fighter-specific web of stances which outline attacks, combos, etc.
		# The timer is set to 0 every time a transition occurs and is incremented by update()
		self.stance_t = 0
		self.stance = stance

		# List of currently ongoing attacks
		self.attacks = []
		
		# The fight instance thaat this fighter belongs to,
		self.f = fight
		
		# Stance variables keep track of the fighter's state
		self.grounded = True
		self.standing = True

		# Position and velocity
		self.pos = vec2(0, 0)
		self.vel = vec2(0, 0)
		self.facing = 1

		# Array of control states
		self.controls = [0, 0, 0, 0, 0]

	# Call this function to send controls to the fighter
	def set_control(self, con, val):
		if not val:
			self.controls[con] = 0
		else:
			if self.controls[con] == 0:
				self.controls[con] = 1
	
	# Position/Velocity manipulation
	def set_position(self, pos):
		self.pos.x = pos[0]
		self.pos.y = pos[1]

	def move(self, d_pos):
		self.pos.x += d_pos[0]
		self.pos.y += d_pos[1]
	
	def set_velocity(self, vel):
		self.vel.x = vel[0]
		self.vel.y = vel[1]
	
	def accelerate(self, d_vel):
		self.vel.x += d_vel[0]
		self.vel.y += d_vel[1]
	
	def step(self, dt):
		self.pos.x += self.vel[0] * dt
		self.pos.y += self.vel[1] * dt

	def attack(self, atk):
		 self.attacks.append(atk.copy())

	# Handles update per-frame.
	def update(self):
		self.standing = not self.controls[fighter.DOWN]
		
		hb = self.stance.hb.copy()

		if self.grounded and self.controls[fighter.JUMP]:
			self.accelerate((0, -800))

		self.accelerate((0, 50))

		if self.controls[fighter.LEFT]:
			self.move((-5, 0))
			self.facing = -1

		if self.controls[fighter.RIGHT]:
			self.move((5, 0))
			self.facing = 1

		self.step(1/30)

		hb.move(self.pos)

		# Collision Testing and resolution
		# Sets grounded to true if a collision is detected whose resolution requires going up.
		self.grounded = False
		for p in self.f.platforms:
			col = hb.collide_hitbox(p.collider)
		
			if col is not None:
				if col.r.x != 0:
					self.vel[0] = 0

				if col.r.y != 0:
					self.vel[1] = 0
					if col.r.y < 0:
						self.grounded = True

				self.move(col.r)

		# Test for stance transitions
		for i in range(len(self.controls)):
			if self.controls[i] == 1:
				conn = self.stance.event(i, self.stance_t)
				if conn is not None:
					self.stance_t = 0
					self.attack(conn.atk)
					self.stance = conn.dest

		# Test for stance degredation
		if self.stance.is_degraded(self.stance_t):
			self.stance_t = 0
			self.stance = self.stance.deg

		# Handle attack animations
		new_attacks = []
		for a_i in range(len(self.attacks)):
			a = self.attacks[a_i]

			if a.frame < a.frames:
				new_attacks.append(self.attacks[a_i])

			a.frame += 1

		self.attacks = new_attacks

		# Update control list so that 1s beome 2s (Indicating that those controls are being held)
		for i in range(len(self.controls)):
			if self.controls[i] == 1:
				self.controls[i] = 2

		# Increment the stance timer
		self.stance_t += 1

# Class for holding a fighting scene. One is instantiated whenever a fight begins. 
class fight:
	def __init__(self):
		self.platforms = []
		self.fighters = []
	
	# Add a platform and return its handle.
	def add_platform(self, rect, surf=None):
		self.platforms.append(platform(rect, surf))
		return self.platforms[-1]
	
	# Add a fighter and return the new sprite.
	def add_fighter(self, rect, hb, surf=None):
		self.fighters.append(fighter(rect, surf, self, hb))
		return self.fighters[-1]
	
	# Update the scene by calling update() on all sprites.
	def update(self):
		for p in self.platforms:
			p.update()
		for f in self.fighters:
			f.update()

# Camera designed for fighter games.
class camera:
	# Takes pg rect in world coordinates and surf to render to
	def __init__(self, rect, surf):
		self.t = pg.Rect(rect)
		self.aspect = self.t.w / self.t.height
		self.s = surf
	
	# Change the target.
	def set_target(self, rect):
		self.t = pg.Rect(rect)
	
	# Sets the target rect of the caamera to include this rect without changing the aspect ratio.
	def view_rect(self, rect):
		r_aspect = rect.width / rect.height
		
		if r_aspect > self.t.width / self.t.height:

			n_t = pg.Rect(rect.x, rect.y, rect.width, rect.width / self.aspect)
		else:

			n_t = pg.Rect(rect.x, rect.y, rect.height * self.aspect, rect.height)
		
		self.set_target(n_t)

	# Render the given map from this camera.	
	def render(self, m, debug=False):
		scale_x = self.s.get_width()  / self.t.width
		scale_y = self.s.get_height() / self.t.height
		
		for p in m.platforms:
			img_x = (p.rect.left - self.t.left) / self.t.width	* self.s.get_width()
			img_y = (p.rect.top	- self.t.top)  / self.t.height * self.s.get_height()
			img_w = p.rect.width * scale_x
			img_h = p.rect.height * scale_y

			if p.image == None:
				debug_rect(self.s, (40, 40, 200), pg.Rect(img_x, img_y, img_w, img_h), "Platform")
			else:
				self.s.blit(pg.transform.scale(p.image, (int(img_w), int(img_h))), (img_x, img_y))
		
		for f in m.fighters:
			img_x = (f.rect.left + f.pos.x - self.t.left) / self.t.width  * self.s.get_width()
			img_y = (f.rect.top	 + f.pos.y - self.t.top)  / self.t.height * self.s.get_height()
			img_w = f.rect.width * scale_x
			img_h = f.rect.height * scale_y

			if f.image == None:
				debug_rect(self.s, (180, 180, 40), pg.Rect(img_x, img_y, img_w, img_h), "Platform")
			else:
				self.s.blit(pg.transform.scale(f.image, (int(img_w), int(img_h))), (img_x, img_y))

			if debug:
				# Draw point at this fighter's pos
				img_x = (f.pos.x - self.t.left) / self.t.width  * self.s.get_width()
				img_y = (f.pos.y - self.t.top)  / self.t.height * self.s.get_height()
				pg.draw.circle(self.s, (180, 180, 40), (img_x, img_y), 2)

				# Draw attack hitboxes.
				for a in f.attacks:
					for c in a.hb.colliders:
						if type(c) == Rectangle:
							if f.facing == 1:
								img_x = (c.mx + f.pos.x  - self.t.left) / self.t.width  * self.s.get_width()
							else:
								img_x = (-c.Mx + f.pos.x - self.t.left) / self.t.width  * self.s.get_width()
							img_y = (c.my + f.pos.y - self.t.top)  / self.t.height * self.s.get_height()
							img_w = (c.Mx - c.mx) * scale_x
							img_h = (c.My - c.my) * scale_y

							debug_rect(self.s, (240, 40, 40), pg.Rect(img_x, img_y, img_w, img_h), "atk")







