from __future__ import absolute_import

from datetime import datetime
import logging
import sys
from threading import Timer

from volttron.platform.vip.agent import Agent, Core, PubSub, compat, RPC
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod
import time
from volttron.platform.vip.agent.connection import Connection
#import numpy as np 
import operator
import json
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import time

utils.setup_logging()
_log = logging.getLogger(__name__)


class CPRAgent(Agent):
    def __init__(self, config_path, **kwargs):
        super(CPRAgent, self).__init__(**kwargs)
        self._agent_id = 'CPRAgent'
        self.default_config = {}
        self.vip.config.set_default("config", self.default_config)
        self.vip.config.subscribe(self.configure, actions=["NEW", "UPDATE"], pattern="config")

    def configure(self, config_name, action, contents):
        print(contents)
        config = self.default_config.copy()
        config.update(contents)
        print(config)

        # make sure config variables are valid
        try:
            pass
        except ValueError as e:
            _log.error("ERROR PROCESSING CONFIGURATION: {}".format(e))


    @Core.receiver("onstart")
    def starting(self, sender, **kwargs):
        self.test_solar_anywhere()

    @PubSub.subscribe('pubsub', 'solaranywhere')
    def print_solardata(self, peer, sender, bus, topic, headers, message):
        print('received solar data')
        print(message)

    def test_solar_anywhere(self):
        #POST Create Simulation Request
        url = "https://service.solaranywhere.com/api/v2/Simulation"
        userName = "Intwine.Client@intwineconnect.com"
        password = "Sol@rCar5"

        querystring = {"key":"INTW_TEST"}

        payload = """<CreateSimulationRequest xmlns="http://service.solaranywhere.com/api/v2">
         <EnergySites>
          <EnergySite Name="BulkSimulation V2 Site" Description="Site Description">
           <Location Latitude="34.65" Longitude="-119.1" />
            <PvSystems>
             <PvSystem Albedo_Percent="17" GeneralDerate_Percent="85.00">
              <Inverters>
               <Inverter Count="1" MaxPowerOutputAC_kW="4.470000" EfficiencyRating_Percent="97.000000" />
              </Inverters>
              <PvArrays>
               <PvArray>
                <PvModules>
                 <PvModule Count="1" NameplateDCRating_kW="0.22000" PtcRating_kW="0.19760" PowerTemperatureCoefficient_PercentPerDegreeC="0.4" NominalOperatingCellTemperature_DegreesC="45" />
                </PvModules>
                <ArrayConfiguration Azimuth_Degrees="177.000" Tilt_Degrees="25.000" Tracking="Fixed" TrackingRotationLimit_Degrees="90" ModuleRowCount="1" RelativeRowSpacing="3" />
                <SolarObstructions>
                 <SolarObstruction Azimuth_Degrees="90.000" Elevation_Degrees="33.000" Opacity_Percent="80"/>
                 <SolarObstruction Azimuth_Degrees="120.000" Elevation_Degrees="50.000" />
                 <SolarObstruction Azimuth_Degrees="150.000" Elevation_Degrees="22.000" />
                 <SolarObstruction Azimuth_Degrees="180.000" Elevation_Degrees="3.000" />
                 <SolarObstruction Azimuth_Degrees="210.000" Elevation_Degrees="1.000" />
                 <SolarObstruction Azimuth_Degrees="240.000" Elevation_Degrees="2.000" />
                 <SolarObstruction Azimuth_Degrees="270.000" Elevation_Degrees="4.000" Opacity_Percent="70"/>
                </SolarObstructions>
                <MonthlyShadings>
                 <MonthlyShading MonthNumber="1" SolarAccess_Percent="77.0"/>
                 <MonthlyShading MonthNumber="2" SolarAccess_Percent="87.0"/>
                 <MonthlyShading MonthNumber="3" SolarAccess_Percent="98.0"/>
                 <MonthlyShading MonthNumber="4" SolarAccess_Percent="100.0"/>
                 <MonthlyShading MonthNumber="5" SolarAccess_Percent="100.0"/>
                 <MonthlyShading MonthNumber="6" SolarAccess_Percent="100.0"/>
                 <MonthlyShading MonthNumber="7" SolarAccess_Percent="100.0"/>
                 <MonthlyShading MonthNumber="8" SolarAccess_Percent="100.0"/>
                 <MonthlyShading MonthNumber="9" SolarAccess_Percent="100.0"/>
                 <MonthlyShading MonthNumber="10" SolarAccess_Percent="100.0"/>
                 <MonthlyShading MonthNumber="11" SolarAccess_Percent="100.0"/>
                 <MonthlyShading MonthNumber="12" SolarAccess_Percent="91.0"/>
                </MonthlyShadings>
               </PvArray>
              </PvArrays>
               </PvSystem>
             </PvSystems>
            </EnergySite>
          </EnergySites>
         <SimulationOptions
         PowerModel="CprPVForm"
         ShadingModel="MonthlyPercentSolarResource" OutputFields="StartTime,AmbientTemperature_DegreesC,AmbientTemperatureObservationType,EndTime,PowerAC_kW,EnergyAC_kWh,GlobalHorizontalIrradiance_WattsPerMeterSquared">
         <WeatherDataOptions
        WeatherDataSource="SolarAnywhere3_2"
        WeatherDataPreference = "Auto"
        PerformTimeShifting = "true"
        StartTime="2017-07-26T09:00:00-08:00"
        EndTime="2017-07-26T11:00:00-08:00"
        SpatialResolution_Degrees="0.1"
        TimeResolution_Minutes="60"/>
         </SimulationOptions>
        </CreateSimulationRequest>"""

        headers = {
         'content-type': "text/xml; charset=utf-8",
         'content-length': "length",
         }

        response = requests.post(url,auth = HTTPBasicAuth(userName,password),data=payload,headers=headers,params=querystring)

        root = ET.fromstring(response.content)
        print(response.content)
        print("-----")

        publicId = root.attrib.get("SimulationId")
        print(publicId)

        #GET SimulationResult
        url2 = "https://service.solaranywhere.com/api/v2/SimulationResult/"

        requestNumber = 0
        MAX_requestNumber = 100

        while(requestNumber < MAX_requestNumber):
            print(requestNumber)
            time.sleep(5)
            data = requests.get(url2 + publicId,auth = HTTPBasicAuth(userName,password))
            radicle = ET.fromstring(data.content)
            status = radicle.attrib.get("Status")
            self.vip.pubsub.publish('pubsub', 'solaranywhere', {}, data.content)
            if status == "Done":
                break
            else:
                requestNumber = requestNumber +1


        
def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(CPRAgent)
    except Exception as e:
        _log.exception('unhandled exception')


if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())