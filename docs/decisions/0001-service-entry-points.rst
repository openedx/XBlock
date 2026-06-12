0001 Plugin-provided runtime services via entry points
######################################################

Status
******

Proposed

Context
*******

XBlocks consume capabilities from their environment through *runtime
services*: a block declares ``@XBlock.needs("name")`` or
``@XBlock.wants("name")`` and calls ``self.runtime.service(self, "name")``.
The base ``Runtime.service()`` resolves the name against the ``_services``
dict that the runtime application populated at construction time.

This makes the *consumption* side of services fully generic, but the
*provision* side closed: only the application that instantiates the runtime
can decide which services exist.  In Open edX — by far the largest user of
this library — service wiring is hardcoded in several places
(``ModuleStoreRuntime`` service dicts for LMS/Studio/preview, and the
``if/elif`` chain in the newer ``XBlockRuntime``), and there is no supported
way for a separately installed package to offer a new service.

The need is real and recurring.  The motivating case is an AI-extensions
plugin that wants to offer an ``"ai_extensions"`` service so that blocks like
ORA can call LLM workflows without pinning provider SDKs or importing plugin
internals (see the community thread in the References).  But the same gap
applies to any optional capability a pip-installed package might offer to
blocks: translation backends, proctoring integrations, institution-specific
storage, and so on.

Two facts about the existing design make this library the right place to
close the gap:

1. **Every runtime already funnels through ``Runtime.service()``.**  Open edX
   runtimes either populate ``_services`` and delegate to the base method
   (``ModuleStoreRuntime``), or run their own chain and fall back to the base
   method (``XBlockRuntime``).  The xblock-sdk workbench uses the base
   behavior directly.  A fallback added here is therefore reached by every
   known runtime without any changes to host applications.

2. **The library already has the discovery machinery and the stated intent.**
   ``xblock/plugin.py`` loads XBlocks (``xblock.v1``) and asides
   (``xblock_asides.v1``) from entry points, with caching, ambiguity
   detection, and an ``.overrides`` group.  The reference ``Service`` class in
   ``xblock/reference/plugins.py`` has documented the goal for years: services
   should *"be able to load through Stevedore, and have a plug-in mechanism
   similar to XBlock."*

Decision
********

Add a third entry-point group to the XBlock framework, ``xblock.service.v1``,
and a fallback in ``Runtime.service()`` — the ``_load_service_from_entry_point``
method — that consults it.

A package provides a service by declaring::

    entry_points={
        "xblock.service.v1": [
            "my_service = my_package.services:MyService",
        ],
    }

where the entry-point name is the service name blocks declare with
``needs``/``wants``.  Resolution order in ``Runtime.service()`` becomes:

1. Reject undeclared requests (unchanged): a block that never declared the
   service still gets ``NoSuchServiceError``.
2. Return the runtime-provided service from ``_services`` if present
   (unchanged).
3. **New:** if the runtime has nothing, try
   ``_load_service_from_entry_point(block, service_name)``, which loads the
   provider class from the ``xblock.service.v1`` group and instantiates it as
   ``provider_class(runtime=self, xblock=block)``.
4. Apply ``need``/``want`` semantics to the result (unchanged): ``None`` for
   a wanted-but-absent service, ``NoSuchServiceError`` for a needed one.

Reasoning behind the specific choices
=====================================

**Why a fallback in the base class rather than a hook in each runtime.**
Placing the lookup after the ``_services`` miss, inside the one method every
runtime inherits, gives complete coverage (all Open edX runtimes, the
workbench, third-party runtimes that don't override ``service()``) for a
single small change, and gives a hard guarantee: *runtime-provided services
always shadow plugin-provided ones*.  A pip package cannot replace or
intercept ``user``, ``field-data``, ``i18n``, or any other service the host
application provides deliberately.  "Provided" is decided by key presence in
``_services``, not truthiness: runtimes use an explicit ``None`` to mean
"this service exists but is disabled here" — the Open edX LMS maps
``completion`` to ``None`` for anonymous users, and this library's own test
suite passes ``services={'i18n': None}`` — and a plugin must not resurrect a
service the runtime switched off.  Runtimes that override ``service()``
entirely keep that freedom — the fallback only exists in the default path
they opt into by calling ``super().service()``.

**Why entry points rather than configuration.**  Entry points are how this
library already discovers XBlocks and asides, so providers and operators deal
with one consistent model: installing a package is the act that makes its
plugins available, and the trust decision is the install decision — exactly
as it is for XBlocks themselves.  A settings-based registry would be
runtime-application-specific (this library is not Django-bound) and would put
the burden of wiring on every operator instead of on the providing package.

**Why the existing ``Plugin`` loader.**  Reusing ``Plugin.load_class`` buys,
for free: per-process caching of hits *and misses* (steady-state cost of the
fallback is one dict lookup); loud ``AmbiguousPluginError`` when two installed
packages claim the same service name, instead of last-write-wins — the exact
failure mode that makes monkey-patching unacceptable; a sanctioned override
path (``xblock.service.v1.overrides``) when replacing a default implementation
is intentional; and ``register_temp_plugin`` for tests.

**Why ``provider_class(runtime=…, xblock=…)``.**  This mirrors the
constructor of the reference ``Service`` class, gives the provider the two
context objects almost every service needs (and from which the rest — user,
usage key, learning context — is reachable), and keeps the contract so small
that providers do not need to import ``xblock`` at all.  Note that the
fallback returns an *instance*, never a class: some runtimes
(``ModuleStoreRuntime``) call callable services with ``(block)``, and a
class-valued service would be invoked accidentally.  Instantiation is
per-request for now; providers with expensive set-up are expected to cache it
themselves (module- or class-level), consistent with the long-standing
"don't over-initialize" guidance in ``reference/plugins.py``.  Memoizing per
``(runtime, service_name)`` in the base class is a possible follow-up once
real-world usage shows it is needed.

**Why the ``needs``/``wants`` gate stays in front.**  The declaration check
runs before any entry-point lookup, so a plugin-provided service is only ever
handed to blocks that explicitly asked for it.  ``wants`` gives blocks a
portable soft-dependency: the same block works on installs with and without
the providing package, enabling features conditionally.

Rejected alternatives
=====================

* **Wiring extension points into each host-application runtime** (new
  ``openedx.*`` entry-point group, an ``XBLOCK_EXTRA_SERVICES`` Django
  setting, or an openedx-filters filter at resolution time) — all viable, but
  each covers only the call sites it patches, must be replicated for every
  current and future runtime, and lives in repositories whose architectural
  direction is to *shrink* their XBlock-runtime surface, not grow it.  These
  were prototyped and documented by the openedx-ai-extensions project (see
  References) before converging here.

Consequences
************

* Installed packages can provide named runtime services to consenting blocks
  on any runtime that uses the default resolution path; no host-application
  changes are required.
* The service namespace becomes shared between runtime applications and
  installed packages.  Runtimes always win, and duplicate provider claims
  fail loudly, but a future registry of well-known service names would help
  providers avoid accidental collisions.
* Operators implicitly accept a package's service registrations by installing
  it, as with XBlocks.  If field experience shows a need for finer control, a
  block-list mechanism can be layered on without changing the provider
  contract.
* The behavior of every existing runtime and block is unchanged unless a
  package registering ``xblock.service.v1`` entry points is installed.

References
**********

* Community discussion: https://discuss.openedx.org/t/plugin-provided-xblock-runtime-services/18682
* Prior analysis and prototypes of the platform-side alternatives:
  ADR-0005 and ADR-0011 in https://github.com/openedx/openedx-ai-extensions
* Original pluggability intent: ``xblock/reference/plugins.py`` (``Service``
  docstring)
* Discovery machinery reused: ``xblock/plugin.py``
* Open edX platform ADR *Role of XBlocks* (scope reduction of the platform
  runtime): ``docs/decisions/0006-role-of-xblock.rst`` in edx-platform
