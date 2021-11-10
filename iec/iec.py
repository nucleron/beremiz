
import os
import util.paths as paths
from PLCControler import LOCATION_CONFNODE, LOCATION_VAR_MEMORY

base_folder = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
base_folder = os.path.join(base_folder, "..")
IECPath = os.path.join(os.path.join(os.path.join(base_folder, "lib60870"), "lib60870-C"), "build")
IECIncPath = os.path.join(os.path.join(os.path.join(base_folder, "lib60870"), "lib60870-C"), "src")


class _IECTCPclientPlug(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
        <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            <xsd:element name="IecTcpClient">
              <xsd:complexType>
              <xsd:attribute name="IecTcpClientAttr" use="optional" default="10">
                <xsd:simpleType>
                    <xsd:restriction base="xsd:integer">
                        <xsd:minInclusive value="0"/>
                        <xsd:maxInclusive value="65535"/>
                    </xsd:restriction>
                </xsd:simpleType>
              </xsd:attribute>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>
        """
    PlugType = "IecTcpClient"

    def __init__(self):
        loc_str = ".".join(map(str, self.GetCurrentLocation()))
        #self.IecTcpClient.setConfiguration_Name("Iec Tcp Client " + loc_str)

    def CTNGenerate_C(self, buildpath, locations):
        return [], "", False


class _IECServerMemoryPlug(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="MemoryArea">
        <xsd:complexType>
          <xsd:attribute name="MemoryAreaType" type="xsd:string" use="optional" default="01 - Coils"/>
          <xsd:attribute name="Nr_of_Channels" use="optional" default="1">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="1"/>
                    <xsd:maxInclusive value="65536"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
          <xsd:attribute name="Start_Address" use="optional" default="0">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="0"/>
                    <xsd:maxInclusive value="65535"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """
    PlugType = "IecTcpServerMemory"

    def GetVariableLocationTree(self):
        current_location = self.GetCurrentLocation()
        name = self.BaseParams.getName()
        entries = []
        # Last nodes of IEC tree, It means variables.
        address = self.GetParamsAttributes()[0]["children"][2]["value"]
        count = self.GetParamsAttributes()[0]["children"][1]["value"]
        for offset in range(address, address + count):
            entries.append({
                "name": 'Variable' + " " + str(offset),
                "type": LOCATION_VAR_MEMORY,
                "size": 16,
                "IEC_type": "WORD",
                "var_name": "IEC_" + "VARIABLE_" + str(offset),
                "location": "W" + ".".join([str(i) for i in current_location]) + "." + str(offset),
                "description": "description",
                "children": []})
        return {"name": name,
                "type": LOCATION_CONFNODE,
                "location": ".".join([str(i) for i in current_location]) + ".x",
                "children": entries}


class _IECTCPserverPlug(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
        <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
          <xsd:element name="IecTcpServer">
              <xsd:complexType>
                <xsd:attribute name="Configuration_Name" type="xsd:string" use="optional" default=""/>
                <xsd:attribute name="Local_IP_Address" type="xsd:string" use="optional"  default="localhost"/>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>
        """
    CTNChildrenTypes = [("IecTcpServerMemory", _IECServerMemoryPlug, "Memory Area")]
    PlugType = "IecTcpServer"

    def __init__(self):
        loc_str = ".".join(map(str, self.GetCurrentLocation()))
        self.IecTcpServer.setConfiguration_Name("IEC TCP Server " + loc_str)

    def GetServerIP(self):
        return self.IecTcpServer.getLocal_IP_Address()

    def CTNGenerate_C(self, buildpath, locations):
        return [], "", False

#
#
#
# R O O T    C L A S S                #
#
#
#
class RootClass(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="IECRoot">
        <xsd:complexType>
          <xsd:attribute name="MyTestAttribute" use="optional" default="10">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="0"/>
                    <xsd:maxInclusive value="65535"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """
    CTNChildrenTypes = [("IecTcpClient", _IECTCPclientPlug, "IEC TCP Client"),
                        ("IecTcpServer", _IECTCPserverPlug, "IEC TCP Server")]


    def CTNGenerate_C(self, buildpath, locations):
        loc_dict = {"locstr": "_".join(map(str, self.GetCurrentLocation()))}

        # Determine the current location in Beremiz's project configuration
        # tree
        current_location = self.GetCurrentLocation()

        # define a unique name for the generated C and h files
        prefix = "_".join(map(str, current_location))
        Gen_IEC_c_path = os.path.join(buildpath, "IEC_%s.c" % prefix)
        Gen_IEC_h_path = os.path.join(buildpath, "IEC_%s.h" % prefix)
        c_filename = os.path.join(os.path.split(__file__)[0], "iec_runtime.c")
        h_filename = os.path.join(os.path.split(__file__)[0], "iec_runtime.h")


        number_of_severs = 0
        iec_server_ips = ""
        loc_vars = []
        for child in self.IECSortedChildren():
            if child.PlugType == "IecTcpServer":
                if number_of_severs > 0:
                    iec_server_ips = iec_server_ips + ", "
                iec_server_ips = iec_server_ips + "\"" + child.GetServerIP() + "\""
                for subchild in child.IECSortedChildren():
                    for iecvar in subchild.GetLocations():
                        absloute_address = iecvar["LOC"][3]
                        loc_vars.append("int32_t* " + str(iecvar["NAME"]) + " = &iec_servers[%d].mem.%s[%d];" % (
                            number_of_severs, "variables", absloute_address))
                number_of_severs = number_of_severs + 1

        loc_dict["number_of_servers"] = str(number_of_severs)
        loc_dict["servers_ips"] = iec_server_ips
        loc_dict["loc_vars"] = "\n".join(loc_vars)
        print(loc_dict)


        # get template file content into a string, format it with dict
        # and write it to proper .h file
        mb_main = open(h_filename).read() % loc_dict
        f = open(Gen_IEC_h_path, 'w')
        f.write(mb_main)
        f.close()
        # same thing as above, but now to .c file
        mb_main = open(c_filename).read() % loc_dict
        f = open(Gen_IEC_c_path, 'w')
        f.write(mb_main)
        f.close()

        LDFLAGS = []
        LDFLAGS.append(" \"-L" + IECPath + "\"")
        LDFLAGS.append(" \"" + os.path.join(IECPath, "lib60870.a") + "\"")
        LDFLAGS.append(" \"-Wl,-rpath," + IECPath + "\"")

        websettingfile = open(paths.AbsNeighbourFile(__file__, "web_settings.py"), 'r')
        websettingcode = websettingfile.read()
        websettingfile.close()

        location_str = "_".join(map(str, self.GetCurrentLocation()))
        websettingcode = websettingcode % locals()

        runtimefile_path = os.path.join(buildpath, "runtime_modbus_websettings.py")
        runtimefile = open(runtimefile_path, 'w')
        runtimefile.write(websettingcode)
        runtimefile.close()

        return ([(Gen_IEC_c_path,
                  ' -I"' + os.path.join(os.path.join(IECIncPath, "inc"), "api") + '"' +
                  ' -I"' + os.path.join(os.path.join(IECIncPath, "inc"), "internal") + '"' +
                  ' -I"' + os.path.join(os.path.join(IECIncPath, "hal"), "inc") + '"' +
                  ' -I"' + os.path.join(os.path.join(IECIncPath, "common"), "inc") + '"' +
                  ' -I"' + os.path.join(os.path.join(os.path.join(IECIncPath), ".."), "config") + '"')],
                LDFLAGS, True,
                ("runtime_iec_websettings_%s.py" % location_str, open(runtimefile_path, "rb")),
        )