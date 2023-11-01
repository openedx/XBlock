.. _Submit Your XBlock to edx.org:

###############################
Submit Your XBlock to edX
###############################

Many developers and institutions submit the XBlocks they develop to edX, to
benefit course teams and learners who create and take classes on
`edx.org`_.

Note that you are not required to submit your XBlock to edX. You and other edX service providers can run your XBlock without involving edX.

To submit your XBlock to edx.org, complete the following steps.

#. Upload the XBlock to a repository on GitHub.

#. Create a new branch in the `edx-platform`_ GitHub repository.

#. In your branch, add a line to the `requirements/edx/github.txt`_ file that
   indicates the version of your XBlock to use.

   .. note::
     The requirements file addition is the only change you should make in your
     branch. Do not include the code for your XBlock in the pull request.

#. Create a pull request for your branch in the edx-platform GitHub repository.

#. Add a thorough description of your XBlock and its intended use to the pull
   request. You must include instructions to manually test that the XBlock is
   working properly.

#. Add a link to your XBlock repository in the pull request.

After you submit the pull request, edX will review your XBlock to ensure that
it is appropriate for use on edx.org. Specifically, edX will review your XBlock
for security, scalability, accessibility, and fitness of purpose. You should be
prepared to respond to questions and comments from edX in your pull request.

.. include:: ../../links.rst
