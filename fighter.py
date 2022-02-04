import pygame as pg

# Super handy functions for drawing rects with names in lieu of sprites
def debug_rect(surf, color, rect, name=""):
	pg.draw.rect(surf, color, rect, width=1)
	
	dbg_fnt = pg.font.SysFont("couriernew", 11)

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

# -------- Math Stuff --------
# Because everyone else's vector implementations suck

class vec2:
	def __init__(self, x, y):
		self.x = x
		self.y = y
	
	def sqr_mag(self):
		return self.x*self.x + self.y*self.y

	def mag(self):
		return self.sqr_mag()**0.5

	def normalize(self, new_mag=1):
		if new_mag == 0:
			return vec2(0, 0)
		m = self.mag() / new_mag
		return vec2(self.x / m, self.y / m)

	# Overloads
	def __str__(self):
		return "<vec2(%.2f, %.2f)>" % (self.x, self.y)

	def __getitem__(self, ind):
		if ind == 0:
			return self.x
		elif ind == 1:
			return self.y
		else:
			raise IndexError("Index for vec2 must be either 0 or 1")

	def __setitem__(self, ind, val):
		if ind == 0:
			self.x = val
		elif ind == 1:
			self.y = val
		else:
			raise IndexError("Index for vec2 must be either 0 or 1")

	# Arithmetic (Component-wise)
	def __add__(self, othr):
		return vec2(self.x + othr.x, self.y + othr.y)

	def __sub__(self, othr):
		return vec2(self.x - othr.x, self.y - othr.y)

	def __mul__(self, othr):
		return vec2(self.x * othr.x, self.y * othr.y)

	__rmul__ = __mul__
	
	def __truediv__(self, othr):
		return vec2(self.x / othr.x, self.y / othr.y)

	def __neg__(self):
		return vec2(-self.x, -self.y)

	# Comparisons
	def __lt__(self, othr):
		return self.sqr_mag() < othr.sqr_mag()

	def __gt__(self, othr):
		return self.sqr_mag() > othr.sqr_mag()

	def __le__(self, othr):
		return self.sqr_mag() <= othr.sqr_mag()

	def __ge__(self, othr):
		return self.sqr_mag() >= othr.sqr_mag()

	def __eq__(self, othr):
		return self.x == othr.x and self.y == othr.y

	def __ne__(self, othr):
		return self.x != othr.x or self.y != othr.y

# -------- Collider & Hitbox Classes --------
# Each collider class defines a function for testing collision with all other classes
# The current primitive colliders are Points, Rectangles, and Circles
# Hitboxes are lists of primitive colliders.
# All collision testing functions return a collision object which contains the collision resolution vector.
# The vector moves the calling object so that it is touching but not intersecting the passed object.

# Collision object returned by a collision
class Collision:
	def __init__(self, collider_a, collider_b, resolution):
		self.a = collider_a
		self.b = collider_b
		self.r = resolution
	
	# Used by collision functions which swap parameters to un-swap the result 
	def swap(self):
		tmp = self.a
		self.a = self.b
		self.b = tmp

		self.r = -self.r

	def __str__(self):
		return "<Collision(" + str(self.a) + ", " + str(self.b) + ", " + str(self.r) + ")>"

# Class for holding Points.
class Point:
	def __init__(self, x, y):
		self.x = x
		self.y = y
	
	def __str__(self):
		return "<Point(%.2f, %.2f)>" % (self.x, self.y)
	
	def move(self, d):
		self.x += d.x
		self.y += d.y
	
	def copy(self):
		return Point(self.x, self.y)

	def collide_point(self, h):
		hit = h.x == self.x and h.y == self.y
		if hit:
			return Collision(self, h, vec2(0, 0)) 
		return None
	
	def collide_rectangle(self, h):
		col = h.collide_point(self)
		if col is not None:
			col.swap()
		return col

	def collide_circle(self, h):
		col = h.collide_point(self)
		if col is not None:
			col.swap()
		return col

# Class for holding Rectangles. Used in hitboxes along with Circles 
# Not to be confused with pygame.Rect
class Rectangle:
	def __init__(self, x1, y1, x2, y2):
		self.mx = x1
		self.my = y1
		self.Mx = x2
		self.My = y2

		# Ensure (mx, my) is less than (Mx, My)
		if self.mx > self.Mx:
			temp = self.mx
			self.mx = self.Mx
			self.Mx = temp

		if self.my > self.My:
			temp = self.my
			self.my = self.My
			self.My = temp
	
	def __str__(self):
		return "<Rectangle(%.2f, %.2f, %.2f, %.2f)>" % (self.mx, self.my, self.Mx, self.My)

	def move(self, d):
		self.mx += d.x
		self.my += d.y
		self.Mx += d.x
		self.My += d.y
	
	def copy(self):
		return Rectangle(self.mx, self.my, self.Mx, self.My)

	def width(self):
		return self.Mx - self.mx
	
	def height(self):
		return self.My - self.my

	def collide_point(self, h):
		hit = h.x >= self.mx and h.x <= self.Mx and h.y >= self.my and h.y <= self.My
		if hit:
			return Collision(self, h, min(vec2(h.x - self.mx, 0), vec2(h.x - self.Mx, 0), vec2(0, h.y - self.my), vec2(0, h.y - self.My)))
		return None

	def collide_rectangle(self, h):
		hit = not (self.Mx < h.mx or self.My < h.my or self.mx > h.Mx or self.my > h.My)
		if hit:
			return Collision(self, h, min(vec2(h.mx - self.Mx, 0), vec2(h.Mx - self.mx, 0), vec2(0, h.my - self.My), vec2(0, h.My - self.my)))
		return None

	def collide_circle(self, h):
		cdx = min(self.Mx, max(self.mx, h.x)) - h.x
		cdy = min(self.My, max(self.my, h.y)) - h.y

		# Generate collision resolution for when the center of the circle is inside or touching the rectangle
		if cdx == 0 and cdy == 0:
			return Collision(
				self, h,
				min(
					vec2(h.x - self.mx + h.r, 0),
					vec2(h.x - self.Mx - h.r, 0),
					vec2(0, h.y - self.my + h.r),
					vec2(0, h.y - self.My - h.r)
				)
			)

		# Generate collision resolution for when the center of the circle is outside the rectangle
		hit = cdx*cdx + cdy*cdy <= h.r*h.r
		if hit:
			return Collision(self, h, vec2(cdx, cdy).normalize(h.r - vec2(cdx, cdy).mag()))
		return None

	def collide_hitbox(self, h):
		col = h.collide_rectangle(self)
		if col is not None:
			col.swap()
		return col

# Circle Class. Used in hitboxes along with Rectangles 
class Circle:
	def __init__(self, x, y, r):
		self.x = x
		self.y = y
		self.r = r

	def __str__(self):
		return "<Circle(%.2f, %.2f, %.2f)>" % (self.x, self.y, self.r)

	def move(self, d):
		self.x += d.x
		self.y += d.y

	def copy(self):
		return Circle(self.x, self.y, self.r)

	def collide_point(self, h):
		cdx = self.x - h.x
		cdy = self.y - h.y
		
		# Generate default resolution when point is at circle center
		if cdx == 0 and cdy == 0:
			return Collision(self, h, vec2(0, -self.r))

		# Generate collision resolution normally otherwise.
		hit = cdx*cdx + cdy*cdy <= self.r*self.r
		if hit:
			cdm = vec2(cdx, cdy)
			return Collision(self, h, cdm.normalize(self.r - cdm.mag()))
		return None

	def collide_rectangle(self, h):
		col = h.collide_circle(self)
		if col is not None:
			col.swap()
		return col

	def collide_circle(self, h):
		cdx = self.x - h.x
		cdy = self.y - h.y
		r_sum = self.r + h.r

		if cdx == 0 and cdy == 0:
			return Collision(self, h, vec2(0, -r_sum))

		hit = cdx*cdx + cdy*cdy <= r_sum*r_sum
		if hit:
			cdm = vec2(cdx, cdy)
			return Collision(self, h, cdm.normalize(r_sum - cdm.mag()))
		return None

	def collide_hitbox(self, h):
		col = h.collide_circle(self)
		if col is not None:
			col.swap()
		return col

# Class for holding a hitbox. This is a collection of rectangles and circles.
class Hitbox:
	def __init__(self, colliders=None):
		self.colliders = []
		if colliders is not None:
			try:
				for c in colliders:
					self.add_collider(c)
			except TypeError:
				self.add_collider(colliders)

	def __str__(self):
		s = "<Hitbox("
		if len(self.colliders) > 0:
			s = s + str(self.colliders[0])
			for c in self.colliders[1:]:
				s = s + ", " + str(c)
		return s + ")>"

	def move(self, d):
		for c in self.colliders:
			c.move(d)

	def copy(self):
		hb = Hitbox()
		for c in self.colliders:
			hb.add_collider(c.copy())
		return hb

	def add_collider(self, c):
		if type(c) != Rectangle and type(c) != Circle and type(c) != Point:
			raise TypeError("Attmpted to add non-collider object to hitbox.")
		self.colliders.append(c.copy())
	
	# Colliding hitboxes against primitives returns the index in self.colliders of the collider that first hit.
	def collide_point(self, h):
		for c in range(len(self.colliders)):
			col = self.colliders[c].collide_point(h)
			if col is not None:
				return col
		return None

	def collide_circle(self, h):
		for c in range(len(self.colliders)):
			col = self.colliders[c].collide_circle(h)
			if col is not None:
				return col
		return None

	def collide_rectangle(self, h):
		for c in range(len(self.colliders)):
			col = self.colliders[c].collide_rectangle(h)
			if col is not None:
				return col
		return None

	# Returns a pair of indeces for the first pair of colliders to hit.
	# If there are no hits, return None, None
	def collide_hitbox(self, h):
		for c_i in range(len(h.colliders)):
			c = h.colliders[c_i]

			if type(c) == Rectangle:
				col = self.collide_rectangle(c)
			elif type(c) == Circle:
				col = self.collide_circle(c)
			elif type(c) == Point:
				col = self.collide_point(c)
			
			if col is not None:
				return col

		return None

# Class for holding a platform.
class platform(pg.sprite.Sprite):
	def __init__(self, rect, surf=None):
		pg.sprite.Sprite.__init__(self)
		self.rect = pg.Rect(rect)
		self.image = surf
		self.collider = Hitbox(Rectangle(rect.left, rect.top, rect.right, rect.bottom))

# Class for holding a fighter.
class fighter(pg.sprite.Sprite):
	JUMP = 0
	LEFT = 1
	RIGHT = 2
	DOWN = 3

	BASIC = 4

	def __init__(self, rect, surf, setting):
		pg.sprite.Sprite.__init__(self)
		self.rect = pg.Rect(rect)
		self.image = surf
		
		# The fight instance thaat this fighter belongs to,
		self.f = setting
		
		# Stance variables keep track of the fighter's state
		self.grounded = True
		self.standing = True

		# Position and velocity
		self.pos = vec2(0, 0)
		self.vel = vec2(0, 0)

		# Array of control states
		self.controls = [False, False, False, False, False]

		# Profiles that this fighter takes up in different positions
		self.stand = Hitbox(Rectangle(0, 0, 25, 75))
		self.crouch = Hitbox(Rectangle(-10, 35, 35, 75))
		self.air = Hitbox(Rectangle(0, 0, 25, 75))
		self.air_crouch = Hitbox(Rectangle(-10, 35, 35, 75))

	# Call this function to send controls to the fighter
	def set_control(self, con, val):
		self.controls[con] = val
	
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

	# Handles update per-frame.
	def update(self):
		self.standing = not self.controls[fighter.DOWN]
		
		if self.grounded:
			if self.standing:
				stance = self.stand.copy()
			else:
				stance = self.crouch.copy()
		else:
			if self.standing:
				stance = self.air.copy()
			else:
				stance = self.air_crouch.copy()


		if self.grounded and self.controls[fighter.JUMP]:
			self.accelerate((0, -800))

		self.accelerate((0, 50))

		if self.controls[fighter.LEFT]:
			self.move((-5, 0))

		if self.controls[fighter.RIGHT]:
			self.move((5, 0))

		self.step(1/30)

		stance.move(self.pos)

		# Collision Testing and resolution
		# Sets grounded to true if a collision is detected whose resolution requires going up.

		for p in self.f.platforms:

			col = stance.collide_hitbox(p.collider)
			
			self.grounded = False
			if col is not None:

				if col.r.x != 0:
					self.vel[0] = 0

				if col.r.y != 0:
					self.vel[1] = 0
					if col.r.y < 0:
						self.grounded = True

				self.move(col.r)
		


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
	def add_fighter(self, rect, surf=None):
		self.fighters.append(fighter(rect, surf, self))
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
	def render(self, m):
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
			img_x = (f.rect.left - self.t.left) / self.t.width	* self.s.get_width() + f.pos[0]
			img_y = (f.rect.top	- self.t.top)  / self.t.height * self.s.get_height() + f.pos[1]
			img_w = f.rect.width * scale_x
			img_h = f.rect.height * scale_y

			if f.image == None:
				debug_rect(self.s, (200, 40, 40), pg.Rect(img_x, img_y, img_w, img_h), "Platform")
			else:
				self.s.blit(pg.transform.scale(f.image, (int(img_w), int(img_h))), (img_x, img_y))







