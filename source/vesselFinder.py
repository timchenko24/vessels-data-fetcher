import csv
import requests
from bs4 import BeautifulSoup
import pandas as pd


class VesselFinder:

    __user_agent = ('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) '
                  'Gecko/20100101 Firefox/50.0')

    def __init__(self, mmsi_array, csv_vessels, csv_ports):
        self.mmsi_array = mmsi_array
        self.csv_vessels = csv_vessels
        self.csv_ports = csv_ports


    def __get_vessel_url(self, mmsi):
        url = f"https://www.myshiptracking.com/vessels?name={mmsi}"
        response = requests.get(url, headers={'User-Agent': self.__user_agent})

        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.select_one("a[href^='/vessels/']").get('href')

    def __get_port_url(self, port_name):
        url = f"https://www.myshiptracking.com/ports?name={port_name}"
        response = requests.get(url, headers={'User-Agent': self.__user_agent})

        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.select_one("a[href^='/ports/']").get('href')


    def __get_main_vessel_information(self, mmsi):
        vessel_url = self.__get_vessel_url(mmsi)
        url = f"https://www.myshiptracking.com{vessel_url}"
        response = requests.get(url, headers={'User-Agent': self.__user_agent})

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table", {"class": "vessels_table"})

        results = dict()
        for row in table.findAll('tr'):
            aux = row.findAll('td')

            if aux[0].string in {'Draught AVG', 'Speed AVG/MAX'}:
                continue

            elif aux[0].string == 'Flag':
                results[aux[0].string] = aux[1].text.strip()

            elif aux[0].string == 'Size':
                temp = aux[1].text.split()
                results['Length'] = temp[0]
                results['Width'] = temp[2]

            elif aux[0].string in {'GRT', 'DWT', 'Build'}:
                results[aux[0].string] = aux[1].text.split()[0]

            elif aux[1].text == '---':
                continue

            else:
                results[aux[0].string] = aux[1].text

        return results


    def __get_vessel_voyage(self, mmsi):
        vessel_url = self.__get_vessel_url(mmsi)
        url = f"https://www.myshiptracking.com{vessel_url}"
        response = requests.get(url, headers={'User-Agent': self.__user_agent})

        table = pd.read_html(response.text)[3]

        destination = table.iloc[0].to_dict()
        departure = table.iloc[1].to_dict()

        departure['Departure port'] = departure.pop('Port')
        del departure['Arrival (UTC)']
        del departure['Time in Port']

        destination['Destination port'] = destination.pop('Port')
        del destination['Departure (UTC)']
        del destination['Time in Port']

        return departure, destination


    def __get_port_information(self, port_name):
        port_url = self.__get_port_url(port_name)
        url = f"https://www.myshiptracking.com{port_url}"
        response = requests.get(url, headers={'User-Agent': self.__user_agent})

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table", {"class": "vessels_table"})

        results = {}
        for row in table.findAll('tr'):
            aux = row.findAll('td')

            if aux[0].string in {'UN/LOCODE', 'Area size', 'Vessels In Port', 'Arrivals (24h)', 'Departures (24h)',
                                 'Expected Arrivals', 'Local Time', 'Timezone'}:
                continue

            elif aux[0].string == 'Country':
                results[aux[0].string] = aux[1].text.split()[-1]

            elif aux[0].string in {'Longitude', 'Latitude'}:
                results[aux[0].string] = aux[1].text.replace('°', '')

            else:
                results[aux[0].string] = aux[1].text

        return results


    def __get_all_vessels_inf(self):
        temp = []

        for mmsi in self.mmsi_array:
            departure, destination = self.__get_vessel_voyage(mmsi)
            t = self.__get_main_vessel_information(mmsi)
            t.update(departure)
            t.update(destination)
            temp.append(t)
        return temp


    def __get_all_ports_inf(self):
        vessels = self.__get_all_vessels_inf()

        departure_ports = [p['Departure port'] for p in vessels]
        destination_ports = [p['Destination port'] for p in vessels]

        result_ports = set(departure_ports + destination_ports)
        temp = []

        for port in result_ports:
            t = self.__get_port_information(port)
            temp.append(t)
        return temp


    def write_vessels(self):
        with open(self.csv_vessels, mode='w', newline='') as csv_file_w:
            fieldnames = ['Name', 'Flag', 'MMSI', 'IMO', 'Call Sign', 'Type', 'Length', 'Width', 'GRT', 'DWT', 'Build',
                          'Departure (UTC)', 'Departure port', 'Arrival (UTC)', 'Destination port']
            temp = self.__get_all_vessels_inf()
            writer = csv.DictWriter(csv_file_w, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(temp)


    def write_ports(self):
        with open(self.csv_ports, mode='w', newline='') as csv_file_w:
            fieldnames = ['Name', 'Type', 'Country', 'Longitude', 'Latitude']
            temp = self.__get_all_ports_inf()

            writer = csv.DictWriter(csv_file_w, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(temp)


    def write_vessels_img(self):
        for mmsi in self.mmsi_array:
            url = f"https://www.myshiptracking.com/requests/getimage-normal/{mmsi}.jpg"
            img_data = requests.get(url).content
            with open(f"{mmsi}.jpg", 'wb') as handler:
                handler.write(img_data)
