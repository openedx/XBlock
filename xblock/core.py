"""
Core classes for the XBlock family.

This code is in the Runtime layer, because it is authored once by edX
and used by all runtimes.
"""
from __future__ import annotations

import inspect
import os
import warnings
import typing as t
from collections import defaultdict

import pkg_resources
from lxml import etree
from opaque_keys.edx.keys import LearningContextKey, UsageKey
from web_fragments.fragment import Fragment

import xblock.exceptions
from xblock.exceptions import DisallowedFileError
from xblock.fields import String, List, Scope, ScopeIds
from xblock.field_data import FieldData
from xblock.internal import class_lazy
import xblock.mixins
from xblock.mixins import (
    ScopedStorageMixin,
    HierarchyMixin,
    RuntimeServicesMixin,
    HandlersMixin,
    XmlSerializationMixin,
    IndexInfoMixin,
    ViewsMixin,
)
from xblock.plugin import Plugin
from xblock.validation import Validation


if t.TYPE_CHECKING:
    from xblock.runtime import Runtime

# exposing XML_NAMESPACES as a member of core, in order to avoid importing mixins where
# XML_NAMESPACES are needed (e.g. runtime.py).
XML_NAMESPACES = xblock.mixins.XML_NAMESPACES

# __all__ controls what classes end up in the docs.
__all__ = ['XBlock']
UNSET = object()


class XBlockMixin(ScopedStorageMixin):
    """
    Base class for XBlock Mixin classes.

    XBlockMixin classes can add new fields and new properties to all XBlocks
    created by a particular runtime.

    """


class SharedBlockBase(Plugin):
    """
    Behaviors and attrs which all XBlock like things should share
    """

    resources_dir: str = ''
    public_dir: str = 'public'
    i18n_js_namespace: str | None = None

    @classmethod
    def get_resources_dir(cls) -> str:
        """
        Gets the resource directory for this XBlock.
        """
        return cls.resources_dir

    @classmethod
    def get_public_dir(cls) -> str:
        """
        Gets the public directory for this XBlock.
        """
        return cls.public_dir

    @classmethod
    def get_i18n_js_namespace(cls) -> str | None:
        """
        Gets the JavaScript translations namespace for this XBlock.

        Returns:
            str: The JavaScript namespace for this XBlock.
            None: If this doesn't have JavaScript translations configured.
        """
        return cls.i18n_js_namespace

    @classmethod
    def open_local_resource(cls, uri: str) -> t.IO[bytes]:
        """
        Open a local resource.

        The container calls this method when it receives a request for a
        resource on a URL which was generated by Runtime.local_resource_url().
        It will pass the URI from the original call to local_resource_url()
        back to this method. The XBlock must parse this URI and return an open
        file-like object for the resource.

        For security reasons, the default implementation will return only a
        very restricted set of file types, which must be located in a folder
        that defaults to "public".  The location used for public resources can
        be changed on a per-XBlock basis. XBlock authors who want to override
        this behavior will need to take care to ensure that the method only
        serves legitimate public resources. At the least, the URI should be
        matched against a whitelist regex to ensure that you do not serve an
        unauthorized resource.
        """

        if isinstance(uri, bytes):
            uri = uri.decode('utf-8')

        # If no resources_dir is set, then this XBlock cannot serve local resources.
        if cls.resources_dir is None:
            raise DisallowedFileError("This XBlock is not configured to serve local resources")

        # Make sure the path starts with whatever public_dir is set to.
        if not uri.startswith(cls.public_dir + '/'):
            raise DisallowedFileError(f"Only files from {cls.public_dir!r}/ are allowed: {uri!r}")

        # Disalow paths that have a '/.' component, as `/./` is a no-op and `/../`
        # can be used to recurse back past the entry point of this XBlock.
        if "/." in uri:
            raise DisallowedFileError("Only safe file names are allowed: %r" % uri)

        return pkg_resources.resource_stream(cls.__module__, os.path.join(cls.resources_dir, uri))


# -- Base Block
class XBlock(XmlSerializationMixin, HierarchyMixin, ScopedStorageMixin, RuntimeServicesMixin, HandlersMixin,
             IndexInfoMixin, ViewsMixin, SharedBlockBase):
    """
    Base class for XBlocks.

    Derive from this class to create a new kind of XBlock.  There are no
    required methods, but you will probably need at least one view.

    Don't provide the ``__init__`` method when deriving from this class.
    """
    entry_point: str = 'xblock.v1'

    name = String(help="Short name for the block", scope=Scope.settings)
    tags: List[str] = List(help="Tags for this block", scope=Scope.settings)

    has_children: bool

    @class_lazy
    def _class_tags(cls: type[XBlock]) -> set[str]:  # type: ignore[misc]
        """
        Collect the tags from all base classes.
        """
        class_tags: set[str] = set()

        for base in cls.mro()[1:]:  # pylint: disable=no-member
            class_tags.update(getattr(base, '_class_tags', set()))

        return class_tags

    @staticmethod
    def tag(tags):
        """Returns a function that adds the words in `tags` as class tags to this class."""
        def dec(cls: type[XBlock]) -> type[XBlock]:
            """Add the words in `tags` as class tags to this class."""
            # Add in this class's tags
            cls._class_tags.update(tags.replace(",", " ").split())  # pylint: disable=protected-access
            return cls
        return dec

    @classmethod
    def load_tagged_classes(
        cls, tag: str, fail_silently: bool = True
    ) -> t.Iterable[tuple[str, type[XBlock]]]:
        """
        Produce a sequence of all XBlock classes tagged with `tag`.

        fail_silently causes the code to simply log warnings if a
        plugin cannot import. The goal is to be able to use part of
        libraries from an XBlock (and thus have it installed), even if
        the overall XBlock cannot be used (e.g. depends on Django in a
        non-Django application). There is diagreement about whether
        this is a good idea, or whether we should see failures early
        (e.g. on startup or first page load), and in what
        contexts. Hence, the flag.
        """
        for name, class_ in cls.load_classes(fail_silently):
            xblock_class: type[XBlock] = class_  # type: ignore
            if tag in xblock_class._class_tags:  # pylint: disable=protected-access
                yield name, xblock_class

    # pylint: disable=keyword-arg-before-vararg
    def __init__(
        self,
        runtime: Runtime,
        field_data: FieldData | None = None,
        scope_ids: ScopeIds | object = UNSET,
        *args,
        **kwargs
    ):
        """
        Construct a new XBlock.

        This class should only be instantiated by runtimes.

        Arguments:

            runtime (:class:`.Runtime`): Use it to access the environment.
                It is available in XBlock code as ``self.runtime``.

            field_data (:class:`.FieldData`): Interface used by the XBlock
                fields to access their data from wherever it is persisted.
                Deprecated.

            scope_ids (:class:`.ScopeIds`): Identifiers needed to resolve
                scopes.
        """
        if scope_ids is UNSET:
            raise TypeError('scope_ids are required')
        else:
            assert isinstance(scope_ids, ScopeIds)

        # Provide backwards compatibility for external access through _field_data
        super().__init__(runtime=runtime, scope_ids=scope_ids, field_data=field_data, *args, **kwargs)

    @property
    def usage_key(self) -> UsageKey:
        """
        A key identifying this particular usage of the XBlock, unique across all learning contexts in the system.

        Equivalent to to `.scope_ids.usage_id`.
        """
        return self.scope_ids.usage_id

    @property
    def context_key(self) -> LearningContextKey | None:
        """
        A key identifying the learning context (course, library, etc.) that contains this XBlock usage.

        Equivalent to `.scope_ids.usage_id.context_key`.

        Returns:
        * `LearningContextKey`, if `.scope_ids.usage_id` is a `UsageKey` instance.
        * `None`, otherwise.

        After https://github.com/openedx/XBlock/issues/708 is complete, we can assume that
        `.scope_ids.usage_id` is always a `UsageKey`, and that this method will
        always return a `LearningContextKey`.
        """
        return getattr(self.scope_ids.usage_id, "context_key", None)

    def render(self, view: str, context: dict | None = None) -> Fragment:
        """Render `view` with this block's runtime and the supplied `context`"""
        return self.runtime.render(self, view, context)

    def validate(self) -> Validation:
        """
        Ask this xblock to validate itself. Subclasses are expected to override this
        method, as there is currently only a no-op implementation. Any overriding method
        should call super to collect validation results from its superclasses, and then
        add any additional results as necessary.
        """
        return Validation(self.scope_ids.usage_id)

    def ugettext(self, text) -> str:
        """
        Translates message/text and returns it in a unicode string.
        Using runtime to get i18n service.
        """
        runtime_service = self.runtime.service(self, "i18n")
        runtime_ugettext = runtime_service.ugettext
        return runtime_ugettext(text)

    def add_xml_to_node(self, node: etree._Element) -> None:
        """
        For exporting, set data on etree.Element `node`.
        """
        super().add_xml_to_node(node)
        # Add children for each of our children.
        self.add_children_to_node(node)


# An XBlockAside's view method takes itself, an XBlock, and optional context dict,
# and returns a Fragment.
AsideView = t.Callable[["XBlockAside", XBlock, t.Optional[dict]], Fragment]


class XBlockAside(XmlSerializationMixin, ScopedStorageMixin, RuntimeServicesMixin, HandlersMixin, SharedBlockBase):
    """
    This mixin allows Xblock-like class to declare that it provides aside functionality.
    """
    entry_point: str = "xblock_asides.v1"

    @classmethod
    def aside_for(cls, view_name: str) -> t.Callable[[AsideView], AsideView]:
        """
        A decorator to indicate a function is the aside view for the given view_name.

        Aside views should have a signature like::

            @XBlockAside.aside_for('student_view')
            def student_aside(self, block, context=None):
                ...
                return Fragment(...)

        """
        # pylint: disable=protected-access
        def _decorator(func: AsideView) -> AsideView:
            if not hasattr(func, '_aside_for'):
                func._aside_for = []  # type: ignore

            func._aside_for.append(view_name)  # type: ignore
            return func
        return _decorator

    @classmethod
    def should_apply_to_block(cls, block: XBlock) -> bool:  # pylint: disable=unused-argument
        """
        Return True if the aside should be applied to a given block. This can be overridden
        if some aside should only wrap blocks with certain properties.
        """
        return True

    @class_lazy
    def _combined_asides(cls) -> dict[str, str | None]:  # pylint: disable=no-self-argument
        """
        A dictionary mapping XBlock view names to the aside method that
        decorates them (or None, if there is no decorator for the specified view).
        """
        # The method declares what views it decorates. We rely on `dir`
        # to handle subclasses and overrides.
        combined_asides: dict[str, str | None] = defaultdict(None)
        for _view_name, view_func in inspect.getmembers(cls, lambda attr: hasattr(attr, '_aside_for')):
            aside_for = getattr(view_func, '_aside_for', [])
            for view in aside_for:
                combined_asides[view] = view_func.__name__
        return combined_asides

    def aside_view_declaration(self, view_name: str) -> AsideView | None:
        """
        Find and return a function object if one is an aside_view for the given view_name

        Aside methods declare their view provision via @XBlockAside.aside_for(view_name)
        This function finds those declarations for a block.
        """
        if view_name in self._combined_asides:  # pylint: disable=unsupported-membership-test
            return getattr(self, self._combined_asides[view_name])  # pylint: disable=unsubscriptable-object
        else:
            return None

    def needs_serialization(self) -> bool:
        """
        Return True if the aside has any data to serialize to XML.

        If all of the aside's data is empty or a default value, then the aside shouldn't
        be serialized as XML at all.
        """
        return any(field.is_set_on(self) for field in self.fields.values())  # pylint: disable=no-member


class KeyValueMultiSaveError(xblock.exceptions.KeyValueMultiSaveError):
    """
    Backwards compatibility class wrapper around :class:`.KeyValueMultiSaveError`.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn("Please use xblock.exceptions.KeyValueMultiSaveError", DeprecationWarning, stacklevel=2)
        super().__init__(*args, **kwargs)


class XBlockSaveError(xblock.exceptions.XBlockSaveError):
    """
    Backwards compatibility class wrapper around :class:`.XBlockSaveError`.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn("Please use xblock.exceptions.XBlockSaveError", DeprecationWarning, stacklevel=2)
        super().__init__(*args, **kwargs)
