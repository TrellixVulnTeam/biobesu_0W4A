#!/user/bin/env python3

from datetime import datetime
from biobesu.helper import validate
import requests


class Converter:
    @staticmethod
    def key_to_value(keys, conversion_dict, include_na=False):
        if type(keys) is list:
            values = []
            missing = set()
            for key in keys:
                try:
                    values.append(conversion_dict[key])
                except KeyError:
                    if include_na:
                        values.append('NA')
                    missing.add(key)

            return values, missing

        else:
            try:
                return conversion_dict[keys]
            except KeyError:
                return None


class PhenotypeConverter(Converter):
    def __init__(self, hpo_obo):
        # Defines dictionaries for fast retrieval.
        self.names_by_id = {}
        self.id_by_names = {}

        # Stores hpo obo relevant information.
        self.hpo_obo_version = ""

        # Processes hpo obo file.
        self.read_hpo_obo(hpo_obo)

    def read_hpo_obo(self, hpo_obo):
        # Match terms for header.
        match_version = 'data-version:'

        # Match terms for phenotypes.
        match_term = '[Term]'
        match_id = 'id: '
        match_name = 'name: '

        # Initializes variables.
        hpo_id = None
        hpo_name = None
        added = False

        # Goes through the .obo file.
        with open(hpo_obo) as file:
            for line in file:
                if line.startswith(match_version):
                    self.hpo_obo_version = line.split('/')[1].rstrip()
                # Resets id and name for new phenotype.
                if line.startswith(match_term):
                    hpo_id = None
                    hpo_name = None
                    added = False
                # Once a phenotype is added, skips lines until next term.
                elif added is True:
                    continue
                # Sets id/name when found.
                elif line.startswith(match_id):
                    hpo_id = line.lstrip(match_id).strip()
                elif line.startswith(match_name):
                    hpo_name = line.lstrip(match_name).strip()

                # If a combination of an id and a name/synonym is stored, saves it to the dictionaries.
                # Afterwards, reset id to None so that next lines will be ignored till the next phenotype.
                if hpo_id is not None and hpo_name is not None:
                    self.names_by_id[hpo_id] = hpo_name
                    self.id_by_names[hpo_name] = hpo_id
                    added = True

    def id_to_name(self, hpo_ids, include_na=False):
        return self.key_to_value(hpo_ids, self.names_by_id, include_na)

    def name_to_id(self, hpo_names, include_na=False):
        return self.key_to_value(hpo_names, self.id_by_names, include_na)

    def id_to_phenopacket(self, phenopacket_id, phenotype_ids):
        # Writes opening bracket.
        output_string = '{'

        # Convert row id to phenopackets.
        output_string += '\n\t"id": "' + phenopacket_id + '",' + \
                         '\n\t"phenotypic_features": ['

        # Converts phenotypes phenopackets.
        for i, phenotype_id in enumerate(phenotype_ids):
            output_string += '{' \
                             '\n\t\t"type": {' \
                             '\n\t\t\t"id": "' + phenotype_id + '",' + \
                             '\n\t\t\t"label": "' + self.names_by_id[phenotype_id] + '"' + \
                             '\n\t\t}' \
                             '\n\t}'
            if i < len(phenotype_ids)-1:
                output_string += ', '

        # Closing bracket for phenotypicFeatures.
        output_string += '],'

        # Add metadata.
        output_string += '\n\t"meta_data": {' \
                         '\n\t\t"created": "' + datetime.utcnow().isoformat() + 'Z",' + \
                         '\n\t\t"created_by": "biobesu",' \
                         '\n\t\t"resources": [{' \
                         '\n\t\t\t"id": "hp",' \
                         '\n\t\t\t"name": "Human Phenotype Ontology",' \
                         '\n\t\t\t"namespacePrefix": "HP",' \
                         '\n\t\t\t"url": "http://purl.obolibrary.org/obo/hp.owl",' \
                         '\n\t\t\t"version": "' + self.hpo_obo_version + '",' \
                         '\n\t\t\t"iriPrefix": "http://purl.obolibrary.org/obo/HP_"' \
                         '\n\t\t}]' \
                         '\n\t}'

        # Writes closing bracket.
        output_string += '\n}'

        return output_string


class GeneConverter(Converter):
    """
    If existing file is used, assumes it was downloaded through this class previously. Watch out with a manually
    downloaded file!

    """
    # Download URL (ordered by gene ID).
    download_file = 'https://www.genenames.org/cgi-bin/download/custom?col=gd_pub_eg_id&col=gd_app_sym' \
                    '&status=Approved&status=Entry%20Withdrawn&hgnc_dbtag=on&order_by=gd_pub_eg_id' \
                    '&format=text&submit=submit'

    # Expected file name.
    file_name = 'gene_ids_symbols.tsv'

    # Expected header format.
    expected_file_header = "NCBI Gene ID\tApproved symbol"

    def __init__(self, gene_file_dir):
        # The file location that needs to be loaded.
        self.gene_file = gene_file_dir + self.file_name

        # Downloads info file if not yet present in dir.
        try:
            validate.file(self.gene_file, expected_extension='.tsv')
        except OSError:
            self.__download_info_file()

        # Defines dictionaries for fast retrieval.
        self.id_by_symbol = {}
        self.symbol_by_id = {}

        # Retrieves data.
        self.__read_file()

    def __download_info_file(self):
        with requests.get(self.download_file, allow_redirects=True) as r:
            with open(self.gene_file, 'x') as file_writer:
                file_writer.write(r.content.decode('utf-8'))

    def __read_file(self):
        # Goes through the file.
        for counter, line in enumerate(open(self.gene_file)):
            # Validates if all expected columns are present and in expected order.
            if counter == 0 and line.rstrip() != self.expected_file_header:
                raise Exception("Unexpected gene info file header.\nExpected: {0}\nActual: {1}"
                                .format(self.expected_file_header, line))

            # Processes items.
            if counter > 0:
                line = line.rstrip().split("\t")

                # Ensures all items are of equal length after splitting.
                while len(line) < 2:
                    line.append('')

                # Clearer usage of data.
                gene_id = line[0]
                gene_symbol = line[1]

                # Adds gene to dict.
                if gene_id != '':
                    if self.id_by_symbol.get(gene_symbol) is not None:
                        raise Exception("The symbol {} was already assigned to {}".format(gene_symbol, gene_id))
                    self.id_by_symbol[gene_symbol] = gene_id
                    self.symbol_by_id[gene_id] = gene_symbol

    def id_to_symbol(self, gene_ids, include_na=False):
        return self.key_to_value(gene_ids, self.symbol_by_id, include_na)

    def symbol_to_id(self, gene_symbols, include_na=False):
        return self.key_to_value(gene_symbols, self.id_by_symbol, include_na)