from bs4 import BeautifulSoup
import urllib2
from re import sub
import operator
import csv
import gspread

class PopulationTableGrabber(object):
    def __init__(self, url):
        self.page = urllib2.urlopen(url)
        self.soup = BeautifulSoup(self.page)

        username = "cel.chang@gmail.com"
        password = "princeton24"

        docid = "0AkN5iuAvAuTedGh2YnoyVzJ2QlBRNFMtUUJjWHFVZ0E"

        client = gspread.login(username, password)
        spreadsheet = client.open_by_key(docid)
        worksheet = spreadsheet.get_worksheet(0)
        self.data = worksheet.get_all_records()

    def find_all_tabs(self):
        def table_has_enough_rows(elm):
            ''' actually table of interest has a border,
                AND enough rows.'''
            return elm.name == 'table' and \
              elm.has_attr('bordercolor') and \
              len(elm.find_all('tr')) > 20
        return self.soup.find_all(table_has_enough_rows)

    def parse_one_table(self, tab):
        ''' somewhat dirty, but grabs the year, skips a row, and parses the rest
            would break if there were and asterisk row for example
        '''
        yearElement = tab.find(colspan='3')
        year = int(yearElement.get_text())
        rows = yearElement.find_parent().find_next_sibling().find_next_siblings()
        out = []
        for row in rows:
            tds = row.find_all('td')
            rowdata = {
                'year': year,
                'rank': self.fix_ordinals(tds[0].get_text()), 
                'city': self.remove_state(tds[1].get_text()), 
                'city_pop (thousands)': float(tds[2].get_text()),
                'total_pop (millions)': self.get_total_pop_by_year(year),
                'percent': float(tds[2].get_text()) / (self.get_total_pop_by_year(year) * 10)
            }
            out.append(rowdata)
        return out

    def get_total_pop_by_year(self, year):
        for popdata in self.data:
            if popdata['year'] == year:
                return popdata['totalpop']


    def reshape_city_data(self, all_tabs):
        ''' list += rows, for all the tables'''
        return reduce(operator.add, 
                      [self.parse_one_table(tab) for tab in all_tabs]
        )


    def fix_ordinals(self, string):
        ''' oh look, "1."
        '''
        return int(sub('[.]', '', string))

    def remove_state(self, string):
        return string.split(',')[0]


    def write_csv(self, dicts, filename="citypop_temp.csv"):
        ''' could do without ceremony, but this preserves key order
        '''
        keys = ['year', 'rank', 'city', 'city_pop (thousands)', 'total_pop (millions)', 'percent']
        f = open(filename, 'wb')
        dict_writer = csv.DictWriter(f, keys)
        dict_writer.writer.writerow(keys)
        dict_writer.writerows(dicts)
        f.close()
        

pop = PopulationTableGrabber('http://www.peakbagger.com/pbgeog/histmetropop.aspx') #pop is class PopulationTableGrabber
pop.write_csv(pop.reshape_city_data(pop.find_all_tabs()))

## copied total pop data from malecki's google spreadsheet to my own (had problems acessing his using gspread even though it's public)

