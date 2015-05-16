import errno
import os
import re
import shutil
import unittest
import uuid

from Pegasus.db import connection
from Pegasus.db.admin.admin_loader import *
from Pegasus.db.schema import *

class TestDBAdmin(unittest.TestCase):
    
    def test_create_database(self):
        filename = str(uuid.uuid4())
        _silentremove(filename)
        dburi = "sqlite:///%s" % filename
        
        db = connection.connect(dburi, create=True)
        self.assertTrue(db_verify(db))
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        
        db.execute("DROP TABLE dbversion")
        self.assertRaises(DBAdminError, db_verify, db)
        db.close()
        db = connection.connect(dburi, create=True)
        self.assertTrue(db_verify(db))
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        
        db.execute("DELETE FROM dbversion")
        self.assertTrue(db_verify(db))
        db.close()
        db = connection.connect(dburi, create=True)
        self.assertTrue(db_verify(db))
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        
        # db_downgrade(db, "4.4.2")
        # self.assertEquals(db_current_version(db), 2)
        db.execute("DROP TABLE rc_lfn")
        self.assertRaises(DBAdminError, db_verify, db)
        db.close()
        db = connection.connect(dburi, create=True)
        self.assertTrue(db_verify(db))
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        
        # db_downgrade(db, "4.3.0")
        # self.assertEquals(db_current_version(db), 1)
        db.execute("DROP TABLE rc_lfn")
        db.execute("DROP TABLE workflow")
        db.execute("DROP TABLE master_workflow")
        self.assertRaises(DBAdminError, db_verify, db)
        self.assertRaises(DBAdminError, db_verify, db, "4.3.0")
        self.assertRaises(DBAdminError, db_current_version, db)
        db.close()
        db = connection.connect(dburi, create=True)
        self.assertTrue(db_verify(db))
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        _remove(filename)
        
    def test_parse_pegasus_version(self):
        self.assertEquals(parse_pegasus_version(), CURRENT_DB_VERSION)
        self.assertEquals(parse_pegasus_version(""), CURRENT_DB_VERSION)
        self.assertEquals(parse_pegasus_version("4.3.0"), 1)
        self.assertRaises(DBAdminError, parse_pegasus_version, 0)
        self.assertRaises(DBAdminError, parse_pegasus_version, 1)
        self.assertRaises(DBAdminError, parse_pegasus_version, 4.5)
        self.assertRaises(DBAdminError, parse_pegasus_version, "1.2.3")
        self.assertRaises(DBAdminError, parse_pegasus_version, "a.b.c")
        self.assertRaises(DBAdminError, parse_pegasus_version, "4.3.a")
        self.assertRaises(DBAdminError, parse_pegasus_version, "4.3")
        self.assertRaises(DBAdminError, parse_pegasus_version, "4")
        
    def test_version_operations(self):
        filename = str(uuid.uuid4())
        _silentremove(filename)
        dburi = "sqlite:///%s" % filename
        db = connection.connect(dburi, create=True)

        # db_downgrade(db, "4.4.2")
        # self.assertEquals(db_current_version(db), 2)
        # self.assertRaises(DBAdminError, db_verify, db)
        #
        # db_downgrade(db)
        # self.assertEquals(db_current_version(db), 1)
        # self.assertRaises(DBAdminError, db_verify, db)
        # db.close()
        #
        # db = connection.connect(dburi, create=True, pegasus_version="4.4.0")
        # self.assertEquals(db_current_version(db), 2)
        # self.assertRaises(DBAdminError, db_verify, db)
        # db.close()
        
        db = connection.connect(dburi, create=True)
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        self.assertTrue(db_verify(db))
        _remove(filename)
        
    # def test_minimum_downgrade(self):
    #     filename = str(uuid.uuid4())
    #     _silentremove(filename)
    #     dburi = "sqlite:///%s" % filename
    #     db = connection.connect(dburi, create=True)
    #
    #     db_downgrade(db, "4.3.0")
    #     self.assertEquals(db_current_version(db), 1)
    #
    #     db_downgrade(db)
    #     self.assertEquals(db_current_version(db), 1)
    #     _remove(filename)
    #
    # def test_all_downgrade_update(self):
    #     filename = str(uuid.uuid4())
    #     print filename
    #     _silentremove(filename)
    #     dburi = "sqlite:///%s" % filename
    #     db = connection.connect(dburi, create=True)
    #
    #     db_downgrade(db, "4.3.0")
    #     self.assertEquals(db_current_version(db), 1)
    #     self.assertRaises(DBAdminError, db_verify, db)
    #     self.assertTrue(db_verify(db, "4.3.0"))
    #     db.close()
    #
    #     db = connection.connect(dburi, create=True)
    #     self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
    #     self.assertTrue(db_verify(db))
    #     _remove(filename)
        
    def test_partial_database(self):
        filename = str(uuid.uuid4())
        _silentremove(filename)
        dburi = "sqlite:///%s" % filename
        db = connection.connect(dburi, schema_check=False, create=False)
        rc_sequences.create(db.get_bind(), checkfirst=True)
        rc_lfn.create(db.get_bind(), checkfirst=True)
        rc_attr.create(db.get_bind(), checkfirst=True)
        self.assertRaises(DBAdminError, db_verify, db)
        db.close()
        
        db = connection.connect(dburi, create=True)
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        self.assertTrue(db_verify(db))
        _remove(filename)
        
        db = connection.connect(dburi, schema_check=False, create=False)
        pg_workflow.create(db.get_bind(), checkfirst=True)
        pg_workflowstate.create(db.get_bind(), checkfirst=True)
        pg_ensemble.create(db.get_bind(), checkfirst=True)
        pg_ensemble_workflow.create(db.get_bind(), checkfirst=True)
        self.assertRaises(DBAdminError, db_verify, db)
        db.close()
        
        db = connection.connect(dburi, create=True)
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        self.assertTrue(db_verify(db))
        _remove(filename)
        
        db = connection.connect(dburi, schema_check=False, create=False)
        st_workflow.create(db.get_bind(), checkfirst=True)
        st_workflowstate.create(db.get_bind(), checkfirst=True)
        st_host.create(db.get_bind(), checkfirst=True)
        st_job.create(db.get_bind(), checkfirst=True)
        st_job_edge.create(db.get_bind(), checkfirst=True)
        st_job_instance.create(db.get_bind(), checkfirst=True)
        st_jobstate.create(db.get_bind(), checkfirst=True)
        st_task.create(db.get_bind(), checkfirst=True)
        st_task_edge.create(db.get_bind(), checkfirst=True)
        st_invocation.create(db.get_bind(), checkfirst=True)
        st_file.create(db.get_bind(), checkfirst=True)
        self.assertRaises(DBAdminError, db_verify, db)
        db.close()
        
        db = connection.connect(dburi, create=True)
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        self.assertTrue(db_verify(db))
        _remove(filename)
        
    def test_malformed_db(self):
        filename = str(uuid.uuid4())
        _silentremove(filename)
        dburi = "sqlite:///%s" % filename
        db = connection.connect(dburi, create=True)
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        db.execute("DROP TABLE rc_lfn")
        self.assertRaises(DBAdminError, db_verify, db)
        db.close()
        
        db = connection.connect(dburi, create=True)
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        db.close()
        _remove(filename)

    def test_connection_from_properties_file(self):
        props_filename = str(uuid.uuid4())
        filename = str(uuid.uuid4())
        _silentremove(filename)
        dburi = "sqlite:///%s" % filename

        f = open(props_filename,'w')
        # JDBCRC
        f.write('pegasus.catalog.replica=JDBCRC\n')
        f.write('pegasus.catalog.replica.db.driver=SQLite\n')
        f.write('pegasus.catalog.replica.db.url=jdbc:sqlite:%s\n' % filename)
        # MASTER
        f.write('pegasus.dashboard.output=%s\n' % dburi)
        # WORKFLOW
        f.write('pegasus.monitord.output=%s\n' % dburi)
        f.close()

        db = connection.connect_by_properties(props_filename, connection.DBType.JDBCRC, create=True)
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        db.close()
        _remove(filename)

        db = connection.connect_by_properties(props_filename, connection.DBType.MASTER, create=True)
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        db.close()
        _remove(filename)

        db = connection.connect_by_properties(props_filename, connection.DBType.WORKFLOW, create=True)
        self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
        db.close()
        _remove(filename)
        _silentremove(props_filename)
        
    def test_dbs(self):
        dbs = ["test-01.db", "test-02.db"]

        for db in dbs:
            orig_filename = os.path.dirname(os.path.abspath(__file__)) + "/input/" + db
            filename = str(uuid.uuid4())
            shutil.copyfile(orig_filename, filename)
            dburi = "sqlite:///%s" % filename
            
            db = connection.connect(dburi, create=False, schema_check=False)
            self.assertRaises(DBAdminError, db_verify, db)
            db.close()
            
            db = connection.connect(dburi, create=True)
            self.assertEquals(db_current_version(db), CURRENT_DB_VERSION)
            db.close()
            _remove(filename)
            
                
def _silentremove(filename):
    try:
        os.remove(filename)
    except OSError, e:
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured
            
            
def _remove(filename):
    for f in os.listdir("."):
        if re.search(filename + ".*", f):
            os.remove(f)


if __name__ == '__main__':
    unittest.main()
