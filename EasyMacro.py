import FreeCAD
import Part
import PartDesign
import PartDesignGui
import Sketcher
import FreeCADGui
import math

App = FreeCAD

def initm():
	doc = FreeCAD.ActiveDocument
	return (doc)

def getSels():
	return FreeCAD.Gui.Selection.getSelectionEx()

def getSup(what):
	support = eval(what.FullName)
	return support

class BodySketchBase:
	def __init__(self, sketch, body, id):
		self.sketch = sketch
		self.body = body
		self.id = id

class Body:
	def __init__(self, body):
		self.body = body
		self.ori = body.Origin.Name[-3:999]
		self.orip = '_Plane' + self.ori
		self.oria = '_Axis' + self.ori
		self.Group = body.Group

	# mode = FlatFace | Translate | ThreePointsPlane | TangentPlane
	def newPlane(self, support, mode = 'FlatFace', placement = [0.0, 0.0, 0.0], rotation = [0.0, 0.0, 0.0]):
		plane = self.body.newObject('PartDesign::Plane','DatumPlane')
		plane.AttachmentOffset = App.Placement(App.Vector(placement[0], placement[1], placement[2]),  App.Rotation(rotation[0], rotation[1], rotation[2]))
		plane.MapReversed = False
		plane.Support = support
		plane.MapPathParameter = 0.000000
		plane.MapMode = mode
		plane.recompute()
		plane.Visibility = False
		return plane

	def newLine(self, support, mode = 'TwoPointLine', placement = [0.0, 0.0, 0.0]):
		line = self.body.newObject('PartDesign::Line','DatumLine')
		line.AttachmentOffset = App.Placement(App.Vector(placement[0], placement[1], placement[2]),  App.Rotation(0.0000000000, 0.0000000000, 0.0000000000))
		line.MapReversed = False
		line.Support = support
		line.MapPathParameter = 0.000000
		line.MapMode = mode
		line.recompute()
		line.Visibility = False
		return line

	def newPoint(self, support, mode = 'CenterOfCurvature', placement = [0.0, 0.0, 0.0]):
		point = self.body.newObject('PartDesign::Point','DatumPoint')
		point.Support = support
		point.MapMode = mode
		point.AttachmentOffset = App.Placement(App.Vector(placement[0], placement[1], placement[2]),  App.Rotation(0.0000000000, 0.0000000000, 0.0000000000))
		point.MapReversed = False
		point.MapPathParameter = 0.000000
		point.recompute()
		point.Visibility = False
		return point

	def newPipe(self, circle, spine, edge = []):
		pipe = self.body.newObject('PartDesign::AdditivePipe','AdditivePipe')
		pipe.Profile = circle
		pipe.Spine = (spine, edge)
		return pipe

	class Sketch:
		def __init__(self, sketch):
			self.body = sketch
			self.x = self._line(None, -1, 0)
			self.y = self._line(None, -2, 0)
			self.o = self.x.p1
			self.Name = sketch.Name

		def getPoint(self, pos = (1, 1), cons = False):
			body = Part.Point(App.Vector(pos[0], pos[1], 0))
			id = self.body.addGeometry(body, cons)
			return self._point(body, id)

		def _point(self, body, id, ud = 1):
			return Body.Sketch.Point(self, body, id, ud)
		class Point(BodySketchBase):
			TypeId = 'Point'
			def __init__(self, sketch, body, id, ud):
				super().__init__(sketch, body, id)
				self.ud = ud

			@property
			def pos(self):
				return self.sketch.body.getPoint(self.id, self.ud)

			def coin(self, p):
				return self.sketch.body.addConstraint(Sketcher.Constraint('Coincident', self.id, self.ud, p.id, p.ud))

			def on(self, b):
				return self.sketch.body.addConstraint(Sketcher.Constraint('PointOnObject', self.id, self.ud, b.id))

			def tan(self, p):
				return self.sketch.body.addConstraint(Sketcher.Constraint('Tangent', self.id, self.ud, p.id, p.ud))

		def getLine(self, p1 = (0, 0), p2 = (1, 1), cons = False):
			body = Part.LineSegment(App.Vector(p1[0], p1[1], 0),App.Vector(p2[0], p2[1], 0))
			id = self.body.addGeometry(body,cons)
			return self._line(body, id)

		def _line(self, body, id, ud = 0):
			return Body.Sketch.Line(self, body, id, ud)
		class Line(BodySketchBase):
			TypeId = 'Line'
			def __init__(self, sketch, body, id, ud):
				super().__init__(sketch, body, id)
				self.ud = ud
				self.p1 = sketch._point(None, id, 1)
				self.p2 = sketch._point(None, id, 2)

			def ver(self):
				return self.sketch.body.addConstraint(Sketcher.Constraint('Vertical', self.id))

			def hor(self):
				return self.sketch.body.addConstraint(Sketcher.Constraint('Horizontal', self.id))

			def equal(self, b):
				return self.sketch.body.addConstraint(Sketcher.Constraint('Equal', self.id, b.id))

		def getCircle(self, p = (0, 0), r = 5, cons = False):
			body = Part.Circle(App.Vector(p[0], p[1], 0),App.Vector(0,0,1),r)
			id = self.body.addGeometry(c,cons)
			return self._circle(body, id)

		def _circle(self, body, id):
			return Body.Sketch.Circle(self, body, id)
		class Circle(BodySketchBase):
			TypeId = 'Circle'
			def __init__(self, sketch, body, id):
				super().__init__(sketch, body, id)
				self.p = sketch._point(None, id, 3)

			def dia(self, r):
				return self.sketch.body.addConstraint(Sketcher.Constraint('Diameter', self.id, r))

			def rad(self, r):
				return self.sketch.body.addConstraint(Sketcher.Constraint('Radius', self.id, r))

			def tan(self, w):
				return self.sketch.body.addConstraint(Sketcher.Constraint('Tangent', self.id, w.id))

		# fr, to, o
		# fr, to, (x, y), r
		def getArc(self, fr, to, o, r = False, cons = False):
			fr = math.radians(fr)
			to = math.radians(to)
			if type(o) == type((0, 0)):
				o = Part.Circle(App.Vector(o[0], o[1]), App.Vector(0, 0, 1), r)
			else:
				o = o.body
				cons = r
			body = Part.ArcOfCircle(o, fr, to)
			id = self.body.addGeometry(body,cons)
			return self._arc(body, id)

		def _arc(self, body, id):
			return Body.Sketch.Arc(self, body, id)
		class Arc(BodySketchBase):
			TypeId = 'Arc'
			def __init__(self, sketch, body, id):
				super().__init__(sketch, body, id)
				self.fr = sketch._point(None, id, 1)
				self.to = sketch._point(None, id, 2)
				self.p = sketch._point(None, id, 3)

			def dia(self, r):
				return self.sketch.body.addConstraint(Sketcher.Constraint('Diameter', self.id, r))

			def rad(self, r):
				return self.sketch.body.addConstraint(Sketcher.Constraint('Radius', self.id, r))

			def tan(self, w):
				return self.sketch.body.addConstraint(Sketcher.Constraint('Tangent', self.id, w.id))

		def getBspline(self, ps, cons = False):
			poss = []
			for p in ps:
				poss.append(p.pos)
			body = Part.BSplineCurve(poss)
			id = self.body.addGeometry(body,cons)
			count = 0
			for p in ps:
				cc = self.getCircle(cons = True)
				cc.p.coin(p)
				cc.dia(2)
				con = Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',cc.p.id,cc.p.ud,id,count)
				self.body.addConstraint(con)
				count += 1
			return self._bspline(id, body, ps)

		def _bspline(self, body, id, ps):
			return Body.Sketch.Bspline(self, body, id, ps)
		class Bspline(BodySketchBase):
			type = 'Bspline'
			def __init__(self, sketch, body, id, ps):
				super().__init__(sketch, id)
				self.ps = ps

		extId = -2
		# type = 'Plane' | 'Point' | 'Line'
		def ext(self, ele, type, ot = False):
			ot = ot or type
			self.body.addExternal(ele.Name, type)
			self.extId -= 1
			if ot == 'Point':
				return self._point(None, self.extId)
			else:
				return self._line(None, self.extId)

		def re(self):
			self.body.recompute()

	def newSketch(self, support):
		sketch = self.body.newObject('Sketcher::SketchObject','Sketch112')
		sketch.Support = (support,[''])
		sketch.MapMode = 'FlatFace'
		sketch.Visibility = False
		return Body.Sketch(sketch)

	def newSketchCircle(self, support, d):
		sketchCircle = self.newSketch(support)
		circle = sketchCircle.getCircle()
		circle.dia(d)
		circle.p.coin(sketchCircle.o)
		return sketchCircle.body



