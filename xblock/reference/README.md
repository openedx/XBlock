XBlocks Reference Implementations
=================================

This directory contains reference implementations for XBlock services,
fields, and common XBlocks.

All of the plug-ins in this directory are intended either as standard
components which most runtimes are expected to implement, or
candidates there-of.

Plug-ins within XBlocks fall into three categories right now: 

* XBlocks. Client-viewable self-contained chunks of functionality,
  including data and code.
* Services. Things like tools for getting at data from other parts of
  the system, creating and extracting educational analytics, and
  similar.
* Fields. These store data for XBlocks. 

It is likely that this taxonomy may be rethought at some point, and
become more fluid. XBlocks need to talk to each other, in much the
same way they talk to services. Fields and XBlocks both store data,
and XBlocks need access to not only their own Field data, but of other
XBlocks. Fields need editing views (now up to each runtime). XBlocks
provide editing views. We may try to tease apart or refactor in the
future. Etc.

The reference implementations are intended to serve as a good starting
point for building your own runtime. They are: 

* In contrast to the rest of the XBlock repo, dependent on specific
  technologies (e.g. Django). In general, the choice of technologies
  is for maximum simplicity, debuggability, and readability (as 
  opposed to scalability and performance). 
* Intended to be readable, documented and easy to understand. 
* As a side-effect of the above, implementations are intended to be
  relatively minimal. Practical runtimes are likely to need higher
  complexity, higher-performance implementations. 

The reference implementations include both completed plug-ins, and
prototypes intended to serve as RFCs and points of discussion. 

