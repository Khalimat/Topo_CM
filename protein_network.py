from collections import defaultdict

import requests
import tqdm
from graph_tool.all import *


class protein_network:

    def __init__(self, score, genes, FC):

        self.genes = genes
        self.FC = dict(zip(self.genes, FC))
        self.interactions = None
        self.adjac_list = None
        self.trust_array = None
        self.score = score
        self.graph = None
        self.not_in_STRING = None

    def data_preprocessing(self, species=9606):

        string_api_url = "https://string-db.org/api"
        output_format = "tsv-no-header"
        method = "network"

        # Construct URL

        request_url = "/".join([string_api_url, output_format, method])

        # Set parameters

        my_genes = self.genes
        genes_in_string = []

        for gene in tqdm.tqdm(my_genes):

            params = {

                "identifiers": "%0d".join(gene),  # your protein
                "species": species,  # species NCBI identifier
                "caller_identity": "www.awesome_app.org"  # your app name

            }

            # Call STRING

            response = requests.post(request_url, data=params)

            flag = True
            for line in response.text.strip().split("\n"):
                l = line.strip().split("\t")
                try:
                    l[2]

                except IndexError:
                    flag = False
                    continue

            if flag:
                genes_in_string.append(gene)

        self.not_in_STRING = [x for x in self.genes if x not in genes_in_string]
        self.genes = genes_in_string

        print(len(genes_in_string))

    def API_request(self):

        # Preprocessing genes
        species = 9606
        self.data_preprocessing()

        string_api_url = "https://string-db.org/api"
        output_format = "tsv-no-header"
        method = "network"

        request_url = "/".join([string_api_url, output_format, method])

        my_genes = self.genes

        # Set parameters

        params = {

            "identifiers": "%0d".join(my_genes),  # your protein
            "species": species,  # species NCBI identifier
            "caller_identity": "www.awesome_app.org"  # your app name

        }

        # Call STRING

        response = requests.post(request_url, data=params)

        interactions = []

        for line in response.text.strip().split("\n"):
            l = line.strip().split("\t")
            try:
                p1, p2 = l[2], l[3]
                # filter the interaction according to experimental score
                experimental_score = float(l[5])
                interactions.append((p1, p2, experimental_score))
            except IndexError:
                print("Getting an error")
                print(response.text)

        self.interactions = interactions


    def creating_adj_list(self):

        self.API_request()
        adja_list = defaultdict(list)
        scores = defaultdict(lambda: defaultdict(list))

        for ind_i, line in enumerate(self.genes):
            for ind_j, col in enumerate(self.genes):
                for ind_k, inter in enumerate(self.interactions):
                    if line == inter[0] and col == inter[1] and float(inter[2]) >= self.score:
                        if adja_list[self.genes[ind_i]] != [] and adja_list[self.genes[ind_i]][-1] != inter[1]:
                            adja_list[self.genes[ind_i]] .append(inter[1])
                            scores[self.genes[ind_i]][inter[1]].append(float(inter[2]))
                        elif adja_list[self.genes[ind_i]] == [] and inter[1] != "":
                            adja_list[self.genes[ind_i]].append(inter[1])
                            scores[self.genes[ind_i]][inter[1]].append(float(inter[2]))

        for gene in self.not_in_STRING:
            for gene_1 in self.genes + self.not_in_STRING:
                adja_list[gene] = []
                scores[gene][gene_1] = []
        self.adjac_list = adja_list
        self.trust_array = scores



    def creating_network(self):

        self.creating_adj_list()
        gene_set = self.genes + self.not_in_STRING
        g = Graph(directed=False)
        g.add_vertex(n=len(gene_set))
        print(len(gene_set))
        vprop_proteins = g.new_vp("string")
        for i in range(len(gene_set)):
            vprop_proteins[i] = gene_set[i]
        g.vertex_properties['proteins'] = vprop_proteins
        eprop_scores = g.new_edge_property("double")
        for gene in self.adjac_list.items():
            for inter in gene[1]:
                edge = g.add_edge(self.genes.index(gene[0]), self.genes.index(inter))
                eprop_scores[edge] = self.trust_array[gene[0]][inter][0]

        g.edge_properties["scores"] = eprop_scores
        self.graph = g
        return g

    def writing_adj_lists(self):

        if self.graph:
            graph = self.graph
        else:
            graph = self.creating_network()
        ## добавить директорию для записи
        graph.save("~/Topo_Camp/genes.gt")

    def visualising_graph(self, file):

        if self.graph:
            graph = self.graph
        else:
            graph = self.creating_network()

        return graph_draw(graph, output=file)