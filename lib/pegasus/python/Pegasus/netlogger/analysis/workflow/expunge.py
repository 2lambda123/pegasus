__author__ = "Monte Goode"

import os, time

from Pegasus.netlogger.analysis.schema.stampede_schema import *
from Pegasus.netlogger.analysis.schema.stampede_dashboard_schema import *
from Pegasus.netlogger.analysis.modules import SQLAlchemyInit
from Pegasus.netlogger import util
from Pegasus.netlogger.nllog import DoesLogging


class Expunge(SQLAlchemyInit, DoesLogging):
    """
    Utility class to expunge a workflow and the associated data from
    a stampede schema database in the case of running with the replay
    option or a similar situation.

    The wf_uuid that is passed into the constructor MUST be the
    "top-level" workflow the user wants to delete.  Which is to
    say if the wf_uuid is a the child of another workflow, then
    only the data associated with that workflow will be deleted.
    Any parent or sibling workflows will be left untouched.

    Usage::

     from Pegasus.netlogger.analysis.workflow.expunge import Expunge

     connString = 'sqlite:///pegasusMontage.db'
     wf_uuid = '1249335e-7692-4751-8da2-efcbb5024429'
     e = Expunge(connString, wf_uuid)
     e.expunge()

    All children/grand-children/etc information and associated
    workflows will be removed.
    """
    def __init__(self, connString, wf_uuid):
        """
        Init object

        @type   connString: string
        @param  connString: SQLAlchemy connection string - REQUIRED
        @type   wf_uuid: string
        @param  wf_uuid: The wf_uuid string of the workflow to remove
                along with associated data from the database
        """
        raise NotImplementedError( "Please Load the appropriate Expunge Implementation")

    def expunge(self):
        """
        Invoke this to remove workflow/information from DB.
        """

        raise NotImplementedError( "Please Load the appropriate Expunge Implementation")

class StampedeExpunge(Expunge):
    """
    Utility class to expunge a workflow and the associated data from
    a stampede schema database in the case of running with the replay
    option or a similar situation.

    The wf_uuid that is passed into the constructor MUST be the 
    "top-level" workflow the user wants to delete.  Which is to
    say if the wf_uuid is a the child of another workflow, then
    only the data associated with that workflow will be deleted.  
    Any parent or sibling workflows will be left untouched.

    Usage::

     from Pegasus.netlogger.analysis.workflow.expunge import Expunge

     connString = 'sqlite:///pegasusMontage.db'
     wf_uuid = '1249335e-7692-4751-8da2-efcbb5024429'
     e = Expunge(connString, wf_uuid)
     e.expunge()

    All children/grand-children/etc information and associated
    workflows will be removed.
    """
    def __init__(self, connString, wf_uuid):
        """
        Init object

        @type   connString: string
        @param  connString: SQLAlchemy connection string - REQUIRED
        @type   wf_uuid: string
        @param  wf_uuid: The wf_uuid string of the workflow to remove
                along with associated data from the database
        """
        DoesLogging.__init__(self)
        self.log.info('init.start')
        SQLAlchemyInit.__init__(self, connString, initializeToPegasusDB)
        self._connString = connString
        self._wf_uuid = wf_uuid
        self.log.info('init.end')

    def expunge(self):
        """
        Invoke this to remove workflow/information from DB.
        """

        #PM-652 do nothing for sqlite
        #DB is already rotated in pegasus-monitord
        if self._connString.startswith( "sqlite:" ):
            return

        self.log.info('stampede.expunge.start')


        self.session.autoflush=True
        # delete main workflow uuid and start cascade
        query = self.session.query(Workflow).filter(Workflow.wf_uuid == self._wf_uuid)
        try:
            wf = query.one()
        except orm.exc.NoResultFound, e:
            self.log.warn('stampede.expunge', msg='No workflow found with wf_uuid %s - aborting expunge' % self._wf_uuid)
            return

        root_wf_id = wf.wf_id

        self.log.info('expunge', msg='Flushing top-level workflow: %s' % wf.wf_uuid)
        i = time.time()
        self.session.delete(wf)
        self.session.flush()
        self.session.commit()
        self.log.info('expunge', msg=' Flush took: %f seconds' % (time.time() - i) )
        # Disable autoflush
        self.session.autoflush=False


class DashboardExpunge(Expunge):
    """
    Utility class to expunge a workflow and the associated data from
    a stampede schema database in the case of running with the replay
    option or a similar situation.

    The wf_uuid that is passed into the constructor MUST be the
    "top-level" workflow the user wants to delete.  Which is to
    say if the wf_uuid is a the child of another workflow, then
    only the data associated with that workflow will be deleted.
    Any parent or sibling workflows will be left untouched.

    Usage::

    from Pegasus.netlogger.analysis.workflow.expunge import Expunge

    connString = 'sqlite:///pegasusMontage.db'
    wf_uuid = '1249335e-7692-4751-8da2-efcbb5024429'
    e = Expunge(connString, wf_uuid)
    e.expunge()

    All children/grand-children/etc information and associated
    workflows will be removed.
    """
    def __init__(self, connString, wf_uuid):
        """
        Init object

        @type   connString: string
        @param  connString: SQLAlchemy connection string - REQUIRED
        @type   wf_uuid: string
        @param  wf_uuid: The wf_uuid string of the workflow to remove
                along with associated data from the database
        """
        DoesLogging.__init__(self)
        self.log.info('init.start')
        SQLAlchemyInit.__init__(self, connString, initializeToDashboardDB )
        self._wf_uuid = wf_uuid
        self.log.info('init.end')

    def expunge(self):
        """
        Invoke this to remove workflow/information from DB.
        """
        self.log.info('dashboard.expunge.start')
        self.session.autoflush=True
        # delete main workflow uuid and start cascade
        query = self.session.query(DashboardWorkflow).filter(DashboardWorkflow.wf_uuid == self._wf_uuid)
        try:
            wf = query.one()
        except orm.exc.NoResultFound, e:
            self.log.warn('dashboard.expunge', msg='No workflow found with wf_uuid %s - aborting expunge' % self._wf_uuid)
            return


        query = self.session.query( DashboardWorkflowstate ).filter( DashboardWorkflowstate.wf_id == wf.wf_id )
        try:
            states = query.all()
        except orm.exc.NoResultFound, e:
            self.log.warn('dashboard.expunge', msg='No dashboard workflow state found with workflow found with wf_uuid %s - aborting expunge' % self._wf_uuid)
            return

        # expunge all the associated workflow states first
        for state in states:
            self.log.info('dashboard.expunge', msg='Expunging workflow state for workflow : %s' % wf.wf_id )
            i = time.time()
            self.session.delete(state)
            self.session.flush()
            self.session.commit()
            self.log.info('dashboard.expunge', msg='Flush took: %f seconds' % (time.time() - i))


        # expunge the workflow from the workflow table
        self.log.info('dashboard.expunge', msg='Flushing workflow from workflow table: %s' % wf.wf_uuid)
        i = time.time()
        self.session.delete(wf)
        self.session.flush()
        self.session.commit()
        self.log.info('dashboard.expunge', msg=' Flush took: %f seconds' % (time.time() - i) )
        # Disable autoflush
        self.session.autoflush=False

