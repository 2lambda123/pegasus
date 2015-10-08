import os
import unittest

from Pegasus.db.admin.admin_loader import *
from Pegasus.db.modules.stampede_loader import Analyzer
from Pegasus.service.monitoring.anomaly_handler import AnomalyHandler
from Pegasus.monitoring import event_output as eo

import Pegasus.test.dax3


class TestAnomalyHandler(unittest.TestCase):
    def setUp(self):
        logging.basicConfig()
        self.db_file = "anomalies-test.stampede.db"
        db_test_path = os.path.dirname(Pegasus.test.dax3.__file__)

        shutil.copy(("%s/%s" % (db_test_path, self.db_file)), self.db_file)

        dburi = "sqlite:///%s" % os.path.abspath(self.db_file)
        # print "DB URI: %s" % dburi
        self.analyzer = Analyzer(dburi)
        self.db_session = self.analyzer.session

        self.wf_uuid = "143acf4d-8494-4c0f-baf0-2b0ff4464390"
        self.anomaly_handler = None

        try:
            self.anomaly_handler = AnomalyHandler("test-anomalies", self.wf_uuid, dburi)
        except eo.SchemaVersionError:
            print "****************************************************"
            print "Detected database schema version mismatch!"
            print "cannot create events output... disabling event output!"
            print "****************************************************"
        except:
            print "cannot create events output... disabling event output!"

    def tearDown(self):
        # print "Removing test stampede db"
        self.db_session.close()
        self.anomaly_handler.close()
        for fl in glob.glob("anomalies-test.stampede.db*"):
            os.remove(fl)

    def test_insert_measurement(self):
        anomaly = {
            "ts": "1496389227",
            "dag_job_id": "namd_ID0000002",
            "wf_uuid": "143acf4d-8494-4c0f-baf0-2b0ff4464390",
            "anomaly_type": "kickstart.threshold_exceeded",
            "metrics": { "kickstart": ["stime"] },
            "value": 293847324,
            "threshold": "12832131",
            "message": "The 'vmRSS' value exceeded the threshold (293847324 > 12832131)"
        }

        self.analyzer.anomaly_detected(anomaly)

        result = self.db_session.query(Anomaly).filter(Anomaly.anomaly_type == anomaly["anomaly_type"]).all()

        self.assertEquals(len(result), 1)
        self.assertEquals(int(result[0].ts), int(anomaly["ts"]))
        self.assertEquals(int(result[0].job_instance_id), 6)

    def test_on_message_integration(self):
        self.assertIsNotNone(self.anomaly_handler, "anomaly handler wasn't initialized correctly")

        msg_body = "ts=1437389227|||" \
                   "wf_uuid=143acf4d-8494-4c0f-baf0-2b0ff4464390|||" \
                   "dag_job_id=namd_ID0000003|||" \
                   "anomaly_type=kickstart.threshold_exceeded|||" \
                   "message=The 'stime' value exceeded the threshold (10.83 > 10.0)|||" \
                   "metrics={\"kickstart\": [\"stime\"] }|||" \
                   "value=10.83|||" \
                   "threshold=10.0|||"\
                   "raw_data={\"ts\":1437389227}"

        self.anomaly_handler.on_message(None, None, None, msg_body)

        result = self.anomaly_handler.event_sink._db.session.query(Anomaly). \
            filter(Anomaly.ts == 1437389227, Anomaly.job_instance_id == 10).all()

        self.assertEquals(len(result), 1)

    def test_on_message_infrastructure_anomalies(self):
        self.assertIsNotNone(self.anomaly_handler, "anomaly handler wasn't initialized correctly")

        msg_body = "ts=1435854843134|||" \
                   "wf_uuid=143acf4d-8494-4c0f-baf0-2b0ff4464390|||" \
                   "dag_job_id=sassena_ID0000005|||" \
                   "infra_db_io=sarIO|||" \
                   "infra_series_io=wsu-w6|141.217.114.152|172.16.1.1|2015-07-30 11:56:26|||" \
                   "anomaly_type=correlated.app.infra.io|||" \
                   "metrics={\"kickstart\": [\"iowait\", \"write_bytes\"] , \"infra\": [\"write_bandwidth\"]}|||" \
                   "message=string about infra i/o anomaly and corresponding observed app anomaly; output of time series analysis; also thresholdX was exceeded|||" \
                   "value=2.1|||" \
                   "threshold=2.0|||" \
                   "ts_stop=1435857000|||" \
                   "raw_data={\"ts\": 1437389227, \"wf_uuid\": \"143acf4d-8494-4c0f-baf0-2b0ff4464390\", \"dag_job_id\": \"sassena_ID0000005\",    \"infra_db_io\": \"sarIO\",    \"infra_series_io\": \"wsu-w6|141.217.114.152|172.16.1.1|2015-07-30 11:56:26\",    \"anomaly_type\": \"correlated.app.infra.io\",    \"metrics\": {        \"kickstart\": [            \"iowait\",            \"write_bytes\"        ],        \"infra\": [            \"write_bandwidth\"        ]    },\"message\": \"string about infra i/o anomaly and corresponding observed app anomaly; output of time series analysis; also thresholdX was exceeded\",    \"value\": 10.83,    \"threshold\": 10, \"ts_stop\": 1435857000}"

        print msg_body
        self.anomaly_handler.on_message(None, None, None, msg_body)

        result = self.anomaly_handler.event_sink._db.session.query(Anomaly). \
            filter(Anomaly.dag_job_id == "sassena_ID0000005", Anomaly.ts == 1435854843134).all()

        self.assertEquals(len(result), 1)


if __name__ == '__main__':
    unittest.main()
