import unittest

from mdssdk.vsan import Vsan, VsanNotPresent, InvalidInterface
from mdssdk.connection_manager.errors import CLIError
from mdssdk.fc import Fc
from mdssdk.portchannel import PortChannel
from tests.test_vsan.vsan_vars import *

log = logging.getLogger(__name__)

class TestVsanAddInterfaces(unittest.TestCase):

    def setUp(self) -> None:
        self.switch = sw
        log.info(sw.version)
        log.info(sw.ipaddr)
        self.vsandb = sw.vsans
        while True:
            self.id = get_random_id()
            if self.id not in self.vsandb.keys():
                break
        self.v = Vsan(switch=self.switch, id=self.id)
        self.fc = self.vsandb[1].interfaces[1]   ## fc interface from vsan 1
        self.interfaces = self.switch.interfaces
        while True:
            self.pc_id = get_random_id(1, 256)
            if "port-channel"+str(self.pc_id) not in self.interfaces.keys():
                break
        self.pc = PortChannel(self.switch, self.pc_id) 
        self.invalid_fc = Fc(self.switch, "fc48/48")  ## matches fc pattern but is not present on switch

    def test_addinterfaces_type_error(self):
        self.v.create()
        with self.assertRaises(TypeError) as e:
            self.v.add_interfaces(self.fc)
        self.assertIn("object is not iterable", str(e.exception))
        self.v.delete()

    def test_addinterfaces(self):
        self.v.create()
        self.pc.create()
        self.v.add_interfaces([self.fc, self.pc])
        self.assertEqual(self.fc.name, self.v.interfaces[0].name)
        self.assertEqual(self.pc.name, self.v.interfaces[1].name)
        self.pc.delete()
        self.v.delete()

    def test_addinterfaces_fc_invalid(self):
        self.v.create()
        with self.assertRaises(CLIError) as e:
            self.v.add_interfaces([self.invalid_fc])
        self.assertIn('Invalid interface format', str(e.exception))
        self.v.delete()

    def test_addinterfaces_invalid(self):
        self.v.create()
        with self.assertRaises(AttributeError) as e:
            self.v.add_interfaces("asdfg")
        self.assertEqual("'str' object has no attribute 'name'", str(e.exception))
        self.v.delete()

    def test_addinterfaces_nonexistingvsan(self):
        with self.assertRaises(VsanNotPresent) as e:
            self.v.add_interfaces([self.fc])
        self.assertEqual("VsanNotPresent: Vsan " + str(self.id) + " is not present on the switch.", str(e.exception))

    def test_addinterfaces_repeated(self):
        self.v.create()
        self.pc.create()
        self.v.add_interfaces([self.fc, self.fc, self.pc]) ## pc will not be added
        self.assertEqual(self.fc.name, self.v.interfaces[0].name)
        self.assertEqual(1, len(self.v.interfaces))
        self.pc.delete()
        self.v.delete()

    def test_addinterfaces_portchannelnotpresent(self):
        self.v.create()
        with self.assertRaises(CLIError) as e: 
            self.v.add_interfaces([self.pc])
        self.assertEqual(
            'The command " vsan database ; vsan ' + str(self.id) + ' interface port-channel' + str(
                self.pc.id) + ' " gave the error " Invalid range ".',
            str(e.exception))
        self.v.delete()

    def tearDown(self) -> None:
        if self.v.id is not None:
            self.v.delete()
        if self.pc.name is not None:
            self.pc.delete()
        self.vsandb[1].add_interfaces([self.fc])
        self.assertEqual(self.vsandb.keys(), sw.vsans.keys())
