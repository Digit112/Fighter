import pygame as pg

# This library implements a quick vec2 class, primitive rect, circle, and point classes, 
# and a Hitbox class, which is a list of primitive colliders with utilities.

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
			return Collision(
				self, h,
				min(
					vec2(h.x - self.mx, 0),
					vec2(h.x - self.Mx, 0),
					vec2(0, h.y - self.my),
					vec2(0, h.y - self.My)
				)
			)
		return None

	def collide_rectangle(self, h):
		hit = not (self.Mx < h.mx or self.My < h.my or self.mx > h.Mx or self.my > h.My)
		if hit:
			return Collision(
				self, h,
				min(
					vec2(h.mx - self.Mx, 0),
					vec2(h.Mx - self.mx, 0),
					vec2(0, h.my - self.My),
					vec2(0, h.My - self.my)
				)
			)
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
