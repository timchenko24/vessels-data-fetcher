import sys
import csv
import requests
from bs4 import BeautifulSoup
import pandas as pd
from vesselFinder import VesselFinder


mmsi_arr = [636015563, 211330520, 369285000, 538005860, 244735000, 249137000, 636092074, 636018188, 636018682]

vessel_csv = r'your_vessel.csv_path'
ports_csv = r'your_ports.csv_path'

vf = VesselFinder(mmsi_arr, vessel_csv, ports_csv)

vf.write_vessels()
vf.write_ports()
vf.write_vessels_img()
