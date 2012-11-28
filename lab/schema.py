"""Experiment with schema definitions for XModules."""

class SchemaType(object):
    sequence = 0

    def __init__(self, help=None):
        self._seq = self.sequence
        self._name = "unknown"
        SchemaType.sequence += 1

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self._name)

    def __lt__(self, other):
        return self._seq < other._seq

class SchemaMetaclass(type):
    def __new__(cls, name, bases, attrs):
        print name, attrs
        fields = []
        for n, v in attrs.items():
            if isinstance(v, SchemaType):
                v._name = n
                fields.append(v)
        fields.sort()
        attrs['fields'] = fields
        return super(SchemaMetaclass, cls).__new__(cls, name, bases, attrs)

class Schema(object):
    __metaclass__ = SchemaMetaclass

Int = Float = SchemaType

class SomeXModule(object):
    class StateSchema(Schema):
        position = Int(help="This is the position in the sequence.")
        position1 = Int(help="This is the position in the sequence.")
        position2 = Int(help="This is the position in the sequence.")
        position3 = Int(help="This is the position in the sequence.")

    class PreferencesSchema(Schema):
        speed = Float(help="How fast to play the videos.")

    # OR:

    schemas = {
        'state': {
            'position': Int(help="assdf"),
        },
        'preferences': {
            'speed': 'float',
        },
    }


    # OR:

    schemas = {
        'state': [
            scope(student=False, etc),
            Int('position', help="The position in the sequence."),
            Int('stars', help="How many stars did you give to this sequence?"),
            String('last_answer', help="something else", default="foo"),
        ],
        'preferences': [
            Float('speed', help="How fast should videos play?", default=1.0),
        ],

    # OR:

    state_schema = [
        Int('position', help="The position in the sequence."),
        Int('stars', help="How many stars did you give to this sequence?"),
        String('last_answer', help="something else", default="foo"),
    ]
    preferences_schema = [
        Float('speed', help="How fast should videos play?", default=1.0),
    ]
