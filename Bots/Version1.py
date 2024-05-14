import random

from Classes.Constants import *
from Classes.Materials import Materials
from Classes.TradeOffer import TradeOffer
from Classes.Hand import Hand
from Interfaces.BotInterface import BotInterface


class Version1(BotInterface):
    """
    Es necesario poner super().nombre_de_funcion() para asegurarse de que coge la función del padre
    """
    player_hand_of_each_player = {
        0: Hand(),
        1: Hand(),
        2: Hand(),
        3: Hand()
    }
    town_number = 0
    material_given_more_than_three = None
    # Son los materiales más necesarios en construcciones, luego se piden con year of plenty para tener en mano
    year_of_plenty_material_one = MaterialConstants.CEREAL
    year_of_plenty_material_two = MaterialConstants.MINERAL

    def __init__(self, bot_id):
        super().__init__(bot_id)

    def on_trade_offer(self, incoming_trade_offer=TradeOffer()):
        """
        Hay que tener en cuenta que gives se refiere a los materiales que da el jugador que hace la oferta,
        luego en este caso es lo que recibe
        :param incoming_trade_offer:
        :return:
        """
        if incoming_trade_offer.gives.has_this_more_materials(incoming_trade_offer.receives):
            return True
        else:
            return False
        # return super().on_trade_offer(incoming_trade_offer)

    def on_turn_start(self):
        # Si tiene mano de cartas de desarrollo
        if len(self.development_cards_hand.check_hand()):
            # Mira todas las cartas
            for i in range(0, len(self.development_cards_hand.check_hand())):
                # Si una es un caballero
                #Añadir comprobacion de solo jugarla si el ladron esta en tu territorio, o si está pero tienes más de 1 caballero o si con ello ganas. 
                if self.development_cards_hand.hand[i].type == DevelopmentCardConstants.KNIGHT:
                    # La juega
                    return self.development_cards_hand.select_card_by_id(self.development_cards_hand.hand[i].id)
        return None

    def on_having_more_than_7_materials_when_thief_is_called(self):
        # Comprueba si tiene materiales para construir una ciudad. Si los tiene, descarta el resto que no le sirvan.
        if self.hand.resources.has_this_more_materials(BuildConstants.CITY):
            while self.hand.get_total() > 7:
                if self.hand.resources.wool > 0:
                    self.hand.remove_material(4, 1)

                if self.hand.resources.cereal > 2:
                    self.hand.remove_material(0, 1)
                if self.hand.resources.mineral > 3:
                    self.hand.remove_material(1, 1)

                if self.hand.resources.clay > 0:
                    self.hand.remove_material(2, 1)
                if self.hand.resources.wood > 0:
                    self.hand.remove_material(3, 1)
        # Si no tiene materiales para hacer una ciudad descarta de manera aleatoria cartas de su mano
        return self.hand

    def on_moving_thief(self):
        # Bloquea un número 6 u 8 donde no tenga un pueblo, pero que tenga uno del rival
        # Si no se dan las condiciones lo deja donde está, lo que hace que el GameManager lo ponga en un lugar aleatorio
        terrain_with_thief_id = -1
        for terrain in self.board.terrain:
            if not terrain['has_thief']:
                if terrain['probability'] == 6 or terrain['probability'] == 8:
                    nodes = self.board.__get_contacting_nodes__(terrain['id'])
                    has_own_town = False
                    has_enemy_town = False
                    enemy = -1
                    for node_id in nodes:
                        if self.board.nodes[node_id]['player'] == self.id:
                            has_own_town = True
                            break
                        if self.board.nodes[node_id]['player'] != -1:
                            has_enemy_town = True
                            enemy = self.board.nodes[node_id]['player']

                    if not has_own_town and has_enemy_town:
                        return {'terrain': terrain['id'], 'player': enemy}
            else:
                terrain_with_thief_id = terrain['id']

        return {'terrain': terrain_with_thief_id, 'player': -1}

    def on_turn_end(self):
        # Si tiene mano de cartas de desarrollo
        if len(self.development_cards_hand.check_hand()):
            # Mira todas las cartas
            for i in range(0, len(self.development_cards_hand.check_hand())):
                # Si una es un punto de victoria
                if self.development_cards_hand.hand[i].type == DevelopmentCardConstants.VICTORY_POINT:
                    # La juega
                    return self.development_cards_hand.select_card_by_id(self.development_cards_hand.hand[i].id)
        return None

    def on_commerce_phase(self):
        """
        Se podría complicar mucho más la negociación, cambiando lo que hace en función de si tiene o no puertos y demás
        """
        # Juega monopolio si ha entregado más de 3 del mismo tipo de material a un jugador en el intercambio
        if self.material_given_more_than_three is not None:
            if len(self.development_cards_hand.check_hand()):
                # Mira todas las cartas
                for i in range(0, len(self.development_cards_hand.check_hand())):
                    # Si una es un punto de monopolio
                    if self.development_cards_hand.hand[i].effect == DevelopmentCardConstants.MONOPOLY_EFFECT:
                        # La juega
                        return self.development_cards_hand.select_card_by_id(self.development_cards_hand.hand[i].id)

        gives = Materials()
        receives = Materials()

        # No pide nada porque puede hacer una ciudad
        if self.town_number >= 1 and self.hand.resources.has_this_more_materials(BuildConstants.CITY):
            self.material_given_more_than_three = None
            return None
        # Pedir lo que falte para una ciudad, ofrece el resto de materiales iguales a los que pide
        elif self.town_number >= 1:
            cereal_hand = self.hand.resources.cereal
            mineral_hand = self.hand.resources.mineral
            wood_hand = self.hand.resources.wood
            clay_hand = self.hand.resources.clay
            wool_hand = self.hand.resources.wool
            total_given_materials = (2 - cereal_hand) + (3 - mineral_hand)

            # Si hay más materiales que los pedidos
            if total_given_materials < (wood_hand + clay_hand + wool_hand):
                materials_to_give = [0, 0, 0, 0, 0]
                for i in range(0, total_given_materials):
                    # Se mezcla el orden de materiales
                    order = [MaterialConstants.CLAY, MaterialConstants.WOOD, MaterialConstants.WOOL]
                    random.shuffle(order)
                    # una vez mezclado se recorre el orden de los materiales y se coge el primero que tenga un valor
                    for mat in order:
                        if self.hand.resources.get_from_id(mat) > 0:
                            self.hand.remove_material(mat, 1)
                            materials_to_give[mat] += 1
                            break
                gives = Materials(materials_to_give[0], materials_to_give[1], materials_to_give[2],
                                  materials_to_give[3], materials_to_give[4])

            # Si no hay más materiales que los pedidos, simplemente se prueba a entregar todos lo que se tenga en mano
            else:
                gives = Materials(0, 0, clay_hand, wood_hand, wool_hand)

            receives = Materials(2, 3, 0, 0, 0)

        # Como no puede construir una ciudad pide materiales para hacer un pueblo
        elif self.town_number == 0:
            # Si tiene materiales para hacer un pueblo directamente no comercia
            if self.hand.resources.has_this_more_materials(Materials(1, 0, 1, 1, 1)):
                return None
            # Si no los tiene hace un intercambio
            else:
                # Puedes cambiar materiales repetidos o minerales
                materials_to_receive = [0, 0, 0, 0, 0]
                materials_to_give = [0, 0, 0, 0, 0]

                number_of_materials_received = 0

                materials_to_receive[0] = 1 - self.hand.resources.cereal
                materials_to_receive[1] = 0 - self.hand.resources.mineral
                materials_to_receive[2] = 1 - self.hand.resources.clay
                materials_to_receive[3] = 1 - self.hand.resources.wood
                materials_to_receive[4] = 1 - self.hand.resources.wool

                # Nos aseguramos de que solo pida materiales que necesita, y que no hayan negativos
                for i in range(0, len(materials_to_receive)):
                    if materials_to_receive[i] <= 0:
                        materials_to_receive[i] = 0
                    else:
                        number_of_materials_received += 1

                # Por cada material que recibe, ofrece 1 de entre los que tiene en mano,
                #   pero guardándose al menos 1 de cada uno de los necesarios para hacer un pueblo
                for j in range(0, number_of_materials_received):
                    # Se mezcla el orden de materiales
                    order = [MaterialConstants.CEREAL, MaterialConstants.MINERAL, MaterialConstants.CLAY,
                             MaterialConstants.WOOD, MaterialConstants.WOOL]
                    random.shuffle(order)
                    # una vez mezclado se recorre el orden de los materiales y se coge el primero que tenga un valor
                    for mat in order:
                        if self.hand.resources.get_from_id(mat) > 1 or mat == MaterialConstants.MINERAL:
                            self.hand.remove_material(mat, 1)
                            materials_to_give[mat] += 1
                            break

                gives = Materials(materials_to_give[0], materials_to_give[1], materials_to_give[2],
                                  materials_to_give[3], materials_to_give[4])
                receives = Materials(materials_to_receive[0], materials_to_receive[1], materials_to_receive[2],
                                     materials_to_receive[3], materials_to_receive[4])

        trade_offer = TradeOffer(gives, receives)
        return trade_offer

    def on_build_phase(self, board_instance):
        self.board = board_instance
        board_data = self.board.get_board_data()

        def get_longest_road_path(start_node, visited_nodes, current_length):
            # Si el nodo actual ya fue visitado, se devuelve la longitud actual del camino
            if start_node in visited_nodes:
                return current_length
            
            # Se agrega el nodo actual al conjunto de nodos visitados
            visited_nodes.add(start_node)
            
            # Inicializa la longitud máxima con la longitud actual
            max_length = current_length
            
            # Itera sobre las carreteras del nodo actual
            for road in board_data['nodes'][start_node]['roads']:
                # Si la carretera pertenece al jugador y el nodo adyacente no ha sido visitado
                if road['player_id'] == self.id and road['node_id'] not in visited_nodes:
                    # Se realiza una llamada recursiva incrementando la longitud del camino
                    length = get_longest_road_path(road['node_id'], visited_nodes.copy(), current_length + 1)
                    # Se actualiza la longitud máxima si la nueva longitud es mayor
                    max_length = max(max_length, length)
            
            # Devuelve la longitud máxima del camino encontrado
            return max_length

        def valid_road_nodes_with_longest_path(player_id):
            # Lista para almacenar nodos válidos para construir carreteras
            valid_nodes = []
            
            # Itera sobre todos los nodos en el tablero
            for node in board_data['nodes']:
                # Itera sobre los nodos adyacentes de cada nodo
                for adjacent_node_id in node['adjacent']:
                    allowed_to_build = False
                    
                    # Comprueba si el nodo adyacente pertenece al jugador o está libre
                    if board_data['nodes'][adjacent_node_id]['player'] == player_id or board_data['nodes'][adjacent_node_id]['player'] == -1:
                        # Itera sobre las carreteras del nodo adyacente
                        for road in board_data['nodes'][adjacent_node_id]['roads']:
                            # Si la carretera no es una carretera de vuelta
                            if road['node_id'] != node['id']:
                                # Si la carretera pertenece al jugador, se permite construir
                                if road['player_id'] == player_id:
                                    allowed_to_build = True
                                else:
                                    allowed_to_build = False
                            # Si hay una carretera de vuelta, se prohíbe construir
                            else:
                                allowed_to_build = False
                                break
                    # Si se permite construir, se añade a la lista de nodos válidos
                    if allowed_to_build:
                        valid_nodes.append({'starting_node': adjacent_node_id, 'finishing_node': node['id']})

            best_road_option = None
            longest_road_length = 0
            
            # Itera sobre los nodos válidos para construir carreteras
            for road_obj in valid_nodes:
                # Conjunto para almacenar nodos visitados
                visited_nodes = set()
                # Añade el nodo de inicio al conjunto de nodos visitados
                visited_nodes.add(road_obj['starting_node'])
                # Calcula la longitud del camino desde el nodo de inicio
                path_length = get_longest_road_path(road_obj['finishing_node'], visited_nodes, 1)
                # Si la longitud del camino es mayor que la longitud máxima encontrada, se actualiza
                if path_length > longest_road_length:
                    longest_road_length = path_length
                    best_road_option = road_obj

            # Devuelve la mejor opción de carretera para extender el camino más largo
            return best_road_option

        # Compra objetivo
        compra_objetivo = self.compra_objetivo(turnoActual, board_instance)

        if compra_objetivo == BuildConstants.TOWN:
            if self.hand.resources.has_this_more_materials(BuildConstants.TOWN):
                possibilities = self.board.valid_town_nodes(self.id)
                for node_id in possibilities:
                    for terrain_piece_id in self.board.nodes[node_id]['contacting_terrain']:
                        if self.board.terrain[terrain_piece_id]['probability'] in [4, 5, 6, 8, 9, 10]:
                            self.town_number += 1
                            return {'building': BuildConstants.TOWN, 'node_id': node_id}

        elif compra_objetivo == BuildConstants.CITY:
            if self.hand.resources.has_this_more_materials(BuildConstants.CITY) and self.town_number > 0:
                possibilities = self.board.valid_city_nodes(self.id)
                for node_id in possibilities:
                    for terrain_piece_id in self.board.nodes[node_id]['contacting_terrain']:
                        if self.board.terrain[terrain_piece_id]['probability'] in [5, 6, 8, 9]:
                            self.town_number -= 1
                            return {'building': BuildConstants.CITY, 'node_id': node_id}

        elif compra_objetivo == BuildConstants.ROAD:
            if self.hand.resources.has_this_more_materials(BuildConstants.ROAD):
                best_road_option = valid_road_nodes_with_longest_path(self.id)
                if best_road_option:
                    return {'building': BuildConstants.ROAD,
                            'node_id': best_road_option['starting_node'],
                            'road_to': best_road_option['finishing_node']}

        elif compra_objetivo == BuildConstants.CARD:
            if self.hand.resources.has_this_more_materials(BuildConstants.CARD):
                return {'building': BuildConstants.CARD}

        # Construir cualquier cosa si tiene más de 7 cartas
        if self.hand.resources.total() > 7:
            if self.hand.resources.has_this_more_materials(BuildConstants.CITY) and self.town_number > 0:
                possibilities = self.board.valid_city_nodes(self.id)
                for node_id in possibilities:
                    for terrain_piece_id in self.board.nodes[node_id]['contacting_terrain']:
                        if self.board.terrain[terrain_piece_id]['probability'] in [5, 6, 8, 9]:
                            self.town_number -= 1
                            return {'building': BuildConstants.CITY, 'node_id': node_id}

            if self.hand.resources.has_this_more_materials(BuildConstants.TOWN):
                possibilities = self.board.valid_town_nodes(self.id)
                for node_id in possibilities:
                    for terrain_piece_id in self.board.nodes[node_id]['contacting_terrain']:
                        if self.board.terrain[terrain_piece_id]['probability'] in [4, 5, 6, 8, 9, 10]:
                            self.town_number += 1
                            return {'building': BuildConstants.TOWN, 'node_id': node_id}

            if self.hand.resources.has_this_more_materials(BuildConstants.ROAD):
                best_road_option = valid_road_nodes_with_longest_path(self.id)
                if best_road_option:
                    return {'building': BuildConstants.ROAD,
                            'node_id': best_road_option['starting_node'],
                            'road_to': best_road_option['finishing_node']}

            if self.hand.resources.has_this_more_materials(BuildConstants.CARD):
                return {'building': BuildConstants.CARD}

        return None


    def on_game_start(self, board_instance): #VT version

        #VT o VT+ o VTT+
        # Plantar en la casilla de más valor disponible 
        self.board = board_instance
        possibilities = self.board.valid_starting_nodes()
        dictNode = self.__VT__(possibilities)
        maxValue=0
        bestNode=random.randint(0, 53)
        for node_id in possibilities:
            if dictNode[node_id]>maxValue:
                maxValue = dictNode[node_id]
                bestNode = node_id
        possible_roads = self.board.nodes[bestNode]['adjacent']
    
        return node_id, possible_roads[random.randint(0, len(possible_roads) - 1)]

    def on_monopoly_card_use(self):
        # Elige el material que más haya intercambiado (variable global de esta clase)
        return self.material_given_more_than_three

    def update_hand_from_a_given_player_id(self, player_id: int, player_hand: Hand):
        self.player_hand_of_each_player[player_id] = player_hand
    
    # noinspection DuplicatedCode
    def on_road_building_card_use(self):
        # Elige dos carreteras aleatorias entre las opciones
        valid_nodes = self.board.valid_road_nodes(self.id)
        # Se supone que solo se ha usado la carta si hay más de 2 carreteras disponibles a construir,
        # pero se dejan por si acaso
        if len(valid_nodes) > 1:
            while True:
                road_node = random.randint(0, len(valid_nodes) - 1)
                road_node_2 = random.randint(0, len(valid_nodes) - 1)
                if road_node != road_node_2:
                    return {'node_id': valid_nodes[road_node]['starting_node'],
                            'road_to': valid_nodes[road_node]['finishing_node'],
                            'node_id_2': valid_nodes[road_node_2]['starting_node'],
                            'road_to_2': valid_nodes[road_node_2]['finishing_node'],
                            }
        elif len(valid_nodes) == 1:
            return {'node_id': valid_nodes[0]['starting_node'],
                    'road_to': valid_nodes[0]['finishing_node'],
                    'node_id_2': None,
                    'road_to_2': None,
                    }
        return None

    def on_year_of_plenty_card_use(self):
        return {'material': self.year_of_plenty_material_one, 'material_2': self.year_of_plenty_material_two}
        
    def __VT__(self, nodes):
        dictNode = {}
        for node in nodes:
            terrains = self.board.__get_contacting_terrain__( node)
            nodeProb=0
            for terrain in terrains:
                nodeProb = nodeProb + self.board.__get_probability__(terrain)
            dictNode[node]=nodeProb
        return dictNode
    
    def __VTPlus__(self, nodes):
        dictNode = {}
        for node in nodes:
            terrains = self.board.__get_contacting_terrain__(self, node)
            nodeProb=0
            arrayTypes = [0,0,0,0,0]
            for terrain in terrains:
                terrainType = self.terrain_constants.__get_terrain_type__(terrain_id)
                arrayTypes[terrainType] = arrayTypes[terrainType] + self.board.__get_probability__(terrain)
            dictNode[node]=arrayTypes
        return dictNode
       

    def __CR__(self, nodes):
        playerDict = {}
        globalDictNode = {}
        for player in players:
            dictNode = {}
            for node in nodes:
                if node['player'] == player:
                    terrains = self.board__get_contacting_terrain__(node)
                    nodeProb=0
                    arrayTypes = [0,0,0,0,0]
                    for terrain in terrains:
                        terrainType = self.terrain_constants.__get_terrain_type__(terrain_id)
                        arrayTypes[terrainType] = arrayTypes[terrainType] + self.board.__get_probability__(terrain)
                    dictNode[node]=arrayTypes
                    globalDictNode[node]=arrayTypes
                elif node['player'] == -1:
                    terrains = self.board__get_contacting_terrain__(node)
                    nodeProb=0
                    arrayTypes = [0,0,0,0,0]
                    for terrain in terrains:
                        terrainType = self.terrain_constants.__get_terrain_type__(terrain_id)
                        arrayTypes[terrainType] = arrayTypes[terrainType] + self.board.__get_probability__(terrain)
                    globalDictNode[node]=arrayTypes
            playerDict[player] = dictNode
        return playerDict
