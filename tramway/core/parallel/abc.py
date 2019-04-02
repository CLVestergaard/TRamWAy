# -*- coding: utf-8 -*-

# Copyright © 2019, Institut Pasteur
#   Contributor: François Laurent

# This file is part of the TRamWAy software available at
# "https://github.com/DecBayComp/TRamWAy" and is distributed under
# the terms of the CeCILL license as circulated at the following URL
# "http://www.cecill.info/licenses.en.html".

# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


from abc import *


class Workspace(metaclass=ABCMeta):
    """ Parameter singleton.

    A computation will typically instanciates a unique workspace that will be
    embedded in and shared between multiple :class:`JobStep` instances.

    It embarks resources that a job step may access.
    """
    @abstractmethod
    def update(self, step):
        """ Update the workspace with a completed job step.

        Arguments:

            step (JobStep): completed job step.

        May be implemented as follows::

            step.set_workspace(self)

        """
        raise NotImplementedError('abstract method')

    @abstractmethod
    def __len__(self):
        """ `int`: Total number of resource items."""
        raise NotImplementedError('abstract method')

    @abstractmethod
    def resources(self, step):
        """ May be implemented as follows::

            return step.resources

        See also: `JobStep.resources`."""
        raise NotImplementedError('abstract method')

    #@abstractmethod
    #def set_extensions(self, extensions):
    #    raise NotImplementedError('abstract method')


class JobStep(metaclass=ABCMeta):
    """ Job step data.

    A job step object contains all the necessary input data for a job step
    to be performed as well as the output data resulting from the step completion.

    A job step object merely contains a reference to a shared workspace.

    The `resource_id` attribute refers to a series of the job steps that operate
    on the same subset of resource items.

    """
    @abstractmethod
    def get_workspace(self):
        raise NotImplementedError('abstract method')
    @abstractmethod
    def set_workspace(self, ws):
        raise NotImplementedError('abstract method')
    @abstractmethod
    def unset_workspace(self):
        raise NotImplementedError('abstract method')
    @property
    @abstractmethod
    def workspace_set(self):
        """ `bool`: Is the workspace set?"""
        raise NotImplementedError('abstract method')
    @property
    @abstractmethod
    def resource_id(self):
        """ `int`: Resource-related job ID.

        A job step is one of many that operate on a same subset of resources.
        `resource_id` uniquely designates this specific subset of resources.
        """
        raise NotImplementedError('abstract ro property')
    @property
    @abstractmethod
    def resources(self):
        """ `sequence`: Indices or keys of the required items of resource in the workspace.

        May be implemented as follows::

            return self.get_workspace().resources(self)

        """
        raise NotImplementedError('abstract ro property')


class WorkspaceExtension(metaclass=ABCMeta):
    @abstractmethod
    def pop_workspace_update(self):
        raise NotImplementedError('abstract method')
    @abstractmethod
    def push_workspace_update(self, upload):
        raise NotImplementedError('abstract method')


__all__ = [ 'Workspace', 'JobStep', 'WorkspaceExtension' ]

