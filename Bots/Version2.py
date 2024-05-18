import random

from Classes.Constants import *
from Classes.Materials import Materials
from Classes.TradeOffer import TradeOffer
from Classes.Hand import Hand
from Interfaces.BotInterface import BotInterface
import numpy as np


class Version2(BotInterface):
    """
    Es necesario poner super().nombre_de_funcion() para asegurarse de que coge la función del padre
    """

    player_hand_of_each_player = {0: Hand(), 1: Hand(), 2: Hand(), 3: Hand()}
    town_number = 0
    material_given_more_than_three = None
    # Son los materiales más necesarios en construcciones, luego se piden con year of plenty para tener en mano
    year_of_plenty_material_one = MaterialConstants.CEREAL
    year_of_plenty_material_two = MaterialConstants.MINERAL
    PESO_TOCHO = 10

    competitivo = 1
    GustoCiudad = 1
    GustoPoblado = 1
    GustoCarretera = 1
    GustoDesarrollo = 1
    timeChange = 0.4
    importanciaTiempo = 10
    turnoActual = 0
    compraObjetivo = None
    GustoMar = 1.5

    def __init__(self, bot_id):
        super().__init__(bot_id)

    def on_trade_offer(self, incoming_trade_offer=TradeOffer()):
        """
        Hay que tener en cuenta que gives se refiere a los materiales que da el jugador que hace la oferta,
        luego en este caso es lo que recibe
        :param incoming_trade_offer:
        :return:
        """
        if incoming_trade_offer.gives.has_this_more_materials(
            incoming_trade_offer.receives
        ):
            return True
        else:
            return False
        # return super().on_trade_offer(incoming_trade_offer)

    def on_turn_start(self):

        self.turnoActual = self.turnoActual + 1
        # print(str(self.turnoActual))
        # Si tiene mano de cartas de desarrollo
        if len(self.development_cards_hand.check_hand()) == 0:
            return None

        knight_cards = (
            self.development_cards_hand.select_cards_by_development_card_type(
                DevelopmentCardConstants.KNIGHT_EFFECT
            )
        )
        progress_cards = (
            self.development_cards_hand.select_cards_by_development_card_type(
                DevelopmentCardConstants.YEAR_OF_PLENTY_EFFECT
            )
        )
        monopoly_cards = (
            self.development_cards_hand.select_cards_by_development_card_type(
                DevelopmentCardConstants.MONOPOLY_EFFECT
            )
        )
        CO = BuildConstants.TOWN
        if self.compraObjetivo is not None:
            CO = self.compraObjetivo
        totlaDiff, _ = self.materialesNecesarios(CO)

        play_knight_card = (
            self.check_thief_is_in_one_of_my_terrains() * self.PESO_TOCHO
            + self.competitivo
        ) * (len(knight_cards) > 0) - (totlaDiff / 2) * (
            len(progress_cards) > 0 or len(monopoly_cards) > 0
        )

        if play_knight_card > 0:
            return self.development_cards_hand.select_card_by_id(knight_cards[0].id)

        return None

    def any_player_with_the_required_material(self, max_material_idx, p=0.25):
        for player_id, other_players_hand in self.player_hand_of_each_player.items():
            other_players_materials = other_players_hand.resources
            total_materials = sum(other_players_materials.get_materials())
            if total_materials == 0:
                continue
            if other_players_hand.get_from_id(max_material_idx) / total_materials > p:
                return True
        return False

    def on_having_more_than_7_materials_when_thief_is_called(self):
        # Comprueba si tiene materiales para construir una ciudad. Si los tiene, descarta el resto que no le sirvan.
        CO = self.compra_objetivo(self.board)
        _, materiales_necesarios = self.materialesNecesarios(CO)
        
        temp_hand = Hand(resources=materiales_necesarios)
        while self.hand.get_total() > 7:
            materiales_amount_with_idx = max(enumerate(temp_hand.resources.get_array_ids()), key=lambda x:x[1])
            most_frequent_material_idx, most_frequent_material = materiales_amount_with_idx
            self.hand.remove_material(most_frequent_material_idx, 1)
            temp_hand.remove_material(most_frequent_material_idx, 1)
        return self.hand

    def on_moving_thief(self):
        # Bloquea un número 6 u 8 donde no tenga un pueblo, pero que tenga uno del rival
        # Si no se dan las condiciones lo deja donde está, lo que hace que el GameManager lo ponga en un lugar aleatorio
        if self.compraObjetivo is None:
            self.compraObjetivo = self.compra_objetivo(self.board)
        requested_material_id, requested_material = self.get_most_requested_material_for_compra_objetivo(self.compraObjetivo)
        players_hand_materials_with_probability = self.get_probability_for_materials_given_player_hands()

        #Crear una EDA dict {terrain_id:puntos}
        #Sacar dnd más pueda putear
        #Ver a quien puedo putear más
        eda = self.__VTE__()
        terrain_with_thief_id, values_for_putting_thief_here = max(eda.items(), key=lambda x: x[1])
        player_ids = list(filter(lambda x: x != self.id ,self.board.get_players_adjacent_to_terrain(terrain_with_thief_id)))
        
                # get the one with the most resources
        terrain_with_thief_id, values_for_putting_thief_here = max(
            eda.items(), key=lambda x: x[1]
        )
        #Get all players ids adjacent to a terrain
        player_ids = list(
            filter(
                lambda x: x != self.id,
                self.board.get_players_adjacent_to_terrain(terrain_with_thief_id),
            )
        )
        #List((int, list)) 
        target_enemy_players = [
            (player_id, prob_for_card)
            for player_id, prob_for_card in players_hand_materials_with_probability.items()
            if player_id in player_ids
        ]
        #Get the player with the most resources in that area
        target_enemy_player_id, _ = max(
            target_enemy_players, key=lambda x: x[1][requested_material_id]
        )
        return {"terrain": terrain_with_thief_id, "player": target_enemy_player_id}

    def on_turn_end(self):
        # Si tiene mano de cartas de desarrollo
        if len(self.development_cards_hand.check_hand()):
            # Mira todas las cartas
            for i in range(0, len(self.development_cards_hand.check_hand())):
                # Si una es un punto de victoria
                if (
                    self.development_cards_hand.hand[i].type
                    == DevelopmentCardConstants.VICTORY_POINT
                ):
                    # La juega
                    return self.development_cards_hand.select_card_by_id(
                        self.development_cards_hand.hand[i].id
                    )
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
                    if (
                        self.development_cards_hand.hand[i].effect
                        == DevelopmentCardConstants.MONOPOLY_EFFECT
                    ):
                        # La juega
                        return self.development_cards_hand.select_card_by_id(
                            self.development_cards_hand.hand[i].id
                        )

        gives = Materials()
        receives = Materials()

        # No pide nada porque puede hacer una ciudad
        if self.town_number >= 1 and self.hand.resources.has_this_more_materials(
            BuildConstants.CITY
        ):
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
                    order = [
                        MaterialConstants.CLAY,
                        MaterialConstants.WOOD,
                        MaterialConstants.WOOL,
                    ]
                    random.shuffle(order)
                    # una vez mezclado se recorre el orden de los materiales y se coge el primero que tenga un valor
                    for mat in order:
                        if self.hand.resources.get_from_id(mat) > 0:
                            self.hand.remove_material(mat, 1)
                            materials_to_give[mat] += 1
                            break
                gives = Materials(
                    materials_to_give[0],
                    materials_to_give[1],
                    materials_to_give[2],
                    materials_to_give[3],
                    materials_to_give[4],
                )

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
                    order = [
                        MaterialConstants.CEREAL,
                        MaterialConstants.MINERAL,
                        MaterialConstants.CLAY,
                        MaterialConstants.WOOD,
                        MaterialConstants.WOOL,
                    ]
                    random.shuffle(order)
                    # una vez mezclado se recorre el orden de los materiales y se coge el primero que tenga un valor
                    for mat in order:
                        if (
                            self.hand.resources.get_from_id(mat) > 1
                            or mat == MaterialConstants.MINERAL
                        ):
                            self.hand.remove_material(mat, 1)
                            materials_to_give[mat] += 1
                            break

                gives = Materials(
                    materials_to_give[0],
                    materials_to_give[1],
                    materials_to_give[2],
                    materials_to_give[3],
                    materials_to_give[4],
                )
                receives = Materials(
                    materials_to_receive[0],
                    materials_to_receive[1],
                    materials_to_receive[2],
                    materials_to_receive[3],
                    materials_to_receive[4],
                )

        trade_offer = TradeOffer(gives, receives)
        return trade_offer

    def on_build_phase(self, board_instance):
        # Juega año de la cosecha si le faltan 2 o 1 materiales para completar una construcción
        # Juega construir carreteras si le da para camino más largo o con ello puede alcanzar un puerto (que no tenga)
        # Juega Monopoli si solo necesita un tipo de material
        self.board = board_instance
        self.compraObjetivo = self.compra_objetivo(self.board)
        # print(self.compraObjetivo)
        total, materialesNecesarios = self.materialesNecesarios(self.compraObjetivo)
        contadorMatDiferentesNecesarios = 0
        for mat in materialesNecesarios.get_array_ids():
            if mat != 0:
                contadorMatDiferentesNecesarios = contadorMatDiferentesNecesarios + 1
        # Si tiene mano de cartas de desarrollo
        if len(self.development_cards_hand.check_hand()):
            # Mira todas las cartas
            for i in range(0, len(self.development_cards_hand.check_hand())):
                # Comprueba primero de que hay más de 2 carreteras disponibles para construirlas
                road_possibilities = self.board.valid_road_nodes(self.id)

                # Si una es año de la cosecha o construir carreteras y hay al menos 2 carreteras disponibles a construir
                if (
                    self.development_cards_hand.hand[i].effect
                    == DevelopmentCardConstants.YEAR_OF_PLENTY_EFFECT
                    and total < 3
                ):
                    # La juega
                    return self.development_cards_hand.select_card_by_id(
                        self.development_cards_hand.hand[i].id
                    )
                if (
                    self.development_cards_hand.hand[i].effect
                    == DevelopmentCardConstants.ROAD_BUILDING_EFFECT
                    and len(road_possibilities) > 1
                ):
                    return self.development_cards_hand.select_card_by_id(
                        self.development_cards_hand.hand[i].id
                    )
                if (
                    self.development_cards_hand.hand[i].effect
                    == DevelopmentCardConstants.YEAR_OF_PLENTY_EFFECT
                    and contadorMatDiferentesNecesarios == 1
                ):
                    return self.development_cards_hand.select_card_by_id(
                        self.development_cards_hand.hand[i].id
                    )

        if total == 0:
            return self.construyeCompraObjetivo()

        matActuales = sum(self.hand.resources.get_array_ids())
        if matActuales > 6:
            return self.construyeSobras()
        return None

    def on_game_start(self, board_instance):  # VT version

        # VT o VT+ o VTT+
        # Plantar en la casilla de más valor disponible
        self.board = board_instance
        possibilities = self.board.valid_starting_nodes()
        currentArrayTerrain = self.__CR__(self.board.nodes)[self.id]
        bestNode = self.__getBestScoreNode__(currentArrayTerrain, possibilities)
        possible_roads = self.board.nodes[bestNode]["adjacent"]

        return bestNode, possible_roads[random.randint(0, len(possible_roads) - 1)]

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
                    return {
                        "node_id": valid_nodes[road_node]["starting_node"],
                        "road_to": valid_nodes[road_node]["finishing_node"],
                        "node_id_2": valid_nodes[road_node_2]["starting_node"],
                        "road_to_2": valid_nodes[road_node_2]["finishing_node"],
                    }
        elif len(valid_nodes) == 1:
            return {
                "node_id": valid_nodes[0]["starting_node"],
                "road_to": valid_nodes[0]["finishing_node"],
                "node_id_2": None,
                "road_to_2": None,
            }
        return None

    def on_year_of_plenty_card_use(self):
        return {
            "material": self.year_of_plenty_material_one,
            "material_2": self.year_of_plenty_material_two,
        }

    def __VT__(self, nodes):
        dictNode = {}
        for node in nodes:
            terrains = self.board.__get_contacting_terrain__(node)
            nodeProb = 0
            for terrain in terrains:
                nodeProb = nodeProb + self.__CalculateProb__(
                    self.board.__get_probability__(terrain)
                )
            dictNode[node] = nodeProb
        return dictNode

    def __VTPlus__(self, nodes):
        dictNode = {}
        for node in nodes:
            terrains = self.board.__get_contacting_terrain__(node)
            nodeProb = 0
            arrayTypes = [0, 0, 0, 0, 0]
            for terrain in terrains:
                terrainType = self.board.__get_terrain_type__(terrain)
                arrayTypes[terrainType] = arrayTypes[
                    terrainType
                ] + self.__CalculateProb__(self.board.__get_probability__(terrain))
            dictNode[node] = arrayTypes
        return dictNode

    def __VTE__(self):
        terrains = self.board.terrain
        res = {}
        for terrain in terrains:
            prob_for_terrain = self.__CalculateProb__(self.board.__get_probability__(terrain["id"])) #get_prob * cal
            val = 0
            #Por cada nodo adjacente a un terreno
            node_ids_by_terrain_ids = self.board.__get_contacting_nodes__(terrain["id"])
            nodes = [self.board.get_nodes_by_id(id) for id in node_ids_by_terrain_ids]
            for node in nodes:
                mult = 0
                if node["player"] >= 0:
                    mult = 1
                if node["has_city"]:
                    mult = 2
                if node["player"] == self.id:
                    mult = -1 * mult

                val += mult * prob_for_terrain
            res[terrain["id"]] = val
        return res

    def __CR__(self, nodes):
        arrayPlayer0 = [0, 0, 0, 0, 0]
        arrayPlayer1 = [0, 0, 0, 0, 0]
        arrayPlayer2 = [0, 0, 0, 0, 0]
        arrayPlayer3 = [0, 0, 0, 0, 0]
        playersArrays = [arrayPlayer0, arrayPlayer1, arrayPlayer2, arrayPlayer3]
        for node in nodes:
            if node["player"] >= 0:
                arrayPlayer = playersArrays[node["player"]]
                terrains = self.board.__get_contacting_terrain__(node["id"])
                nodeProb = 0
                arrayTypes = [0, 0, 0, 0, 0]
                for terrain in terrains:
                    terrainType = self.board.__get_terrain_type__(terrain)
                    arrayTypes[terrainType] = arrayTypes[
                        terrainType
                    ] + self.__CalculateProb__(self.board.__get_probability__(terrain))
                arrayPlayer = [x + y for x, y in zip(arrayTypes, arrayPlayer)]
                playersArrays[node["player"]] = arrayPlayer
        return playersArrays

    def __CalculateProb__(self, node_number):
        if node_number > 0:
            if node_number > 7:
                return 13 - node_number
            elif node_number < 7:
                return node_number - 1
        return 0

    def __nodeScore__(self, node, nodeArray, currentArray, mode=BuildConstants.TOWN):
        # Añadir self.board__get_harbors__(node) is not None: \ puntuaction = + algo Genetico?
        possible_array = [x + y for x, y in zip(nodeArray, currentArray)]
        suma_total = sum(possible_array)
        desviacion_estandar = np.std(possible_array)
        puntuacion = suma_total - desviacion_estandar
        harbor_type = self.board.__get_harbors__(node)
        if mode != BuildConstants.CITY and harbor_type != HarborConstants.NONE:
            if harbor_type < 5:
                puntuacion = puntuacion + currentArray[harbor_type] * 2 * self.GustoMar
            else:
                puntuacion = puntuacion + suma_total * 4 / 3 * self.GustoMar
        elif mode == BuildConstants.ROAD and self.board.is_it_a_coastal_node(node):
            puntuacion = puntuacion + 5 * self.GustoMar + 2 * self.GustoPoblado
        return puntuacion

    def __getBestScoreNode__(self, currentArray, nodes, mode=BuildConstants.TOWN):
        bestScore = 0
        bestNode = -1
        for node in nodes:
            terrains = self.board.__get_contacting_terrain__(node)
            nodeProb = 0
            arrayTypes = [0, 0, 0, 0, 0]
            for terrain in terrains:
                terrainType = self.board.__get_terrain_type__(terrain)
                arrayTypes[terrainType] = arrayTypes[
                    terrainType
                ] + self.__CalculateProb__(self.board.__get_probability__(terrain))
            score = self.__nodeScore__(node, arrayTypes, currentArray, mode)
            if score > bestScore:
                bestScore = score
                bestNode = node
        return bestNode

    def materialesNecesarios(self, buildConstant_type):
        """Dado un string, te indica los materiales que te faltan de cada tipo para
            completar la compra

        Args:
            buildConstant_type (str): Str proveniente de DevelopmentCardConstants

        Returns:
            tuple: (Total diff, Materiales que me faltan)
        """
        if buildConstant_type == "town":
            materials = Materials(1, 0, 1, 1, 1)
        elif buildConstant_type == "city":
            materials = Materials(2, 3, 0, 0, 0)
        elif buildConstant_type == "road":
            materials = Materials(0, 0, 1, 1, 0)
        elif buildConstant_type == "card":
            materials = Materials(1, 1, 0, 0, 1)
        else:
            return False
        arrayObjetivo = (
            materials.get_array_ids()
        )  # Puede ser que sea necesario crear un getArrayids
        arrayActual = self.hand.resources.get_array_ids()
        diff = [0, 0, 0, 0, 0]
        totalDiff = 0
        step = 0
        i = 0

        for i in range(len(arrayObjetivo)):
            step = arrayActual[i] - arrayObjetivo[i]
            diff[i] = step
            if step < 0:
                totalDiff = totalDiff + step

        return -totalDiff, Materials(diff[0], diff[1], diff[2], diff[3], diff[4])

    def calcula_BeneficiosCoste(self, arrayCostes, arrayBeneficios):
        i = 0
        resultado = 0
        for coste in arrayCostes:
            if coste < 0:
                resultado = resultado + arrayBeneficios[i] / (-coste)
            else:
                resultado = resultado + arrayBeneficios[i] * 3
            i = i + 1
        return resultado

    def compra_objetivo(self, board):
        # Variables Alg Genetico = GustoCiudad,GustoPoblado,GustoCarretera,GustoDesarrollo,timechange,timechange2,timechange3, importanciaTiempo
        townPossibilities = self.board.valid_town_nodes(self.id)
        cityPossibilities = self.board.valid_city_nodes(self.id)
        # print("townPossibilities: "+str(townPossibilities)+" city: "+str(cityPossibilities))
        # print("Time change diff "+ str(self.importanciaTiempo-min((self.turnoActual/(35*self.timeChange)*self.importanciaTiempo),self.importanciaTiempo*2)))
        materialesCiudad = self.hand.resources.has_this_more_materials(
            BuildConstants.CITY
        )
        Vt = self.__CR__(board.nodes)[self.id]
        if cityPossibilities and townPossibilities:
            Cc, arrayCosteCiudad = self.materialesNecesarios(BuildConstants.CITY)
            Cp, arrayCostePueblo = self.materialesNecesarios(BuildConstants.TOWN)
            arrayCosteCiudad = arrayCosteCiudad.get_array_ids()
            arrayCostePueblo = arrayCostePueblo.get_array_ids()
            Cc = self.calcula_BeneficiosCoste(arrayCosteCiudad, Vt)
            Cp = self.calcula_BeneficiosCoste(arrayCostePueblo, Vt)
            result = (
                self.GustoCiudad * Cc
                - self.GustoPoblado * Cp
                - (
                    self.importanciaTiempo
                    - min(
                        (
                            self.turnoActual
                            / (35 * self.timeChange)
                            * self.importanciaTiempo
                        ),
                        self.importanciaTiempo * 2,
                    )
                )
            )
            # print("CC"+str(Cc)+" CP"+str(Cp))
            if result > 0:
                return BuildConstants.CITY
            else:
                return BuildConstants.TOWN
        elif townPossibilities:
            Cd, arrayCosteDesarrollo = self.materialesNecesarios(BuildConstants.CARD)
            Cp, arrayCostePueblo = self.materialesNecesarios(BuildConstants.TOWN)
            arrayCosteDesarrollo = arrayCosteDesarrollo.get_array_ids()
            arrayCostePueblo = arrayCostePueblo.get_array_ids()
            Cd = self.calcula_BeneficiosCoste(arrayCosteDesarrollo, Vt)
            Cp = self.calcula_BeneficiosCoste(arrayCostePueblo, Vt)
            # print("Cd"+str(Cd)+" CP"+str(Cp))
            result = (
                self.GustoCiudad * Cd
                - self.GustoPoblado * 2 * Cp
                - (
                    self.importanciaTiempo
                    - min(
                        (
                            self.turnoActual
                            / (35 * self.timeChange)
                            * self.importanciaTiempo
                        ),
                        self.importanciaTiempo * 2,
                    )
                )
            )
            if result > 0:
                return BuildConstants.CARD
            else:
                return BuildConstants.TOWN
        elif cityPossibilities:
            carreteraConstruible = 0
            if len(board.valid_road_nodes(self.id)) > 0:
                carreteraConstruible = 1
            Cc, arrayCosteCiudad = self.materialesNecesarios(BuildConstants.CITY)
            Cr, arrayCosteCarretera = self.materialesNecesarios(BuildConstants.ROAD)
            arrayCosteCiudad = arrayCosteCiudad.get_array_ids()
            arrayCosteCarretera = arrayCosteCarretera.get_array_ids()
            Cc = self.calcula_BeneficiosCoste(arrayCosteCiudad, Vt)
            Cr = self.calcula_BeneficiosCoste(arrayCosteCarretera, Vt)
            # print("CC"+str(Cc)+" Cr"+str(Cr))
            result = (
                self.GustoCiudad * Cc
                - self.GustoPoblado * Cr * carreteraConstruible
                - (
                    self.importanciaTiempo
                    - min(
                        (
                            self.turnoActual
                            / (35 * self.timeChange)
                            * self.importanciaTiempo
                        ),
                        self.importanciaTiempo * 2,
                    )
                )
            )
            if result > 0:
                return BuildConstants.CITY
            else:
                return BuildConstants.ROAD
        else:
            carreteraConstruible = 0
            if len(board.valid_road_nodes(self.id)) > 0:
                carreteraConstruible = 1
            Cd, arrayCosteDesarrollo = self.materialesNecesarios(BuildConstants.CARD)
            Cr, arrayCosteCarretera = self.materialesNecesarios(BuildConstants.ROAD)
            arrayCosteDesarrollo = arrayCosteDesarrollo.get_array_ids()
            arrayCosteCarretera = arrayCosteCarretera.get_array_ids()
            Cd = self.calcula_BeneficiosCoste(arrayCosteDesarrollo, Vt)
            Cr = self.calcula_BeneficiosCoste(arrayCosteCarretera, Vt)
            result = (
                self.GustoCiudad * Cd - self.GustoPoblado * Cr * carreteraConstruible
            )
            # print("Cd"+str(Cd)+" Cr"+str(Cr))
            if result > 0:
                return BuildConstants.CARD
            else:
                return BuildConstants.ROAD

    def construyeCompraObjetivo(self):
        if self.compraObjetivo == BuildConstants.CARD:
            return {"building": BuildConstants.CARD}
        if self.compraObjetivo == BuildConstants.ROAD:
            nodes = self.board.valid_road_nodes(self.id)
            if len(nodes) == 0:
                return None
            node_id, road_to = self.mejorCarretera(nodes)
            return {
                "building": BuildConstants.ROAD,
                "node_id": node_id,
                "road_to": road_to,
            }
        currentArrayTerrain = self.__CR__(self.board.nodes)[self.id]
        if self.compraObjetivo == BuildConstants.TOWN:
            nodes = self.board.valid_town_nodes(self.id)
            node_id = self.__getBestScoreNode__(
                currentArrayTerrain, nodes, BuildConstants.TOWN
            )
            return {"building": BuildConstants.TOWN, "node_id": node_id}
        if self.compraObjetivo == BuildConstants.CITY:
            nodes = self.board.valid_city_nodes(self.id)
            node_id = self.__getBestScoreNode__(
                currentArrayTerrain, nodes, BuildConstants.CITY
            )
            return {"building": BuildConstants.CITY, "node_id": node_id}
        return None

    def mejorCarretera(self, nodes):
        currentArrayTerrain = self.__CR__(self.board.nodes)[self.id]
        nodes_to = [diccionario["finishing_node"] for diccionario in nodes]
        road_to = self.__getBestScoreNode__(
            currentArrayTerrain, nodes_to, BuildConstants.ROAD
        )
        for diccionario in nodes:
            if diccionario["finishing_node"] == road_to:
                node_id = diccionario["starting_node"]
                break
        return node_id, road_to

    def construyeSobras(self):
        if (
            self.hand.resources.has_this_more_materials(BuildConstants.CARD)
            and self.compraObjetivo != BuildConstants.CITY
        ):
            return {"building": BuildConstants.CARD}
        if self.hand.resources.has_this_more_materials(BuildConstants.ROAD):
            nodes = self.board.valid_road_nodes(self.id)
            if len(nodes) == 0:
                return None
            node_id, road_to = self.mejorCarretera(nodes)
            return {
                "building": BuildConstants.ROAD,
                "node_id": node_id,
                "road_to": road_to,
            }

        nodes = self.board.valid_town_nodes(self.id)
        if len(nodes) > 0:
            currentArrayTerrain = self.__CR__(self.board.nodes)[self.id]
            node_id = self.__getBestScoreNode__(
                currentArrayTerrain, nodes, BuildConstants.TOWN
            )
            return {"building": BuildConstants.TOWN, "node_id": node_id}

        nodes = self.board.valid_city_nodes(self.id)
        if len(nodes) > 0:
            currentArrayTerrain = self.__CR__(self.board.nodes)[self.id]
            node_id = self.__getBestScoreNode__(
                currentArrayTerrain, nodes, BuildConstants.CITY
            )
            return {"building": BuildConstants.CITY, "node_id": node_id}

        return None

    def get_most_requested_material_for_compra_objetivo(self, compra_objetivo):
        _, materiales_necesarios = self.materialesNecesarios(compra_objetivo)
        materiales_necesarios_formato_lista = [
            (material_id, amount_of_material)
            for material_id, amount_of_material in enumerate(
                materiales_necesarios.get_array_ids()
            )
        ]
        # we need the minimum resource
        material_id, material_amount = min(
            materiales_necesarios_formato_lista, key=lambda x: x[1]
        )
        return material_id, material_amount

    def get_probability_for_materials_given_player_hands(self):
        from_total_to_prob_given_a_hand = lambda lst: (
            [l / sum(lst) for l in lst] if sum(lst) > 0 else lst
        )
        return {
            k: from_total_to_prob_given_a_hand(v.resources.get_array_ids())
            for k, v in self.player_hand_of_each_player.items()
        }

    def check_thief_is_in_one_of_my_terrains(self):
        # Todos nuestros nodos
        player_nodes = [node for node in self.board.nodes if node["player"] == self.id]
        # Todos nuestros terrenos
        player_terrains_id = []
        for node in player_nodes:
            player_terrains_id.extend(self.board.__get_contacting_terrain__(node["id"]))
        # Id -> Terrains
        player_terrains = [
            self.board.get_terrain_by_id(terrain_id)
            for terrain_id in player_terrains_id
        ]
        # Si el ladrón está en alguno de nuestros terrenos
        return any([terrain["has_thief"] for terrain in player_terrains])
