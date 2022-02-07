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

class collider_anim:
	def __init__(self):
		self.frame_markers = []
		self.cols = []
		self.damage = []
		self.anim_type = None
	
	def add_col(self, col, dmg, frame):
		if self.anim_type == None:
			self.anim_type = type(col)

		if type(col) != self.anim_type:
			raise ValueError("Subsequent colliders added to collider_anim object where not of like type.")
		
		self.frame_markers.append(frame)
		self.damage.append(dmg)
		self.cols.append(col)
	
	def get_col(self, t):
		if t < self.frame_markers[0] or t > self.frame_markers[-1]:
			return None
		if t == self.frame_markers[-1]:
			return self.cols[-1]

		for i in range(len(self.frame_markers)-2, -1, -1):
			if self.frame_markers[i] <= t:
				t_val = (t - self.frame_markers[i]) / (self.frame_markers[i+1] - self.frame_markers[i])
				return self.anim_type.lerp(self.cols[i], self.cols[i+1], t_val)

	def get_dmg(self, t):
		print(self.damage, t)
		if t < self.frame_markers[0] or t > self.frame_markers[-1]:
			return 0
		if t == self.frame_markers[-1]:
			return self.damage[-1]
		
		for i in range(len(self.frame_markers)-2, -1, -1):
			if self.frame_markers[i] <= t:
				t_val = (t - self.frame_markers[i]) / (self.frame_markers[i+1] - self.frame_markers[i])
				return lerp(self.damage[i], self.damage[i+1], t_val)

# Class for storing an attack
class attack:
	def __init__(self, n):
		self.frames = n
		self.frame = 0

		# List of collider_anim instances.
		self.anim = []
	
	def add_anim(self, a):
		self.anim.append(a)

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
	def __init__(self, srce, dest, trigger, transition_time = 0, time_in=0, time_out=None, atk=None):
		self.srce = srce
		self.dest = dest
		self.trigger = trigger

		# Number of frames after this connection is folled before another transition can occur.
		self.t_time = transition_time

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
	def add_connection(self, dest, trigger, transition_time=0, time_in=0, time_out=None, atk=None):
		self.connections.append(connection(self, dest, trigger, transition_time, time_in, time_out, atk))
	
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

	def __init__(self, rect, surf, fight, stance, team):
		pg.sprite.Sprite.__init__(self)
		self.rect = pg.Rect(rect)
		self.image = surf

		# The current stance. The passed variable is usually cookie-cutter, but may link, through its connections, to a fighter-specific web of stances which outline attacks, combos, etc.
		# The timer is set to 0 every time a transition occurs and is incremented by update()
		self.stance_t = 0
		self.stance = stance

		# Players only check collision (take damage from) the hitboxes of players on different teams.
		self.team = team

		self.health = 100

		# List of currently ongoing attacks
		self.attacks = []
		
		# List of attacks which have already damaged this fighter
		self.immunities = []
		self.immunity_t = []

		# The fight instance thaat this fighter belongs to,
		self.f = fight

		# Set by transitions. Decremented by update(). Cannot transition until this equals 0
		self.t_wait = 0
		
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
		# If attack animation is already playing, reset it.
		for a in self.attacks:
			if a is atk:
				a.frame = 0
				return

		self.attacks.append(atk)
		self.attacks[-1].frame = 0

	def add_immunity(self, f):
		self.immunities.append(f)
		self.immunities_t.append(f.attacks[0].frames - f.attacks[0].frame + 1)
	
	def update_immunity(self):
		n_immunities = []
		n_immunities_t = []

		for i in range(len(self.immunities)):
			self.immunities_t[i] -= 1
			if self.immunities_t[i] == 0:
				continue
			
			n_immunities.append(self.immunities[i])
			n_immunities_t.append(self.immunities_t[i])

		self.immunities = n_immunities
		self.immunities_t = n_immunities_t

	# Handles update per-frame.
	def update(self):
		self.standing = not self.controls[fighter.DOWN]
		
		self.update_immunity()

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
		if self.t_wait > 0:
			self.t_wait -= 1
		else:
			for i in range(len(self.controls)):
				if self.controls[i] == 1:
					conn = self.stance.event(i, self.stance_t)
					if conn is not None:
						self.stance_t = 0
						self.t_wait = conn.t_time
						if conn.atk is not None:
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
	def add_fighter(self, rect, hb, team, surf=None):
		self.fighters.append(fighter(rect, surf, self, hb, team))
		return self.fighters[-1]
	
	# Update the scene by calling update() on all sprites.
	def update(self):
		# Do attack collision tests.
		for a in self.fighters:
			for b in self.fighters:
				# Test that the fighters are on different teams
				if b.team == a.team:
					continue
				if a in b.immunities:
					continue

				dmg = 0
				for atk in a.attacks:
					for anm in atk.anim:
						# Collide the collider from the current frame of the animation "anm" from attack "atk" from fighter "a" with the hitbox from fighter "b"
						col1 = anm.get_col(atk.frame)
						if col1 is None:
							continue

						col1 = col1.copy()
						if a.facing == -1:
							col1.flip_x()
						col1.move(a.pos)

						col2 = b.stance.hb.copy()
						if b.facing == -1:
							co2.flip_x()
						col2.move(b.pos)

						collision = col1.collide_hitbox(col2)
						if collision is not None:
							tmp = anm.get_dmg(atk.frame)
							dmg = max(dmg, anm.get_dmg(atk.frame))

				if dmg > 0:
					b.health -= dmg
					b.add_immunity(a)

		for p in self.platforms:
			p.update()
		for f in self.fighters:
			f.update()

# Camera designed for fighter games.
class camera:
	# Takes pg rect in world coordinates and surf to render to
	def __init__(self, rect, surf):
		self.t = pg.Rect(rect)
		self.c = pg.Rect(rect)
		self.aspect = self.t.width / self.t.height
		self.s = surf

	# Change the target based on the passed fight
	def set_target_from_fight(self, f):
		mx = 1000
		my = 1000
		Mx = -1000
		My = -1000

		for c in f.fighters:
			mx = min(mx, c.stance.hb.left() + c.pos.x)
			Mx = max(Mx, c.stance.hb.right() + c.pos.x)
			my = min(my, c.stance.hb.top() + c.pos.y)
			My = max(My, c.stance.hb.bottom() + c.pos.y)

		self.view_rect((mx-100, my-100, (Mx-mx)+200, (My-my)+200))

	# Change the target.
	def set_target(self, rect):
		self.t = pg.Rect(rect)
	
	# Sets the target rect of the camera to include this rect without changing the aspect ratio.
	def view_rect(self, rect, min_width=600):
		rect = pg.Rect(rect)
		r_aspect = rect.width / rect.height
		
		if r_aspect > self.aspect: 
			n_t = pg.Rect(rect.x, rect.y, rect.width, rect.width / self.aspect)
		else:
			n_t = pg.Rect(rect.x, rect.y, rect.height * self.aspect, rect.height)
	
		if n_t.width < min_width:
			n_t.height *= min_width / n_t.width
			n_t.width = min_width

		dx = (rect.x + rect.width/2)  - (n_t.x + n_t.width/2)
		dy = (rect.y + rect.height/2) - (n_t.y + n_t.height/2)

		n_t.x += dx
		n_t.y += dy

		self.set_target(n_t)

	# Render the given map from this camera.	
	def render(self, m, debug=False):
		self.c.x = lerp(self.c.x, self.t.x, 0.1)
		self.c.y = lerp(self.c.y, self.t.y, 0.1)
		self.c.w = lerp(self.c.w, self.t.w, 0.1)
		self.c.h = lerp(self.c.h, self.t.h, 0.1)

		scale_x = self.s.get_width()  / self.c.width
		scale_y = self.s.get_height() / self.c.height
		
		for p in m.platforms:
			img_x = (p.rect.left - self.c.left) / self.c.width	* self.s.get_width()
			img_y = (p.rect.top	- self.c.top)  / self.c.height * self.s.get_height()
			img_w = p.rect.width * scale_x
			img_h = p.rect.height * scale_y

			if p.image == None:
				debug_rect(self.s, (40, 40, 200), pg.Rect(img_x, img_y, img_w, img_h), "Platform")
			else:
				self.s.blit(pg.transform.scale(p.image, (int(img_w), int(img_h))), (img_x, img_y))
		
		for f in m.fighters:
			img_x = (f.rect.left + f.pos.x - self.c.left) / self.c.width  * self.s.get_width()
			img_y = (f.rect.top	 + f.pos.y - self.c.top)  / self.c.height * self.s.get_height()
			img_w = f.rect.width * scale_x
			img_h = f.rect.height * scale_y

			if f.image == None:
				debug_rect(self.s, (180, 180, 40), pg.Rect(img_x, img_y, img_w, img_h), "Fighter")
			else:
				self.s.blit(pg.transform.scale(f.image, (int(img_w), int(img_h))), (img_x, img_y))

			if debug:
				# Draw point at this fighter's pos
				img_x = (f.pos.x - self.c.left) / self.c.width  * self.s.get_width()
				img_y = (f.pos.y - self.c.top)  / self.c.height * self.s.get_height()
				pg.draw.circle(self.s, (180, 180, 40), (img_x, img_y), 2)

				# Draw attack hitboxes.
				for atk in f.attacks:
					for anim in atk.anim:
						c = anim.get_col(atk.frame)
						if type(c) == Rectangle:
							if f.facing == 1:
								img_x = (c.mx + f.pos.x  - self.c.left) / self.c.width  * self.s.get_width()
							else:
								img_x = (-c.Mx + f.pos.x - self.c.left) / self.c.width  * self.s.get_width()
							img_y = (c.my + f.pos.y - self.c.top)  / self.c.height * self.s.get_height()
							img_w = (c.Mx - c.mx) * scale_x
							img_h = (c.My - c.my) * scale_y

							debug_rect(self.s, (240, 40, 40), pg.Rect(img_x, img_y, img_w, img_h), "atk")







