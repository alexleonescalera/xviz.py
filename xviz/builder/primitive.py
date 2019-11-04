
import numpy as np
from easydict import EasyDict as edict

from xviz.builder.base_builder import XVIZBaseBuilder
from xviz.builder.validator import CATEGORY, PRIMITIVE_TYPES

class XVIZPrimitiveBuilder(XVIZBaseBuilder):
    """
    Method chaining is supported by this builder.
    
    # Reference
    [@xviz/builder/xviz-primitive-builder]/(https://github.com/uber/xviz/blob/master/modules/builder/src/builders/xviz-primitive-builder.js)
    """
    def __init__(self, metadata, validator):
        super().__init__(CATEGORY.PRIMITIVE, metadata, validator)

        self._primitives = edict()
        self.reset()

    def image(self, data):
        '''
        Add image data
        '''
        if self._type:
            self._flush()

        if not isinstance(data, np.ndarray) or not isinstance(data, str):
            # TODO: support PILLOW and other image types
            self.validate_error("An image data must be a string or numpy array")
        self.validate_prop_set_once("_image")
        self._type = PRIMITIVE_TYPES.image
        self._image = edict(data=data)

        return self

    def dimensions(self, widthPixel=None, heightPixel=None):
        '''
        Add dimension specs for image data
        '''
        if not self._image:
            self.validate_error("An image needs to be set first")

        self._image.width_px = widthPixel
        self._image.height_px = heightPixel

        return self

    def polygon(self, vertices):
        if self._type:
            self._flush()

        self.validate_prop_set_once("_vertices")
        self._vertices = vertices
        self._type = PRIMITIVE_TYPES.polygon

        return self

    def polyline(self, vertices):
        if self._type:
            self._flush()

        self.validate_prop_set_once("_vertices")
        self._vertices = vertices
        self._type = PRIMITIVE_TYPES.polyline

        return self

    def points(self, vertices):
        if self._type:
            self._flush()

        self.validate_prop_set_once("_vertices")
        self._vertices = vertices
        self._type = PRIMITIVE_TYPES.point

        return self

    def circle(self, position, radius):
        if self._type:
            self._flush()

        self.validate_prop_set_once("_radius")
        self.position(position)

        self._radius = radius
        self._type = PRIMITIVE_TYPES.circle

        return self

    def stadium(self, start, end, radius):
        if self._type:
            self._flush()

        self.validate_prop_set_once("_radius")

        if len(start) != 3:
            self.validate_error("The start position must be of the form [x, y, z] where {} was provided".format(start))
        if len(end) != 3:
            self.validate_error("The end position must be of the form [x, y, z] where {} was provided".format(end))
        
        
        self._vertices = [start, end]
        self._radius = radius
        self._type = PRIMITIVE_TYPES.stadium

        return self

    def text(self, message):
        # XXX: is not actually defined yet
        if self._type:
            self._flush()

        self.validate_prop_set_once('_text')

        self._text = message
        self._type = PRIMITIVE_TYPES.text

        return self
    
    def position(self, point):
        self.validate_prop_set_once("_vertices")

        if len(point) != 3:
            self.validate_error("A position must be of the form [x, y, z] where {} was provided".format(point))
        
        self._vertices = [point]
        return self

    def colors(self, colorArray):
        self.validate_prop_set_once('_colors')
        self._colors = colorArray

        return self

    def style(self, style):
        self._validate_prerequisite()
        self.validate_prop_set_once('_style')
        self._stype = style

        return self

    def id(self, identifier):
        self._validate_prerequisite()
        self.validate_prop_set_once('_id')
        self._id = identifier

        return self

    def classes(self, classList):
        self._validate_prerequisite()
        self.validate_prop_set_once('_classes')

        self._classes = classList
        return self
        
    def _validate(self):
        super()._validate()

        if self._type == PRIMITIVE_TYPES.image:
            if self._image == None or self._image.data == None:
                self.validate_warn("Stream {} image data are not provided.".format(self._stream_id))
        else:
            if self._vertices == None:
                self.validate_warn("Stream {} primitives vertices are not provided.".format(self._stream_id))

    def _flush(self):
        self._validate()
        self._flush_primitives()

    def get_data(self):
        if self._type:
            self._flush()

        if len(self._primitives) == 0:
            return None

        return self._primitives

    def _validate_prerequisite(self):
        if self._type:
            self.validate_error("Start from a primitive first, e.g polygon(), image(), etc.")

    def _flush_primitives(self):
        if self._stream_id not in self._primitives.keys():
            self._primitives[self._stream_id] = edict()
        stream = self._primitives[self._stream_id]

        array_field_name = self._type + 's'
        if array_field_name not in stream:
            stream[array_field_name] = []
        array = stream[array_field_name]

        obj = self._format_primitives()
        array.append(obj)

        self.reset()

    def _format_primitives(self):
        obj = edict()

        # Embed primitive data
        if self._type == PRIMITIVE_TYPES.polygon or self._type == PRIMITIVE_TYPES.polyline:
            obj.vertices = self._vertices
        elif self._type == PRIMITIVE_TYPES.point:
            if self._colors:
                obj.colors = self._colors
            obj.points = self._vertices
        elif self._type == PRIMITIVE_TYPES.text:
            obj.position = self._vertices[0]
            obj.text = self._text
        elif self._type == PRIMITIVE_TYPES.circle:
            obj.center = self._vertices[0]
            obj.radius = self._radius
        elif self._type == PRIMITIVE_TYPES.stadium:
            obj.start = self._vertices[0]
            obj.end = self._vertices[1]
            obj.radius = self._radius
        elif self._type == PRIMITIVE_TYPES.image:
            if self._vertices:
                self._image.position = self._vertices[0]

            obj.update(self._image)

        # Embed base data
        have_base = False
        base = edict()

        if self._id:
            have_base = True
            base.object_id = self._id
        if self._style:
            have_base = True
            base.style = self._style
        if self._classes:
            have_base = True
            base.classes = self._classes

        if have_base:
            obj.base = base

        return obj

    def _validate_style(self):
        self._validator.validateStyle(self)

    def reset(self):
        self._type = None

        self._image = None
        self._vertices = None
        self._radius = None
        self._text = None
        self._colors = None

        self._id = None
        self._style = None
        self._classes = None